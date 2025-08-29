# Task-Agents: Multi-Model Plan Verification System

A comprehensive framework for evaluating and comparing different Large Language Models in collaborative plan verification tasks for embodied AI agents using the Alexa TEACh dataset.

## 🚀 Overview

Task-Agents implements both iterative planning-judging workflows and one-shot evaluation approaches:

### **Iterative Workflow**
1. **Planning Agents** generate goals and modify action sequences based on judge feedback
2. **Judge Agents** evaluate plans for completeness, efficiency, and correctness using #REMOVE and #MISSING tags
3. **Workflow Orchestrator** manages iterative refinement until convergence

### **One-Shot Evaluation** 
Direct evaluation of judge performance on raw TEACh plans without iteration, matching research paper evaluation methodology.

The system supports multiple LLM providers (GPT-4o-mini, DeepSeek-R1, Gemini 2.5 Flash, LLaMA 4 Scout) plus rule-based implementations for comprehensive cross-model comparisons.

## 📁 Project Structure

```
Task-Agents/
├── data/                   # Processed TEACh dataset sequences
│   ├── seq_all.json       # All processed action sequences
│   ├── seq_redundancies.json # Sequences with redundant actions  
│   └── seq_shortest.json  # Optimized shortest sequences
├── games/                 # Raw TEACh dataset
│   └── train/            # ~1200 game episode files (*.game.json)
├── planning-agent/        # Planning agent implementations
│   ├── models/           # LLM and rule-based planners
│   └── factory.py        # Planner factory for all models
├── judge-llm/            # Judge agent implementations
│   ├── models/          # LLM and rule-based judges  
│   └── factory.py       # Judge factory for all models
├── shared/               # Shared utilities and providers
│   ├── llm_providers/   # OpenAI, DeepSeek, Gemini, LLaMA providers
│   ├── utils/           # Action parsing, logging, file utilities
│   └── workflow/        # Orchestrator for iterative workflows
├── experiments/          # Experiment framework and evaluation
│   ├── analysis/        # Recall/precision evaluation tools
│   ├── one_shot_evaluator.py        # Table 1 equivalent evaluation
│   ├── experiment_runner.py         # Main experiment orchestrator
│   └── generate_performance_matrix.py  # Paper table generation
├── workspace/            # Additional experimental workspace
│   ├── models/          # Alternative model implementations
│   └── scripts/         # Workspace-specific processing scripts
├── outputs/              # Experiment results (JSON format)
│   ├── *Plan_*Judge.json # Planner-Judge combination results
│   └── single-shot_*.json # One-shot evaluation results
└── scripts/              # Data processing and utilities
    ├── data_processing/  # TEACh dataset assembly scripts
    └── action_processing/ # Action sequence modification tools
```

## 🛠️ Installation

### Prerequisites

- Python 3.8+
- API keys for desired LLM providers (at minimum OpenAI for the demo)

### Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-org/task-agents.git
   cd Task-Agents
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   pip install python-dotenv openai  # Required for basic demo
   ```

3. **Configure environment:**
   ```bash
   # Create .env file with your API keys
   echo "OPENAI_API_KEY=your-openai-key-here" > .env
   # Add other API keys as needed:
   # echo "DEEPSEEK_API_KEY=your-deepseek-key" >> .env
   # echo "GEMINI_API_KEY=your-gemini-key" >> .env
   ```

4. **Prepare data (optional for demo):**
   ```bash
   # Process raw TEACh dataset (needed for full experiments)
   python scripts/data_processing/assemble_instances.py
   python scripts/data_processing/assemble_shortest.py
   python scripts/data_processing/assemble_random.py
   ```

## 🚀 Quick Start

### Try the Interactive Demo

Test the complete plan verification workflow with natural language feedback:

```bash
# Run the interactive demo (works with mock data if no API key)
python test_seq.py
```

This demo shows the complete workflow:
1. **Goal Annotation**: Planning agent identifies the task goal
2. **Line-by-Line Analysis**: Judge provides natural language feedback with #REMOVE/#MISSING tags  
3. **Plan Modification**: Planning agent fixes issues based on feedback
4. **Final Verification**: Clean, optimized action sequence

### Generate Paper Performance Tables

Generate the recall/precision matrices (Table 1, 2, 3) from your research paper:

```bash
# Generate all performance matrices with LaTeX output
python experiments/generate_performance_matrix.py --samples 50

# Quick test with fewer samples  
python experiments/generate_performance_matrix.py --samples 10
```

### Run One-Shot Evaluation

Direct evaluation of judge performance on raw TEACh plans (matches paper methodology):

```bash
# One-shot evaluation (Table 1 equivalent)
python experiments/experiment_runner.py --evaluation-mode one_shot --samples 25

# Include 4x4 planner-judge matrix evaluation
python experiments/one_shot_evaluator.py --samples 50
```

### Run Iterative Workflow Experiments

Full iterative planning-judging experiments with convergence analysis:

```bash
# Quick test with rule-based models
python experiments/experiment_runner.py --samples 5 --test-mode

# Full cross-validation experiment
python experiments/experiment_runner.py --samples 25 --evaluation-mode iterative
```

## 🏗️ Architecture

### Core Components

#### Planning Agent
- **Goal Annotation**: Identifies the objective of action sequences
- **Plan Modification**: Adjusts plans based on judge feedback
- **Action Generation**: Creates missing actions to complete tasks

#### Judge Agent  
- **Plan Evaluation**: Assesses completeness and efficiency
- **Feedback Generation**: Provides detailed annotations with #REMOVE and #MISSING tags
- **Quality Scoring**: Rates plan quality across multiple dimensions

#### Workflow Orchestrator
- **Iterative Processing**: Manages planning-judging cycles
- **Convergence Detection**: Determines when plans are optimized
- **Cross-Validation**: Tests all model combinations

### Supported Models

| Provider | Model | Planning | Judging | Type |
|----------|-------|----------|---------|------|
| OpenAI | GPT-4o-mini | ✅ | ✅ | LLM |
| DeepSeek | DeepSeek-R1 | ✅ | ✅ | LLM |
| Google | Gemini 2.5 Flash | ✅ | ✅ | LLM |
| Meta | LLaMA 4 Scout | ✅ | ✅ | LLM |
| Custom | Rule-Based | ✅ | ✅ | Heuristic |

## 📊 Research Paper Results

The system generates evaluation results matching your research paper's methodology:

### **Table 1: Judge LLM Performance on Raw TEACh Plans**
Direct evaluation of judge performance without iterative refinement:

| Judge LLM        | Recall (%) | Precision (%) |
|------------------|------------|---------------|
| GPT-4o-mini      | **82**     | 76            |
| DeepSeek-R1      | 78         | **79**        |
| Gemini 2.5 Flash | 74         | 73            |
| LLaMA 4 Scout    | 71         | 71            |
| Rule-based       | 69         | 74            |

### **Tables 2 & 3: 4×4 Planner-Judge Matrix**
Performance matrices showing recall and precision for all planner-judge combinations:

**Recall (%) by Model Combination**

| Judge LLM \ Planner | GPT-4o-mini | DeepSeek-R1 | Gemini 2.5 | LLaMA 4 | Rule-based |
|---------------------|-------------|-------------|------------|---------|------------|
| GPT-4o-mini         | **85**      | 83          | 81         | 79      | 77         |
| DeepSeek-R1         | 82          | **84**      | 80         | 78      | 76         |
| Gemini 2.5 Flash    | 79          | 78          | **81**     | 76      | 74         |
| LLaMA 4 Scout       | 76          | 75          | 74         | **77**  | 73         |
| Rule-based          | 74          | 73          | 72         | 71      | **75**     |

**Precision (%) by Model Combination**

| Judge LLM \ Planner | GPT-4o-mini | DeepSeek-R1 | Gemini 2.5 | LLaMA 4 | Rule-based |
|---------------------|-------------|-------------|------------|---------|------------|
| GPT-4o-mini         | 78          | **80**      | 77         | 75      | 76         |
| DeepSeek-R1         | **81**      | 79          | 78         | 76      | 77         |
| Gemini 2.5 Flash    | 76          | 75          | **78**     | 74      | 75         |
| LLaMA 4 Scout       | 74          | 73          | 72         | **76**  | 74         |
| Rule-based          | 77          | 76          | 75         | 74      | **78**     |

### **Generated Outputs**
- **JSON Results**: Individual experiment results in `outputs/` directory
  - Format: `[Planner]Plan_[Judge]Judge.json` (e.g., `GPT-Plan_DS-Judge.json`)
  - One-shot results: `single-shot_[Model].json`
- **Performance Matrices**: Generated LaTeX tables for research papers
- **Detailed Metrics**: Recall, precision, and F1-score breakdowns
- **Statistical Analysis**: Cross-model performance comparisons

## 🔧 Configuration

### Environment Variables

```bash
# API Keys (required for LLM providers)
OPENAI_API_KEY=your_openai_key
DEEPSEEK_API_KEY=your_deepseek_key  
GEMINI_API_KEY=your_gemini_key
LLAMA_API_KEY=your_llama_key

# Model settings
TASK_AGENTS_TEMPERATURE=0.3
TASK_AGENTS_MAX_TOKENS=512
TASK_AGENTS_RATE_LIMIT=1.0

# Workflow settings  
TASK_AGENTS_MAX_ITERATIONS=5
TASK_AGENTS_CONVERGENCE_THRESHOLD=2
```

### Command Line Options

```bash
# Evaluation modes
--evaluation-mode iterative    # Full iterative workflow
--evaluation-mode one_shot     # Direct evaluation (paper methodology)

# Model selection  
--include-rule-based          # Include rule-based implementations
--test-mode                   # Quick test with fewer model combinations

# Data and output
--samples N                   # Number of test sequences to process
--data-path PATH             # Path to TEACh dataset
--output-dir PATH            # Results output directory
```

## 📈 Analysis Features

### Evaluation Metrics
- **Recall**: Ability to identify problematic actions that should be removed
- **Precision**: Accuracy of removal predictions (avoiding false positives)
- **F1-Score**: Harmonic mean of recall and precision
- **Confusion Matrix**: True/false positives and negatives analysis

### Research Paper Outputs
- **LaTeX Tables**: Publication-ready table formatting with `\usepackage{booktabs}`
- **Performance Matrices**: 4×4 planner-judge combination analysis
- **Statistical Analysis**: Significance testing and confidence intervals
- **Error Analysis**: Common failure patterns and model-specific behaviors

### Visualization Options
- **Heatmaps**: Model combination performance matrices
- **Distribution Plots**: Recall/precision score distributions  
- **Convergence Analysis**: Iterative workflow efficiency metrics
- **Comparative Charts**: Cross-model performance comparisons

### Development Setup

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black .

# Lint code
flake8
```

## 🙏 Acknowledgments

- Built using the **Alexa TEACh dataset** for embodied AI research
- Implements evaluation methodology from plan verification research
- Supports multiple state-of-the-art LLM providers
- Includes both neural and rule-based approaches for comprehensive comparison

## 🔧 Troubleshooting

### Common Issues

#### Import Errors
If you encounter import errors, it's due to hyphens in directory names (`judge-llm`, `planning-agent`). The demo (`test_seq.py`) includes mock classes to work around this.

**Solutions:**
- Use the demo script: `python test_seq.py` (includes mock implementations)
- For development, use `importlib.util.spec_from_file_location()` for direct imports
- Alternative: Use the `workspace/` directory which has underscore-based naming

#### API Key Issues
```bash
# Make sure .env file exists and has correct format
echo "OPENAI_API_KEY=sk-..." > .env

# Verify it's loaded
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('API Key set:', bool(os.getenv('OPENAI_API_KEY')))"
```

#### Missing Dependencies
```bash
# Install all required packages
pip install python-dotenv openai deepseek-ai google-generativeai anthropic
```

### Development Notes

The codebase has some architectural considerations:
- **Directory naming**: Uses hyphens for readability but requires import workarounds
- **Mock classes**: `test_seq.py` includes mock implementations for demos
- **Environment loading**: Uses `python-dotenv` for `.env` file support
- **Multi-provider support**: Abstract base classes allow switching LLM providers

## 📞 Support

- **Research Paper**: [Plan Verification for LLM-Based Embodied Task Completion Agents](paper/Plan_Verification.pdf)
- **Dataset**: [Alexa TEACh Dataset](https://github.com/alexa/teach)
- **Issues**: Report bugs and feature requests in GitHub Issues
- **Demo**: Run `python test_seq.py` for interactive demonstration

## 📄 License

This project is licensed under the MIT License.

---

*Task-Agents: Multi-model plan verification system for embodied AI research using natural language feedback and recall/precision evaluation on the TEACh dataset.*
