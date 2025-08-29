#!/usr/bin/env python3

import re
from typing import List, Dict, Any
from .base_planner import BasePlanner
from shared.llm_providers.base_provider import LLMProvider
from shared.utils.logging_utils import LoggerMixin

class LLMPlanner(BasePlanner, LoggerMixin):
    def __init__(self, provider: LLMProvider, name: str = None):
        super().__init__(name or str(provider))
        self.provider = provider
        self.system_prompt = (
            "You are a Planning Agent for embodied AI tasks. Your role is to:\n"
            "1. Analyze action sequences and identify their goals\n"
            "2. Modify action sequences based on feedback from a Judge\n"
            "3. Remove redundant actions and add missing actions as needed\n"
            "4. Ensure action sequences are efficient and complete\n\n"
            "Always preserve the original format and only make necessary changes."
        )

    def annotate_goal(self, action_sequence: List[str], context: str = "") -> str:
        """Step 1: Annotate the goal of an action sequence"""
        self.logger.info(f"Annotating goal for sequence with {len(action_sequence)} actions")

        actions_text = "\n".join(action_sequence)

        prompt = (
            f"Analyze the following action sequence and determine the overall goal:\n\n"
            f"Context: {context}\n"
            f"Actions:\n{actions_text}\n\n"
            f"Provide a concise goal statement starting with 'GOAL: '"
        )

        response = self.provider.generate(prompt, self.system_prompt)

        if not response.startswith("GOAL:"):
            response = f"GOAL: {response}"

        self.logger.debug(f"Identified goal: {response}")
        return response.strip()

    def modify_plan(self, action_sequence: List[str], judge_feedback: str, goal: str) -> List[str]:
        """Step 3: Modify the plan based on judge feedback"""
        self.logger.info(f"Modifying plan based on judge feedback")

        actions_text = "\n".join(action_sequence)

        prompt = (
            f"You received feedback from a Judge about this action sequence. "
            f"Modify the plan accordingly:\n\n"
            f"GOAL: {goal}\n\n"
            f"Current Action Sequence:\n{actions_text}\n\n"
            f"Judge Feedback:\n{judge_feedback}\n\n"
            f"Instructions:\n"
            f"1. Remove any actions marked with #REMOVE\n"
            f"2. Add actions to address any #MISSING requirements\n"
            f"3. Preserve dialogue actions (Driver.Say, Commander.Say) unless explicitly marked for removal\n"
            f"4. Maintain the logical flow of the action sequence\n"
            f"5. Return the modified action sequence, one action per line\n\n"
            f"Modified Action Sequence:"
        )

        response = self.provider.generate(prompt, self.system_prompt)

        modified_actions = []
        for line in response.split('\n'):
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('Modified'):
                line = re.sub(r'^\d+\.\s*', '', line)
                line = re.sub(r'^-\s*', '', line)
                modified_actions.append(line)

        self.logger.debug(f"Modified plan: {len(action_sequence)} -> {len(modified_actions)} actions")
        return modified_actions

    def generate_missing_actions(self, goal: str, current_actions: List[str],
                               missing_requirement: str) -> List[str]:
        """Generate new actions to fulfill missing requirements"""
        self.logger.info(f"Generating actions for missing requirement: {missing_requirement}")

        actions_text = "\n".join(current_actions)

        prompt = (
            f"Generate additional actions to fulfill this missing requirement:\n\n"
            f"GOAL: {goal}\n"
            f"Current Actions:\n{actions_text}\n\n"
            f"Missing Requirement: {missing_requirement}\n\n"
            f"Generate the minimum necessary actions to fulfill this requirement. "
            f"Use the same format as existing actions (e.g., Driver.PickUp('Object'), Commander.Say('text')).\n"
            f"Return only the new actions, one per line:"
        )

        response = self.provider.generate(prompt, self.system_prompt)

        new_actions = []
        for line in response.split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                new_actions.append(line)

        self.logger.debug(f"Generated {len(new_actions)} new actions")
        return new_actions
