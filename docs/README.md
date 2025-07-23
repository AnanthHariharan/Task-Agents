# Task-Agents Documentation

Welcome to the Task-Agents documentation! This directory contains comprehensive guides and references for using the multi-model plan verification system.

## 📚 Documentation Structure

### Getting Started
- [Installation Guide](installation.md) - Set up the system
- [Quick Start Tutorial](quickstart.md) - Your first experiment  
- [Configuration Guide](configuration.md) - Customize settings

### Architecture
- [System Overview](architecture/overview.md) - High-level architecture
- [Planning Agents](architecture/planning-agents.md) - Plan generation and modification
- [Judge Agents](architecture/judge-agents.md) - Plan evaluation and feedback
- [LLM Providers](architecture/llm-providers.md) - Multi-model support

### User Guides
- [Running Experiments](guides/experiments.md) - Experiment setup and execution
- [Data Processing](guides/data-processing.md) - Prepare datasets
- [Analysis and Visualization](guides/analysis.md) - Interpret results
- [Custom Models](guides/custom-models.md) - Add new LLM providers

### API Reference
- [Core Classes](api/core.md) - Main system components
- [Utilities](api/utils.md) - Helper functions and tools
- [Configuration](api/config.md) - Settings and parameters

### Examples
- [Basic Usage](examples/basic-usage.md) - Simple examples
- [Advanced Workflows](examples/advanced.md) - Complex scenarios
- [Custom Experiments](examples/custom-experiments.md) - Tailored evaluations

### Development
- [Contributing](development/contributing.md) - How to contribute
- [Testing](development/testing.md) - Test framework and practices
- [Debugging](development/debugging.md) - Troubleshooting guide

## 🔍 Quick Navigation

| Topic | Description | Link |
|-------|-------------|------|
| **Installation** | Get up and running | [📖 Guide](installation.md) |
| **Experiments** | Run comparisons | [🧪 Tutorial](guides/experiments.md) |
| **Architecture** | System design | [🏗️ Overview](architecture/overview.md) |
| **API** | Code reference | [📋 Reference](api/core.md) |
| **Examples** | Code samples | [💡 Examples](examples/) |

## 📖 Key Concepts

### Planning-Judging Workflow
The core workflow involves iterative refinement:
1. **Planner** generates/modifies action sequences
2. **Judge** evaluates and provides feedback  
3. **Orchestrator** manages iterations until convergence

### Multi-Model Comparison
Compare different LLMs across:
- Planning capabilities
- Evaluation accuracy
- Convergence behavior
- Performance metrics

### Action Sequence Processing
Transform raw TEACh dataset into:
- Structured action sequences
- Goal annotations
- Efficiency optimizations

## 🚀 Quick Examples

### Run Basic Experiment
```python
from experiments import ExperimentRunner

runner = ExperimentRunner()
results = runner.run_full_experiment(max_samples=5)
```

### Custom Model Configuration
```python
from planning_agent import PlannerFactory
from judge_llm import JudgeFactory

planner = PlannerFactory.create_planner("openai", "gpt-4o")
judge = JudgeFactory.create_judge("gemini", "gemini-pro")
```

### Process Dataset
```python
from scripts.data_processing import assemble_instances

# Convert raw TEACh data to action sequences
assemble_instances.main()
```

## 🤔 Need Help?

- **Bug Reports**: [GitHub Issues](https://github.com/your-org/task-agents/issues)
- **Feature Requests**: [GitHub Discussions](https://github.com/your-org/task-agents/discussions)
- **Questions**: Check existing documentation or open a discussion

## 📝 Contributing to Documentation

Documentation improvements are welcome! Please:

1. Follow the existing structure and style
2. Include code examples where helpful
3. Update the navigation if adding new sections
4. Test all code examples before submitting

---

*Happy experimenting with Task-Agents! 🤖*