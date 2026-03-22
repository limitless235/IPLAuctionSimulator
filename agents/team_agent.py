import json
from typing import Dict, Any, Optional
from pydantic import BaseModel

from engine.state import Player, Team
from tools.valuation_filter import ValuationFilter
from agents.llm_client import BaseLLMClient

class AgentDecision(BaseModel):
    decision: str  # "BID" or "PASS"
    bid_amount: Optional[int] = None

class TeamAgent:
    def __init__(self, team: Team, personality: Dict[str, float], client: BaseLLMClient):
        self.team = team
        self.personality = personality
        self.client = client

    def generate_prompt(self, player: Player, current_bid: int, scarcity_index: float) -> str:
        squad_summary = {
            "total_size": self.team.squad_size,
            "roles": self.team.roles_count
        }

        prompt = f"""You are the auction decision engine for {self.team.name}.

You must:
- Act according to your personality traits.
- Never exceed your remaining budget.
- Never violate squad constraints.
- Only output structured JSON.

Your personality parameters:
{json.dumps(self.personality, indent=2)}

You are given:
- Current player: {player.name} (Role: {player.role}, Base Price: {player.base_price}, Star: {player.is_star}, Youth: {player.is_youth})
- Current bid: {current_bid}
- Your squad composition: {json.dumps(squad_summary)}
- Your remaining budget: {self.team.remaining_budget}
- Role scarcity index: {scarcity_index} (Lower means fewer players of this role are left)

Decision Rules:
1. If current_bid exceeds your maximum valuation -> PASS.
2. If squad need for this role is low -> PASS.
3. If player matches star_bias and aggression is high -> consider BID.
4. Near low budget -> increase risk_aversion.
5. If scarcity_index < 0.3 -> Increase valuation by 20%.
6. If squad has fewer than minimum required players for a role -> Increase priority weight by 50%.
7. If squad is near max size -> Decrease aggression by 50%.

Output must be valid JSON matching this schema exactly:
{{
  "decision": "BID" | "PASS",
  "bid_amount": number | null
}}

No markdown. No commentary. No reasoning text. No trailing commas.
If unsure, output:
{{"decision": "PASS", "bid_amount": null}}
"""
        return prompt

    def make_decision(self, player: Player, current_bid: int, scarcity_index: float) -> AgentDecision:
        # 1. Performance Control: Heuristic Pre-Filter
        filter_tool = ValuationFilter(self.team, player, self.personality, scarcity_index)
        if filter_tool.should_auto_pass(current_bid):
            return AgentDecision(decision="PASS", bid_amount=None)

        # 2. LLM decision
        prompt = self.generate_prompt(player, current_bid, scarcity_index)

        try:
            raw_content = self.client.generate_json(prompt)
            data = json.loads(raw_content)
            
            # Additional safety: fallback to pass if valid JSON but missing keys
            if "decision" not in data:
                return AgentDecision(decision="PASS", bid_amount=None)
                
            return AgentDecision(**data)
        except Exception as e:
            # Fallback to PASS on any API, timeout, or formatting error
            print(f"[{self.team.id}] Agent API Error/Formatting Error: {e}")
            return AgentDecision(decision="PASS", bid_amount=None)
