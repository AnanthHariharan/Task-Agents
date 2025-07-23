#!/usr/bin/env python3

import re
from typing import List, Dict, Any, Optional
from .base_judge import BaseJudge
from shared.llm_providers.base_provider import LLMProvider
from shared.utils.logging_utils import LoggerMixin

class LLMJudge(BaseJudge, LoggerMixin):
    """LLM-based judge agent"""
    
    def __init__(self, provider: LLMProvider, name: str = None):
        super().__init__(name or str(provider))
        self.provider = provider
        self.system_prompt = (
            "You are a Judge Agent for embodied AI task planning. Your role is to:\n"
            "1. Analyze action sequences for completeness and efficiency\n"
            "2. Annotate each action with its purpose and relevance\n"
            "3. Identify redundant actions and mark them with #REMOVE\n"
            "4. Identify missing actions and mark them with #MISSING\n"
            "5. Provide clear natural language justifications for all feedback\n\n"
            "Be thorough but fair in your analysis. Focus on task completion and efficiency."
        )
    
    def judge_plan(self, action_sequence: List[str], goal: str) -> Dict[str, Any]:
        """Step 2 & 4: Judge the action sequence and provide detailed feedback"""
        self.logger.info(f"Judging plan with {len(action_sequence)} actions for goal: {goal}")
        
        actions_text = "\n".join([f"{i+1}. {action}" for i, action in enumerate(action_sequence)])
        
        prompt = (
            f"Evaluate this action sequence for the given goal:\n\n"
            f"GOAL: {goal}\n\n"
            f"Action Sequence:\n{actions_text}\n\n"
            f"For each action, provide:\n"
            f"1. A brief annotation explaining what the action does\n"
            f"2. Mark redundant/unnecessary actions with '#REMOVE: <reason>'\n"
            f"3. At the end, if actions are missing, add '#MISSING: <requirements>'\n\n"
            f"Rules for #REMOVE tags:\n"
            f"- ToggleOff actions before any ToggleOn actions\n"
            f"- PickUp actions for objects irrelevant to the goal\n"
            f"- Consecutive Move/Turn actions that cancel each other\n"
            f"- Any action that doesn't contribute to achieving the goal\n\n"
            f"Rules for #MISSING tags:\n"
            f"- Actions needed to complete the goal that aren't present\n"
            f"- Safety actions (e.g., turning off devices after use)\n"
            f"- Logical prerequisites (e.g., opening containers before accessing contents)\n\n"
            f"Format your response as:\n"
            f"ACTION: <action>\n"
            f"ANNOTATION: <explanation> [#REMOVE: <reason>] OR [#MISSING: <requirement>]\n\n"
            f"Provide feedback:"
        )
        
        response = self.provider.generate(prompt, self.system_prompt)
        result = self._parse_judge_response(response, action_sequence)
        
        self.logger.debug(f"Judge feedback: {len(result['remove_actions'])} removals, "
                         f"{len(result['missing_requirements'])} missing requirements")
        
        return result
    
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
                # Save previous action if exists
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
        
        # Don't forget the last action
        if current_action and current_annotation:
            annotated_actions.append({
                'action': current_action,
                'annotation': current_annotation,
                'remove': '#REMOVE:' in current_annotation,
                'remove_reason': self._extract_tag_content(current_annotation, '#REMOVE:')
            })
        
        # Extract global missing requirements from the full response
        for line in response.split('\n'):
            if '#MISSING:' in line and not line.startswith('ANNOTATION:'):
                missing_req = self._extract_tag_content(line, '#MISSING:')
                if missing_req and missing_req not in missing_requirements:
                    missing_requirements.append(missing_req)
        
        return {
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
        # Remove any trailing tags or formatting
        content = re.sub(r'#\w+:.*$', '', content).strip()
        return content if content else None
    
    def compare_plans(self, plan1: List[str], plan2: List[str], goal: str) -> Dict[str, Any]:
        """Compare two plans and determine which is better"""
        self.logger.info(f"Comparing two plans for goal: {goal}")
        
        plan1_text = "\n".join([f"{i+1}. {action}" for i, action in enumerate(plan1)])
        plan2_text = "\n".join([f"{i+1}. {action}" for i, action in enumerate(plan2)])
        
        prompt = (
            f"Compare these two action sequences for achieving the goal:\n\n"
            f"GOAL: {goal}\n\n"
            f"Plan A:\n{plan1_text}\n\n"
            f"Plan B:\n{plan2_text}\n\n"
            f"Evaluate both plans on:\n"
            f"1. Completeness (achieves the goal)\n"
            f"2. Efficiency (minimal unnecessary actions)\n"
            f"3. Logical flow (actions in correct order)\n\n"
            f"Which plan is better and why? Provide detailed reasoning."
        )
        
        response = self.provider.generate(prompt, self.system_prompt)
        
        return {
            'comparison': response,
            'plan1': plan1,
            'plan2': plan2,
            'goal': goal
        }