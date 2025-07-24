#!/usr/bin/env python3

"""
Test script to demonstrate the natural language feedback capabilities of the Judge LLM
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print(f"✓ Loaded .env file. OPENAI_API_KEY is {'set' if os.getenv('OPENAI_API_KEY') else 'not set'}")
except ImportError:
    print("⚠ python-dotenv not installed. Install with: pip install python-dotenv")
    print("Or set OPENAI_API_KEY manually with: export OPENAI_API_KEY='your-key'")

# Add both current directory and subdirectories to path
sys.path.append('/Users/ananthhariharan/Documents/Research/Task-Agents')
sys.path.append('/Users/ananthhariharan/Documents/Research/Task-Agents/judge-llm')
sys.path.append('/Users/ananthhariharan/Documents/Research/Task-Agents/shared')

try:
    from models.llm_judge import LLMJudge
    from llm_providers.openai_provider import OpenAIProvider
except ImportError:
    print("Could not import modules. Please run from the Task-Agents directory.")
    exit(1)

def test_natural_language_feedback():
    """Test the Judge LLM's natural language feedback capabilities"""
    
    # Initialize the judge with OpenAI provider
    provider = OpenAIProvider(model_name="gpt-4o-mini")
    judge = LLMJudge(provider, name="Natural Language Judge")
    
    # Example action sequence with some issues
    action_sequence = [
        "Driver.Move(1.0)",
        "Driver.PickUp('Soap')",  # Irrelevant to coffee making
        "Driver.Place('CounterTop')",
        "Driver.ToggleOff('CoffeeMachine')",  # Turning off before turning on
        "Driver.PickUp('CoffeeCup')",
        "Driver.Place('CoffeeMachine')",
        "Driver.ToggleOn('CoffeeMachine')",
        "Driver.PickUp('CoffeeCup')"
        # Missing: Actually making coffee, turning off machine
    ]
    
    goal = "Make coffee in a cup"
    
    print("=" * 60)
    print("TESTING NATURAL LANGUAGE JUDGE FEEDBACK")
    print("=" * 60)
    print(f"\nGOAL: {goal}")
    print(f"\nACTION SEQUENCE:")
    for i, action in enumerate(action_sequence, 1):
        print(f"{i}. {action}")
    
    print("\n" + "=" * 60)
    print("STRUCTURED JUDGE FEEDBACK:")
    print("=" * 60)
    
    # Get structured feedback (original method)
    result = judge.judge_plan(action_sequence, goal)
    print(result['natural_language_feedback'])
    
    print("\n" + "=" * 60)
    print("PURE NATURAL LANGUAGE FEEDBACK:")
    print("=" * 60)
    
    # Get pure natural language feedback (new method)
    natural_feedback = judge.get_natural_language_feedback(action_sequence, goal)
    print(natural_feedback)
    
    print("\n" + "=" * 60)
    print("PLAN COMPARISON EXAMPLE:")
    print("=" * 60)
    
    # Test plan comparison
    plan_a = [
        "Driver.PickUp('CoffeeCup')",
        "Driver.Place('CoffeeMachine')",
        "Driver.ToggleOn('CoffeeMachine')",
        "Driver.PickUp('CoffeeCup')"
    ]
    
    plan_b = [
        "Driver.ToggleOn('CoffeeMachine')",
        "Driver.PickUp('CoffeeCup')",
        "Driver.Place('CoffeeMachine')",
        "Driver.PickUp('CoffeeCup')",
        "Driver.ToggleOff('CoffeeMachine')"
    ]
    
    comparison = judge.compare_plans(plan_a, plan_b, goal)
    print(comparison['comparison'])

if __name__ == "__main__":
    test_natural_language_feedback()