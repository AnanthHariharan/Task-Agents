#!/usr/bin/env python3

import re
from typing import List, Dict, Any, Tuple

class ActionModifier:
    """Utility class for modifying action sequences based on REMOVE/MISSING tags"""
    
    @staticmethod
    def remove_tagged_actions(actions: List[str]) -> Tuple[List[str], List[str]]:
        """
        Remove actions marked with #REMOVE tags
        Returns: (clean_actions, removed_actions)
        """
        clean_actions = []
        removed_actions = []
        
        for action in actions:
            if '#REMOVE:' in action:
                # Extract the original action without the tag
                original_action = action.split('#REMOVE:')[0].strip().rstrip(',')
                removed_actions.append(action)  # Keep full tagged version for logging
            else:
                clean_actions.append(action)
        
        return clean_actions, removed_actions
    
    @staticmethod
    def extract_missing_requirements(text: str) -> List[str]:
        """Extract all missing requirements from judge feedback"""
        missing_requirements = []
        
        # Look for #MISSING: tags in the text
        missing_pattern = r'#MISSING:\s*([^#\n]+)'
        matches = re.findall(missing_pattern, text, re.IGNORECASE)
        
        for match in matches:
            requirement = match.strip()
            if requirement and requirement not in missing_requirements:
                missing_requirements.append(requirement)
        
        return missing_requirements
    
    @staticmethod
    def insert_actions_at_position(actions: List[str], new_actions: List[str], position: int = -1) -> List[str]:
        """
        Insert new actions at specified position
        position: -1 for end, 0 for beginning, or specific index
        """
        if position == -1:
            return actions + new_actions
        elif position == 0:
            return new_actions + actions
        else:
            return actions[:position] + new_actions + actions[position:]
    
    @staticmethod
    def find_best_insertion_point(actions: List[str], new_action: str, goal: str) -> int:
        """
        Determine the best position to insert a new action based on context
        Returns the index where the action should be inserted
        """
        # Simple heuristic-based insertion logic
        action_lower = new_action.lower()
        
        # If it's a cleanup action (toggle off, close, etc.), insert near the end
        if any(keyword in action_lower for keyword in ['toggleoff', 'close', 'clean']):
            return len(actions)
        
        # If it's a setup action (open, toggle on, etc.), insert early
        if any(keyword in action_lower for keyword in ['toggleon', 'open', 'pickup']):
            # Find the first non-dialogue action
            for i, existing_action in enumerate(actions):
                if not any(speech in existing_action.lower() for speech in ['say(', 'speech(']):
                    return i
            return 0
        
        # Default: insert at the end
        return len(actions)
    
    @staticmethod
    def deduplicate_actions(actions: List[str]) -> List[str]:
        """Remove duplicate consecutive actions"""
        if not actions:
            return actions
        
        deduplicated = [actions[0]]
        
        for i in range(1, len(actions)):
            current_action = actions[i].strip()
            previous_action = actions[i-1].strip()
            
            # Remove annotations for comparison
            current_clean = re.sub(r'//.*$', '', current_action).strip()
            previous_clean = re.sub(r'//.*$', '', previous_action).strip()
            
            if current_clean != previous_clean:
                deduplicated.append(current_action)
        
        return deduplicated
    
    @staticmethod
    def validate_action_sequence(actions: List[str], goal: str) -> Dict[str, Any]:
        """
        Validate an action sequence for logical consistency
        Returns validation report
        """
        issues = []
        warnings = []
        
        # Track state for validation
        picked_objects = set()
        open_containers = set()
        on_devices = set()
        
        for i, action in enumerate(actions):
            action_clean = action.split('//')[0].strip()
            
            # Parse action components
            if '.PickUp(' in action_clean:
                obj_match = re.search(r"PickUp\('([^']+)'\)", action_clean)
                if obj_match:
                    obj = obj_match.group(1)
                    if obj in picked_objects:
                        issues.append(f"Line {i+1}: Picking up {obj} that is already held")
                    picked_objects.add(obj)
            
            elif '.PutAOnB(' in action_clean:
                match = re.search(r"PutAOnB\('([^']+)',\s*'([^']+)'\)", action_clean)
                if match:
                    obj, surface = match.groups()
                    if obj not in picked_objects:
                        issues.append(f"Line {i+1}: Placing {obj} without picking it up first")
                    else:
                        picked_objects.remove(obj)
            
            elif '.Open(' in action_clean:
                obj_match = re.search(r"Open\('([^']+)'\)", action_clean)
                if obj_match:
                    obj = obj_match.group(1)
                    if obj in open_containers:
                        warnings.append(f"Line {i+1}: Opening {obj} that may already be open")
                    open_containers.add(obj)
            
            elif '.Close(' in action_clean:
                obj_match = re.search(r"Close\('([^']+)'\)", action_clean)
                if obj_match:
                    obj = obj_match.group(1)
                    if obj not in open_containers:
                        warnings.append(f"Line {i+1}: Closing {obj} that wasn't opened")
                    else:
                        open_containers.remove(obj)
            
            elif '.ToggleOn(' in action_clean:
                obj_match = re.search(r"ToggleOn\('([^']+)'\)", action_clean)
                if obj_match:
                    obj = obj_match.group(1)
                    if obj in on_devices:
                        warnings.append(f"Line {i+1}: Turning on {obj} that may already be on")
                    on_devices.add(obj)
            
            elif '.ToggleOff(' in action_clean:
                obj_match = re.search(r"ToggleOff\('([^']+)'\)", action_clean)
                if obj_match:
                    obj = obj_match.group(1)
                    if obj not in on_devices:
                        issues.append(f"Line {i+1}: Turning off {obj} that wasn't turned on")
                    else:
                        on_devices.remove(obj)
        
        # Final state checks
        if picked_objects:
            warnings.append(f"Objects still being held at end: {', '.join(picked_objects)}")
        
        if on_devices:
            warnings.append(f"Devices still on at end: {', '.join(on_devices)}")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings,
            'final_state': {
                'holding': list(picked_objects),
                'open_containers': list(open_containers),
                'on_devices': list(on_devices)
            }
        }
    
    @classmethod
    def apply_modifications(cls, 
                          actions: List[str], 
                          judge_feedback: Dict[str, Any], 
                          new_actions: List[str] = None) -> Dict[str, Any]:
        """
        Apply all modifications based on judge feedback
        Returns: {
            'modified_actions': List[str],
            'removed_actions': List[str],
            'added_actions': List[str],
            'validation_report': Dict
        }
        """
        # Step 1: Remove tagged actions
        clean_actions, removed_actions = cls.remove_tagged_actions(actions)
        
        # Step 2: Add new actions if provided
        added_actions = new_actions or []
        if added_actions:
            # Insert new actions at appropriate positions
            for new_action in added_actions:
                insertion_point = cls.find_best_insertion_point(
                    clean_actions, new_action, judge_feedback.get('goal', '')
                )
                clean_actions = cls.insert_actions_at_position(
                    clean_actions, [new_action], insertion_point
                )
        
        # Step 3: Deduplicate
        final_actions = cls.deduplicate_actions(clean_actions)
        
        # Step 4: Validate
        validation_report = cls.validate_action_sequence(
            final_actions, judge_feedback.get('goal', '')
        )
        
        return {
            'modified_actions': final_actions,
            'removed_actions': removed_actions,
            'added_actions': added_actions,
            'validation_report': validation_report
        }