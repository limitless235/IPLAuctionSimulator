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

    def make_decision(self, player: Player, current_bid: int,
                      scarcity_index: float, auction_progress: float = 0.5) -> AgentDecision:
        from engine.auction_engine import get_next_bid

        next_bid = get_next_bid(current_bid)

        # Hard filters
        if next_bid > self.team.remaining_budget:
            return AgentDecision(decision="PASS")
        if self.team.squad_size >= self.team.max_squad_size:
            return AgentDecision(decision="PASS")
        if player.nationality == "overseas" and self.team.overseas_slots_used >= 4:
            return AgentDecision(decision="PASS")

        # Valuation filter
        filter_tool = ValuationFilter(self.team, player, self.personality, scarcity_index)
        if filter_tool.should_auto_pass(current_bid):
            return AgentDecision(decision="PASS")

        # Base score
        score = 0.0

        # Early vs late aggression
        if auction_progress < 0.33:
            score += self.personality["early_aggression"] * 0.4
        else:
            score += self.personality["aggression"] * 0.4

        # Late value hunting — boost score in final third for cheap players
        if auction_progress > 0.66 and player.tier >= 3:
            score += self.personality["late_value_hunting"] * 0.2

        # Star and brand value
        if player.is_star:
            score += self.personality["star_bias"] * 0.25
        score += player.brand_value * self.personality["star_bias"] * 0.15

        # Tier scoring
        tier_score = {1: 0.3, 2: 0.2, 3: 0.1, 4: 0.0}
        score += tier_score.get(player.tier, 0.0)

        # Recent form
        score += (player.recent_form - 0.5) * 0.2

        # Youth and veteran bias
        if player.is_youth or player.age < 23:
            score += self.personality["youth_bias"] * 0.15
        if player.age > 30:
            score += self.personality["veteran_bias"] * 0.1

        # Bowling type bias
        if player.pace_bowler:
            score += self.personality["pace_bias"] * 0.15
        if player.spin_bowler:
            score += self.personality["spin_bias"] * 0.15

        # Allrounder bias
        if player.role == "all_rounder":
            score += self.personality["allrounder_bias"] * 0.15

        # Overseas bias
        if player.nationality == "overseas":
            score += self.personality["foreign_bias"] * 0.1
            score += self.personality["value_foreign_bias"] * 0.1

        # Scarcity sensitivity
        if scarcity_index < 0.4:
            score += self.personality["scarcity_sensitivity"] * (1.0 - scarcity_index) * 0.2

        # Role need
        role_count = self.team.roles_count.get(player.role, 0)
        if role_count == 0:
            score += self.personality["role_urgency_weight"] * 0.25
        elif role_count <= 2:
            score += self.personality["role_urgency_weight"] * 0.1

        # Budget pressure
        budget_ratio = self.team.remaining_budget / self.team.total_budget
        if budget_ratio < 0.3:
            score -= self.personality["risk_aversion"] * 0.3
        if budget_ratio < 0.15:
            score -= 0.3

        # Budget conservatism — hold back if early and conservative
        if auction_progress < 0.33:
            score -= self.personality["budget_conservatism"] * 0.15

        # Disruption tendency — occasionally bid even on low-score players
        # to run up rivals' costs, then pass next round
        # Only triggers when score is borderline (0.35-0.50) and disruption is high
        disruption_triggered = False
        if 0.35 <= score < 0.50:
            if random.random() < self.personality["disruption_tendency"] * 0.3:
                score += 0.2
                disruption_triggered = True

        # Jitter for run-to-run variation
        score += random.gauss(0, 0.08)

        if score >= 0.5:
            return AgentDecision(decision="BID")
        return AgentDecision(decision="PASS")
