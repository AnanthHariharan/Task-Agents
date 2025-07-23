#!/usr/bin/env python3

import json
import re
from typing import List, Dict, Any, Set, Tuple
from dataclasses import dataclass
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from shared.utils.action_utils import ActionParser
from shared.utils.logging_utils import LoggerMixin

@dataclass
class GroundTruthAnnotation:
    """Ground truth annotation for recall/precision evaluation"""
    action_index: int
    action_text: str
    should_remove: bool
    remove_reason: str = ""
    is_missing_requirement: bool = False
    missing_description: str = ""

@dataclass
class PredictionResult:
    """Prediction result from a judge"""
    action_index: int
    action_text: str
    predicted_remove: bool
    predicted_reason: str = ""
    confidence: float = 1.0

@dataclass
class EvaluationMetrics:
    """Recall and precision metrics"""
    recall: float
    precision: float
    f1_score: float
    true_positives: int
    false_positives: int
    false_negatives: int
    true_negatives: int

class RecallPrecisionEvaluator(LoggerMixin):
    """Evaluates recall and precision for judge predictions"""
    
    def __init__(self):
        # Load ground truth annotations if available
        self.ground_truth_cache = {}
        
        # Define patterns for automatic ground truth generation
        self.automatic_removal_patterns = {
            'toggle_off_before_on': {
                'pattern': r'ToggleOff.*before.*ToggleOn',
                'confidence': 0.95
            },
            'duplicate_pickup': {
                'pattern': r'PickUp.*same.*object',
                'confidence': 0.90
            },
            'contradictory_moves': {
                'pattern': r'Move.*cancel.*each.*other',
                'confidence': 0.85
            },
            'irrelevant_object': {
                'pattern': r'PickUp.*irrelevant.*object',
                'confidence': 0.80
            }
        }
    
    def evaluate_judge_performance(self, 
                                 judge_predictions: List[Dict[str, Any]], 
                                 ground_truth: List[GroundTruthAnnotation]) -> EvaluationMetrics:
        """
        Evaluate judge performance against ground truth
        
        Args:
            judge_predictions: List of judge prediction results
            ground_truth: List of ground truth annotations
            
        Returns:
            EvaluationMetrics with recall, precision, F1
        """
        self.logger.info(f"Evaluating judge performance on {len(judge_predictions)} predictions")
        
        # Convert predictions to binary classification format
        predicted_removals = set()
        actual_removals = set()
        
        # Process predictions
        for pred in judge_predictions:
            action_idx = pred.get('action_index', -1)
            if pred.get('predicted_remove', False):
                predicted_removals.add(action_idx)
        
        # Process ground truth
        for gt in ground_truth:
            if gt.should_remove:
                actual_removals.add(gt.action_index)
        
        # Calculate confusion matrix
        all_indices = set(range(len(judge_predictions)))
        
        tp = len(predicted_removals.intersection(actual_removals))
        fp = len(predicted_removals - actual_removals)
        fn = len(actual_removals - predicted_removals)
        tn = len(all_indices - predicted_removals - actual_removals)
        
        # Calculate metrics
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        
        return EvaluationMetrics(
            recall=recall,
            precision=precision,
            f1_score=f1_score,
            true_positives=tp,
            false_positives=fp,
            false_negatives=fn,
            true_negatives=tn
        )
    
    def generate_ground_truth_from_sequence(self, 
                                          action_sequence: List[str], 
                                          goal: str) -> List[GroundTruthAnnotation]:
        """
        Generate ground truth annotations for an action sequence using heuristics
        
        This is used when manual annotations are not available
        """
        self.logger.info(f"Generating ground truth for sequence with {len(action_sequence)} actions")
        
        ground_truth = []
        parsed_actions = [ActionParser.parse_action(action) for action in action_sequence]
        
        # Rule 1: ToggleOff before any ToggleOn
        device_states = {}
        for i, parsed in enumerate(parsed_actions):
            if parsed['valid'] and parsed['method'] in ['ToggleOn', 'ToggleOff'] and parsed['arguments']:
                device = parsed['arguments'][0]
                if device not in device_states:
                    device_states[device] = []
                device_states[device].append((i, parsed['method']))
        
        for device, actions in device_states.items():
            if actions and actions[0][1] == 'ToggleOff':
                ground_truth.append(GroundTruthAnnotation(
                    action_index=actions[0][0],
                    action_text=action_sequence[actions[0][0]],
                    should_remove=True,
                    remove_reason=f"unnecessary to turn off {device} when not turned on yet"
                ))
        
        # Rule 2: Duplicate pickups
        pickup_objects = {}
        for i, parsed in enumerate(parsed_actions):
            if parsed['valid'] and parsed['method'] == 'PickUp' and parsed['arguments']:
                obj = parsed['arguments'][0]
                if obj not in pickup_objects:
                    pickup_objects[obj] = []
                pickup_objects[obj].append(i)
        
        for obj, indices in pickup_objects.items():
            if len(indices) > 1:
                # Mark subsequent pickups as removals
                for idx in indices[1:]:
                    ground_truth.append(GroundTruthAnnotation(
                        action_index=idx,
                        action_text=action_sequence[idx],
                        should_remove=True,
                        remove_reason=f"already holding {obj}"
                    ))
        
        # Rule 3: Contradictory movements (simplified heuristic)
        move_actions = [(i, parsed) for i, parsed in enumerate(parsed_actions) 
                       if parsed['valid'] and parsed['method'] == 'Move']
        
        for i in range(len(move_actions) - 1):
            curr_idx, curr_action = move_actions[i]
            next_idx, next_action = move_actions[i + 1]
            
            if (next_idx == curr_idx + 1 and 
                curr_action['arguments'] and next_action['arguments']):
                try:
                    curr_dist = float(curr_action['arguments'][0])
                    next_dist = float(next_action['arguments'][0])
                    
                    if abs(curr_dist + next_dist) < 0.1:  # Cancel each other
                        ground_truth.extend([
                            GroundTruthAnnotation(
                                action_index=curr_idx,
                                action_text=action_sequence[curr_idx],
                                should_remove=True,
                                remove_reason="movement cancelled by next action"
                            ),
                            GroundTruthAnnotation(
                                action_index=next_idx,
                                action_text=action_sequence[next_idx],
                                should_remove=True,
                                remove_reason="cancels previous movement"
                            )
                        ])
                except ValueError:
                    pass
        
        self.logger.debug(f"Generated {len(ground_truth)} ground truth removals")
        return ground_truth
    
    def evaluate_one_shot_performance(self, 
                                    judge_results: Dict[str, Any], 
                                    action_sequence: List[str],
                                    goal: str) -> EvaluationMetrics:
        """
        Evaluate one-shot judge performance (without iterative feedback)
        """
        # Generate ground truth for this sequence
        ground_truth = self.generate_ground_truth_from_sequence(action_sequence, goal)
        
        # Convert judge results to prediction format
        predictions = []
        
        if 'annotated_actions' in judge_results:
            for i, annotated_action in enumerate(judge_results['annotated_actions']):
                predictions.append({
                    'action_index': i,
                    'action_text': annotated_action.get('action', ''),
                    'predicted_remove': annotated_action.get('remove', False),
                    'predicted_reason': annotated_action.get('remove_reason', '')
                })
        
        return self.evaluate_judge_performance(predictions, ground_truth)
    
    def create_performance_matrix(self, 
                                results: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
        """
        Create 4x4 performance matrix for planners vs judges
        
        Args:
            results: Nested dict {planner_name: {judge_name: evaluation_results}}
            
        Returns:
            Matrices for recall and precision
        """
        recall_matrix = {}
        precision_matrix = {}
        
        for planner_name, planner_results in results.items():
            recall_matrix[planner_name] = {}
            precision_matrix[planner_name] = {}
            
            for judge_name, judge_results in planner_results.items():
                if 'metrics' in judge_results:
                    metrics = judge_results['metrics']
                    recall_matrix[planner_name][judge_name] = metrics.recall * 100  # Convert to percentage
                    precision_matrix[planner_name][judge_name] = metrics.precision * 100
                else:
                    recall_matrix[planner_name][judge_name] = 0.0
                    precision_matrix[planner_name][judge_name] = 0.0
        
        return {
            'recall': recall_matrix,
            'precision': precision_matrix
        }
    
    def generate_latex_table(self, 
                           matrix: Dict[str, Dict[str, float]], 
                           metric_name: str) -> str:
        """Generate LaTeX table from performance matrix"""
        
        # Get all planner and judge names
        planners = list(matrix.keys())
        judges = list(matrix[planners[0]].keys()) if planners else []
        
        # Start LaTeX table
        latex = "\\begin{table}[h]\n\\centering\n"
        latex += f"\\caption{{{metric_name} (\\%) by Model Combination}}\n"
        latex += "\\begin{tabular}{l" + "c" * len(judges) + "}\n"
        latex += "\\toprule\n"
        
        # Header row
        latex += "\\textbf{Judge LLM} & \\multicolumn{" + str(len(judges)) + "}{c}{\\textbf{Planner LLM – " + metric_name + " (\\%)}} \\\\\n"
        latex += "\\cmidrule{2-" + str(len(judges) + 1) + "}\n"
        latex += " & " + " & ".join(judges) + " \\\\\n"
        latex += "\\midrule\n"
        
        # Data rows
        for planner in planners:
            row_values = []
            for judge in judges:
                value = matrix[planner][judge]
                # Bold the highest value in each row
                row_max = max(matrix[planner].values())
                if value == row_max and value > 0:
                    row_values.append(f"\\textbf{{{value:.0f}}}")
                else:
                    row_values.append(f"{value:.0f}")
            
            latex += f"{planner} & " + " & ".join(row_values) + " \\\\\n"
        
        latex += "\\bottomrule\n\\end{tabular}\n\\end{table}"
        
        return latex
    
    def analyze_error_patterns(self, 
                             predictions: List[Dict[str, Any]], 
                             ground_truth: List[GroundTruthAnnotation]) -> Dict[str, Any]:
        """Analyze common error patterns in predictions"""
        
        false_positives = []  # Predicted remove but shouldn't
        false_negatives = []  # Should remove but didn't predict
        
        # Create lookup dictionaries
        gt_dict = {gt.action_index: gt for gt in ground_truth}
        pred_dict = {pred['action_index']: pred for pred in predictions}
        
        # Find all action indices
        all_indices = set(gt_dict.keys()) | set(pred_dict.keys())
        
        for idx in all_indices:
            gt = gt_dict.get(idx)
            pred = pred_dict.get(idx, {'predicted_remove': False})
            
            should_remove = gt.should_remove if gt else False
            predicted_remove = pred.get('predicted_remove', False)
            
            if predicted_remove and not should_remove:
                false_positives.append({
                    'action_index': idx,
                    'predicted_reason': pred.get('predicted_reason', ''),
                    'action_text': pred.get('action_text', '')
                })
            
            elif should_remove and not predicted_remove:
                false_negatives.append({
                    'action_index': idx,
                    'correct_reason': gt.remove_reason if gt else '',
                    'action_text': gt.action_text if gt else ''
                })
        
        return {
            'false_positives': false_positives,
            'false_negatives': false_negatives,
            'fp_count': len(false_positives),
            'fn_count': len(false_negatives)
        }
    
    def save_evaluation_results(self, 
                              results: Dict[str, Any], 
                              output_path: str) -> None:
        """Save evaluation results to file"""
        
        # Convert any non-serializable objects
        serializable_results = self._make_serializable(results)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(serializable_results, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Evaluation results saved to {output_path}")
    
    def _make_serializable(self, obj: Any) -> Any:
        """Convert objects to JSON-serializable format"""
        if isinstance(obj, dict):
            return {k: self._make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_serializable(item) for item in obj]
        elif isinstance(obj, (GroundTruthAnnotation, EvaluationMetrics)):
            return obj.__dict__
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        else:
            return obj