#!/usr/bin/env python3

import os
import time
from typing import Optional
from .base_provider import LLMProvider

class GeminiProvider(LLMProvider):
    """Google Gemini 2.5 Flash provider"""
    
    def __init__(self, model_name: str = "gemini-2.5-flash", **kwargs):
        super().__init__(model_name, **kwargs)
        try:
            import google.generativeai as genai
            genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
            self.model = genai.GenerativeModel(model_name)
        except ImportError:
            raise ImportError("google-generativeai package is required for Gemini provider")
    
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