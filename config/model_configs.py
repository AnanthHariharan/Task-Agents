#!/usr/bin/env python3

from dataclasses import dataclass
from typing import Dict, Any, Optional

@dataclass
class ModelConfig:
    """Configuration for a specific model"""
    
    provider: str
    model_name: str
    temperature: float = 0.3
    max_tokens: int = 512
    rate_limit_delay: float = 1.0
    
    # Provider-specific settings
    additional_params: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.additional_params is None:
            self.additional_params = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'provider': self.provider,
            'model_name': self.model_name,
            'temperature': self.temperature,
            'max_tokens': self.max_tokens,
            'rate_limit_delay': self.rate_limit_delay,
            'additional_params': self.additional_params
        }

# Default model configurations
DEFAULT_MODEL_CONFIGS = {
    "openai_gpt4o_mini": ModelConfig(
        provider="openai",
        model_name="gpt-4o-mini",
        temperature=0.3,
        max_tokens=512,
        rate_limit_delay=1.0
    ),
    
    "deepseek_r1": ModelConfig(
        provider="deepseek", 
        model_name="deepseek-r1",
        temperature=0.3,
        max_tokens=512,
        rate_limit_delay=1.0
    ),
    
    "gemini_2_5_flash": ModelConfig(
        provider="gemini",
        model_name="gemini-2.5-flash", 
        temperature=0.3,
        max_tokens=512,
        rate_limit_delay=1.0
    ),
    
    "llama_4_scout": ModelConfig(
        provider="llama",
        model_name="llama4-scout",
        temperature=0.3,
        max_tokens=512,
        rate_limit_delay=2.0  # Slower for local models
    )
}

# Specialized configurations for different use cases
PLANNER_CONFIGS = {
    name: ModelConfig(
        provider=config.provider,
        model_name=config.model_name,
        temperature=0.2,  # Lower temperature for more focused planning
        max_tokens=1024,  # More tokens for complex plan modifications
        rate_limit_delay=config.rate_limit_delay
    )
    for name, config in DEFAULT_MODEL_CONFIGS.items()
}

JUDGE_CONFIGS = {
    name: ModelConfig(
        provider=config.provider,
        model_name=config.model_name,
        temperature=0.1,  # Very low temperature for consistent evaluation
        max_tokens=768,   # Medium tokens for detailed feedback
        rate_limit_delay=config.rate_limit_delay
    )
    for name, config in DEFAULT_MODEL_CONFIGS.items()
}

def get_model_config(config_type: str, model_name: str) -> Optional[ModelConfig]:
    """Get model configuration by type and name"""
    configs = {
        'default': DEFAULT_MODEL_CONFIGS,
        'planner': PLANNER_CONFIGS,
        'judge': JUDGE_CONFIGS
    }
    
    config_dict = configs.get(config_type, DEFAULT_MODEL_CONFIGS)
    return config_dict.get(model_name)