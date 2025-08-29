# Task-Agents Project Structure

```
Task-Agents/
├── README.md                           # Main project documentation
├── PROJECT_STRUCTURE.md               # This file - project structure overview
├── requirements.txt                    # Python dependencies
├── setup.py                           # Package setup configuration
├── pyproject.toml                     # Modern Python packaging
├── test_seq.py                        # Interactive demo script
│
├── games/                             # Raw TEACh dataset
│   └── train/                         # Training game files (~1200 files)
│       └── *.game.json               # Individual game episodes
│
├── data/                              # Processed dataset files
│   ├── seq_all.json                  # All processed sequences
│   ├── seq_redundancies.json         # Sequences with redundancies
│   └── seq_shortest.json             # Shortest action sequences
│
├── shared/                           # Shared components across modules
│   ├── __init__.py
│   ├── dataset_adapters/             # Dataset processing adapters
│   ├── llm_providers/               # LLM provider implementations
│   │   ├── __init__.py
│   │   ├── base_provider.py         # Abstract base provider
│   │   ├── openai_provider.py       # OpenAI GPT provider
│   │   ├── deepseek_provider.py     # DeepSeek provider
│   │   ├── gemini_provider.py       # Google Gemini provider
│   │   └── llama_provider.py        # LLaMA provider
│   ├── utils/                       # Shared utilities
│   │   ├── __init__.py
│   │   ├── action_utils.py          # Action parsing/validation
│   │   ├── file_utils.py            # File I/O utilities
│   │   └── logging_utils.py         # Logging configuration
│   └── workflow/                    # Workflow orchestration
│       ├── __init__.py
│       ├── orchestrator.py          # Main workflow orchestrator
│       └── iteration_manager.py     # Iteration management
│
├── planning-agent/                   # Planning agent components
│   ├── __init__.py
│   ├── factory.py                   # Planner factory
│   └── models/                      # Planner model implementations
│       ├── __init__.py
│       ├── base_planner.py          # Abstract base planner
│       ├── llm_planner.py           # LLM-based planner
│       └── rule_based_planner.py    # Rule-based planner
│
├── judge-llm/                       # Judge LLM components
│   ├── __init__.py
│   ├── factory.py                   # Judge factory
│   └── models/                      # Judge model implementations
│       ├── __init__.py
│       ├── base_judge.py            # Abstract base judge
│       ├── llm_judge.py             # LLM-based judge
│       └── rule_based_judge.py      # Rule-based judge
│
├── scripts/                         # Data processing and utility scripts
│   ├── data_processing/             # Data processing scripts
│   │   ├── assemble_instances.py    # Convert raw games to actions
│   │   ├── assemble_random.py       # Random sampling
│   │   └── assemble_shortest.py     # Shortest sequences
│   └── action_processing/           # Action modification scripts
│       ├── action_modifier.py       # REMOVE/MISSING tag processing
│       └── sequence_validator.py    # Action sequence validation
│
├── experiments/                     # Experiment definitions and runners
│   ├── __init__.py
│   ├── experiment_runner.py         # Main experiment orchestrator
│   ├── one_shot_evaluator.py        # One-shot evaluation mode
│   ├── generate_performance_matrix.py # Performance table generation
│   └── analysis/                    # Analysis modules
│       ├── __init__.py
│       └── recall_precision_evaluator.py # Recall/precision metrics
│
├── workspace/                       # Additional workspace files
│   ├── experiment_runner.py         # Alternative experiment runner
│   ├── requirements.txt             # Workspace-specific requirements
│   ├── models/                      # Alternative model implementations
│   │   ├── __init__.py
│   │   ├── judge_llm.py            # Judge LLM implementation
│   │   ├── planner_llm.py          # Planner LLM implementation
│   │   ├── llm_providers.py        # LLM provider utilities
│   │   ├── workflow_orchestrator.py # Workflow orchestration
│   │   ├── llm_annotator.py        # LLM annotation utilities
│   │   ├── llm_simplifier.py       # LLM simplification utilities
│   │   └── llm_single_shot.py      # Single-shot evaluation
│   └── scripts/                     # Workspace scripts
│       ├── action_modifier.py       # Action modification utilities
│       ├── assemble_instances.py    # Instance assembly
│       ├── assemble_random.py       # Random assembly
│       └── assemble_shortest.py     # Shortest path assembly
│
├── outputs/                         # Experiment results and outputs
│   ├── *.json                       # Individual experiment results
│   │                                # Format: [Planner]_[Judge].json
│   └── single-shot_*.json           # One-shot evaluation results
│
├── config/                          # Configuration files
│   ├── __init__.py
│   ├── settings.py                  # Global settings
│   ├── model_configs.py             # Model-specific configurations
│   └── experiment_configs/          # Experiment-specific configs
│       ├── default.yaml             # Default experiment config
│       ├── quick_test.yaml          # Quick test configuration
│       └── full_evaluation.yaml     # Full evaluation config
│
├── docs/                            # Documentation
│   └── README.md                    # Documentation index
│
├── paper/                           # Research paper
│   └── Plan_Verification.pdf        # Published research paper
│
└── mcp-servers/                     # MCP server implementations
```
