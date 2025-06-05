import time
import os
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

prompt = (
    "Given a JSON file containing action sequences, process it to output a new annotated JSON file following these strict rules:\n\n"
    "1. Add a '# GOAL' statement at the start of each file's action sequence, summarising the overall objective.\n"
    "2. Do NOT modify dialogue actions (i.e., Commander.Say() and Driver.Say() should remain unchanged).\n"
    "3. Add annotations for each non-dialogue action. Example: Driver.PickUp('Newspaper') → 'Driver picks up the newspaper'.\n"
    "4. Mark actions that are unnecessary to achieve the goal with '# REMOVE' and a brief explanation. \n\n"
    "REMOVE tagging rules:\n"
    "- Add a '# REMOVE' tag to 'PickUp' actions involving objects irrelevant to the GOAL. If any object in a 'PickUp' action is irrelevant, also add '# REMOVE' to the next 'PlaceAOnB' action.\n"
    "- Do NOT mark a 'PickUp' action as REMOVE if the object is used for a relevant 'PourFromAIntoB' action later. For instance, picking up a mug to wash it or pouring liquid for a task should be kept.\n"
    "- Do NOT mark 'PlaceAOnB' actions as REMOVE unless the preceding 'PickUp' action was marked REMOVE.\n"
    "- Add a '# REMOVE' tag to consecutive 'Move' and 'Turn' actions that cancel each other out (e.g., 'Move(1.0)' followed by 'Move(-1.0)').\n"
    "\nExample:\n"
    "Commander.Say('I need the mug to be washed.'),\n"
    "Driver.Say('ok.'),\n"
    "Driver.ToggleOff('Faucet'), // Driver turns off faucet # REMOVE: unnecessary to turn off faucet when not turned on yet\n"
    "Driver.PickUp('Egg'), // Driver picks up an egg. # REMOVE: unnecessary to pick up egg\n"
    "Driver.PlaceAOnB('Egg', 'CoffeeTable'), // Driver places an egg on coffee table. # REMOVE: previous 'PickUp' action was unnecessary\n"
    "Driver.PickUp('Mug'), // Driver picks up the mug.\n"
    "Driver.PlaceAOnB('Mug', 'Sink'), // Driver places mug in the sink.\n"
    "Driver.ToggleOn('Faucet'), // Driver turns on faucet to wash the mug\n"
    "Driver.ToggleOff('Faucet'), // Driver turns off faucet after washing the mug\n\n"
    "Now, process the provided JSON file exactly as described, preserving the original format while adding these modifications. Ensure that all 100 file action sequences are processed without omission."
)

import time
import json

def query_gpt4o_mini(prompt):
    response = client.chat.completions.create(
        messages=[
            {"role": "system", "content": "You are a helpful assistant that provides concise annotations for game actions."},
            {"role": "user", "content": prompt}
        ],
        model="gpt-4o",
        prompt=prompt,
        max_tokens=150,
        temperature=0.7,
        n=1,
        stop=None
    )
    return response["choices"][0]["text"].strip()

def get_goal(block):
    prompt = (
        "Read the following actions and determine the overall goal of the sequence:\n\n"
        f"{json.dumps(block['actions'], indent=2)}\n\n"
        "Provide a concise goal statement."
    )
    goal = query_gpt4o_mini(prompt)
    return goal.strip()

def check_pickup_relevance(goal, pickup_action):
    prompt = (
        f"Given the goal: {goal}\n\n"
        f"Is the PickUp action '{pickup_action}' relevant to achieving this goal? "
        "If yes, reply with 'relevant'. If not, reply with '# REMOVE:' followed by a brief explanation of why it is irrelevant."
    )
    response = query_gpt4o_mini(prompt)
    return response.strip()

def process_block(block):
    annotated_actions = []
    
    goal = get_goal(block)
    annotated_actions.append(f"# GOAL: {goal}")

    prev_pickup_removed = False 

    for i, action in enumerate(block["actions"]):
        original_action = action.strip()

        if "Commander.Say(" in original_action or "Driver.Say(" in original_action:
            annotated_actions.append(original_action)
            continue

        if "Driver.ToggleOff(" in original_action and not any("Driver.ToggleOn(" in a for a in block["actions"][:i]):
            annotated_actions.append(original_action + "  # REMOVE: unnecessary to turn off before turning on")
            continue

        if "Driver.PickUp(" in original_action:
            relevance_response = check_pickup_relevance(goal, original_action)
            if relevance_response.startswith("# REMOVE:"):
                annotated_actions.append(original_action + "  " + relevance_response)
                prev_pickup_removed = True
            else:
                annotated_actions.append(original_action)
            continue

        if "Driver.PutAOnB(" in original_action and prev_pickup_removed:
            annotated_actions.append(original_action + "  # REMOVE: unnecessary placement due to previous irrelevant PickUp")
            prev_pickup_removed = False
            continue

        if "Driver.Move(" in original_action and i > 0:
            prev_action = block["actions"][i - 1]
            if "Driver.Move(" in prev_action:
                try:
                    prev_distance = float(prev_action.split("(")[1].split(")")[0])
                    current_distance = float(original_action.split("(")[1].split(")")[0])
                    if prev_distance == -current_distance:
                        annotated_actions.append(original_action + "  # REMOVE: redundant movement")
                        continue
                except ValueError:
                    pass

        if "Driver.TurnLeft(" in original_action:
            try:
                degrees = float(original_action.split("(")[1].split(")")[0])
                if degrees % 360 == 0:
                    annotated_actions.append(original_action + "  # REMOVE: redundant full rotation")
                    continue
            except ValueError:
                pass

        annotated_actions.append(original_action)

    return {
        "file": block["file"],
        "actions": annotated_actions
    }

def main():
    with open('seq_random.json', 'r', encoding='utf-8') as infile:
        content = json.load(infile)

    processed_content = [process_block(block) for block in content]

    with open('test_gpt_ann.json', 'w', encoding='utf-8') as outfile:
        json.dump(processed_content, outfile, indent=4)

if __name__ == "__main__":
    main()
