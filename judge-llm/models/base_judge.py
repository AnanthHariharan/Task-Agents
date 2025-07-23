#!/usr/bin/env python3

from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseJudge(ABC):
    """Abstract base class for all judge agents"""
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    def judge_plan(self, action_sequence: List[str], goal: str) -> Dict[str, Any]:
        """Evaluate an action sequence and provide feedback"""
        pass
    
    @abstractmethod
    def compare_plans(self, plan1: List[str], plan2: List[str], goal: str) -> Dict[str, Any]:
        """Compare two action sequences"""
        pass
    
    def __str__(self):
        return f"{self.__class__.__name__}({self.name})"
    
    def __repr__(self):
        return self.__str__()