import json
import random
from typing import Dict
from pydantic import BaseModel
from engine.state import Player, Team
from tools.valuation_filter import ValuationFilter


class AgentDecision(BaseModel):
    decision: str  # "BID" or "PASS"


class TeamAgent:
    def __init__(self, team: Team, personality: Dict[str, float]):
        self.team = team
        self.personality = personality

    def make_decision(self, player: Player, current_bid: int, scarcity_index: float) -> AgentDecision:
        from engine.auction_engine import get_next_bid

        next_bid = get_next_bid(current_bid)

        # Hard filters first
        if next_bid > self.team.remaining_budget:
            return AgentDecision(decision="PASS")
        if self.team.squad_size >= self.team.max_squad_size:
            return AgentDecision(decision="PASS")

        # Valuation filter
        filter_tool = ValuationFilter(self.team, player, self.personality, scarcity_index)
        if filter_tool.should_auto_pass(current_bid):
            return AgentDecision(decision="PASS")

        # Personality-weighted scoring
        score = 0.0

        # Aggression baseline
        score += self.personality["aggression"] * 0.4

        # Star bias
        if player.is_star:
            score += self.personality["star_bias"] * 0.3

        # Youth bias
        if player.is_youth:
            score += self.personality.get("youth_bias", 0.5) * 0.2

        # Scarcity pressure
        if scarcity_index < 0.4:
            score += (1.0 - scarcity_index) * 0.2

        # Role need
        role_count = self.team.roles_count.get(player.role, 0)
        if role_count == 0:
            score += 0.25
        elif role_count <= 2:
            score += 0.1

        # Budget pressure
        budget_ratio = self.team.remaining_budget / self.team.total_budget
        if budget_ratio < 0.3:
            score -= self.personality["risk_aversion"] * 0.3
        if budget_ratio < 0.15:
            score -= 0.3

        # Price pressure
        max_price = int(self.team.remaining_budget * self.personality["price_tolerance"])
        if next_bid > max_price * 0.8:
            score -= 0.2
        if next_bid > max_price:
            return AgentDecision(decision="PASS")

        # Jitter for run-to-run variation
        score += random.gauss(0, 0.08)

        if score >= 0.5:
            return AgentDecision(decision="BID")
        return AgentDecision(decision="PASS")