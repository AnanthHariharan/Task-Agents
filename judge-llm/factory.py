#!/usr/bin/env python3

from typing import Dict
from .models import BaseJudge, LLMJudge
from .models.rule_based_judge import RuleBasedJudge
from shared.llm_providers import get_provider, DEFAULT_MODELS

class JudgeFactory:
    """Factory to create Judge agents with different providers"""
    
    @staticmethod
    def create_judge(provider_name: str, model_name: str = None, **kwargs) -> BaseJudge:
        """Create a single judge"""
        if provider_name.lower() == "rule_based":
            return RuleBasedJudge(name=model_name or "RuleBased")
        
        provider = get_provider(provider_name, model_name, **kwargs)
        return LLMJudge(provider)
    
    @staticmethod
    def create_all_judges(include_rule_based: bool = True, **kwargs) -> Dict[str, BaseJudge]:
        """Create judges for all available providers"""
        judges = {}
        
        # Add LLM-based judges
        for provider_name, model_name in DEFAULT_MODELS.items():
            try:
                judges[provider_name] = JudgeFactory.create_judge(
                    provider_name, model_name, **kwargs
                )
            except Exception as e:
                print(f"Failed to create {provider_name} judge: {e}")
        
        # Add rule-based judge
        if include_rule_based:
            try:
                judges["rule_based"] = RuleBasedJudge()
            except Exception as e:
                print(f"Failed to create rule-based judge: {e}")
        
        return judges