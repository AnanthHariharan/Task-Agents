#!/usr/bin/env python3

import os
import time
import requests
from typing import Optional
from .base_provider import LLMProvider

class LlamaProvider(LLMProvider):
    """LLaMA 4 Scout provider (via Ollama or API)"""
    
    def __init__(self, model_name: str = "llama4-scout", **kwargs):
        super().__init__(model_name, **kwargs)
        self.base_url = os.environ.get("LLAMA_BASE_URL", "http://localhost:11434")
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        try:
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
            
            response = requests.post(f"{self.base_url}/api/generate", 
                                   json=data, timeout=60)
            response.raise_for_status()
            
            time.sleep(self.rate_limit_delay)
            return response.json().get("response", "").strip()
        except Exception as e:
            print(f"Error with LLaMA {self.model_name}: {e}")
            return f"ERROR: {str(e)}"