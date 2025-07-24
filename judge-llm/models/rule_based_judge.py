#!/usr/bin/env python3

import re
from typing import List, Dict, Any, Set, Tuple
from .base_judge import BaseJudge
from shared.utils.action_utils import ActionParser
from shared.utils.logging_utils import LoggerMixin

class RuleBasedJudge(BaseJudge, LoggerMixin):
    """Rule-based judge using heuristics and logical consistency checks"""
    
    def __init__(self, name: str = "RuleBased"):
        super().__init__(name)
        
        # Define rules for different types of inefficiencies
        self.redundancy_rules = {
            'toggle_off_before_on': {
                'pattern': 'ToggleOff before any ToggleOn',
                'description': 'turning off device before turning it on'
            },
            'duplicate_pickup': {
                'pattern': 'Multiple PickUp of same object',
                'description': 'picking up same object multiple times'
            },
            'contradictory_movement': {
                'pattern': 'Move actions that cancel each other',
                'description': 'contradictory movement actions'
            },
            'unnecessary_object': {
                'pattern': 'PickUp of irrelevant objects',
                'description': 'picking up objects not needed for task'
            }
        }
        
        # Define completeness requirements for common tasks
        self.completeness_rules = {
            'clean_task': {
                'required_sequence': ['PickUp', 'PutAOnB', 'ToggleOn', 'ToggleOff'],
                'required_objects': ['object_to_clean', 'Sink', 'Faucet'],
                'safety_actions': ['ToggleOff']
            },
            'place_task': {
                'required_sequence': ['PickUp', 'PutAOnB'],
                'required_objects': ['object_to_move', 'target_location'],
                'safety_actions': []
            },
            'heat_task': {
                'required_sequence': ['PickUp', 'PutAOnB', 'ToggleOn', 'ToggleOff'],
                'required_objects': ['object_to_heat', 'Microwave'],
                'safety_actions': ['ToggleOff']
            }
        }
    
    def judge_plan(self, action_sequence: List[str], goal: str) -> Dict[str, Any]:
        """Evaluate action sequence using rule-based analysis"""
        self.logger.info(f"Rule-based evaluation of {len(action_sequence)} actions")
        
        # Parse all actions for analysis
        parsed_actions = [ActionParser.parse_action(action) for action in action_sequence]
        
        # Analyze for redundancies
        redundancy_analysis = self._analyze_redundancies(parsed_actions, action_sequence)
        
        # Analyze for completeness
        completeness_analysis = self._analyze_completeness(parsed_actions, goal)
        
        # Analyze logical consistency
        consistency_analysis = self._analyze_consistency(parsed_actions)
        
        # Generate structured feedback
        annotated_actions = self._generate_action_annotations(
            action_sequence, parsed_actions, redundancy_analysis, consistency_analysis
        )
        
        # Compile missing requirements
        missing_requirements = completeness_analysis['missing_requirements']
        
        # Determine if changes are needed
        has_changes = (len(redundancy_analysis['remove_actions']) > 0 or 
                      len(missing_requirements) > 0 or
                      len(consistency_analysis['issues']) > 0)
        
        return {
            'annotated_actions': annotated_actions,
            'remove_actions': redundancy_analysis['remove_actions'],
            'missing_requirements': missing_requirements,
            'has_changes': has_changes,
            'raw_response': self._generate_raw_response(
                annotated_actions, missing_requirements
            ),
            'analysis_details': {
                'redundancy': redundancy_analysis,
                'completeness': completeness_analysis,
                'consistency': consistency_analysis
            }
        }
    
    def _analyze_redundancies(self, parsed_actions: List[Dict], action_sequence: List[str]) -> Dict[str, Any]:
        """Analyze for redundant actions"""
        remove_actions = []
        issues = []
        
        # Track device states
        device_states = {}  # device -> [list of (action_index, on/off)]
        picked_objects = {}  # object -> [list of action_indices]
        
        for i, parsed in enumerate(parsed_actions):
            if not parsed['valid']:
                continue
                
            method = parsed['method']
            args = parsed['arguments']
            
            # Track toggle actions
            if method in ['ToggleOn', 'ToggleOff'] and args:
                device = args[0]
                if device not in device_states:
                    device_states[device] = []
                device_states[device].append((i, method))
            
            # Track pickup actions
            elif method == 'PickUp' and args:
                obj = args[0]
                if obj not in picked_objects:
                    picked_objects[obj] = []
                picked_objects[obj].append(i)
        
        # Check for toggle redundancies
        for device, actions in device_states.items():
            # ToggleOff before any ToggleOn
            first_toggle = actions[0] if actions else None
            if first_toggle and first_toggle[1] == 'ToggleOff':
                action_idx = first_toggle[0]
                remove_actions.append({
                    'action': action_sequence[action_idx],
                    'annotation': f"turning off {device} before turning it on",
                    'remove': True,
                    'remove_reason': f"unnecessary to turn off {device} when not turned on yet"
                })
                issues.append(f"ToggleOff {device} before ToggleOn")
        
        # Check for duplicate pickups
        for obj, pickup_indices in picked_objects.items():
            if len(pickup_indices) > 1:
                # Mark subsequent pickups as redundant
                for idx in pickup_indices[1:]:
                    remove_actions.append({
                        'action': action_sequence[idx],
                        'annotation': f"picking up {obj} again",
                        'remove': True,
                        'remove_reason': f"already holding {obj}"
                    })
                    issues.append(f"Duplicate pickup of {obj}")
        
        # Check for contradictory movements
        move_actions = [(i, parsed) for i, parsed in enumerate(parsed_actions) 
                       if parsed['valid'] and parsed['method'] == 'Move']
        
        for i in range(len(move_actions) - 1):
            curr_idx, curr_action = move_actions[i]
            next_idx, next_action = move_actions[i + 1]
            
            # Check if consecutive moves cancel each other
            if (next_idx == curr_idx + 1 and 
                len(curr_action['arguments']) > 0 and 
                len(next_action['arguments']) > 0):
                
                try:
                    curr_dist = float(curr_action['arguments'][0])
                    next_dist = float(next_action['arguments'][0])
                    
                    if abs(curr_dist + next_dist) < 0.1:  # Cancel each other out
                        remove_actions.extend([
                            {
                                'action': action_sequence[curr_idx],
                                'annotation': "contradictory movement",
                                'remove': True,
                                'remove_reason': "movement cancelled by next action"
                            },
                            {
                                'action': action_sequence[next_idx],
                                'annotation': "contradictory movement", 
                                'remove': True,
                                'remove_reason': "cancels previous movement"
                            }
                        ])
                        issues.append(f"Contradictory moves at positions {curr_idx+1}, {next_idx+1}")
                except ValueError:
                    pass
        
        return {
            'remove_actions': remove_actions,
            'issues': issues,
            'device_states': device_states,
            'picked_objects': picked_objects
        }
    
    def _analyze_completeness(self, parsed_actions: List[Dict], goal: str) -> Dict[str, Any]:
        """Analyze completeness based on goal and task patterns"""
        missing_requirements = []
        task_type = self._identify_task_type(goal, parsed_actions)
        
        if task_type in self.completeness_rules:
            rules = self.completeness_rules[task_type]
            
            # Check required action sequence
            action_types = [parsed['method'] for parsed in parsed_actions if parsed['valid']]
            required_actions = rules['required_sequence']
            
            for required_action in required_actions:
                if required_action not in action_types:
                    missing_requirements.append(f"Missing {required_action} action for {task_type}")
            
            # Check safety actions (like turning off devices)
            if 'ToggleOn' in action_types and 'ToggleOff' not in action_types:
                missing_requirements.append("Turn off devices after use for safety")
            
            # Check for proper object handling
            has_pickup = 'PickUp' in action_types
            has_place = 'PutAOnB' in action_types
            
            if has_pickup and not has_place:
                missing_requirements.append("Place picked up objects appropriately")
            
            # Check for communication/dialogue
            has_dialogue = any(parsed['method'] in ['Say', 'Speech'] 
                             for parsed in parsed_actions if parsed['valid'])
            
            if not has_dialogue:
                missing_requirements.append("Add communication or acknowledgment")
        
        return {
            'task_type': task_type,
            'missing_requirements': missing_requirements,
            'completeness_score': self._calculate_completeness_score(
                parsed_actions, task_type
            )
        }
    
    def _identify_task_type(self, goal: str, parsed_actions: List[Dict]) -> str:
        """Identify the type of task based on goal and actions"""
        goal_lower = goal.lower()
        
        if any(word in goal_lower for word in ['clean', 'wash', 'rinse']):
            return 'clean_task'
        elif any(word in goal_lower for word in ['heat', 'warm', 'microwave']):
            return 'heat_task'
        elif any(word in goal_lower for word in ['place', 'put', 'move']):
            return 'place_task'
        else:
            # Infer from actions
            action_types = [parsed['method'] for parsed in parsed_actions if parsed['valid']]
            if 'ToggleOn' in action_types and any(
                any(arg.lower() in ['microwave', 'oven'] for arg in parsed['arguments']) 
                for parsed in parsed_actions if parsed['valid'] and parsed['arguments']
            ):
                return 'heat_task'
            elif 'ToggleOn' in action_types and any(
                any(arg.lower() in ['faucet', 'sink'] for arg in parsed['arguments'])
                for parsed in parsed_actions if parsed['valid'] and parsed['arguments']
            ):
                return 'clean_task'
            else:
                return 'place_task'
    
    def _analyze_consistency(self, parsed_actions: List[Dict]) -> Dict[str, Any]:
        """Analyze logical consistency of action sequence"""
        issues = []
        warnings = []
        
        # Track state for consistency checking
        holding = set()
        open_containers = set()
        on_devices = set()
        
        for i, parsed in enumerate(parsed_actions):
            if not parsed['valid']:
                continue
                
            method = parsed['method']
            args = parsed['arguments']
            
            if method == 'PickUp' and args:
                obj = args[0]
                if obj in holding:
                    issues.append(f"Line {i+1}: Already holding {obj}")
                holding.add(obj)
            
            elif method == 'PutAOnB' and len(args) >= 2:
                obj = args[0]
                if obj not in holding:
                    issues.append(f"Line {i+1}: Cannot place {obj} - not holding it")
                else:
                    holding.remove(obj)
            
            elif method == 'Open' and args:
                container = args[0]
                if container in open_containers:
                    warnings.append(f"Line {i+1}: Opening {container} that may already be open")
                open_containers.add(container)
            
            elif method == 'Close' and args:
                container = args[0]
                if container not in open_containers:
                    warnings.append(f"Line {i+1}: Closing {container} that wasn't opened")
                else:
                    open_containers.remove(container)
            
            elif method == 'ToggleOn' and args:
                device = args[0]
                if device in on_devices:
                    warnings.append(f"Line {i+1}: Turning on {device} that may already be on")
                on_devices.add(device)
            
            elif method == 'ToggleOff' and args:
                device = args[0]
                if device not in on_devices:
                    issues.append(f"Line {i+1}: Turning off {device} that wasn't turned on")
                else:
                    on_devices.remove(device)
        
        return {
            'issues': issues,
            'warnings': warnings,
            'final_state': {
                'holding': list(holding),
                'open_containers': list(open_containers),
                'on_devices': list(on_devices)
            }
        }
    
    def _calculate_completeness_score(self, parsed_actions: List[Dict], task_type: str) -> float:
        """Calculate completeness score (0-1)"""
        if task_type not in self.completeness_rules:
            return 1.0
        
        rules = self.completeness_rules[task_type]
        action_types = [parsed['method'] for parsed in parsed_actions if parsed['valid']]
        
        # Check how many required actions are present
        required_actions = rules['required_sequence']
        present_actions = sum(1 for action in required_actions if action in action_types)
        
        base_score = present_actions / len(required_actions)
        
        # Bonus for safety actions
        safety_actions = rules['safety_actions']
        if safety_actions:
            safety_bonus = sum(0.1 for action in safety_actions if action in action_types)
            base_score = min(1.0, base_score + safety_bonus)
        
        return base_score
    
    def _generate_action_annotations(self, action_sequence: List[str], 
                                   parsed_actions: List[Dict],
                                   redundancy_analysis: Dict,
                                   consistency_analysis: Dict) -> List[Dict]:
        """Generate annotations for each action"""
        annotated_actions = []
        remove_indices = {item['action']: item for item in redundancy_analysis['remove_actions']}
        
        for i, (action, parsed) in enumerate(zip(action_sequence, parsed_actions)):
            annotation_parts = []
            
            # Basic action description
            if parsed['valid']:
                method = parsed['method']
                args = parsed['arguments']
                
                if method == 'Say' or method == 'Speech':
                    annotation_parts.append("communication")
                elif method == 'PickUp' and args:
                    annotation_parts.append(f"picks up {args[0]}")
                elif method == 'PutAOnB' and len(args) >= 2:
                    annotation_parts.append(f"places {args[0]} on {args[1]}")
                elif method == 'ToggleOn' and args:
                    annotation_parts.append(f"turns on {args[0]}")
                elif method == 'ToggleOff' and args:
                    annotation_parts.append(f"turns off {args[0]}")
                elif method == 'Open' and args:
                    annotation_parts.append(f"opens {args[0]}")
                elif method == 'Close' and args:
                    annotation_parts.append(f"closes {args[0]}")
                elif method == 'Move' and args:
                    annotation_parts.append(f"moves {args[0]} units")
                else:
                    annotation_parts.append(f"performs {method.lower()}")
            
            # Check if this action should be removed
            is_remove = action in remove_indices
            remove_reason = remove_indices[action]['remove_reason'] if is_remove else None
            
            annotated_actions.append({
                'action': action,
                'annotation': ' '.join(annotation_parts),
                'remove': is_remove,
                'remove_reason': remove_reason
            })
        
        return annotated_actions
    
    def _generate_raw_response(self, annotated_actions: List[Dict], missing_requirements: List[str]) -> str:
        """Generate raw response text in expected format"""
        lines = []
        
        for i, item in enumerate(annotated_actions):
            lines.append(f"ACTION: {item['action']}")
            
            annotation = f"ANNOTATION: {item['annotation']}"
            if item['remove']:
                annotation += f" #REMOVE: {item['remove_reason']}"
            
            lines.append(annotation)
            lines.append("")  # Empty line between actions
        
        # Add missing requirements
        for requirement in missing_requirements:
            lines.append(f"#MISSING: {requirement}")
        
        return '\n'.join(lines)
    
    def compare_plans(self, plan1: List[str], plan2: List[str], goal: str) -> Dict[str, Any]:
        """Compare two plans using rule-based analysis"""
        self.logger.info(f"Rule-based comparison of two plans for goal: {goal}")
        
        # Analyze both plans
        analysis1 = self.judge_plan(plan1, goal)
        analysis2 = self.judge_plan(plan2, goal)
        
        # Compare key metrics
        score1 = self._calculate_plan_score(analysis1)
        score2 = self._calculate_plan_score(analysis2)
        
        better_plan = "Plan A" if score1 > score2 else "Plan B" if score2 > score1 else "Equal"
        
        comparison_text = f"""
        Plan A Analysis:
        - Actions to remove: {len(analysis1['remove_actions'])}
        - Missing requirements: {len(analysis1['missing_requirements'])}
        - Completeness score: {analysis1['analysis_details']['completeness']['completeness_score']:.2f}
        - Overall score: {score1:.2f}
        
        Plan B Analysis:
        - Actions to remove: {len(analysis2['remove_actions'])}
        - Missing requirements: {len(analysis2['missing_requirements'])}
        - Completeness score: {analysis2['analysis_details']['completeness']['completeness_score']:.2f}
        - Overall score: {score2:.2f}
        
        Better plan: {better_plan}
        """
        
        return {
            'comparison': comparison_text,
            'plan1': plan1,
            'plan2': plan2,
            'goal': goal,
            'plan1_score': score1,
            'plan2_score': score2,
            'better_plan': better_plan
        }
    
    def _calculate_plan_score(self, analysis: Dict[str, Any]) -> float:
        """Calculate overall plan quality score"""
        completeness = analysis['analysis_details']['completeness']['completeness_score']
        efficiency = 1.0 - (len(analysis['remove_actions']) * 0.1)  # Penalty for redundancies
        consistency = 1.0 - (len(analysis['analysis_details']['consistency']['issues']) * 0.1)
        
        # Weighted average
        score = (completeness * 0.4 + efficiency * 0.3 + consistency * 0.3)
        return max(0.0, min(1.0, score))