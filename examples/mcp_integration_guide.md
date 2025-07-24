# Universal Dataset MCP Integration Guide

This guide shows how to integrate the Universal Dataset MCP framework into your Task-Agents workflow for cross-domain plan verification research.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Install MCP (Model Context Protocol)
pip install mcp

# Install additional dependencies for dataset handling
pip install numpy pandas
```

### 2. Run the MCP Server

```bash
# Start the universal dataset server
python mcp-servers/universal-dataset-server.py

# Or run in mock mode for development (if MCP not available)
python mcp-servers/universal-dataset-server.py --mock
```

### 3. Test the Framework

```bash
# Run the demonstration
python examples/universal_dataset_demo.py

# This will show:
# - Dataset registration
# - Cross-dataset comparison  
# - Universal format examples
# - Research scenario templates
```

## 🏗️ Architecture Overview

### Universal Dataset Framework Components

```
Task-Agents/
├── mcp-servers/
│   └── universal-dataset-server.py    # MCP server for dataset access
├── shared/dataset_adapters/
│   ├── base_adapter.py                # Abstract base class
│   ├── teach_adapter.py               # TEACh dataset adapter
│   └── alfred_adapter.py              # ALFReD dataset adapter
└── examples/
    ├── universal_dataset_demo.py      # Framework demonstration
    └── mcp_integration_guide.md       # This guide
```

### MCP Tools Available

| Tool Name | Description | Use Case |
|-----------|-------------|----------|
| `register_dataset` | Add new dataset to server | Plugin new datasets |
| `list_datasets` | Show all registered datasets | Discovery |
| `load_episodes` | Load episodes from dataset | Data access |
| `sample_episodes` | Random episode sampling | Evaluation |
| `get_dataset_statistics` | Dataset metrics | Analysis |
| `cross_dataset_comparison` | Compare multiple datasets | Research |

## 📊 Integration with Existing Task-Agents

### Before: TEACh-Specific Code

```python
# Old approach - TEACh specific
from scripts.data_processing.assemble_instances import load_teach_data

teach_episodes = load_teach_data("games/train/")
for episode in teach_episodes:
    # TEACh-specific parsing
    actions = parse_teach_actions(episode)
    goal = extract_teach_goal(episode)
```

### After: Universal MCP Integration  

```python
# New approach - Universal MCP
import asyncio
from mcp_client import MCPClient

async def load_universal_data():
    client = MCPClient()
    await client.connect("universal-dataset-server")
    
    # Load from any registered dataset
    teach_data = await client.call_tool("sample_episodes", {
        "dataset_name": "teach",
        "n_samples": 100
    })
    
    alfred_data = await client.call_tool("sample_episodes", {
        "dataset_name": "alfred", 
        "n_samples": 100
    })
    
    # Both have same universal format!
    for episode in teach_data["episodes"]:
        actions = episode["actions"]  # Standardized format
        goal = episode["goal"]        # Standardized format
```

## 🔬 Research Applications

### 1. Cross-Domain Evaluation Matrix

Replace your current 4×4 planner-judge matrix with multi-dataset evaluation:

```python
async def cross_domain_evaluation():
    """Evaluate all model combinations across all datasets."""
    
    datasets = ["teach", "alfred", "habitat", "minecraft"]  
    planners = ["gpt4o-mini", "deepseek-r1", "gemini-2.5", "llama4"]
    judges = ["gpt4o-mini", "deepseek-r1", "gemini-2.5", "llama4"]
    
    results = {}
    
    for dataset in datasets:
        # Load episodes via MCP
        episodes = await client.call_tool("sample_episodes", {
            "dataset_name": dataset,
            "n_samples": 50
        })
        
        for planner in planners:
            for judge in judges:
                key = f"{dataset}_{planner}_{judge}"
                
                # Run your existing evaluation pipeline
                results[key] = await evaluate_planner_judge_combination(
                    episodes["episodes"], planner, judge
                )
    
    # Generate extended performance matrices
    generate_cross_domain_latex_tables(results)
```

### 2. Domain Transfer Analysis

```python
async def domain_transfer_study():
    """Study how well models transfer between domains."""
    
    # Train on household tasks (TEACh)
    teach_episodes = await client.call_tool("load_episodes", {
        "dataset_name": "teach",
        "split": "train",
        "limit": 1000
    })
    
    model = train_judge_model(teach_episodes["episodes"])
    
    # Test on instruction following (ALFReD)  
    alfred_episodes = await client.call_tool("load_episodes", {
        "dataset_name": "alfred",
        "split": "valid_seen", 
        "limit": 200
    })
    
    # Evaluate transfer performance
    transfer_results = evaluate_model(model, alfred_episodes["episodes"])
    
    print(f"Household→Instruction transfer: {transfer_results['accuracy']:.2f}")
```

### 3. Action Complexity Analysis

```python
async def action_complexity_analysis():
    """Compare action complexity across domains."""
    
    datasets = await client.call_tool("list_datasets", {})
    
    complexity_results = {}
    
    for dataset_name in datasets["registered_datasets"]:
        stats = await client.call_tool("get_dataset_statistics", {
            "dataset_name": dataset_name
        })
        
        complexity_results[dataset_name] = {
            "avg_sequence_length": stats["avg_sequence_length"],
            "action_space_size": len(stats["action_space"]["Agent"]),
            "domain": stats["domain"]
        }
    
    # Generate complexity comparison visualizations
    create_complexity_heatmap(complexity_results)
```

## 🔧 Adding New Datasets

### 1. Create Dataset Adapter

```python
# shared/dataset_adapters/your_dataset_adapter.py

from .base_adapter import UniversalDatasetAdapter

class YourDatasetAdapter(UniversalDatasetAdapter):
    def __init__(self, dataset_path: str):
        super().__init__(dataset_path, "YourDataset")
    
    def load_episodes(self, split: str = "train", limit: Optional[int] = None):
        # Your dataset loading logic
        pass
    
    def parse_action_sequence(self, episode: Dict) -> List[str]:
        # Convert to standardized format: "Agent.Method(args)"
        pass
    
    def extract_goal(self, episode: Dict) -> str:
        # Extract natural language goal
        pass
    
    def get_domain(self) -> str:
        return "your_domain"  # e.g., "navigation", "manipulation"
    
    def get_action_space(self) -> Dict[str, List[str]]:
        return {"Agent": ["Move", "PickUp", "Place", ...]}
```

### 2. Register with MCP Server

```python
# Register via MCP tool call
await client.call_tool("register_dataset", {
    "name": "your_dataset",
    "adapter_type": "YourDatasetAdapter", 
    "dataset_path": "/path/to/your/data",
    "config": {"custom_param": "value"}
})
```

## 📈 Enhanced Research Outputs

### Extended Performance Tables

Your original Tables 1, 2, 3 become multi-dimensional:

**Table 1: Cross-Domain Judge Performance**
```
Judge LLM        | TEACh | ALFReD | Habitat | Average
-----------------|-------|--------|---------|--------
GPT-4o-mini      | 82%   | 75%    | 68%     | 75%
DeepSeek-R1      | 78%   | 80%    | 72%     | 77%
...
```

**Table 2: Domain Transfer Matrix**
```
Train→Test      | TEACh | ALFReD | Habitat
----------------|-------|--------|--------
TEACh           | 82%   | 67%    | 59%
ALFReD          | 71%   | 80%    | 64%
...
```

### New Research Questions Enabled

1. **Cross-Domain Generalization**: Do models trained on household tasks work for navigation?

2. **Action Space Complexity**: How does performance scale with action space size?

3. **Domain-Specific Biases**: What types of errors are domain-specific vs. universal?

4. **Optimal Training Mixtures**: What combination of datasets produces the most robust models?

## 🚢 Migration Path

### Phase 1: Parallel Integration
- Keep existing TEACh-specific code working
- Add MCP server alongside existing system
- Test with small datasets

### Phase 2: Extended Evaluation  
- Add ALFReD adapter and run cross-domain experiments
- Generate extended performance matrices
- Compare results with original TEACh-only results

### Phase 3: Full Framework
- Migrate all data access to MCP
- Add more dataset adapters (Habitat, MineRL, etc.)
- Publish universal framework for community use

## 🤝 Community Impact

This universal framework enables:

- **Reproducible Research**: Standardized data access across studies
- **Easy Comparison**: Common evaluation metrics across datasets  
- **Rapid Prototyping**: New datasets integrate with existing models
- **Collaborative Development**: Shared adapters and evaluation tools

## 📞 Support

- **Documentation**: See `examples/universal_dataset_demo.py`
- **Testing**: Run MCP server in mock mode for development
- **Extensions**: Add new adapters in `shared/dataset_adapters/`
- **Issues**: Framework handles errors gracefully with detailed logging

---

*This framework transforms Task-Agents from a dataset-specific tool into a universal platform for embodied AI research, enabling cross-domain insights and accelerating research progress.*