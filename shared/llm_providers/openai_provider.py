#!/usr/bin/env python3

import os
import time
from typing import Optional
from .base_provider import LLMProvider

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