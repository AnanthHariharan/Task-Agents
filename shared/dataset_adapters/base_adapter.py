#!/usr/bin/env python3

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
import json
import os
from pathlib import Path

class UniversalDatasetAdapter(ABC):
    """
    Base adapter for converting any embodied AI dataset to universal format.
    
    This enables the Task-Agents framework to work with multiple datasets
    (TEACh, ALFReD, Habitat, etc.) through a standardized interface.
    """
    
    def __init__(self, dataset_path: str, name: str):
        """
        Initialize the dataset adapter.
        
        Args:
            dataset_path: Path to the dataset files
            name: Human-readable name for this dataset
        """
        self.dataset_path = Path(dataset_path)
        self.name = name
        self._episodes_cache = {}
    
    @abstractmethod
    def load_episodes(self, split: str = "train", limit: Optional[int] = None) -> List[Dict]:
        """
        Load episodes from the dataset.
        
        Args:
            split: Dataset split ('train', 'val', 'test')
            limit: Maximum number of episodes to load
            
        Returns:
            List of episode dictionaries in raw dataset format
        """
        pass
    
    @abstractmethod
    def parse_action_sequence(self, episode: Dict) -> List[str]:
        """
        Extract action sequence from episode in standardized format.
        
        Args:
            episode: Raw episode dictionary
            
        Returns:
            List of action strings in format "Agent.Method(args)"
        """
        pass
    
    @abstractmethod
    def extract_goal(self, episode: Dict) -> str:
        """
        Extract task goal description from episode.
        
        Args:
            episode: Raw episode dictionary
            
        Returns:
            Natural language description of the task goal
        """
        pass
    
    @abstractmethod
    def get_domain(self) -> str:
        """
        Get the domain/category this dataset represents.
        
        Returns:
            Domain string (e.g., 'household_tasks', 'navigation', 'manipulation')
        """
        pass
    
    @abstractmethod
    def get_action_space(self) -> Dict[str, List[str]]:
        """
        Get the action space definition for this dataset.
        
        Returns:
            Dictionary mapping agent types to available methods
        """
        pass
    
    def get_episode_id(self, episode: Dict) -> str:
        """
        Extract unique episode identifier.
        
        Args:
            episode: Raw episode dictionary
            
        Returns:
            Unique episode identifier string
        """
        # Default implementation - subclasses can override
        return episode.get('episode_id', episode.get('id', 'unknown'))
    
    def extract_metadata(self, episode: Dict) -> Dict[str, Any]:
        """
        Extract additional metadata from episode.
        
        Args:
            episode: Raw episode dictionary
            
        Returns:
            Dictionary of metadata (scene info, difficulty, etc.)
        """
        # Default implementation - subclasses can override
        metadata = {}
        for key in ['scene_id', 'difficulty', 'task_type', 'duration']:
            if key in episode:
                metadata[key] = episode[key]
        return metadata
    
    def to_universal_format(self, episode: Dict) -> Dict[str, Any]:
        """
        Convert episode to standardized universal format.
        
        Args:
            episode: Raw episode dictionary
            
        Returns:
            Standardized episode dictionary
        """
        return {
            'episode_id': self.get_episode_id(episode),
            'dataset': self.name,
            'domain': self.get_domain(),
            'goal': self.extract_goal(episode),
            'actions': self.parse_action_sequence(episode),
            'action_space': self.get_action_space(),
            'metadata': self.extract_metadata(episode),
            'raw_episode': episode  # Keep original for debugging
        }
    
    def get_schema(self) -> Dict[str, Any]:
        """
        Get dataset schema information.
        
        Returns:
            Schema dictionary with dataset structure info
        """
        return {
            'name': self.name,
            'domain': self.get_domain(),
            'action_space': self.get_action_space(),
            'supported_splits': self.get_supported_splits(),
            'episode_fields': self.get_episode_fields()
        }
    
    def get_supported_splits(self) -> List[str]:
        """
        Get supported dataset splits.
        
        Returns:
            List of supported split names
        """
        # Default implementation - subclasses can override
        return ['train', 'val', 'test']
    
    def get_episode_fields(self) -> List[str]:
        """
        Get fields available in each episode.
        
        Returns:
            List of field names available in universal format
        """
        return [
            'episode_id', 'dataset', 'domain', 'goal', 
            'actions', 'action_space', 'metadata', 'raw_episode'
        ]
    
    def validate_episode(self, episode: Dict) -> Tuple[bool, List[str]]:
        """
        Validate that an episode has required fields.
        
        Args:
            episode: Episode dictionary to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        try:
            # Test that we can extract required fields
            goal = self.extract_goal(episode)
            if not goal or not isinstance(goal, str):
                errors.append("Invalid or missing goal")
                
            actions = self.parse_action_sequence(episode)
            if not actions or not isinstance(actions, list):
                errors.append("Invalid or missing action sequence")
                
            episode_id = self.get_episode_id(episode)
            if not episode_id:
                errors.append("Invalid or missing episode ID")
                
        except Exception as e:
            errors.append(f"Error parsing episode: {str(e)}")
        
        return len(errors) == 0, errors
    
    def sample_episodes(self, 
                       split: str = "train", 
                       n_samples: int = 10, 
                       seed: Optional[int] = None) -> List[Dict]:
        """
        Sample random episodes from the dataset.
        
        Args:
            split: Dataset split to sample from
            n_samples: Number of episodes to sample
            seed: Random seed for reproducibility
            
        Returns:
            List of sampled episodes in universal format
        """
        if seed is not None:
            import random
            random.seed(seed)
        
        all_episodes = self.load_episodes(split)
        
        if n_samples >= len(all_episodes):
            sampled_episodes = all_episodes
        else:
            import random
            sampled_episodes = random.sample(all_episodes, n_samples)
        
        return [self.to_universal_format(ep) for ep in sampled_episodes]
    
    def get_statistics(self, split: str = "train") -> Dict[str, Any]:
        """
        Get dataset statistics.
        
        Args:
            split: Dataset split to analyze
            
        Returns:
            Dictionary of dataset statistics
        """
        episodes = self.load_episodes(split, limit=1000)  # Sample for stats
        
        if not episodes:
            return {'total_episodes': 0}
        
        action_lengths = []
        domains = set()
        
        for episode in episodes:
            try:
                actions = self.parse_action_sequence(episode)
                action_lengths.append(len(actions))
                domains.add(self.get_domain())
            except Exception:
                continue
        
        stats = {
            'total_episodes': len(episodes),
            'avg_sequence_length': sum(action_lengths) / len(action_lengths) if action_lengths else 0,
            'min_sequence_length': min(action_lengths) if action_lengths else 0,
            'max_sequence_length': max(action_lengths) if action_lengths else 0,
            'domains': list(domains),
            'action_space': self.get_action_space()
        }
        
        return stats