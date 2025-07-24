#!/usr/bin/env python3

import json
import os
import sys
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from planning_agent.factory import PlannerFactory
from judge_llm.factory import JudgeFactory
from experiments.analysis.recall_precision_evaluator import RecallPrecisionEvaluator, EvaluationMetrics
from shared.utils.file_utils import FileManager
from shared.utils.logging_utils import setup_logging, LoggerMixin

class OneShotEvaluator(LoggerMixin):
    """
    Evaluates judge performance in one-shot mode (direct evaluation without iteration)
    
    This mode tests how well judges can identify issues in raw action sequences,
    similar to Table 1 in your paper showing direct judge performance.
    """
    
    def __init__(self, output_dir: str = "outputs/experiments/one_shot"):
        self.output_dir = output_dir
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.evaluator = RecallPrecisionEvaluator()
        
        # Setup logging
        self.logger = setup_logging(log_dir="logs")
        
        # Create output directory
        FileManager.ensure_dir(output_dir)
    
    def evaluate_raw_teach_plans(self, 
                                test_data: List[Dict[str, Any]], 
                                judges: Dict[str, Any] = None) -> Dict[str, EvaluationMetrics]:
        """
        Evaluate judges on raw TEACh plans (Table 1 equivalent)
        
        Args:
            test_data: List of action sequences from TEACh dataset
            judges: Dictionary of judge instances (if None, creates all)
            
        Returns:
            Dictionary mapping judge names to their evaluation metrics
        """
        self.logger.info("Evaluating raw TEACh plans (Table 1 equivalent)")
        
        if judges is None:
            judges = JudgeFactory.create_all_judges(include_rule_based=True)
        
        results = {}
        
        for judge_name, judge in judges.items():
            self.logger.info(f"Evaluating judge: {judge_name}")
            
            judge_metrics = []
            
            for i, test_sequence in enumerate(test_data):
                sequence_id = f"seq_{i:03d}"
                actions = test_sequence.get('actions', [])
                file_name = test_sequence.get('file', 'unknown')
                
                if not actions:
                    continue
                
                self.logger.debug(f"Processing {sequence_id}: {len(actions)} actions")
                
                # Generate goal annotation (using first available planner)
                goal = f"GOAL: Complete the task as specified"  # Default goal
                if 'goal' in test_sequence:
                    goal = test_sequence['goal']
                elif actions:
                    # Try to infer goal from dialogue
                    dialogue_actions = [action for action in actions if 'Say(' in action]
                    if dialogue_actions:
                        goal = f"GOAL: {dialogue_actions[0].split('Say(')[-1].split(')')[0].strip('\\'\"')}"
                
                try:
                    # One-shot judge evaluation
                    judge_results = judge.judge_plan(actions, goal)
                    
                    # Evaluate performance using recall/precision
                    metrics = self.evaluator.evaluate_one_shot_performance(
                        judge_results, actions, goal
                    )
                    
                    judge_metrics.append({
                        'sequence_id': sequence_id,
                        'file': file_name,
                        'metrics': metrics,
                        'judge_results': judge_results
                    })
                    
                except Exception as e:
                    self.logger.error(f"Error evaluating {judge_name} on {sequence_id}: {e}")
                    continue
            
            # Aggregate metrics for this judge
            if judge_metrics:
                avg_metrics = self._aggregate_metrics([item['metrics'] for item in judge_metrics])
                results[judge_name] = {
                    'aggregated_metrics': avg_metrics,
                    'individual_results': judge_metrics,
                    'total_sequences': len(judge_metrics)
                }
                
                self.logger.info(f"{judge_name} - Recall: {avg_metrics.recall:.2%}, "
                                f"Precision: {avg_metrics.precision:.2%}")
            else:
                self.logger.warning(f"No valid results for judge: {judge_name}")
        
        return results
    
    def evaluate_planner_judge_matrix(self, 
                                    test_data: List[Dict[str, Any]],
                                    planners: Dict[str, Any] = None,
                                    judges: Dict[str, Any] = None) -> Dict[str, Dict[str, EvaluationMetrics]]:
        """
        Evaluate 4x4 planner-judge matrix (equivalent to your paper's tables)
        
        This tests each judge's ability to evaluate plans modified by different planners.
        """
        self.logger.info("Evaluating 4x4 planner-judge matrix")
        
        if planners is None:
            planners = PlannerFactory.create_all_planners(include_rule_based=True)
        if judges is None:
            judges = JudgeFactory.create_all_judges(include_rule_based=True)
        
        matrix_results = {}
        
        for planner_name, planner in planners.items():
            matrix_results[planner_name] = {}
            self.logger.info(f"Processing planner: {planner_name}")
            
            for judge_name, judge in judges.items():
                self.logger.info(f"  Evaluating with judge: {judge_name}")
                
                combination_metrics = []
                
                for i, test_sequence in enumerate(test_data):
                    sequence_id = f"seq_{i:03d}"
                    original_actions = test_sequence.get('actions', [])
                    file_name = test_sequence.get('file', 'unknown')
                    
                    if not original_actions:
                        continue
                    
                    try:
                        # Step 1: Planner generates goal and potentially modifies plan
                        goal = planner.annotate_goal(original_actions, file_name)
                        
                        # For one-shot, we don't do iterative modification, 
                        # just use the original plan with planner's goal
                        modified_actions = original_actions.copy()
                        
                        # Step 2: Judge evaluates the plan
                        judge_results = judge.judge_plan(modified_actions, goal)
                        
                        # Step 3: Evaluate judge's performance
                        metrics = self.evaluator.evaluate_one_shot_performance(
                            judge_results, modified_actions, goal
                        )
                        
                        combination_metrics.append({
                            'sequence_id': sequence_id,
                            'file': file_name,
                            'goal': goal,
                            'metrics': metrics,
                            'judge_results': judge_results
                        })
                        
                    except Exception as e:
                        self.logger.error(f"Error in {planner_name}+{judge_name} "
                                        f"on {sequence_id}: {e}")
                        continue
                
                # Aggregate results for this combination
                if combination_metrics:
                    avg_metrics = self._aggregate_metrics([item['metrics'] for item in combination_metrics])
                    matrix_results[planner_name][judge_name] = {
                        'aggregated_metrics': avg_metrics,
                        'individual_results': combination_metrics,
                        'total_sequences': len(combination_metrics)
                    }
                    
                    self.logger.debug(f"{planner_name}+{judge_name} - "
                                    f"Recall: {avg_metrics.recall:.2%}, "
                                    f"Precision: {avg_metrics.precision:.2%}")
                else:
                    self.logger.warning(f"No valid results for {planner_name}+{judge_name}")
        
        return matrix_results
    
    def _aggregate_metrics(self, metrics_list: List[EvaluationMetrics]) -> EvaluationMetrics:
        """Aggregate multiple evaluation metrics"""
        if not metrics_list:
            return EvaluationMetrics(0.0, 0.0, 0.0, 0, 0, 0, 0)
        
        # Sum up confusion matrix elements
        total_tp = sum(m.true_positives for m in metrics_list)
        total_fp = sum(m.false_positives for m in metrics_list)
        total_fn = sum(m.false_negatives for m in metrics_list)
        total_tn = sum(m.true_negatives for m in metrics_list)
        
        # Calculate aggregate metrics
        recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0
        precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        
        return EvaluationMetrics(
            recall=recall,
            precision=precision,
            f1_score=f1_score,
            true_positives=total_tp,
            false_positives=total_fp,
            false_negatives=total_fn,
            true_negatives=total_tn
        )
    
    def generate_paper_tables(self, 
                            raw_results: Dict[str, Any], 
                            matrix_results: Dict[str, Dict[str, Any]]) -> Dict[str, str]:
        """Generate LaTeX tables matching your paper format"""
        
        tables = {}
        
        # Table 1: Raw TEACh plan evaluation
        if raw_results:
            table1_data = {}
            for judge_name, results in raw_results.items():
                metrics = results['aggregated_metrics']
                # Convert judge names to paper format
                display_name = self._format_judge_name(judge_name)
                table1_data[display_name] = {
                    'recall': metrics.recall * 100,
                    'precision': metrics.precision * 100
                }
            
            tables['table1'] = self._generate_table1_latex(table1_data)
        
        # Table 2 & 3: 4x4 matrix (Recall and Precision)
        if matrix_results:
            matrices = self.evaluator.create_performance_matrix(
                {planner: {judge: results['aggregated_metrics'] 
                          for judge, results in judge_results.items()}
                 for planner, judge_results in matrix_results.items()}
            )
            
            # Format names for display
            formatted_matrices = self._format_matrix_names(matrices)
            
            tables['table2_recall'] = self.evaluator.generate_latex_table(
                formatted_matrices['recall'], 'Recall'
            )
            tables['table3_precision'] = self.evaluator.generate_latex_table(
                formatted_matrices['precision'], 'Precision'
            )
        
        return tables
    
    def _format_judge_name(self, judge_name: str) -> str:
        """Format judge name for paper display"""
        name_mapping = {
            'openai': 'GPT-4o-mini',
            'deepseek': 'DeepSeek-R1',
            'gemini': 'Gemini 2.5',
            'llama': 'LLaMA 4 Scout',
            'rule_based': 'Rule-based'
        }
        return name_mapping.get(judge_name, judge_name)
    
    def _format_matrix_names(self, matrices: Dict[str, Dict[str, Dict[str, float]]]) -> Dict[str, Dict[str, Dict[str, float]]]:
        """Format all names in the matrices for paper display"""
        formatted = {}
        
        for metric_name, matrix in matrices.items():
            formatted[metric_name] = {}
            for planner_name, planner_data in matrix.items():
                formatted_planner = self._format_judge_name(planner_name)
                formatted[metric_name][formatted_planner] = {}
                
                for judge_name, value in planner_data.items():
                    formatted_judge = self._format_judge_name(judge_name)
                    formatted[metric_name][formatted_planner][formatted_judge] = value
        
        return formatted
    
    def _generate_table1_latex(self, data: Dict[str, Dict[str, float]]) -> str:
        """Generate Table 1 LaTeX (raw TEACh plan evaluation)"""
        latex = "\\begin{table}[h]\n\\centering\n"
        latex += "\\caption{Judge LLM Performance on Raw TEACh Plans}\n"
        latex += "\\begin{tabular}{lcc}\n"
        latex += "\\toprule\n"
        latex += "\\textbf{Judge LLM} & \\textbf{Recall (\\%)} & \\textbf{Precision (\\%)} \\\\\n"
        latex += "\\midrule\n"
        
        for judge_name, metrics in data.items():
            recall = metrics['recall']
            precision = metrics['precision']
            
            # Bold the highest values
            recall_str = f"\\textbf{{{recall:.0f}\\%}}" if recall == max(m['recall'] for m in data.values()) else f"{recall:.0f}\\%"
            precision_str = f"\\textbf{{{precision:.0f}\\%}}" if precision == max(m['precision'] for m in data.values()) else f"{precision:.0f}\\%"
            
            latex += f"{judge_name} & {recall_str} & {precision_str} \\\\\n"
        
        latex += "\\bottomrule\n\\end{tabular}\n\\end{table}"
        return latex
    
    def run_full_evaluation(self, 
                          test_data_path: str = "data/processed/seq_shortest.json",
                          max_samples: int = 50) -> str:
        """Run complete one-shot evaluation"""
        
        self.logger.info("Starting full one-shot evaluation")
        
        # Load test data
        test_data = FileManager.load_json(test_data_path)
        if max_samples > 0:
            test_data = test_data[:max_samples]
        
        self.logger.info(f"Loaded {len(test_data)} test sequences")
        
        # Run evaluations
        self.logger.info("Running raw TEACh plan evaluation...")
        raw_results = self.evaluate_raw_teach_plans(test_data)
        
        self.logger.info("Running 4x4 planner-judge matrix evaluation...")
        matrix_results = self.evaluate_planner_judge_matrix(test_data)
        
        # Generate tables
        tables = self.generate_paper_tables(raw_results, matrix_results)
        
        # Save results
        results_dir = os.path.join(self.output_dir, f"one_shot_{self.timestamp}")
        FileManager.ensure_dir(results_dir)
        
        # Save raw data
        FileManager.save_json(raw_results, os.path.join(results_dir, "raw_results.json"))
        FileManager.save_json(matrix_results, os.path.join(results_dir, "matrix_results.json"))
        
        # Save LaTeX tables
        for table_name, table_latex in tables.items():
            table_file = os.path.join(results_dir, f"{table_name}.tex")
            FileManager.save_text(table_latex, table_file)
        
        # Generate summary report
        self._generate_summary_report(raw_results, matrix_results, results_dir)
        
        self.logger.info(f"One-shot evaluation completed. Results saved to: {results_dir}")
        return results_dir
    
    def _generate_summary_report(self, 
                               raw_results: Dict[str, Any], 
                               matrix_results: Dict[str, Dict[str, Any]], 
                               output_dir: str):
        """Generate summary report"""
        
        report = []
        report.append("ONE-SHOT EVALUATION SUMMARY REPORT")
        report.append("=" * 50)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Raw results summary
        if raw_results:
            report.append("RAW TEACH PLAN EVALUATION (Table 1)")
            report.append("-" * 40)
            for judge_name, results in raw_results.items():
                metrics = results['aggregated_metrics']
                report.append(f"{judge_name:15} | Recall: {metrics.recall:6.1%} | "
                            f"Precision: {metrics.precision:6.1%} | F1: {metrics.f1_score:6.1%}")
            report.append("")
        
        # Matrix results summary
        if matrix_results:
            report.append("4x4 PLANNER-JUDGE MATRIX SUMMARY")
            report.append("-" * 40)
            
            # Calculate averages
            all_recall = []
            all_precision = []
            
            for planner_name, judge_results in matrix_results.items():
                planner_recalls = []
                planner_precisions = []
                
                for judge_name, results in judge_results.items():
                    metrics = results['aggregated_metrics']
                    planner_recalls.append(metrics.recall)
                    planner_precisions.append(metrics.precision)
                
                avg_recall = sum(planner_recalls) / len(planner_recalls) if planner_recalls else 0
                avg_precision = sum(planner_precisions) / len(planner_precisions) if planner_precisions else 0
                
                report.append(f"{planner_name:15} | Avg Recall: {avg_recall:6.1%} | "
                            f"Avg Precision: {avg_precision:6.1%}")
                
                all_recall.extend(planner_recalls)
                all_precision.extend(planner_precisions)
            
            # Overall averages
            if all_recall and all_precision:
                report.append("")
                report.append(f"{'Overall Average':15} | Recall: {sum(all_recall)/len(all_recall):6.1%} | "
                            f"Precision: {sum(all_precision)/len(all_precision):6.1%}")
        
        # Save report
        report_text = "\n".join(report)
        FileManager.save_text(report_text, os.path.join(output_dir, "summary_report.txt"))
        
        # Also log the summary
        self.logger.info("Summary Report Generated:")
        for line in report:
            self.logger.info(line)

def main():
    """Main function for one-shot evaluation"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run one-shot evaluation (Table 1 equivalent)')
    parser.add_argument('--data-path', default='data/processed/seq_shortest.json', 
                       help='Path to test data')
    parser.add_argument('--samples', type=int, default=50, 
                       help='Number of test sequences')
    parser.add_argument('--output-dir', default='outputs/experiments/one_shot',
                       help='Output directory')
    
    args = parser.parse_args()
    
    evaluator = OneShotEvaluator(output_dir=args.output_dir)
    results_dir = evaluator.run_full_evaluation(
        test_data_path=args.data_path,
        max_samples=args.samples
    )
    
    print(f"\nOne-shot evaluation completed!")
    print(f"Results available in: {results_dir}")

if __name__ == "__main__":
    main()