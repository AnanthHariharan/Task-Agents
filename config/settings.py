#!/usr/bin/env python3

import os
from dataclasses import dataclass
from typing import Dict, Any, Optional
from pathlib import Path

@dataclass
class Settings:
    """Global settings for the Task-Agents system"""
    
    # Project paths
    project_root: str = str(Path(__file__).parent.parent)
    data_dir: str = "data"
    outputs_dir: str = "outputs"
    logs_dir: str = "logs"
    
    # Model settings
    default_temperature: float = 0.3
    default_max_tokens: int = 512
    rate_limit_delay: float = 1.0
    
    # Workflow settings
    max_iterations: int = 5
    convergence_threshold: int = 2
    
    # Experiment settings
    default_test_samples: int = 10
    save_intermediate_results: bool = True
    
    # Logging settings
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    @classmethod
    def from_env(cls) -> 'Settings':
        """Create settings from environment variables"""
        return cls(
            default_temperature=float(os.getenv('TASK_AGENTS_TEMPERATURE', '0.3')),
            default_max_tokens=int(os.getenv('TASK_AGENTS_MAX_TOKENS', '512')),
            rate_limit_delay=float(os.getenv('TASK_AGENTS_RATE_LIMIT', '1.0')),
            max_iterations=int(os.getenv('TASK_AGENTS_MAX_ITERATIONS', '5')),
            convergence_threshold=int(os.getenv('TASK_AGENTS_CONVERGENCE_THRESHOLD', '2')),
            log_level=os.getenv('TASK_AGENTS_LOG_LEVEL', 'INFO')
        )
    
    def get_path(self, relative_path: str) -> str:
        """Get absolute path relative to project root"""
        return os.path.join(self.project_root, relative_path)
    
    def ensure_directories(self):
        """Ensure all required directories exist"""
        dirs = [
            self.get_path(self.data_dir),
            self.get_path(self.outputs_dir),
            self.get_path(self.logs_dir),
            self.get_path(os.path.join(self.outputs_dir, "experiments")),
            self.get_path(os.path.join(self.outputs_dir, "analysis")),
            self.get_path(os.path.join(self.outputs_dir, "visualizations"))
        ]
        
        for dir_path in dirs:
            Path(dir_path).mkdir(parents=True, exist_ok=True)

# Global settings instance
settings = Settings.from_env()