#!/usr/bin/env python3

from typing import Dict
from .models import BasePlanner, LLMPlanner
from .models.rule_based_planner import RuleBasedPlanner
from shared.llm_providers import get_provider, DEFAULT_MODELS

class PlannerFactory:
    """Factory to create Planning agents with different providers"""
    
    @staticmethod
    def create_planner(provider_name: str, model_name: str = None, **kwargs) -> BasePlanner:
        """Create a single planner"""
        if provider_name.lower() == "rule_based":
            return RuleBasedPlanner(name=model_name or "RuleBased")
        
        provider = get_provider(provider_name, model_name, **kwargs)
        return LLMPlanner(provider)
    
    @staticmethod
    def create_all_planners(include_rule_based: bool = True, **kwargs) -> Dict[str, BasePlanner]:
        """Create planners for all available providers"""
        planners = {}
        
        # Add LLM-based planners
        for provider_name, model_name in DEFAULT_MODELS.items():
            try:
                planners[provider_name] = PlannerFactory.create_planner(
                    provider_name, model_name, **kwargs
                )
            except Exception as e:
                print(f"Failed to create {provider_name} planner: {e}")
        
        # Add rule-based planner
        if include_rule_based:
            try:
                planners["rule_based"] = RuleBasedPlanner()
            except Exception as e:
                print(f"Failed to create rule-based planner: {e}")
        
        return planners