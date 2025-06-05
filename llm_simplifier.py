import os
import time
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from the .env file.
load_dotenv()

# Initialise the OpenAI client using your API key.
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def process_block(block_text: str) -> str:
    """
    Processes a block of annotated actions from the text file.
    It uses GPT-4o-mini to:
      - Add a GOAL line at the beginning of the block summarising the overall task.
      - For each non-dialogue action (i.e. excluding any actions with .Say()), examine the action.
        If the action is unnecessary for achieving the overall goal—following these rules:
          • 'ToggleOff' actions occurring before any 'ToggleOn' actions,
          • 'PickUp' actions with objects irrelevant to the task (and their corresponding 'Place' actions),
          • Consecutive 'Move' and 'Turn' sequences that cancel each other out,
        then append a "# REMOVE: <reason>" comment with a brief explanation.
    The function returns the processed block text in the same format as the input.
    """
    # Construct the detailed prompt with instructions and examples.
    prompt = (
        "You are an action simplification agent. Your task is to process a block of annotated game actions. "
        "Each block starts with a line beginning with 'File:' followed by several lines of actions. "
        "You must first add a GOAL: line at the top that summarises the overall objective of the action sequence. "
        "Then, for each non-dialogue action (actions that are not Driver.Say() or Commander.Say()), if an action is unnecessary for the goal, append a '# REMOVE: <reason>' comment with a brief explanation. "
        "Follow these rules strictly:\n"
        "- Add a REMOVE tag to any 'ToggleOff' actions appearing BEFORE any 'ToggleOn' actions (because nothing is being done).\n"
        "- Add a REMOVE tag to any 'PickUp' actions involving objects irrelevant to the task. Then, add a REMOVE tag to the next 'PlaceOn' action.\n"
        "- DO NOT add a REMOVE tag to a 'PlaceOn' action unless you added a REMOVE tag to the previous 'PickUp' action. Remember, the PlaceOn action's argument is WHERE it places the object it just picked up, not WHAT it places.\n"
        "- Add a REMOVE tag to consecutive 'Move' and 'Turn' actions that cancel each other out (for example, 'Move(1.0)' followed immediately by 'Move(-1.0)', or sequences like 'TurnLeft(270)', 'TurnLeft(45)').\n"
        "Do not modify dialogue actions (i.e. those using .Say()).\n"
        "Example:\n"
        "File: ../all_game_files/7d2a79f43e605c36_1657.game.json\n"
        "# GOAL: Newspaper needs to be placed on Coffee Table\n"
        "Commander.Say('I need the newspaper to be placed on a single table.')\n,"
        "Driver.Say('ok.')\n,"
        "Driver.ToggleOff('Faucet'), // Driver turns off faucet # REMOVE: unnecessary to turn off faucet when not turned on yet"
        "Driver.PickUp('Egg'), // Driver picks up an egg. # REMOVE: unnecessary to pick up egg\n"
        "Driver.Place('CoffeeTable'), // Driver places an egg on coffee table. # REMOVE: previous 'PickUp' action was unnecessary\n"
        "Driver.PickUp('Newspaper'), // Driver picks up the newspaper.\n"
        "Driver.Place('CoffeeTable'), // Driver places an object on the coffee table.\n"
        "Now, process the following file exactly as described, preserving the original format and adding the modifications:\n\n"
    )
    
    # Append the current block text to the prompt.
    full_prompt = prompt + block_text
    
    try:
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a helpful assistant specialised in simplifying game action sequences."},
                {"role": "user", "content": full_prompt}
            ],
            model="gpt-4o-mini",
            temperature=0.3,
            max_tokens=512,
        )
        processed_block = response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error processing block: {e}")
        processed_block = block_text  # Fallback to the original block if there is an error
    return processed_block

def main():
    # Read the file containing the annotated actions.
    with open('annotated_actions.txt', 'r', encoding='utf-8') as infile:
        content = infile.read().strip()
    
    # Assume each block is separated by two newlines.
    blocks = content.split("\n\n")
    processed_blocks = []
    
    for block in blocks:
        processed_block = process_block(block)
        processed_blocks.append(processed_block)
        # Pause briefly between API calls to help avoid rate limits.
        time.sleep(1)
    
    final_output = "\n\n".join(processed_blocks)
    
    # Write the final processed output to a new file.
    with open('simplified_actions.txt', 'w', encoding='utf-8') as outfile:
        outfile.write(final_output)

if __name__ == '__main__':
    main()