import json
from pydantic import BaseModel
from typing import Optional

class HumanAgentDecision(BaseModel):
    decision: str  # "BID" or "PASS"
    bid_amount: Optional[int] = None

class HumanAgent:
    def __init__(self, team_id: str):
        self.team_id = team_id

    def make_decision(self, current_player_name: str, current_bid: int) -> HumanAgentDecision:
        print(f"\n--- YOUR TURN ({self.team_id}) ---")
        print(f"Player: {current_player_name}")
        print(f"Current bid: {current_bid}")
        
        while True:
            action = input("Enter 'BID <amount>' or 'PASS': ").strip().upper()
            if action == 'PASS':
                return HumanAgentDecision(decision="PASS", bid_amount=None)
            
            if action.startswith('BID'):
                parts = action.split()
                if len(parts) == 2 and parts[1].isdigit():
                    return HumanAgentDecision(decision="BID", bid_amount=int(parts[1]))
                else:
                    print("Invalid format. Example: BID 25000000")
            else:
                 print("Invalid command. Please enter BID <amount> or PASS.")
