#!/usr/bin/env python3

import re
from typing import List, Dict, Any, Optional
from .base_judge import BaseJudge
from shared.llm_providers.base_provider import LLMProvider
from shared.utils.logging_utils import LoggerMixin

class LLMJudge(BaseJudge, LoggerMixin):
    def __init__(self, provider: LLMProvider, name: str = None):
        super().__init__(name or str(provider))
        self.provider = provider
        self.system_prompt = (
            "You are a Judge Agent for embodied AI task planning. Your role is to provide thoughtful, "
            "natural language feedback on action sequences. You should:\n\n"
            "1. Analyze each action's purpose and relevance to the goal\n"
            "2. Explain your reasoning in clear, conversational language\n"
            "3. Point out redundant or unnecessary actions with detailed explanations\n"
            "4. Identify missing actions needed to complete the goal\n"
            "5. Focus on being helpful and constructive in your feedback\n\n"
            "Provide your feedback as natural language commentary, using #REMOVE and #MISSING tags "
            "only when necessary for clarity. Prioritize clear explanations over rigid formatting."
        )

    def judge_plan(self, action_sequence: List[str], goal: str) -> Dict[str, Any]:
        """Step 2 & 4: Judge the action sequence and provide detailed feedback"""
        self.logger.info(f"Judging plan with {len(action_sequence)} actions for goal: {goal}")

        actions_text = "\n".join([f"{i+1}. {action}" for i, action in enumerate(action_sequence)])

        prompt = (
            f"Please evaluate this action sequence for achieving the following goal:\n\n"
            f"GOAL: {goal}\n\n"
            f"Action Sequence:\n{actions_text}\n\n"
            f"Provide line-by-line analysis of each action. For each action, explain what it does "
            f"and whether it's necessary for the goal. Use this format:\n\n"
            f"ACTION: [copy the exact action]\n"
            f"ANNOTATION: [explain what this action does and whether it's needed for the goal. "
            f"If the action should be removed, include '#REMOVE: reason'. If it's good, just explain why.]\n\n"
            f"After analyzing all actions, if any steps are missing to complete the goal, add:\n"
            f"#MISSING: [describe what actions are needed]\n\n"
            f"Be thorough and conversational in your explanations. Focus on helping someone understand "
            f"why each action is or isn't necessary for achieving the goal.\n\n"
            f"Your line-by-line analysis:"
        )

        response = self.provider.generate(prompt, self.system_prompt)
        result = self._parse_judge_response(response, action_sequence)

        self.logger.debug(f"Judge feedback: {len(result['remove_actions'])} removals, "
                         f"{len(result['missing_requirements'])} missing requirements")

        return result

    def get_natural_language_feedback(self, action_sequence: List[str], goal: str) -> str:
        """Get pure natural language feedback without structured parsing"""
        self.logger.info(f"Getting natural language feedback for goal: {goal}")

        actions_text = "\n".join([f"{i+1}. {action}" for i, action in enumerate(action_sequence)])

        prompt = (
            f"Please provide conversational feedback on this action sequence:\n\n"
            f"GOAL: {goal}\n\n"
            f"Action Sequence:\n{actions_text}\n\n"
            f"Review this plan as if you were discussing it with a colleague. Explain what works well, "
            f"what seems problematic, and what might be missing. Be natural and thorough in your analysis."
        )

        return self.provider.generate(prompt, self.system_prompt)

    def _parse_judge_response(self, response: str, original_actions: List[str]) -> Dict[str, Any]:
        """Parse the judge's response into structured feedback"""
        annotated_actions = []
        missing_requirements = []

        lines = response.split('\n')
        current_action = None
        current_annotation = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if line.startswith('ACTION:'):
                if current_action and current_annotation:
                    annotated_actions.append({
                        'action': current_action,
                        'annotation': current_annotation,
                        'remove': '#REMOVE:' in current_annotation,
                        'remove_reason': self._extract_tag_content(current_annotation, '#REMOVE:')
                    })

                current_action = line.replace('ACTION:', '').strip()
                current_annotation = None

            elif line.startswith('ANNOTATION:'):
                current_annotation = line.replace('ANNOTATION:', '').strip()

            elif '#MISSING:' in line:
                missing_req = self._extract_tag_content(line, '#MISSING:')
                if missing_req:
                    missing_requirements.append(missing_req)

        if current_action and current_annotation:
            annotated_actions.append({
                'action': current_action,
                'annotation': current_annotation,
                'remove': '#REMOVE:' in current_annotation,
                'remove_reason': self._extract_tag_content(current_annotation, '#REMOVE:')
            })

        for line in response.split('\n'):
            if '#MISSING:' in line and not line.startswith('ANNOTATION:'):
                missing_req = self._extract_tag_content(line, '#MISSING:')
                if missing_req and missing_req not in missing_requirements:
                    missing_requirements.append(missing_req)

        return {
            'natural_language_feedback': response,
            'annotated_actions': annotated_actions,
            'remove_actions': [item for item in annotated_actions if item['remove']],
            'missing_requirements': missing_requirements,
            'has_changes': len([item for item in annotated_actions if item['remove']]) > 0 or len(missing_requirements) > 0,
            'raw_response': response
        }

    def _extract_tag_content(self, text: str, tag: str) -> Optional[str]:
        """Extract content after a specific tag"""
        if tag not in text:
            return None

        parts = text.split(tag, 1)
        if len(parts) < 2:
            return None

        content = parts[1].strip()
        content = re.sub(r'#\w+:.*$', '', content).strip()
        return content if content else None

    def compare_plans(self, plan1: List[str], plan2: List[str], goal: str) -> Dict[str, Any]:
        """Compare two plans and determine which is better"""
        self.logger.info(f"Comparing two plans for goal: {goal}")

        plan1_text = "\n".join([f"{i+1}. {action}" for i, action in enumerate(plan1)])
        plan2_text = "\n".join([f"{i+1}. {action}" for i, action in enumerate(plan2)])

        prompt = (
            f"I have two different approaches to achieving this goal and would like your analysis:\n\n"
            f"GOAL: {goal}\n\n"
            f"Plan A:\n{plan1_text}\n\n"
            f"Plan B:\n{plan2_text}\n\n"
            f"Please compare these plans thoughtfully. Consider their completeness, efficiency, "
            f"and logical flow. What are the strengths and weaknesses of each approach? "
            f"Which would you recommend and why? Explain your reasoning as if you were "
            f"advising someone on the best way to accomplish this task."
        )

        response = self.provider.generate(prompt, self.system_prompt)

        return {
            'comparison': response,
            'plan1': plan1,
            'plan2': plan2,
            'goal': goal
        }
