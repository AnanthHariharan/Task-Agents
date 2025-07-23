#!/usr/bin/env python3

import os
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

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

class OpenAIProvider(LLMProvider):
    """OpenAI GPT provider"""
    
    def __init__(self, model_name: str = "gpt-4o-mini", **kwargs):
        super().__init__(model_name, **kwargs)
        from openai import OpenAI
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            time.sleep(self.rate_limit_delay)
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error with OpenAI {self.model_name}: {e}")
            return f"ERROR: {str(e)}"

class DeepSeekProvider(LLMProvider):
    """DeepSeek-R1 provider"""
    
    def __init__(self, model_name: str = "deepseek-r1", **kwargs):
        super().__init__(model_name, **kwargs)
        # Note: Replace with actual DeepSeek client initialization
        # This is a placeholder implementation
        self.api_key = os.environ.get("DEEPSEEK_API_KEY")
        self.base_url = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        try:
            # Placeholder for DeepSeek API call
            # Replace with actual DeepSeek client implementation
            import requests
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            data = {
                "model": self.model_name,
                "messages": messages,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens
            }
            
            response = requests.post(f"{self.base_url}/chat/completions", 
                                   headers=headers, json=data)
            response.raise_for_status()
            
            time.sleep(self.rate_limit_delay)
            return response.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            print(f"Error with DeepSeek {self.model_name}: {e}")
            return f"ERROR: {str(e)}"

class GeminiProvider(LLMProvider):
    """Google Gemini 2.5 Flash provider"""
    
    def __init__(self, model_name: str = "gemini-2.5-flash", **kwargs):
        super().__init__(model_name, **kwargs)
        import google.generativeai as genai
        genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
        self.model = genai.GenerativeModel(model_name)
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        try:
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"System: {system_prompt}\n\nUser: {prompt}"
            
            response = self.model.generate_content(
                full_prompt,
                generation_config={
                    "temperature": self.temperature,
                    "max_output_tokens": self.max_tokens,
                }
            )
            time.sleep(self.rate_limit_delay)
            return response.text.strip()
        except Exception as e:
            print(f"Error with Gemini {self.model_name}: {e}")
            return f"ERROR: {str(e)}"

class LlamaProvider(LLMProvider):
    """LLaMA 4 Scout provider (via Ollama or API)"""
    
    def __init__(self, model_name: str = "llama4-scout", **kwargs):
        super().__init__(model_name, **kwargs)
        # Note: Replace with actual LLaMA client initialization
        self.base_url = os.environ.get("LLAMA_BASE_URL", "http://localhost:11434")
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        try:
            # Placeholder for LLaMA API call via Ollama
            import requests
            
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"System: {system_prompt}\n\nUser: {prompt}"
            
            data = {
                "model": self.model_name,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": self.temperature,
                    "num_predict": self.max_tokens
                }
            }
            
            response = requests.post(f"{self.base_url}/api/generate", json=data)
            response.raise_for_status()
            
            time.sleep(self.rate_limit_delay)
            return response.json().get("response", "").strip()
        except Exception as e:
            print(f"Error with LLaMA {self.model_name}: {e}")
            return f"ERROR: {str(e)}"

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

# Default model configurations
DEFAULT_MODELS = {
    "openai": "gpt-4o-mini",
    "deepseek": "deepseek-r1",
    "gemini": "gemini-2.5-flash",
    "llama": "llama4-scout"
}