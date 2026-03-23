import json
from typing import Dict, Any, Optional
from pydantic import BaseModel

from engine.state import Player, Team
from tools.valuation_filter import ValuationFilter
from agents.llm_client import BaseLLMClient

class AgentDecision(BaseModel):
    decision: str  # "BID" or "PASS"

class TeamAgent:
    def __init__(self, team: Team, personality: Dict[str, float], client: BaseLLMClient):
        self.team = team
        self.personality = personality
        self.client = client

    def generate_prompt(self, player: Player, current_bid: int, next_bid: int, scarcity_index: float) -> str:
        squad_summary = {"total_size": self.team.squad_size, "roles": self.team.roles_count}
        prompt = f"""You are the auction AI for {self.team.name}.
    Respond with ONLY a JSON object. No explanation. No reasoning.

    Player: {player.name} | Role: {player.role} | Star: {player.is_star} | Youth: {player.is_youth}
    Current bid: {current_bid} | Next bid if you BID: {next_bid}
    Your budget remaining: {self.team.remaining_budget}
    Your squad: {json.dumps(squad_summary)}
    Scarcity index for this role: {scarcity_index}
    Your personality: aggression={self.personality['aggression']} star_bias={self.personality['star_bias']} risk_aversion={self.personality['risk_aversion']}

    Output exactly one of these two JSON objects:
    {{"decision": "BID"}}
    {{"decision": "PASS"}}"""
        return prompt

    def make_decision(self, player: Player, current_bid: int, scarcity_index: float) -> AgentDecision:
        from engine.auction_engine import get_next_bid
        next_bid = get_next_bid(current_bid)

        filter_tool = ValuationFilter(self.team, player, self.personality, scarcity_index)
        if filter_tool.should_auto_pass(current_bid):
            return AgentDecision(decision="PASS")

        if next_bid > self.team.remaining_budget:
            return AgentDecision(decision="PASS")

        prompt = self.generate_prompt(player, current_bid, next_bid, scarcity_index)
        try:
            raw_content = self.client.generate_json(prompt)
            data = json.loads(raw_content)
            if data.get("decision") not in ("BID", "PASS"):
                return AgentDecision(decision="PASS")
            return AgentDecision(decision=data["decision"])
        except Exception as e:
            print(f"[{self.team.id}] Agent API Error/Formatting Error: {e}")
            return AgentDecision(decision="PASS")

