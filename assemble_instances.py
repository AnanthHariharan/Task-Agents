#!/usr/bin/env python3

import os
import json

def escape_single_quotes(text: str) -> str:
    """
    Escape any single quotes in text so that when we produce lines like
    Driver.Say('some text'), it won't break if the text has apostrophes.
    """
    return text.replace("'", "\\'")

def parse_game_file(filename):
    """
    Parse a single .game.json file, produce aggregated lines for (Driver/Commander)
    with single-quoted arguments.

    Additionally, we now track the last object that was picked up and,
    if act == 201, produce PutAOnB(object, surface). If the first argument
    is "None" then we skip printing that line altogether.
    """
    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Gather interactions
    all_interactions = []
    tasks = data.get("tasks", [])
    for task in tasks:
        for ep in task.get("episodes", []):
            all_interactions.extend(ep.get("interactions", []))

    # Sort them
    all_interactions.sort(key=lambda x: x.get("time_start", 0))

    # The final lines of output
    final_lines = []

    # Logic to skip certain actions, aggregator, etc.
    commander_motion_ids = {0,1,2,3,4,5,6,7,10,11,12,13}
    driver_move_ids = {2,3,12,13}   # forward/back/double fwd/back
    driver_turn_ids = {4,5}        # turn left/right

    aggregator_mode = None
    aggregator_value = 0.0

    # For short object naming
    name_map = {}
    type_counts = {}

    # Keep track of the last object that was successfully picked up.
    last_object = None

    def simplify_oid(oid: str) -> str:
        if not oid or oid == "None":
            return "None"
        if oid in name_map:
            return name_map[oid]
        parts = oid.split('|', 1)
        base_type = parts[0]
        old_count = type_counts.get(base_type, 0)
        new_count = old_count + 1
        type_counts[base_type] = new_count

        if new_count == 1:
            short_name = base_type
        else:
            short_name = f"{base_type}{new_count}"

        name_map[oid] = short_name
        return short_name

    def flush_aggregator():
        nonlocal aggregator_mode, aggregator_value, final_lines
        if aggregator_mode == "move":
            if abs(aggregator_value) > 1e-9:
                final_lines.append(f"Driver.Move({aggregator_value})")
        elif aggregator_mode == "turn":
            if abs(aggregator_value) > 1e-9:
                if aggregator_value > 0:
                    final_lines.append(f"Driver.TurnLeft({aggregator_value})")
                else:
                    angle = -aggregator_value
                    final_lines.append(f"Driver.TurnRight({angle})")
        aggregator_mode = None
        aggregator_value = 0.0

    def agent_name(agent_id):
        return "Commander" if agent_id == 0 else "Driver"

    for interaction in all_interactions:
        a_id  = interaction["agent_id"]
        act   = interaction["action_id"]
        succ  = interaction.get("success", 1)
        utt   = interaction.get("utterance", "")
        pdel  = interaction.get("pose_delta", [])
        oid   = interaction.get("oid", "")

        # skip progress checks/panning
        if act in (500, 501, 502, 8, 9, 0, 1, 6, 7, 10, 11):
            continue

        ag = agent_name(a_id)

        # skip Commander motion
        if ag == "Commander" and act in commander_motion_ids:
            continue

        # aggregator for Driver's move or turn
        if ag == "Driver" and act in driver_move_ids:
            dx = pdel[0] if len(pdel) > 0 else 0.0
            if aggregator_mode == "move":
                aggregator_value += dx
            else:
                flush_aggregator()
                aggregator_mode = "move"
                aggregator_value = dx
            continue

        if ag == "Driver" and act in driver_turn_ids:
            angleVal = pdel[5] if len(pdel) > 5 else 0.0
            angle = float(angleVal) if act == 4 else -float(angleVal)
            if aggregator_mode == "turn":
                aggregator_value += angle
            else:
                flush_aggregator()
                aggregator_mode = "turn"
                aggregator_value = angle
            continue

        # if we reach a different kind of action, flush aggregator
        flush_aggregator()

        # handle other actions
        #if act == 0:
        #    final_lines.append(f"{ag}.Stop()")
        #elif act == 1:
        #    final_lines.append(f"{ag}.MoveTo()")
        #elif act == 6:
        #    final_lines.append(f"{ag}.LookUp()")
        #elif act == 7:
        #    final_lines.append(f"{ag}.LookDown()")
        #elif act == 10:
        #    final_lines.append(f"{ag}.MoveUp()")
        #elif act == 11:
        #    final_lines.append(f"{ag}.MoveDown()")

        if act == 100:
            escaped = escape_single_quotes(utt)
            final_lines.append(f"{ag}.Say('{escaped}')")

        elif act == 101:
            escaped = escape_single_quotes(utt)
            final_lines.append(f"{ag}.Speech('{escaped}')")

        elif act == 102:
            beep_repeat = interaction.get("repeat", 1)
            final_lines.append(f"{ag}.Beep({beep_repeat})")

        elif act == 200:  # PickUp
            if succ == 1:
                sn = simplify_oid(oid)
                final_lines.append(f"{ag}.PickUp('{sn}')")
                last_object = sn  # store the name of the last object successfully picked up

        elif act == 201:  # Place => We'll rename method to "PutAOnB" with two arguments
            if succ == 1:
                sn = simplify_oid(oid)
                # if we have a last_object, we use it. if not, skip printing
                obj_to_place = last_object if last_object else "None"
                if obj_to_place != "None":
                    final_lines.append(f"{ag}.PutAOnB('{obj_to_place}', '{sn}')")
                last_object = None

        elif act == 202:
            if succ == 1:
                sn = simplify_oid(oid)
                final_lines.append(f"{ag}.Open('{sn}')")

        elif act == 203:
            if succ == 1:
                sn = simplify_oid(oid)
                final_lines.append(f"{ag}.Close('{sn}')")

        elif act == 204:
            if succ == 1:
                sn = simplify_oid(oid)
                final_lines.append(f"{ag}.ToggleOn('{sn}')")

        elif act == 205:
            if succ == 1:
                sn = simplify_oid(oid)
                final_lines.append(f"{ag}.ToggleOff('{sn}')")

        elif act == 206:
            if succ == 1:
                sn = simplify_oid(oid)
                final_lines.append(f"{ag}.Slice('{sn}')")

        elif act == 207:
            if succ == 1:
                sn = simplify_oid(oid)
                final_lines.append(f"{ag}.Dirty('{sn}')")

        elif act == 208:
            if succ == 1:
                sn = simplify_oid(oid)
                final_lines.append(f"{ag}.Clean('{sn}')")

        elif act == 209:
            if succ == 1:
                sn = simplify_oid(oid)
                final_lines.append(f"{ag}.Fill('{sn}')")

        elif act == 210:
            if succ == 1:
                sn = simplify_oid(oid)
                final_lines.append(f"{ag}.Empty('{sn}')")

        elif act == 211:
            if succ == 1:
                sn = simplify_oid(oid)
                obj_to_place = last_object if last_object else "None"
                if obj_to_place != "None":
                    final_lines.append(f"{ag}.PourFromAIntoB('{obj_to_place}', '{sn}')")
                last_object = None

        elif act == 212:
            if succ == 1:
                sn = simplify_oid(oid)
                final_lines.append(f"{ag}.Break('{sn}')")

        elif act == 300:
            final_lines.append(f"{ag}.Navigation()")
        elif act == 400:
            final_lines.append(f"{ag}.BehindAboveOn()")
        elif act == 401:
            final_lines.append(f"{ag}.BehindAboveOff()")
        else:
            pass

    # flush aggregator at end
    flush_aggregator()

    return {
        "file": filename,
        "actions": final_lines
    }

def main():
    input_folder = "../all_game_files"
    output_file = "seq_all.json"

    big_result = []
    for fname in os.listdir(input_folder):
        if fname.endswith(".game.json"):
            full_path = os.path.join(input_folder, fname)
            result_dict = parse_game_file(full_path)
            big_result.append(result_dict)

    with open(output_file, "w", encoding="utf-8") as out_f:
        json.dump(big_result, out_f, indent=2)

    print(f"Wrote {len(big_result)} results to {output_file}")


if __name__ == "__main__":
    main()
