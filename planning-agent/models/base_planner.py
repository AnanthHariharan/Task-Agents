#!/usr/bin/env python3

from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BasePlanner(ABC):
    """Abstract base class for all planning agents"""
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    def annotate_goal(self, action_sequence: List[str], context: str = "") -> str:
        """Analyze action sequence and identify the goal"""
        pass
    
    @abstractmethod
    def modify_plan(self, action_sequence: List[str], judge_feedback: str, goal: str) -> List[str]:
        """Modify the plan based on judge feedback"""
        pass
    
    @abstractmethod
    def generate_missing_actions(self, goal: str, current_actions: List[str], 
                               missing_requirement: str) -> List[str]:
        """Generate actions to fulfill missing requirements"""
        pass
    
    def __str__(self):
        return f"{self.__class__.__name__}({self.name})"
    
    def __repr__(self):
        return self.__str__()