"""
LLM Provider implementations for multi-model support.
"""

from .base_provider import LLMProvider
from .openai_provider import OpenAIProvider
from .deepseek_provider import DeepSeekProvider
from .gemini_provider import GeminiProvider
from .llama_provider import LlamaProvider

__all__ = [
    'LLMProvider',
    'OpenAIProvider', 
    'DeepSeekProvider',
    'GeminiProvider',
    'LlamaProvider'
]

# Default model configurations
DEFAULT_MODELS = {
    "openai": "gpt-4o-mini",
    "deepseek": "deepseek-r1", 
    "gemini": "gemini-2.5-flash",
    "llama": "llama4-scout"
}

def get_provider(provider_name: str, model_name: str = None, **kwargs) -> LLMProvider:
    """Factory function to get LLM provider"""
    providers = {
        "openai": OpenAIProvider,
        "deepseek": DeepSeekProvider,
        "gemini": GeminiProvider,
        "llama": LlamaProvider
    }
    
    provider_class = providers.get(provider_name.lower())
    if not provider_class:
        raise ValueError(f"Unknown provider: {provider_name}")
    
    if model_name:
        return provider_class(model_name, **kwargs)
    else:
        return provider_class(**kwargs)