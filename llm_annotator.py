import os
import json
import time
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def annotate_action(action: str) -> str:
    """
    Uses GPT to generate a short annotation for a given action.
    The prompt instructs GPT to describe the action in plain English.
    """
    prompt = (
        "Annotate each non-dialogue game action in the given json file with a short comment that explains what the action does in the context of the whole file task sequence in plain English. "
        "Do NOT annotate dialogue actions (Driver.Say or Commander.Say)."
        "Format is given below. YOU ONLY need to add the description of action.:" 
        "For example, given a non-dialogue action: Driver.<ACTION>(<OBJECT>), you just need to add: // <Description of action>"
        "HOW IT SHOULD LOOK AT THE END: EXAMPLES BELOW:\n"
        "“Driver.Say('hi'),”\n"
        "Commander.Say('Get the mug and clean it in the sink'),\n"
        "“Driver.PickUp('Mug'),” // Driver picks up mug to wash\n"
        "“Driver.PlaceOn('Sink'),” // Driver places mug in sink to wash\n"
        "“Driver.ToggleOn('Faucet'),” // Driver toggles on faucet to wash dishes\n"
        "“Driver.ToggleOff('Faucet'),” // Driver toggles off faucet after use\n"
    )
    # Append the specific action to be annotated. 
    prompt += f"\nAction: {action}\nAnnotation:"
    
    try:
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a helpful assistant that provides concise annotations for game actions."},
                {"role": "user", "content": prompt}
            ],
            model="gpt-4o",
            temperature=0.3,
            max_tokens=30,
        )
        # Extract and return the annotation text
        annotation = response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error annotating action {action}: {e}")
        annotation = "Annotation unavailable"
    return annotation

def main():
    # Load the sequences from 'shortest_sequences.json'
    with open('shortest_sequences.json', 'r', encoding='utf-8') as infile:
        sequences = json.load(infile)
    
    # Open output file to write annotated actions
    with open('annotated_actions.txt', 'w', encoding='utf-8') as outfile:
        # Iterate over each sequence in the JSON file
        for seq in sequences:
            file_path = seq.get("file", "Unknown file")
            outfile.write(f"File: {file_path}\n")
            
            actions = seq.get("actions", [])
            for action in actions:
                # Get GPT annotation for the current action
                annotation = annotate_action(action)
                # Write the action with its annotation as a comment
                outfile.write(f"{action}, // {annotation}\n")
                # Delay to help avoid rate limits; adjust if necessary
                time.sleep(1)
            outfile.write("\n")  # Separate each file's annotations with a blank line

if __name__ == '__main__':
    main()