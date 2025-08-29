#!/usr/bin/env python3

import re
from typing import List, Dict, Any, Set
from .base_planner import BasePlanner
from shared.utils.action_utils import ActionParser
from shared.utils.logging_utils import LoggerMixin

class RuleBasedPlanner(BasePlanner, LoggerMixin):
    """Rule-based planning agent using heuristics and patterns"""

    def __init__(self, name: str = "RuleBased"):
        super().__init__(name)

        self.task_patterns = {
            'clean': {
                'keywords': ['clean', 'wash', 'rinse'],
                'required_actions': ['PickUp', 'PutAOnB', 'ToggleOn', 'ToggleOff'],
                'typical_objects': ['Mug', 'Plate', 'Cup', 'Bowl'],
                'typical_locations': ['Sink', 'Faucet']
            },
            'heat': {
                'keywords': ['heat', 'warm', 'microwave', 'cook'],
                'required_actions': ['PickUp', 'PutAOnB', 'ToggleOn', 'ToggleOff'],
                'typical_objects': ['Mug', 'Plate', 'Food'],
                'typical_locations': ['Microwave']
            },
            'make_coffee': {
                'keywords': ['coffee', 'brew'],
                'required_actions': ['PickUp', 'Fill', 'PutAOnB', 'ToggleOn'],
                'typical_objects': ['Mug', 'CoffeeMaker'],
                'typical_locations': ['CoffeeMaker', 'Sink']
            },
            'place': {
                'keywords': ['place', 'put', 'move'],
                'required_actions': ['PickUp', 'PutAOnB'],
                'typical_objects': ['*'],  # Any object
                'typical_locations': ['Table', 'Counter', 'Shelf']
            },
            'water_plant': {
                'keywords': ['water', 'plant'],
                'required_actions': ['PickUp', 'Fill', 'PourFromAIntoB'],
                'typical_objects': ['Cup', 'Mug', 'WateringCan'],
                'typical_locations': ['HousePlant', 'Sink']
            }
        }

    def annotate_goal(self, action_sequence: List[str], context: str = "") -> str:
        """Identify goal using rule-based pattern matching"""
        self.logger.info(f"Rule-based goal annotation for sequence with {len(action_sequence)} actions")
        actions_text = ' '.join(action_sequence).lower()
        dialogue_text = ' '.join([action for action in action_sequence if 'say(' in action.lower()]).lower()
        parsed_actions = [ActionParser.parse_action(action) for action in action_sequence]
        objects = set()
        action_types = set()

        for parsed in parsed_actions:
            if parsed['valid']:
                action_types.add(parsed['method'])
                objects.update(parsed['arguments'])

        goal = self._match_task_pattern(dialogue_text, actions_text, objects, action_types)

        self.logger.debug(f"Rule-based goal identified: {goal}")
        return f"GOAL: {goal}"

    def _match_task_pattern(self, dialogue: str, actions: str, objects: Set[str], action_types: Set[str]) -> str:
        """Match against known task patterns"""

        pattern_scores = {}

        for task_name, pattern in self.task_patterns.items():
            score = 0

            for keyword in pattern['keywords']:
                if keyword in dialogue:
                    score += 3
                if keyword in actions:
                    score += 2

            required_actions = set(pattern['required_actions'])
            matching_actions = required_actions.intersection(action_types)
            score += len(matching_actions) * 2

            if pattern['typical_objects'] != ['*']:
                typical_objects = set(pattern['typical_objects'])
                matching_objects = typical_objects.intersection(objects)
                score += len(matching_objects) * 1

            typical_locations = set(pattern['typical_locations'])
            matching_locations = typical_locations.intersection(objects)
            score += len(matching_locations) * 1

            if score > 0:
                pattern_scores[task_name] = score

        if pattern_scores:
            best_task = max(pattern_scores, key=pattern_scores.get)
            return self._generate_goal_description(best_task, objects)

        if action_types:
            primary_action = max(action_types, key=lambda x: sum(1 for a in actions.split() if x.lower() in a.lower()))
            if 'PickUp' in action_types and 'PutAOnB' in action_types:
                return "Move objects to designated locations"
            elif 'ToggleOn' in action_types:
                return "Activate devices for task completion"
            else:
                return f"Complete task involving {primary_action.lower()} actions"

        return "Complete the specified task"

    def _generate_goal_description(self, task_type: str, objects: Set[str]) -> str:
        """Generate natural language goal description"""

        descriptions = {
            'clean': f"Clean the {self._get_primary_object(objects, ['Mug', 'Plate', 'Cup', 'Bowl'])}",
            'heat': f"Heat the {self._get_primary_object(objects, ['Mug', 'Food', 'Plate'])}",
            'make_coffee': "Make coffee",
            'place': f"Place the {self._get_primary_object(objects)} on the target location",
            'water_plant': "Water the plant"
        }

        return descriptions.get(task_type, f"Complete {task_type} task")

    def _get_primary_object(self, objects: Set[str], preferred: List[str] = None) -> str:
        if preferred:
            for obj in preferred:
                if obj in objects:
                    return obj.lower()

        # Filter out locations and get first object
        non_locations = [obj for obj in objects if obj not in
                        ['Sink', 'Counter', 'Table', 'Microwave', 'CoffeeMaker', 'Faucet']]

        return non_locations[0].lower() if non_locations else "object"

    def modify_plan(self, action_sequence: List[str], judge_feedback: str, goal: str) -> List[str]:
        self.logger.info("Applying rule-based plan modifications")

        modified_actions = action_sequence.copy()

        remove_actions = self._extract_remove_actions(judge_feedback)
        missing_requirements = self._extract_missing_requirements(judge_feedback)

        if remove_actions:
            modified_actions = [action for action in modified_actions
                             if not any(remove_action in action for remove_action in remove_actions)]

        for requirement in missing_requirements:
            new_actions = self._generate_missing_actions_rule_based(
                goal, modified_actions, requirement
            )
            modified_actions.extend(new_actions)

        modified_actions = self._apply_consistency_rules(modified_actions)

        self.logger.debug(f"Rule-based modifications: {len(action_sequence)} -> {len(modified_actions)} actions")
        return modified_actions

    def _extract_remove_actions(self, feedback: str) -> List[str]:
        """Extract actions marked for removal"""
        remove_pattern = r'#REMOVE:?\s*([^#\n]+)'
        matches = re.findall(remove_pattern, feedback, re.IGNORECASE)
        return [match.strip() for match in matches]

    def _extract_missing_requirements(self, feedback: str) -> List[str]:
        """Extract missing requirements"""
        missing_pattern = r'#MISSING:?\s*([^#\n]+)'
        matches = re.findall(missing_pattern, feedback, re.IGNORECASE)
        return [match.strip() for match in matches]

    def generate_missing_actions(self, goal: str, current_actions: List[str],
                               missing_requirement: str) -> List[str]:
        """Generate missing actions using rule-based approach"""
        return self._generate_missing_actions_rule_based(goal, current_actions, missing_requirement)

    def _generate_missing_actions_rule_based(self, goal: str, current_actions: List[str],
                                           requirement: str) -> List[str]:
        """Generate actions based on rules and patterns"""
        new_actions = []
        requirement_lower = requirement.lower()

        parsed_actions = [ActionParser.parse_action(action) for action in current_actions]
        used_objects = set()
        current_action_types = set()

        for parsed in parsed_actions:
            if parsed['valid']:
                current_action_types.add(parsed['method'])
                used_objects.update(parsed['arguments'])

        if 'turn off' in requirement_lower or 'toggle off' in requirement_lower:
            turned_on = set()
            turned_off = set()

            for parsed in parsed_actions:
                if parsed['valid'] and parsed['method'] == 'ToggleOn' and parsed['arguments']:
                    turned_on.add(parsed['arguments'][0])
                elif parsed['valid'] and parsed['method'] == 'ToggleOff' and parsed['arguments']:
                    turned_off.add(parsed['arguments'][0])

            devices_to_turn_off = turned_on - turned_off
            for device in devices_to_turn_off:
                new_actions.append(f"Driver.ToggleOff('{device}')")

        elif 'open' in requirement_lower and 'before' in requirement_lower:
            if 'microwave' in requirement_lower:
                new_actions.append("Driver.Open('Microwave')")
            elif 'drawer' in requirement_lower:
                new_actions.append("Driver.Open('Drawer')")
            elif 'cabinet' in requirement_lower:
                new_actions.append("Driver.Open('Cabinet')")

        elif 'pick up' in requirement_lower or 'pickup' in requirement_lower:
            if 'mug' in requirement_lower:
                new_actions.append("Driver.PickUp('Mug')")
            elif 'cup' in requirement_lower:
                new_actions.append("Driver.PickUp('Cup')")
            elif 'plate' in requirement_lower:
                new_actions.append("Driver.PickUp('Plate')")

        elif 'place' in requirement_lower or 'put' in requirement_lower:
            if 'sink' in goal.lower() and any(obj in used_objects for obj in ['Mug', 'Cup', 'Plate']):
                obj = next((obj for obj in ['Mug', 'Cup', 'Plate'] if obj in used_objects), 'Object')
                new_actions.append(f"Driver.PutAOnB('{obj}', 'Sink')")

        elif 'close' in requirement_lower:
            if 'microwave' in requirement_lower or any('microwave' in action.lower() for action in current_actions):
                new_actions.append("Driver.Close('Microwave')")

        elif 'communication' in requirement_lower or 'dialogue' in requirement_lower:
            new_actions.append("Commander.Say('Task completed successfully')")

        return new_actions

    def _apply_consistency_rules(self, actions: List[str]) -> List[str]:
        """Apply consistency rules to ensure logical action sequences"""

        fixed_actions = []
        holding = set()

        for action in actions:
            parsed = ActionParser.parse_action(action)

            if parsed['valid']:
                if parsed['method'] == 'PickUp' and parsed['arguments']:
                    obj = parsed['arguments'][0]
                    if obj not in holding:
                        holding.add(obj)
                        fixed_actions.append(action)

                elif parsed['method'] == 'PutAOnB' and len(parsed['arguments']) >= 2:
                    obj = parsed['arguments'][0]
                    if obj in holding:
                        holding.remove(obj)
                        fixed_actions.append(action)
                    else:
                        # Need to pick up first
                        fixed_actions.append(f"Driver.PickUp('{obj}')")
                        fixed_actions.append(action)

                else:
                    fixed_actions.append(action)
            else:
                fixed_actions.append(action)

        return fixed_actions
