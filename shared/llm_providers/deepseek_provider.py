#!/usr/bin/env python3

import os
import time
import requests
from typing import Optional
from .base_provider import LLMProvider

class DeepSeekProvider(LLMProvider):
    """DeepSeek-R1 provider"""
    
    def __init__(self, model_name: str = "deepseek-r1", **kwargs):
        super().__init__(model_name, **kwargs)
        self.api_key = os.environ.get("DEEPSEEK_API_KEY")
        self.base_url = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        try:
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
                                   headers=headers, json=data, timeout=30)
            response.raise_for_status()
            
            time.sleep(self.rate_limit_delay)
            return response.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            print(f"Error with DeepSeek {self.model_name}: {e}")
            return f"ERROR: {str(e)}"