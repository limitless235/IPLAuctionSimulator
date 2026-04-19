
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

def _compute_hype(nationality, tier, age, recent_form, specialist_tags):
    """Core hype logic shared by both Player-object and dict-based paths.

    In real IPL auctions, hype disproportionately affects uncapped / lower-tier
    players.  A Tier-1 star sells high regardless — their stats speak.  But for
    a Tier-3/4 domestic youngster, scout buzz, domestic tournament clips, and
    social-media virality are often the PRIMARY differentiator between base
    price and a surprise ₹5 Cr bid.

    Hype sources modelled:
      1. Youth factor  — young Indian players generate domestic circuit buzz
      2. Recent form   — hot Ranji / SMAT / Vijay Hazare stats create hype
      3. Specialist role buzz — finishers, death bowlers, wrist-spinners are
         the most hyped archetypes in modern T20 scouting
      4. Tier-based scaling — lower-tier players get MORE hype lift because
         hype is all they have; higher-tier players are already valued on merit
    """
    hype = 0.0

    # 1. Youth factor — young Indian players of ANY tier generate buzz
    if nationality == "indian" and age < 23:
        hype += 0.25

    # 2. Recent form — strong domestic/international form creates excitement
    if recent_form > 0.8:
        hype += 0.25
    elif recent_form > 0.65:
        hype += 0.1

    # 3. Specialist role buzz — the most hyped archetypes in T20 scouting
    hype_tags = {"finisher", "pace-death", "wrist-spin", "hard-hitting",
                 "pace-powerplay", "death-bowling"}
    if any(tag in specialist_tags for tag in hype_tags):
        hype += 0.2

    # 4. Tier-based scaling — hype matters MORE for lower-tier players
    #    Tier 4: ×1.4  (hype is everything for an uncapped unknown)
    #    Tier 3: ×1.2  (domestic proven, hype amplifies)
    #    Tier 2: ×1.0  (established, hype is a nice-to-have)
    #    Tier 1: ×0.6  (franchise stars — hype is noise)
    tier_scale = {1: 0.6, 2: 1.0, 3: 1.2, 4: 1.4}
    hype *= tier_scale.get(tier, 1.0)

    # 5. Overseas youth — less domestic circuit buzz, but international
    #    T20 leagues and bilateral series create some hype
    if nationality == "overseas" and age < 25 and recent_form > 0.7:
        hype += 0.15

    # Baseline noise — per-player randomness (team-specific noise is added
    # separately in TeamAgent.compute_valuation)
    hype += random.uniform(0, 0.08)

    return round(min(1.0, hype), 2)


def assign_hype_scores(players: List[Player]) -> List[Player]:
    """Assigns hype_score (0.0-1.0) to all players."""
    for player in players:
        player.hype_score = _compute_hype(
            player.nationality, player.tier, player.age,
            player.recent_form, player.specialist_tags
        )
    return players

if __name__ == "__main__":
    # Standalone script capability
    import json
    import os

    json_path = "data/mock_players.json"
    if os.path.exists(json_path):
        with open(json_path, "r") as f:
            data = json.load(f)

        for p in data:
            p["hype_score"] = _compute_hype(
                p.get("nationality", "indian"),
                p.get("tier", 3),
                p.get("age", 25),
                p.get("recent_form", 0.5),
                p.get("specialist_tags", [])
            )

        with open(json_path, "w") as f:
            json.dump(data, f, indent=4)
        print("Updated hype scores in data/mock_players.json")
