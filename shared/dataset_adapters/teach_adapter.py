#!/usr/bin/env python3

import json
import glob
from typing import List, Dict, Any, Optional
from pathlib import Path
from .base_adapter import UniversalDatasetAdapter

class TeachDatasetAdapter(UniversalDatasetAdapter):
    """
    Adapter for the TEACh (Task-driven Embodied Agents that Chat) dataset.
    
    TEACh is a household task dataset where agents perform tasks like
    making coffee, cleaning, cooking while communicating with humans.
    """
    
    def __init__(self, dataset_path: str):
        """
        Initialize TEACh dataset adapter.
        
        Args:
            dataset_path: Path to TEACh dataset directory containing .game.json files
        """
        super().__init__(dataset_path, "TEACh")
        
        # TEACh-specific action mappings
        self.action_mappings = {
            'GotoLocation': 'Move',
            'PickupObject': 'PickUp', 
            'PutObject': 'Place',
            'OpenObject': 'Open',
            'CloseObject': 'Close',
            'ToggleObjectOn': 'ToggleOn',
            'ToggleObjectOff': 'ToggleOff',
            'SliceObject': 'Slice',
            'Navigation': 'Move'
        }
    
    def load_episodes(self, split: str = "train", limit: Optional[int] = None) -> List[Dict]:
        """
        Load TEACh game episodes from .game.json files.
        
        Args:
            split: Dataset split (currently only 'train' supported)
            limit: Maximum number of episodes to load
            
        Returns:
            List of game episode dictionaries
        """
        if split != "train":
            # TEACh dataset structure - adapt as needed
            print(f"Warning: TEACh adapter currently only supports 'train' split, got '{split}'")
        
        # Cache key for this request
        cache_key = f"{split}_{limit}"
        if cache_key in self._episodes_cache:
            return self._episodes_cache[cache_key]
        
        episodes = []
        
        # Load from games/train/ directory
        games_dir = self.dataset_path / "games" / "train"
        if not games_dir.exists():
            # Fallback to direct games/ directory
            games_dir = self.dataset_path / "games"
        
        if not games_dir.exists():
            print(f"Warning: TEACh games directory not found at {games_dir}")
            return []
        
        # Get all .game.json files
        game_files = list(games_dir.glob("*.game.json"))
        
        if limit:
            game_files = game_files[:limit]
        
        print(f"Loading {len(game_files)} TEACh episodes from {games_dir}")
        
        for game_file in game_files:
            try:
                with open(game_file, 'r') as f:
                    episode = json.load(f)
                    episode['_file_path'] = str(game_file)  # Keep track of source
                    episodes.append(episode)
            except Exception as e:
                print(f"Error loading {game_file}: {e}")
                continue
        
        # Cache the results
        self._episodes_cache[cache_key] = episodes
        
        return episodes
    
    def parse_action_sequence(self, episode: Dict) -> List[str]:
        """
        Extract action sequence from TEACh episode.
        
        Args:
            episode: TEACh game episode dictionary
            
        Returns:
            List of standardized action strings
        """
        actions = []
        
        # TEACh episodes contain 'tasks' with action sequences
        if 'tasks' in episode:
            for task in episode['tasks']:
                if 'episodes' in task:
                    for ep in task['episodes']:
                        actions.extend(self._parse_episode_actions(ep))
        
        # Fallback: look for direct action sequences
        elif 'episodes' in episode:
            for ep in episode['episodes']:
                actions.extend(self._parse_episode_actions(ep))
        
        # Another fallback: look for 'interactions' or 'actions'
        elif 'interactions' in episode:
            actions.extend(self._parse_interactions(episode['interactions']))
        
        elif 'actions' in episode:
            actions.extend(self._parse_direct_actions(episode['actions']))
        
        return actions
    
    def _parse_episode_actions(self, episode_data: Dict) -> List[str]:
        """Parse actions from a single episode within a task."""
        actions = []
        
        if 'interactions' in episode_data:
            actions.extend(self._parse_interactions(episode_data['interactions']))
        
        return actions
    
    def _parse_interactions(self, interactions: List[Dict]) -> List[str]:
        """Parse actions from TEACh interactions format."""
        actions = []
        
        for interaction in interactions:
            if interaction.get('action_type') == 'action':
                action_name = interaction.get('action', {}).get('action_type', '')
                
                # Map TEACh action names to standardized format
                standard_action = self.action_mappings.get(action_name, action_name)
                
                # Extract object if present
                obj = None
                if 'object' in interaction.get('action', {}):
                    obj = interaction['action']['object'].get('objectType', '')
                elif 'objectId' in interaction.get('action', {}):
                    obj = interaction['action']['objectId']
                
                # Format as standardized action
                if obj:
                    actions.append(f"Driver.{standard_action}('{obj}')")
                else:
                    actions.append(f"Driver.{standard_action}()")
        
        return actions
    
    def _parse_direct_actions(self, action_list: List) -> List[str]:
        """Parse actions from direct action list format."""
        actions = []
        
        for action in action_list:
            if isinstance(action, str):
                # Already in string format
                if not action.startswith('Driver.'):
                    action = f"Driver.{action}"
                actions.append(action)
            elif isinstance(action, dict):
                # Dictionary format - extract action info
                action_type = action.get('action_type', action.get('type', ''))
                standard_action = self.action_mappings.get(action_type, action_type)
                
                obj = action.get('object', action.get('objectType', ''))
                if obj:
                    actions.append(f"Driver.{standard_action}('{obj}')")
                else:
                    actions.append(f"Driver.{standard_action}()")
        
        return actions
    
    def extract_goal(self, episode: Dict) -> str:
        """
        Extract task goal from TEACh episode.
        
        Args:
            episode: TEACh game episode dictionary
            
        Returns:
            Natural language task description
        """
        # Try multiple possible goal locations in TEACh format
        
        # Check task definition
        if 'tasks' in episode and episode['tasks']:
            task = episode['tasks'][0]  # Use first task
            if 'task_description' in task:
                return task['task_description']
            elif 'desc' in task:
                return task['desc']
            elif 'definition' in task:
                return task['definition']
        
        # Check episode-level goal
        if 'goal' in episode:
            return episode['goal']
        elif 'task_description' in episode:
            return episode['task_description']
        elif 'instruction' in episode:
            return episode['instruction']
        
        # Check game-level goal
        if 'game_id' in episode:
            # Extract meaningful goal from game_id if possible
            game_id = episode['game_id']
            # This is a placeholder - adjust based on actual TEACh format
            return f"Complete household task {game_id}"
        
        # Default fallback
        return "Complete the household task"
    
    def get_domain(self) -> str:
        """Get the domain this dataset represents."""
        return "household_tasks"
    
    def get_action_space(self) -> Dict[str, List[str]]:
        """Get the action space for TEACh dataset."""
        return {
            'Driver': [
                'Move', 'PickUp', 'Place', 'Open', 'Close',
                'ToggleOn', 'ToggleOff', 'Slice', 'Pour', 'Fill',
                'Heat', 'Cool', 'Clean', 'Look'
            ]
        }
    
    def get_episode_id(self, episode: Dict) -> str:
        """Extract episode ID from TEACh episode."""
        # Try multiple possible ID fields
        for id_field in ['game_id', 'episode_id', 'id', 'task_id']:
            if id_field in episode:
                return str(episode[id_field])
        
        # Use filename if available
        if '_file_path' in episode:
            return Path(episode['_file_path']).stem
        
        return f"teach_episode_{hash(str(episode))}"
    
    def extract_metadata(self, episode: Dict) -> Dict[str, Any]:
        """Extract metadata from TEACh episode."""
        metadata = super().extract_metadata(episode)
        
        # TEACh-specific metadata
        teach_fields = [
            'scene_num', 'scene_id', 'task_type', 'task_id',
            'game_id', 'turk_annotations', 'repeat_idx'
        ]
        
        for field in teach_fields:
            if field in episode:
                metadata[field] = episode[field]
        
        # Extract scene information if available
        if 'tasks' in episode and episode['tasks']:
            task = episode['tasks'][0]
            for field in ['scene_id', 'task_type']:
                if field in task:
                    metadata[field] = task[field]
        
        return metadata
    
    def get_supported_splits(self) -> List[str]:
        """Get supported dataset splits."""
        return ['train']  # TEACh primarily has train split
    
    def validate_episode(self, episode: Dict) -> tuple[bool, List[str]]:
        """Validate TEACh episode format."""
        is_valid, errors = super().validate_episode(episode)
        
        # TEACh-specific validation
        if not any(key in episode for key in ['tasks', 'episodes', 'interactions', 'actions']):
            errors.append("Episode missing action data (tasks/episodes/interactions/actions)")
        
        return len(errors) == 0, errors