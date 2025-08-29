#!/usr/bin/env python3

from setuptools import setup, find_packages
from pathlib import Path

# Read README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text() if (this_directory / "README.md").exists() else ""

# Read requirements
def read_requirements():
    requirements = []
    with open('requirements.txt', 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                requirements.append(line)
    return requirements

setup(
    name="task-agents",
    version="1.0.0",
    author="Task-Agents Research Team",
    author_email="research@task-agents.ai",
    description="Multi-model plan verification system for embodied AI agents",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-org/task-agents",
    packages=find_packages(exclude=["tests*", "docs*", "games*", "outputs*", "workspace*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
        ],
        "analysis": [
            "jupyter>=1.0.0",
            "plotly>=5.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "task-agents-experiment=experiments.experiment_runner:main",
            "task-agents-evaluate=experiments.one_shot_evaluator:main", 
            "task-agents-matrix=experiments.generate_performance_matrix:main",
            "task-agents-demo=test_seq:main",
        ],
    },
    include_package_data=True,
    package_data={
        "config": ["experiment_configs/*.yaml"],
    },
)