#!/usr/bin/env python3

import re
from typing import List, Dict, Any, Tuple

class ActionParser:
    """Utility class for parsing action sequences"""
    
    @staticmethod
    def parse_action(action: str) -> Dict[str, Any]:
        """Parse a single action into components"""
        action_clean = action.split('//')[0].strip().rstrip(',')
        
        # Extract agent, method, and arguments
        if '.' not in action_clean:
            return {'raw': action, 'valid': False, 'error': 'No agent specified'}
        
        agent, method_call = action_clean.split('.', 1)
        
        if '(' not in method_call or ')' not in method_call:
            return {'raw': action, 'valid': False, 'error': 'Invalid method call format'}
        
        method = method_call.split('(')[0]
        args_str = method_call[method_call.find('(')+1:method_call.rfind(')')]
        
        # Parse arguments
        args = []
        if args_str.strip():
            # Simple argument parsing (handles quoted strings)
            current_arg = ""
            in_quotes = False
            quote_char = None
            
            for char in args_str:
                if char in ['"', "'"] and not in_quotes:
                    in_quotes = True
                    quote_char = char
                elif char == quote_char and in_quotes:
                    in_quotes = False
                    quote_char = None
                elif char == ',' and not in_quotes:
                    args.append(current_arg.strip().strip('"\''))
                    current_arg = ""
                    continue
                
                current_arg += char
            
            if current_arg.strip():
                args.append(current_arg.strip().strip('"\''))
        
        return {
            'raw': action,
            'valid': True,
            'agent': agent.strip(),
            'method': method.strip(),
            'arguments': args,
            'annotation': action.split('//')[-1].strip() if '//' in action else None
        }
    
    @staticmethod
    def extract_objects(actions: List[str]) -> List[str]:
        """Extract all objects mentioned in actions"""
        objects = set()
        
        for action in actions:
            parsed = ActionParser.parse_action(action)
            if parsed['valid'] and parsed['arguments']:
                objects.update(parsed['arguments'])
        
        return sorted(list(objects))

class ActionValidator:
    """Utility class for validating action sequences"""
    
    @staticmethod
    def validate_sequence(actions: List[str]) -> Dict[str, Any]:
        """Validate an action sequence for logical consistency"""
        issues = []
        warnings = []
        
        # Track state
        holding = set()
        open_containers = set()
        on_devices = set()
        
        for i, action in enumerate(actions):
            parsed = ActionParser.parse_action(action)
            
            if not parsed['valid']:
                issues.append(f"Line {i+1}: {parsed.get('error', 'Invalid action')}")
                continue
            
            method = parsed['method']
            args = parsed['arguments']
            
            # Validate specific action types
            if method == 'PickUp' and args:
                obj = args[0]
                if obj in holding:
                    issues.append(f"Line {i+1}: Already holding {obj}")
                holding.add(obj)
            
            elif method == 'PutAOnB' and len(args) >= 2:
                obj, surface = args[0], args[1]
                if obj not in holding:
                    issues.append(f"Line {i+1}: Not holding {obj}")
                else:
                    holding.remove(obj)
            
            elif method == 'Open' and args:
                obj = args[0]
                if obj in open_containers:
                    warnings.append(f"Line {i+1}: {obj} may already be open")
                open_containers.add(obj)
            
            elif method == 'Close' and args:
                obj = args[0]
                if obj not in open_containers:
                    warnings.append(f"Line {i+1}: {obj} wasn't opened")
                else:
                    open_containers.remove(obj)
            
            elif method == 'ToggleOn' and args:
                obj = args[0]
                if obj in on_devices:
                    warnings.append(f"Line {i+1}: {obj} may already be on")
                on_devices.add(obj)
            
            elif method == 'ToggleOff' and args:
                obj = args[0]
                if obj not in on_devices:
                    issues.append(f"Line {i+1}: {obj} wasn't turned on")
                else:
                    on_devices.remove(obj)
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings,
            'final_state': {
                'holding': list(holding),
                'open_containers': list(open_containers),
                'on_devices': list(on_devices)
            }
        }
    
    @staticmethod
    def check_completeness(actions: List[str], goal: str) -> Dict[str, Any]:
        """Check if action sequence appears complete for the goal"""
        # This is a placeholder for more sophisticated completeness checking
        has_dialogue = any('Say(' in action for action in actions)
        has_actions = any(not any(speech in action for speech in ['Say(', 'Speech(']) 
                         for action in actions)
        
        completeness_score = 0.0
        missing_elements = []
        
        if has_dialogue:
            completeness_score += 0.3
        else:
            missing_elements.append("No dialogue/communication")
        
        if has_actions:
            completeness_score += 0.7
        else:
            missing_elements.append("No physical actions")
        
        return {
            'completeness_score': completeness_score,
            'missing_elements': missing_elements,
            'has_dialogue': has_dialogue,
            'has_actions': has_actions
        }