
import json
import os
from typing import List, Dict

# Map to match the requirements
SPECIALIST_TAGS_SCHEMA = {
    "BATTING": ["opener", "top-order", "middle-order", "finisher", "hard-hitting"],
    "BOWLING": ["pace-powerplay", "pace-death", "pace-middle", "wrist-spin", "finger-spin", "swing"],
    "KEEPING": ["keeper-batter", "keeper-lower"],
    "ALL-ROUNDER": ["batting-allrounder", "bowling-allrounder", "bits-and-pieces"]
}

def assign_tags(player: Dict) -> List[str]:
    tags = []
    role = player.get("role", "").lower()
    pos = player.get("batting_position", "").lower()
    style = player.get("bowling_style", "").lower()
    s_tag = player.get("specialist_tag", "").lower()
    bv = player.get("brand_value", 0.0)
    pace = player.get("pace_bowler", False)
    spin = player.get("spin_bowler", False)

    # Batting Heuristics
    if pos == "opener":
        tags.append("opener")
    elif pos == "top-order":
        tags.append("top-order")
    elif pos == "middle-order":
        tags.append("middle-order")
    elif pos == "finisher" or "finisher" in s_tag:
        tags.append("finisher")
    
    if bv > 0.8 and role in ["batter", "all_rounder"]:
        tags.append("hard-hitting")

    # Bowling Heuristics
    if pace:
        if bv > 0.8:
            tags.append("pace-death")
        elif bv > 0.6:
            tags.append("pace-powerplay")
        else:
            tags.append("pace-middle")
        
        if "swing" in s_tag or "swing" in style or bv > 0.75:
            tags.append("swing")
    
    if spin:
        if "wrist" in style or "leg" in style or "china" in style:
            tags.append("wrist-spin")
        else:
            tags.append("finger-spin")

    # Wicket Keeping
    if role == "wicket_keeper":
        if pos in ["opener", "top-order", "middle-order"]:
            tags.append("keeper-batter")
        else:
            tags.append("keeper-lower")

    # All-rounders
    if role == "all_rounder":
        if "bat" in s_tag or pos not in ["none", ""]:
            tags.append("batting-allrounder")
        if "bowl" in s_tag or pace or spin:
            tags.append("bowling-allrounder")
        
        if not tags or (len(tags) == 1 and tags[0] in ["hard-hitting"]):
            tags.append("bits-and-pieces")

    # Final cleanup - deduplicate and filter
    return list(set(tags))

def main():
    json_path = "data/mock_players.json"
    if not os.path.exists(json_path):
        print(f"Error: {json_path} not found")
        return

    with open(json_path, "r") as f:
        players = json.load(f)

    summary = {}
    for player in players:
        tags = assign_tags(player)
        player["specialist_tags"] = tags
        
        for t in tags:
            summary[t] = summary.get(t, 0) + 1

    with open(json_path, "w") as f:
        json.dump(players, f, indent=4)

    print("--- Specialist Tags Assignment Summary ---")
    for tag, count in sorted(summary.items(), key=lambda x: x[1], reverse=True):
        print(f"{tag}: {count}")
    print(f"Total players processed: {len(players)}")

if __name__ == "__main__":
    main()
