
import random
import hashlib
from typing import List
try:
    from engine.state import Player
except ImportError:
    # For standalone testing if needed
    from pydantic import BaseModel
    class Player(BaseModel):
        name: str
        nationality: str
        tier: int
        age: int = 25
        recent_form: float = 0.5
        specialist_tags: List[str] = []
        hype_score: float = 0.0

def assign_hype_scores(players: List[Player]) -> List[Player]:
    """Assigns hype_score (0.0-1.0) using logic for uncapped/high-potential players."""
    for player in players:
        hype = 0.0
        
        # Base: Uncapped young Indian players
        if player.nationality == "indian" and player.tier <= 2 and player.age < 23:
            hype += 0.3
            
        # Stats surrogates (recent_form as proxy for SR/Economy in current dataset)
        if player.recent_form > 0.8:
            hype += 0.2
            
        # Role-based hype
        if any(tag in player.specialist_tags for tag in ["finisher", "pace-death", "wrist-spin"]):
            hype += 0.15
            
        # Note: Per-team random noise is handled at valuation time in TeamAgent
        # to ensure different teams perceive the same player differently.
        # But we add a small baseline noise here too.
        hype += random.uniform(0, 0.1)
        
        player.hype_score = min(1.0, hype)
        
    return players

if __name__ == "__main__":
    # Standalone script capability
    import json
    import os
    
    json_path = "data/mock_players.json"
    if os.path.exists(json_path):
        with open(json_path, "r") as f:
            data = json.load(f)
        
        # Simple dict-based processing for the JSON file
        for p in data:
            hype = 0.0
            if p.get("nationality") == "indian" and p.get("tier", 3) <= 2 and p.get("age", 25) < 23:
                hype += 0.3
            if p.get("recent_form", 0.5) > 0.8:
                hype += 0.2
            tags = p.get("specialist_tags", [])
            if any(t in tags for t in ["finisher", "pace-death", "wrist-spin"]):
                hype += 0.15
            hype += random.uniform(0, 0.1)
            p["hype_score"] = round(min(1.0, hype), 2)
            
        with open(json_path, "w") as f:
            json.dump(data, f, indent=4)
        print("Updated hype scores in data/mock_players.json")
