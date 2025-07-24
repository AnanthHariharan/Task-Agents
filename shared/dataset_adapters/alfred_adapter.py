#!/usr/bin/env python3

import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from .base_adapter import UniversalDatasetAdapter

class ALFReDatasetAdapter(UniversalDatasetAdapter):
    """
    Adapter for the ALFReD (Action Learning From Realistic Environments and Directives) dataset.
    
    ALFReD focuses on interactive instruction following in household environments,
    providing a different perspective from TEACh with more structured tasks.
    """
    
    def __init__(self, dataset_path: str):
        """
        Initialize ALFReD dataset adapter.
        
        Args:
            dataset_path: Path to ALFReD dataset directory
        """
        super().__init__(dataset_path, "ALFReD")
        
        # ALFReD action mappings to standardized format
        self.action_mappings = {
            'MoveAhead': 'Move',
            'RotateLeft': 'Turn', 
            'RotateRight': 'Turn',
            'LookUp': 'Look',
            'LookDown': 'Look',
            'PickupObject': 'PickUp',
            'PutObject': 'Place',
            'OpenObject': 'Open',
            'CloseObject': 'Close',
            'ToggleObjectOn': 'ToggleOn',
            'ToggleObjectOff': 'ToggleOff',
            'SliceObject': 'Slice',
            'HeatObject': 'Heat',
            'CoolObject': 'Cool',
            'CleanObject': 'Clean'
        }
    
    def load_episodes(self, split: str = "train", limit: Optional[int] = None) -> List[Dict]:
        """
        Load ALFReD episodes from JSON files.
        
        Args:
            split: Dataset split ('train', 'valid_seen', 'valid_unseen', 'tests_seen', 'tests_unseen')
            limit: Maximum number of episodes to load
            
        Returns:
            List of episode dictionaries
        """
        # Cache key for this request
        cache_key = f"{split}_{limit}"
        if cache_key in self._episodes_cache:
            return self._episodes_cache[cache_key]
        
        episodes = []
        
        # ALFReD typical structure: data/splits/split_name/*.json
        split_dir = self.dataset_path / "data" / "splits" / split
        if not split_dir.exists():
            # Alternative structure: json_feat/split_name/
            split_dir = self.dataset_path / "json_feat" / split
        
        if not split_dir.exists():
            print(f"Warning: ALFReD split directory not found at {split_dir}")
            # Create mock data for demonstration
            return self._create_mock_episodes(limit or 5)
        
        # Look for task JSON files
        json_files = list(split_dir.glob("**/*.json"))
        
        if limit:
            json_files = json_files[:limit]
        
        print(f"Loading {len(json_files)} ALFReD episodes from {split_dir}")
        
        for json_file in json_files:
            try:
                with open(json_file, 'r') as f:
                    episode = json.load(f)
                    episode['_file_path'] = str(json_file)
                    episodes.append(episode)
            except Exception as e:
                print(f"Error loading {json_file}: {e}")
                continue
        
        # Cache the results
        self._episodes_cache[cache_key] = episodes
        
        return episodes
    
    def _create_mock_episodes(self, n_episodes: int) -> List[Dict]:
        """Create mock ALFReD episodes for demonstration purposes."""
        mock_episodes = []
        
        for i in range(n_episodes):
            episode = {
                'task_id': f'alfred_mock_{i}',
                'task_type': ['pick_and_place_simple', 'pick_clean_then_place', 'pick_heat_then_place'][i % 3],
                'turk_annotations': {
                    'anns': [{
                        'task_desc': ['Clean a cup and put it on the counter', 
                                    'Heat a slice of bread and place it on a plate',
                                    'Pick up the keys and put them in the drawer'][i % 3],
                        'high_descs': [
                            'go to counter', 'pick up cup', 'go to sink', 'clean cup', 
                            'go to counter', 'place cup on counter'
                        ]
                    }]
                },
                'plan': {
                    'high_pddl': [
                        {'discrete_action': {'action': 'GotoLocation', 'args': ['countertop']}},
                        {'discrete_action': {'action': 'PickupObject', 'args': ['cup']}},
                        {'discrete_action': {'action': 'GotoLocation', 'args': ['sinkbasin']}},
                        {'discrete_action': {'action': 'CleanObject', 'args': ['cup']}},
                        {'discrete_action': {'action': 'GotoLocation', 'args': ['countertop']}},
                        {'discrete_action': {'action': 'PutObject', 'args': ['cup', 'countertop']}}
                    ],
                    'low_actions': [
                        {'api_action': {'action': 'MoveAhead'}},
                        {'api_action': {'action': 'RotateRight'}},
                        {'api_action': {'action': 'PickupObject', 'objectId': 'Cup|+00.50|+00.90|-01.50'}},
                        {'api_action': {'action': 'MoveAhead'}},
                        {'api_action': {'action': 'CleanObject', 'objectId': 'Cup|+00.50|+00.90|-01.50'}},
                        {'api_action': {'action': 'PutObject', 'objectId': 'Cup|+00.50|+00.90|-01.50', 'receptacleObjectId': 'CounterTop|+00.69|+00.95|-02.48'}}
                    ]
                },
                'scene': {'scene_num': i + 1},
                'task': {'task_id': i, 'task_type': 'pick_clean_then_place_in_recv'}
            }
            mock_episodes.append(episode)
        
        return mock_episodes
    
    def parse_action_sequence(self, episode: Dict) -> List[str]:
        """
        Extract action sequence from ALFReD episode.
        
        Args:
            episode: ALFReD episode dictionary
            
        Returns:
            List of standardized action strings
        """
        actions = []
        
        # ALFReD stores actions in plan.low_actions
        if 'plan' in episode and 'low_actions' in episode['plan']:
            for action_data in episode['plan']['low_actions']:
                if 'api_action' in action_data:
                    api_action = action_data['api_action']
                    action_name = api_action.get('action', '')
                    
                    # Map to standardized format
                    standard_action = self.action_mappings.get(action_name, action_name)
                    
                    # Extract object information
                    obj_id = api_action.get('objectId', '')
                    receptacle_id = api_action.get('receptacleObjectId', '')
                    
                    # Format action string
                    if obj_id and receptacle_id:
                        # Extract object type from ID (e.g., "Cup|+00.50|+00.90|-01.50" -> "Cup")
                        obj_type = obj_id.split('|')[0] if '|' in obj_id else obj_id
                        receptacle_type = receptacle_id.split('|')[0] if '|' in receptacle_id else receptacle_id
                        actions.append(f"Agent.{standard_action}('{obj_type}', '{receptacle_type}')")
                    elif obj_id:
                        obj_type = obj_id.split('|')[0] if '|' in obj_id else obj_id
                        actions.append(f"Agent.{standard_action}('{obj_type}')")
                    else:
                        actions.append(f"Agent.{standard_action}()")
        
        # Fallback: check for high-level actions
        elif 'plan' in episode and 'high_pddl' in episode['plan']:
            for action_data in episode['plan']['high_pddl']:
                if 'discrete_action' in action_data:
                    discrete_action = action_data['discrete_action']
                    action_name = discrete_action.get('action', '')
                    args = discrete_action.get('args', [])
                    
                    standard_action = self.action_mappings.get(action_name, action_name)
                    
                    if args:
                        args_str = "', '".join(args)
                        actions.append(f"Agent.{standard_action}('{args_str}')")
                    else:
                        actions.append(f"Agent.{standard_action}()")
        
        return actions
    
    def extract_goal(self, episode: Dict) -> str:
        """
        Extract task goal from ALFReD episode.
        
        Args:
            episode: ALFReD episode dictionary
            
        Returns:
            Natural language task description
        """
        # ALFReD stores goal in turk_annotations
        if 'turk_annotations' in episode and 'anns' in episode['turk_annotations']:
            anns = episode['turk_annotations']['anns']
            if anns and isinstance(anns[0], dict):
                # Get task description
                task_desc = anns[0].get('task_desc', '')
                if isinstance(task_desc, list):
                    return task_desc[0] if task_desc else ''
                return task_desc
        
        # Fallback: use task type
        if 'task_type' in episode:
            task_type = episode['task_type']
            # Convert task type to readable description
            task_descriptions = {
                'pick_and_place_simple': 'Pick up an object and place it somewhere',
                'pick_clean_then_place': 'Clean an object and then place it',
                'pick_heat_then_place': 'Heat an object and then place it',
                'pick_cool_then_place': 'Cool an object and then place it',
                'look_at_obj_in_light': 'Examine an object under light',
                'pick_two_obj_and_place': 'Pick up two objects and place them'
            }
            return task_descriptions.get(task_type, f"Complete task: {task_type}")
        
        # Final fallback
        return "Complete the household instruction task"
    
    def get_domain(self) -> str:
        """Get the domain this dataset represents."""
        return "instruction_following"
    
    def get_action_space(self) -> Dict[str, List[str]]:
        """Get the action space for ALFReD dataset."""
        return {
            'Agent': [
                'Move', 'Turn', 'Look', 'PickUp', 'Place', 
                'Open', 'Close', 'ToggleOn', 'ToggleOff',
                'Slice', 'Heat', 'Cool', 'Clean'
            ]
        }
    
    def get_episode_id(self, episode: Dict) -> str:
        """Extract episode ID from ALFReD episode."""
        # Try multiple possible ID fields
        for id_field in ['task_id', 'episode_id', 'id']:
            if id_field in episode:
                return str(episode[id_field])
        
        # Use task information
        if 'task' in episode and 'task_id' in episode['task']:
            return f"alfred_task_{episode['task']['task_id']}"
        
        # Use filename if available
        if '_file_path' in episode:
            return Path(episode['_file_path']).stem
        
        return f"alfred_episode_{hash(str(episode))}"
    
    def extract_metadata(self, episode: Dict) -> Dict[str, Any]:
        """Extract metadata from ALFReD episode."""
        metadata = super().extract_metadata(episode)
        
        # ALFReD-specific metadata
        alfred_fields = [
            'task_type', 'repeat_idx', 'scene_num'
        ]
        
        for field in alfred_fields:
            if field in episode:
                metadata[field] = episode[field]
        
        # Extract scene information
        if 'scene' in episode:
            scene_info = episode['scene']
            if isinstance(scene_info, dict):
                metadata.update({f"scene_{k}": v for k, v in scene_info.items()})
            else:
                metadata['scene_info'] = scene_info
        
        # Extract task information
        if 'task' in episode:
            task_info = episode['task']
            if isinstance(task_info, dict):
                metadata.update({f"task_{k}": v for k, v in task_info.items()})
        
        return metadata
    
    def get_supported_splits(self) -> List[str]:
        """Get supported dataset splits."""
        return ['train', 'valid_seen', 'valid_unseen', 'tests_seen', 'tests_unseen']
    
    def validate_episode(self, episode: Dict) -> tuple[bool, List[str]]:
        """Validate ALFReD episode format."""
        is_valid, errors = super().validate_episode(episode)
        
        # ALFReD-specific validation
        if 'plan' not in episode:
            errors.append("Episode missing 'plan' field")
        elif not any(key in episode['plan'] for key in ['low_actions', 'high_pddl']):
            errors.append("Plan missing action sequences (low_actions or high_pddl)")
        
        if 'turk_annotations' not in episode:
            errors.append("Episode missing 'turk_annotations' field")
        
        return len(errors) == 0, errors