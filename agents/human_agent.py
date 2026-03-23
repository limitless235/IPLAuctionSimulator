from engine.state import Player
from pydantic import BaseModel


class HumanDecision(BaseModel):
    decision: str  # "BID" or "PASS"


class HumanAgent:
    def __init__(self, team_id: str):
        self.team_id = team_id

    def make_decision(self, player: Player, current_bid: int,
                      next_bid: int, remaining_budget: int,
                      squad_size: int) -> HumanDecision:
        print(f"\n{'='*50}")
        print(f"[YOUR TURN — {self.team_id}]")
        print(f"Player:          {player.name}")
        print(f"Role:            {player.role}")
        print(f"Nationality:     {player.nationality}")
        print(f"Tier:            {player.tier} | Star: {player.is_star} | Form: {player.recent_form}")
        print(f"Current bid:     {current_bid / 10000000:.1f} Cr")
        print(f"Next bid:        {next_bid / 10000000:.1f} Cr")
        print(f"Your budget:     {remaining_budget / 10000000:.1f} Cr remaining")
        print(f"Your squad:      {squad_size} players")
        print(f"{'='*50}")

        while True:
            choice = input("Enter BID or PASS: ").strip().upper()
            if choice in ("BID", "PASS"):
                return HumanDecision(decision=choice)
            print("Invalid input. Enter BID or PASS.")