#!/usr/bin/env python3

from typing import List, Dict, Any
from shared.utils.action_utils import ActionValidator
from shared.utils.logging_utils import LoggerMixin, get_logger

class SequenceValidator(LoggerMixin):
    """Advanced action sequence validation"""
    
    def __init__(self):
        self.logger = get_logger("SequenceValidator")
    
    def comprehensive_validate(self, actions: List[str], goal: str = "") -> Dict[str, Any]:
        """Perform comprehensive validation of an action sequence"""
        self.logger.info(f"Validating sequence with {len(actions)} actions")
        
        # Basic validation
        basic_validation = ActionValidator.validate_sequence(actions)
        
        # Completeness check
        completeness = ActionValidator.check_completeness(actions, goal)
        
        # Additional checks
        efficiency_issues = self._check_efficiency(actions)
        logical_flow_issues = self._check_logical_flow(actions)
        
        overall_score = self._calculate_overall_score(
            basic_validation, completeness, efficiency_issues, logical_flow_issues
        )
        
        return {
            'basic_validation': basic_validation,
            'completeness': completeness,
            'efficiency_issues': efficiency_issues,
            'logical_flow_issues': logical_flow_issues,
            'overall_score': overall_score,
            'recommendations': self._generate_recommendations(
                basic_validation, completeness, efficiency_issues, logical_flow_issues
            )
        }
    
    def _check_efficiency(self, actions: List[str]) -> List[str]:
        """Check for efficiency issues in the action sequence"""
        issues = []
        
        # Check for redundant movements
        consecutive_moves = []
        for i, action in enumerate(actions):
            if 'Move(' in action:
                consecutive_moves.append((i, action))
            else:
                if len(consecutive_moves) > 2:
                    issues.append(f"Excessive consecutive moves: lines {consecutive_moves[0][0]+1}-{consecutive_moves[-1][0]+1}")
                consecutive_moves = []
        
        # Check for unnecessary pickups
        picked_objects = set()
        for i, action in enumerate(actions):
            if 'PickUp(' in action:
                # Extract object name
                obj_match = action.split("'")
                if len(obj_match) >= 2:
                    obj = obj_match[1]
                    if obj in picked_objects:
                        issues.append(f"Line {i+1}: Redundant pickup of {obj}")
                    picked_objects.add(obj)
        
        return issues
    
    def _check_logical_flow(self, actions: List[str]) -> List[str]:
        """Check for logical flow issues"""
        issues = []
        
        # Check if dialogue precedes actions appropriately
        has_initial_dialogue = False
        first_action_index = -1
        
        for i, action in enumerate(actions):
            if any(speech in action for speech in ['Say(', 'Speech(']):
                if i < 3:  # Early dialogue is good
                    has_initial_dialogue = True
            else:
                if first_action_index == -1:
                    first_action_index = i
                    break
        
        if not has_initial_dialogue and first_action_index >= 0:
            issues.append("No initial dialogue/communication before actions")
        
        # Check for proper sequencing of related actions
        open_containers = set()
        for i, action in enumerate(actions):
            if 'Open(' in action:
                obj_match = action.split("'")
                if len(obj_match) >= 2:
                    obj = obj_match[1]
                    open_containers.add(obj)
            elif 'PickUp(' in action and i > 0:
                # Check if picking up from a container that should be opened
                prev_actions = actions[:i]
                # This is a simplified check - in practice, you'd need more context
                pass
        
        return issues
    
    def _calculate_overall_score(self, basic_validation: Dict, completeness: Dict, 
                               efficiency_issues: List, logical_flow_issues: List) -> float:
        """Calculate an overall quality score (0-100)"""
        score = 100.0
        
        # Deduct for basic validation issues
        score -= len(basic_validation.get('issues', [])) * 10
        score -= len(basic_validation.get('warnings', [])) * 5
        
        # Deduct for completeness issues
        score *= completeness.get('completeness_score', 1.0)
        
        # Deduct for efficiency issues
        score -= len(efficiency_issues) * 5
        
        # Deduct for logical flow issues
        score -= len(logical_flow_issues) * 7
        
        return max(0.0, score)
    
    def _generate_recommendations(self, basic_validation: Dict, completeness: Dict,
                                efficiency_issues: List, logical_flow_issues: List) -> List[str]:
        """Generate improvement recommendations"""
        recommendations = []
        
        if basic_validation.get('issues'):
            recommendations.append("Fix logical consistency issues")
        
        if completeness.get('completeness_score', 1.0) < 0.8:
            recommendations.extend([
                f"Address missing elements: {', '.join(completeness.get('missing_elements', []))}"
            ])
        
        if efficiency_issues:
            recommendations.append("Optimize action sequence for efficiency")
        
        if logical_flow_issues:
            recommendations.append("Improve logical flow and sequencing")
        
        if not recommendations:
            recommendations.append("Sequence appears well-structured")
        
        return recommendations