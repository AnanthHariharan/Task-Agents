#!/usr/bin/env python3

"""
Universal Dataset MCP Server for Task-Agents

This MCP server provides standardized access to multiple embodied AI datasets
through a unified interface. It supports dynamic dataset registration and
cross-domain evaluation capabilities.
"""

import asyncio
import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import importlib.util

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

try:
    # Try to import MCP (install with: pip install mcp)
    from mcp.server import Server
    from mcp.server.models import InitializationOptions
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
    MCP_AVAILABLE = True
except ImportError:
    print("Warning: MCP not installed. Install with: pip install mcp")
    print("Creating mock MCP server for development...")
    MCP_AVAILABLE = False
    
    # Mock classes for development
    class Tool:
        def __init__(self, name, description, inputSchema):
            self.name = name
            self.description = description  
            self.inputSchema = inputSchema
    
    class TextContent:
        def __init__(self, type, text):
            self.type = type
            self.text = text
    
    class Server:
        def __init__(self, name):
            self.name = name

# Import our dataset adapters
from shared.dataset_adapters.base_adapter import UniversalDatasetAdapter
from shared.dataset_adapters.teach_adapter import TeachDatasetAdapter

class UniversalDatasetServer:
    """
    MCP Server for universal dataset access across multiple embodied AI datasets.
    
    Provides standardized tools for:
    - Dataset registration and discovery
    - Episode loading and sampling
    - Cross-dataset evaluation
    - Schema validation
    """
    
    def __init__(self):
        self.registered_datasets: Dict[str, UniversalDatasetAdapter] = {}
        self.server = Server("universal-dataset-server") if MCP_AVAILABLE else None
        
        # Auto-register TEACh dataset if available
        self._auto_register_datasets()
        self._setup_tools()
    
    def _auto_register_datasets(self):
        """Auto-register available datasets."""
        
        # Register TEACh dataset if games directory exists
        teach_path = PROJECT_ROOT / "games"
        if teach_path.exists():
            try:
                teach_adapter = TeachDatasetAdapter(str(PROJECT_ROOT))
                self.registered_datasets['teach'] = teach_adapter
                print(f"✓ Auto-registered TEACh dataset from {teach_path}")
            except Exception as e:
                print(f"Warning: Could not register TEACh dataset: {e}")
    
    def _setup_tools(self):
        """Setup MCP tools for dataset operations."""
        if not MCP_AVAILABLE:
            return
        
        # Dataset Management Tools
        self.server.list_tools = self._list_tools
        
        # Register tool handlers
        self.server.call_tool = self._call_tool
    
    async def _list_tools(self) -> List[Tool]:
        """List available MCP tools."""
        return [
            Tool(
                name="register_dataset",
                description="Register a new dataset with the server",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Dataset name"},
                        "adapter_type": {"type": "string", "description": "Adapter class name"},
                        "dataset_path": {"type": "string", "description": "Path to dataset"},
                        "config": {"type": "object", "description": "Additional configuration"}
                    },
                    "required": ["name", "adapter_type", "dataset_path"]
                }
            ),
            Tool(
                name="list_datasets",
                description="List all registered datasets",
                inputSchema={"type": "object", "properties": {}}
            ),
            Tool(
                name="get_dataset_schema",
                description="Get schema information for a dataset",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "dataset_name": {"type": "string", "description": "Name of the dataset"}
                    },
                    "required": ["dataset_name"]
                }
            ),
            Tool(
                name="load_episodes",
                description="Load episodes from a dataset",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "dataset_name": {"type": "string", "description": "Name of the dataset"},
                        "split": {"type": "string", "description": "Dataset split", "default": "train"},
                        "limit": {"type": "integer", "description": "Maximum episodes to load"},
                        "format": {"type": "string", "description": "Output format", "enum": ["universal", "raw"], "default": "universal"}
                    },
                    "required": ["dataset_name"]
                }
            ),
            Tool(
                name="sample_episodes",
                description="Sample random episodes from a dataset",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "dataset_name": {"type": "string", "description": "Name of the dataset"},
                        "n_samples": {"type": "integer", "description": "Number of samples", "default": 10},
                        "split": {"type": "string", "description": "Dataset split", "default": "train"},
                        "seed": {"type": "integer", "description": "Random seed for reproducibility"}
                    },
                    "required": ["dataset_name"]
                }
            ),
            Tool(
                name="get_dataset_statistics",
                description="Get statistics for a dataset",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "dataset_name": {"type": "string", "description": "Name of the dataset"},
                        "split": {"type": "string", "description": "Dataset split", "default": "train"}
                    },
                    "required": ["dataset_name"]
                }
            ),
            Tool(
                name="validate_episodes",
                description="Validate episodes from a dataset",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "dataset_name": {"type": "string", "description": "Name of the dataset"},
                        "split": {"type": "string", "description": "Dataset split", "default": "train"},
                        "limit": {"type": "integer", "description": "Episodes to validate", "default": 100}
                    },
                    "required": ["dataset_name"]
                }
            ),
            Tool(
                name="cross_dataset_comparison",
                description="Compare episodes across multiple datasets",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "dataset_names": {"type": "array", "items": {"type": "string"}, "description": "List of dataset names"},
                        "comparison_metrics": {"type": "array", "items": {"type": "string"}, "description": "Metrics to compare"},
                        "n_samples": {"type": "integer", "description": "Samples per dataset", "default": 50}
                    },
                    "required": ["dataset_names"]
                }
            )
        ]
    
    async def _call_tool(self, name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle tool calls."""
        try:
            if name == "register_dataset":
                result = await self._register_dataset(**arguments)
            elif name == "list_datasets":
                result = await self._list_datasets()
            elif name == "get_dataset_schema":
                result = await self._get_dataset_schema(**arguments)
            elif name == "load_episodes":
                result = await self._load_episodes(**arguments)
            elif name == "sample_episodes":
                result = await self._sample_episodes(**arguments)
            elif name == "get_dataset_statistics":
                result = await self._get_dataset_statistics(**arguments)
            elif name == "validate_episodes":
                result = await self._validate_episodes(**arguments)
            elif name == "cross_dataset_comparison":
                result = await self._cross_dataset_comparison(**arguments)
            else:
                result = {"error": f"Unknown tool: {name}"}
            
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
            
        except Exception as e:
            error_result = {"error": str(e), "tool": name, "arguments": arguments}
            return [TextContent(type="text", text=json.dumps(error_result, indent=2))]
    
    async def _register_dataset(self, name: str, adapter_type: str, dataset_path: str, config: Dict = None) -> Dict:
        """Register a new dataset."""
        try:
            # Dynamic adapter loading based on type
            if adapter_type == "TeachDatasetAdapter":
                adapter = TeachDatasetAdapter(dataset_path)
            else:
                # Try to load custom adapter
                adapter_class = self._load_adapter_class(adapter_type)
                adapter = adapter_class(dataset_path, **(config or {}))
            
            self.registered_datasets[name] = adapter
            
            return {
                "success": True,
                "message": f"Successfully registered dataset '{name}'",
                "schema": adapter.get_schema()
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _list_datasets(self) -> Dict:
        """List all registered datasets."""
        datasets = {}
        for name, adapter in self.registered_datasets.items():
            datasets[name] = {
                "domain": adapter.get_domain(),
                "supported_splits": adapter.get_supported_splits(),
                "action_space": adapter.get_action_space()
            }
        
        return {
            "registered_datasets": datasets,
            "total_datasets": len(datasets)
        }
    
    async def _get_dataset_schema(self, dataset_name: str) -> Dict:
        """Get schema for a specific dataset."""
        if dataset_name not in self.registered_datasets:
            return {"error": f"Dataset '{dataset_name}' not registered"}
        
        adapter = self.registered_datasets[dataset_name]
        return adapter.get_schema()
    
    async def _load_episodes(self, dataset_name: str, split: str = "train", 
                           limit: Optional[int] = None, format: str = "universal") -> Dict:
        """Load episodes from a dataset."""
        if dataset_name not in self.registered_datasets:
            return {"error": f"Dataset '{dataset_name}' not registered"}
        
        adapter = self.registered_datasets[dataset_name]
        
        try:
            raw_episodes = adapter.load_episodes(split, limit)
            
            if format == "universal":
                episodes = [adapter.to_universal_format(ep) for ep in raw_episodes]
            else:
                episodes = raw_episodes
            
            return {
                "dataset": dataset_name,
                "split": split,
                "episode_count": len(episodes),
                "episodes": episodes
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def _sample_episodes(self, dataset_name: str, n_samples: int = 10, 
                             split: str = "train", seed: Optional[int] = None) -> Dict:
        """Sample random episodes from a dataset."""
        if dataset_name not in self.registered_datasets:
            return {"error": f"Dataset '{dataset_name}' not registered"}
        
        adapter = self.registered_datasets[dataset_name]
        
        try:
            episodes = adapter.sample_episodes(split, n_samples, seed)
            
            return {
                "dataset": dataset_name,
                "split": split,
                "requested_samples": n_samples,
                "actual_samples": len(episodes),
                "seed": seed,
                "episodes": episodes
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def _get_dataset_statistics(self, dataset_name: str, split: str = "train") -> Dict:
        """Get statistics for a dataset."""
        if dataset_name not in self.registered_datasets:
            return {"error": f"Dataset '{dataset_name}' not registered"}
        
        adapter = self.registered_datasets[dataset_name]
        
        try:
            stats = adapter.get_statistics(split)
            stats.update({
                "dataset": dataset_name,
                "split": split
            })
            return stats
        except Exception as e:
            return {"error": str(e)}
    
    async def _validate_episodes(self, dataset_name: str, split: str = "train", 
                               limit: int = 100) -> Dict:
        """Validate episodes from a dataset."""
        if dataset_name not in self.registered_datasets:
            return {"error": f"Dataset '{dataset_name}' not registered"}
        
        adapter = self.registered_datasets[dataset_name]
        
        try:
            episodes = adapter.load_episodes(split, limit)
            
            validation_results = []
            total_valid = 0
            
            for i, episode in enumerate(episodes):
                is_valid, errors = adapter.validate_episode(episode)
                
                validation_results.append({
                    "episode_index": i,
                    "episode_id": adapter.get_episode_id(episode),
                    "is_valid": is_valid,
                    "errors": errors
                })
                
                if is_valid:
                    total_valid += 1
            
            return {
                "dataset": dataset_name,
                "split": split,
                "total_episodes": len(episodes),
                "valid_episodes": total_valid,
                "validation_rate": total_valid / len(episodes) if episodes else 0,
                "results": validation_results
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def _cross_dataset_comparison(self, dataset_names: List[str], 
                                      comparison_metrics: List[str] = None,
                                      n_samples: int = 50) -> Dict:
        """Compare multiple datasets."""
        if comparison_metrics is None:
            comparison_metrics = ["episode_count", "avg_sequence_length", "action_space"]
        
        comparison_results = {}
        
        for dataset_name in dataset_names:
            if dataset_name not in self.registered_datasets:
                comparison_results[dataset_name] = {"error": f"Dataset not registered"}
                continue
            
            adapter = self.registered_datasets[dataset_name]
            
            try:
                # Get basic statistics
                stats = adapter.get_statistics()
                
                # Sample episodes for detailed comparison
                sample_episodes = adapter.sample_episodes(n_samples=min(n_samples, 10))
                
                comparison_results[dataset_name] = {
                    "domain": adapter.get_domain(),
                    "statistics": stats,
                    "sample_episodes": len(sample_episodes),
                    "action_space_size": len(adapter.get_action_space().get('Driver', [])),
                }
                
            except Exception as e:
                comparison_results[dataset_name] = {"error": str(e)}
        
        return {
            "comparison_metrics": comparison_metrics,
            "datasets_compared": len(dataset_names),
            "results": comparison_results
        }
    
    def _load_adapter_class(self, adapter_type: str):
        """Dynamically load adapter class."""
        # This is a simplified version - in production, you'd want more robust loading
        adapter_mapping = {
            "TeachDatasetAdapter": TeachDatasetAdapter,
            # Add more adapters as they're implemented
        }
        
        if adapter_type in adapter_mapping:
            return adapter_mapping[adapter_type]
        else:
            raise ValueError(f"Unknown adapter type: {adapter_type}")
    
    async def run(self):
        """Run the MCP server."""
        if not MCP_AVAILABLE:
            print("MCP not available - running in mock mode")
            print("Available datasets:", list(self.registered_datasets.keys()))
            return
        
        async def init_handler(options: InitializationOptions):
            print(f"Universal Dataset Server initialized with {len(self.registered_datasets)} datasets")
        
        self.server.request_handlers["initialize"] = init_handler
        
        # Start the stdio server
        async with stdio_server() as streams:
            await self.server.run(streams[0], streams[1], init_handler)

# Development/Testing Interface (when MCP not available)
class MockMCPServer:
    """Mock server for development when MCP is not installed."""
    
    def __init__(self):
        self.dataset_server = UniversalDatasetServer()
    
    async def test_operations(self):
        """Test server operations."""
        print("🧪 Testing Universal Dataset Server Operations")
        print("=" * 60)
        
        # List datasets
        result = await self.dataset_server._list_datasets()
        print(f"\n📊 Registered Datasets: {json.dumps(result, indent=2)}")
        
        # Test TEACh dataset if available
        if 'teach' in self.dataset_server.registered_datasets:
            print(f"\n🎯 Testing TEACh Dataset Operations...")
            
            # Get schema
            schema = await self.dataset_server._get_dataset_schema('teach')
            print(f"Schema: {json.dumps(schema, indent=2)}")
            
            # Get statistics
            stats = await self.dataset_server._get_dataset_statistics('teach')
            print(f"Statistics: {json.dumps(stats, indent=2)}")
            
            # Sample episodes
            samples = await self.dataset_server._sample_episodes('teach', n_samples=2)
            print(f"Sample Episodes: {len(samples.get('episodes', []))} episodes loaded")
            
            if samples.get('episodes'):
                print(f"First episode goal: {samples['episodes'][0].get('goal', 'N/A')}")
                print(f"First episode actions: {len(samples['episodes'][0].get('actions', []))} actions")

async def main():
    """Main entry point."""
    server = UniversalDatasetServer()
    
    if MCP_AVAILABLE:
        await server.run()
    else:
        # Run in mock mode for development
        mock_server = MockMCPServer()
        await mock_server.test_operations()

if __name__ == "__main__":
    asyncio.run(main())