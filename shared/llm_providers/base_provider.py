#!/usr/bin/env python3

import time
from abc import ABC, abstractmethod
from typing import Optional

class LLMProvider(ABC):
    """Abstract base class for all LLM providers"""
    
    def __init__(self, model_name: str, temperature: float = 0.3, max_tokens: int = 512):
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.rate_limit_delay = 1.0  # Default delay between calls
    
    @abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate response from the LLM"""
        pass
    
    def __str__(self):
        return f"{self.__class__.__name__}({self.model_name})"
    
    def __repr__(self):
        return self.__str__()