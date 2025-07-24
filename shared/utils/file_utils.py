#!/usr/bin/env python3

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path

class FileManager:
    """Utility class for file operations"""
    
    @staticmethod
    def ensure_dir(path: str) -> None:
        """Ensure directory exists, create if it doesn't"""
        Path(path).mkdir(parents=True, exist_ok=True)
    
    @staticmethod
    def load_json(filepath: str) -> Any:
        """Load JSON file with error handling"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {filepath}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {filepath}: {e}")
    
    @staticmethod
    def save_json(data: Any, filepath: str, indent: int = 2) -> None:
        """Save data to JSON file"""
        FileManager.ensure_dir(os.path.dirname(filepath))
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
    
    @staticmethod
    def load_text(filepath: str) -> str:
        """Load text file"""
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    
    @staticmethod
    def save_text(text: str, filepath: str) -> None:
        """Save text to file"""
        FileManager.ensure_dir(os.path.dirname(filepath))
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(text)
    
    @staticmethod
    def generate_timestamped_filename(base_name: str, extension: str = '.json') -> str:
        """Generate filename with timestamp"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{base_name}_{timestamp}{extension}"
    
    @staticmethod
    def get_latest_file(directory: str, pattern: str = "*") -> Optional[str]:
        """Get the most recently modified file matching pattern"""
        files = list(Path(directory).glob(pattern))
        if not files:
            return None
        return str(max(files, key=lambda f: f.stat().st_mtime))
    
    @staticmethod
    def list_files(directory: str, extension: str = None) -> List[str]:
        """List files in directory, optionally filtered by extension"""
        path = Path(directory)
        if not path.exists():
            return []
        
        if extension:
            pattern = f"*.{extension.lstrip('.')}"
            return [str(f) for f in path.glob(pattern)]
        else:
            return [str(f) for f in path.iterdir() if f.is_file()]