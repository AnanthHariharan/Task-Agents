# Task-Agents Project Structure

```
Task-Agents/
├── README.md                           # Main project documentation
├── requirements.txt                    # Python dependencies
├── setup.py                           # Package setup configuration
├── pyproject.toml                     # Modern Python packaging
├── .env.example                       # Environment variables template
├── .gitignore                         # Git ignore patterns
│
├── games/                             # Raw TEACh dataset
│   └── train/                         # Training game files
│       └── *.game.json               # Individual game episodes
│
├── data/                              # Processed dataset files
│   ├── raw/                          # Raw processed data
│   ├── processed/                    # Cleaned and structured data
│   └── test/                         # Test datasets
│
├── shared/                           # Shared components across modules
│   ├── __init__.py
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
│   ├── models/                      # Planner model implementations
│   │   ├── __init__.py
│   │   ├── base_planner.py          # Abstract base planner
│   │   └── llm_planner.py           # LLM-based planner
│   ├── strategies/                  # Planning strategies
│   │   ├── __init__.py
│   │   ├── goal_annotator.py        # Goal identification
│   │   ├── plan_modifier.py         # Plan modification logic
│   │   └── action_generator.py      # Missing action generation
│   └── factory.py                   # Planner factory
│
├── judge-llm/                       # Judge LLM components
│   ├── __init__.py
│   ├── models/                      # Judge model implementations
│   │   ├── __init__.py
│   │   ├── base_judge.py            # Abstract base judge
│   │   └── llm_judge.py             # LLM-based judge
│   ├── evaluators/                  # Evaluation strategies
│   │   ├── __init__.py
│   │   ├── completeness_evaluator.py # Task completeness evaluation
│   │   ├── efficiency_evaluator.py   # Action efficiency evaluation
│   │   └── consistency_evaluator.py  # Logical consistency evaluation
│   └── factory.py                   # Judge factory
│
├── scripts/                         # Data processing and utility scripts
│   ├── data_processing/             # Data processing scripts
│   │   ├── assemble_instances.py    # Convert raw games to actions
│   │   ├── assemble_random.py       # Random sampling
│   │   └── assemble_shortest.py     # Shortest sequences
│   ├── action_processing/           # Action modification scripts
│   │   ├── action_modifier.py       # REMOVE/MISSING tag processing
│   │   └── sequence_validator.py    # Action sequence validation
│   └── setup/                       # Setup and configuration scripts
│       ├── install_deps.py          # Dependency installation
│       └── check_api_keys.py        # API key validation
│
├── experiments/                     # Experiment definitions and runners
│   ├── __init__.py
│   ├── experiment_runner.py         # Main experiment orchestrator
│   ├── configurations/              # Experiment configurations
│   │   ├── __init__.py
│   │   ├── base_config.py           # Base experiment config
│   │   ├── cross_validation_config.py # Cross-validation setup
│   │   └── ablation_config.py       # Ablation study setup
│   └── analysis/                    # Analysis modules
│       ├── __init__.py
│       ├── performance_analyzer.py  # Performance metrics
│       ├── convergence_analyzer.py  # Convergence analysis
│       └── visualization_generator.py # Charts and plots
│
├── outputs/                         # All output files
│   ├── experiments/                 # Experiment results
│   │   ├── runs/                    # Individual experiment runs
│   │   └── summaries/               # Experiment summaries
│   ├── analysis/                    # Analysis results
│   │   ├── metrics/                 # Performance metrics
│   │   ├── reports/                 # Text reports
│   │   └── comparisons/             # Model comparisons
│   └── visualizations/              # Generated plots and charts
│       ├── performance/             # Performance visualizations
│       ├── convergence/             # Convergence plots
│       └── comparisons/             # Comparison charts
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
│   ├── README.md                    # Documentation index
│   ├── api/                         # API documentation
│   ├── tutorials/                   # Usage tutorials
│   ├── examples/                    # Example usage
│   └── architecture/                # Architecture documentation
│
└── tests/                           # Test suite
    ├── __init__.py
    ├── unit/                        # Unit tests
    ├── integration/                 # Integration tests
    └── fixtures/                    # Test data and fixtures
```

## Key Benefits of This Structure:

1. **Clear Separation of Concerns**: Each high-level folder has a specific purpose
2. **Modular Design**: Components are loosely coupled and reusable
3. **Scalability**: Easy to add new models, strategies, or experiments
4. **Professional Standards**: Follows Python packaging best practices
5. **Maintainability**: Clear organization makes code easier to maintain
6. **Extensibility**: Easy to extend with new LLM providers or evaluation methods