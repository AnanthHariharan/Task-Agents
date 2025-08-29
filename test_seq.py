#!/usr/bin/env python3
# Simple demo without complex imports
#
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from dotenv import load_dotenv
    load_dotenv()
    print(f"✓ Loaded .env file. OPENAI_API_KEY is {'set' if os.getenv('OPENAI_API_KEY') else 'not set'}")
except ImportError:
    print("⚠ python-dotenv not installed. Install with: pip install python-dotenv")
    print("Or set OPENAI_API_KEY manually with: export OPENAI_API_KEY='your-key'")

sys.path.append('/Users/ananthhariharan/Documents/Research/Task-Agents')
sys.path.append('/Users/ananthhariharan/Documents/Research/Task-Agents/judge-llm')
sys.path.append('/Users/ananthhariharan/Documents/Research/Task-Agents/planning-agent')
sys.path.append('/Users/ananthhariharan/Documents/Research/Task-Agents/shared')

try:

    print("🚀 Running simplified demo (using mock responses)")

    class MockProvider:
        def __init__(self, **kwargs):
            pass

        def generate(self, prompt, system_prompt=None):
            if "annotate_goal" in prompt.lower() or "goal" in prompt.lower():
                return "Make coffee using the coffee machine"
            elif "judge" in prompt.lower() or "evaluate" in prompt.lower():
                return """ACTION: Driver.Move(1.0)
ANNOTATION: Driver moves towards the coffee area. This is necessary to get to the coffee machine.

ACTION: Driver.PickUp('Soap')
ANNOTATION: Driver picks up soap. #REMOVE: This is unnecessary for making coffee - soap is used for cleaning, not coffee preparation.

ACTION: Driver.Place('CounterTop')
ANNOTATION: Driver places soap on counter. #REMOVE: Since picking up soap was unnecessary, placing it is also unnecessary.

ACTION: Driver.ToggleOff('CoffeeMachine')
ANNOTATION: Driver turns off coffee machine. #REMOVE: This is illogical - you shouldn't turn off a machine before turning it on, especially when it might already be off.

ACTION: Driver.PickUp('CoffeeCup')
ANNOTATION: Driver picks up a coffee cup. This makes sense for making coffee.

ACTION: Driver.Place('CoffeeMachine')
ANNOTATION: Driver places cup in/on coffee machine. Good - this positions the cup to receive coffee.

ACTION: Driver.ToggleOn('CoffeeMachine')
ANNOTATION: Driver turns on coffee machine. Excellent - this starts the brewing process.

ACTION: Driver.PickUp('CoffeeCup')
ANNOTATION: Driver picks up the coffee cup. This would be to get the finished coffee.

#MISSING: The sequence is missing the actual coffee brewing wait time and turning off the machine after use for safety. Also missing coffee grounds or pod insertion."""
            elif "modify" in prompt.lower():
                return """Driver.Move(1.0)
Driver.PickUp('CoffeeCup')
Driver.Place('CoffeeMachine')
Driver.ToggleOn('CoffeeMachine')
Driver.PickUp('CoffeeCup')
Driver.ToggleOff('CoffeeMachine')"""
            else:
                return "The plan looks good now! All unnecessary actions have been removed and the missing safety step of turning off the machine has been added."

    class MockJudge:
        def __init__(self, provider, name=None):
            self.provider = provider

        def judge_plan(self, actions, goal):
            response = self.provider.generate("judge plan")

            has_remove = "#REMOVE" in response
            has_missing = "#MISSING" in response
            return {
                'natural_language_feedback': response,
                'has_changes': has_remove or has_missing,
                'remove_actions': [{'action': 'soap actions'}] if has_remove else [],
                'missing_requirements': ['safety measures'] if has_missing else []
            }

    class MockPlanner:
        def __init__(self, provider, name=None):
            self.provider = provider

        def annotate_goal(self, actions, context):
            return self.provider.generate("annotate goal")

        def modify_plan(self, actions, feedback, goal):
            response = self.provider.generate("modify plan")
            return response.strip().split('\n')

    provider = MockProvider()
    LLMJudge = MockJudge
    LLMPlanner = MockPlanner
    OpenAIProvider = MockProvider

    print("✅ Using mock demo classes")

except Exception as e:
    print(f"❌ Error setting up demo: {e}")
    exit(1)

def demonstrate_complete_workflow():
    """Demonstrate the complete workflow: goal annotation -> judge evaluation -> planner fixes -> final output"""


    provider = OpenAIProvider(model_name="gpt-4o-mini")
    judge = LLMJudge(provider, name="Natural Language Judge")
    planner = LLMPlanner(provider, name="LLM Planner")


    original_actions = [
        "Driver.Move(1.0)",
        "Driver.PickUp('Soap')",  # Irrelevant to coffee making
        "Driver.Place('CounterTop')",  # Unnecessary soap placement
        "Driver.ToggleOff('CoffeeMachine')",  # Turning off before turning on
        "Driver.PickUp('CoffeeCup')",
        "Driver.Place('CoffeeMachine')",
        "Driver.ToggleOn('CoffeeMachine')",
        "Driver.PickUp('CoffeeCup')"
        # Missing: Actually brewing coffee, turning off machine safely
    ]

    print("=" * 80)
    print("COMPLETE PLAN VERIFICATION WORKFLOW DEMO")
    print("=" * 80)

    print("\n📋 ORIGINAL ACTION SEQUENCE:")
    for i, action in enumerate(original_actions, 1):
        print(f"{i:2d}. {action}")

    # Step 1: Goal Annotation by Planner
    print("\n" + "=" * 60)
    print("STEP 1: GOAL ANNOTATION BY PLANNING AGENT")
    print("=" * 60)

    goal = planner.annotate_goal(original_actions, "Household task sequence")
    print(f"🎯 IDENTIFIED GOAL: {goal}")

    # Step 2: Judge Evaluation with Line-by-Line Annotation
    print("\n" + "=" * 60)
    print("STEP 2: JUDGE EVALUATION (LINE-BY-LINE)")
    print("=" * 60)

    judge_result = judge.judge_plan(original_actions, goal)

    print("📝 JUDGE'S LINE-BY-LINE ANALYSIS:")
    print(judge_result['natural_language_feedback'])

    # Step 3: Check if changes are needed
    if judge_result['has_changes']:
        print(f"\n⚠️  ISSUES FOUND:")
        print(f"   • Actions to remove: {len(judge_result['remove_actions'])}")
        print(f"   • Missing requirements: {len(judge_result['missing_requirements'])}")

        # Step 4: Planner fixes the issues
        print("\n" + "=" * 60)
        print("STEP 3: PLANNER FIXES BASED ON JUDGE FEEDBACK")
        print("=" * 60)

        # Extract feedback for planner
        feedback_text = judge_result['natural_language_feedback']

        modified_actions = planner.modify_plan(original_actions, feedback_text, goal)

        print("🔧 PLANNER'S MODIFICATIONS:")
        print("Modified action sequence based on judge feedback:")
        for i, action in enumerate(modified_actions, 1):
            print(f"{i:2d}. {action}")

        # Step 5: Final verification
        print("\n" + "=" * 60)
        print("STEP 4: FINAL VERIFICATION")
        print("=" * 60)

        final_judgment = judge.judge_plan(modified_actions, goal)

        if final_judgment['has_changes']:
            print("⚠️  Judge still found issues:")
            print(final_judgment['natural_language_feedback'])
        else:
            print("✅ JUDGE APPROVAL: Plan is now satisfactory!")
            print(final_judgment['natural_language_feedback'])

        # Final clean output
        print("\n" + "=" * 80)
        print("🎉 FINAL CLEANED-UP ACTION SEQUENCE")
        print("=" * 80)
        print(f"Goal: {goal}")
        print("\nFinal Actions:")
        for i, action in enumerate(modified_actions, 1):
            print(f"{i:2d}. {action}")

    else:
        print("✅ No issues found - original plan is acceptable!")
        print("\n" + "=" * 80)
        print("🎉 FINAL ACTION SEQUENCE (NO CHANGES NEEDED)")
        print("=" * 80)
        print(f"Goal: {goal}")
        print("\nActions:")
        for i, action in enumerate(original_actions, 1):
            print(f"{i:2d}. {action}")

def test_natural_language_feedback():
    """Quick test of natural language feedback only"""
    demonstrate_complete_workflow()

if __name__ == "__main__":
    test_natural_language_feedback()
