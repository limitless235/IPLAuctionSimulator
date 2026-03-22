import json
import time
from typing import Dict, Any, List

from engine.auction_engine import AuctionEngine
from engine.state import AuctionState
from agents.team_agent import TeamAgent
from agents.human_agent import HumanAgent
from tools.valuation_filter import ValuationFilter
from store.memory import MemoryStore

class AuctionOrchestrator:
    def __init__(self, engine: AuctionEngine, team_agents: Dict[str, TeamAgent], human_team_id: str = None, memory: MemoryStore = None):
        self.engine = engine
        self.team_agents = team_agents
        self.human_team_id = human_team_id
        self.memory = memory or MemoryStore()

    def run_auction(self, test_mode: bool = False):
        print("Starting IPL Auction Simulator...")
        # 1. State initialization
        resp = self.engine.start_auction()
        self._log_test(test_mode, "AUCTION START", resp)

        while True:
            # 2. State Sync: Always get latest state after any action
            state = self.engine.get_state()
            
            if state.is_auction_complete:
                print("AUCTION COMPLETE.")
                break
                
            if not state.current_player:
                # No player to bid on but auction not complete? 
                # Could happen if next_player() was needed. Let's force next.
                self.engine.next_player()
                continue
                
            player = state.current_player
            current_bid = state.current_bid
            bidding_rounds = state.bidding_rounds
            
            # 3. Loop Safety Limit Check
            if bidding_rounds >= 20:
                print(f"[LIMIT EXCEEDED] Max rounds reached for {player.name}. Forcing sale.")
                self.engine.next_player()
                continue
                
            active = state.active_bidders
            
            # 4. End Condition Strictness
            # If 0 active bidders, or 1 active bidder (and they are the highest bidder), the player is sold or skipped
            if len(active) == 0:
                print(f"[SOLD/UNSOLD] Resolving {player.name}...")
                self.engine.next_player()
                # Scarcity index update
                self.memory.update_scarcity_index(self.engine.state.unsold_players, self.engine.state.unsold_players + self.engine.state.sold_players)
                continue
                
            if len(active) == 1 and state.highest_bidder == active[0]:
                print(f"[SOLD] {player.name} sold to {state.highest_bidder} for {current_bid}.")
                self.engine.next_player()
                self.memory.update_scarcity_index(self.engine.state.unsold_players, self.engine.state.unsold_players + self.engine.state.sold_players)
                continue
                
            # 5. Iterative Sequential Calling
            # Identify whose turn it is. We simply pick the first active bidder who is NOT the highest bidder
            active_turn_bidders = [t for t in active if t != state.highest_bidder]
            if not active_turn_bidders:
                # Should not happen if len(active) > 1, but safety fallback
                pass
                
            current_team_id = active_turn_bidders[0]
            
            # Human Intervention
            if current_team_id == self.human_team_id:
                human = HumanAgent(self.human_team_id)
                action = human.make_decision(player.name, current_bid)
                self._apply_and_retry(current_team_id, action.decision, action.bid_amount, test_mode)
                continue
                
            # LLM Team Agent
            agent = self.team_agents.get(current_team_id)
            if not agent:
                # Invalid team id? Skip
                self.engine.apply_action({"action_type": "PASS", "team_id": current_team_id})
                continue
                
            # 6. Performance Control: Valuation Filter check (auto-pass)
            scarcity = self.memory.role_scarcity_index.get(player.role, 1.0)
            filter_tool = ValuationFilter(agent.team, player, agent.personality, scarcity)
            
            if filter_tool.should_auto_pass(current_bid):
                 self._log_test(test_mode, f"{current_team_id} Heuristic Skip", "Auto-passing due to budget/value limits.")
                 self.engine.apply_action({"action_type": "PASS", "team_id": current_team_id})
                 continue
                 
            # 7. LLM Call
            self._log_test(test_mode, f"{current_team_id} Calling LLM...", "")
            decision = agent.make_decision(player, current_bid, scarcity)
            self._log_test(test_mode, f"LLM Decision {current_team_id}", str(decision))
            
            # 8. Apply Action & Fallback Retry
            self._apply_and_retry(current_team_id, decision.decision, decision.bid_amount, test_mode)
            
            # Optional: Slow down logging for observability
            if test_mode:
                time.sleep(0.5)

    def _apply_and_retry(self, team_id: str, decision: str, bid_amount: int, test_mode: bool):
        action_payload = {
            "action_type": decision,
            "team_id": team_id,
        }
        if bid_amount is not None:
             action_payload["bid_amount"] = bid_amount
             
        # Call Engine
        resp_json = self.engine.apply_action(action_payload)
        resp = json.loads(resp_json)
        
        # 9. Failure Handling Instructions
        if resp["status"] == "ERROR":
            self._log_test(test_mode, f"[ERROR] Engine rejected {team_id}", resp["error_msg"])
            # Fallback treat as PASS
            self.engine.apply_action({
                "action_type": "PASS",
                "team_id": team_id
            })
            
    def _log_test(self, test_mode: bool, prefix: str, data: Any):
        if test_mode:
            print(f"[{prefix}] {data}")
