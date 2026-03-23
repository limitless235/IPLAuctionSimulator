from typing import Dict
from engine.state import Player, Team

class ValuationFilter:
    def __init__(self, team: Team, player: Player, personality: Dict[str, float], scarcity_index: float):
        self.team = team
        self.player = player
        self.personality = personality
        self.scarcity_index = scarcity_index

    def calculate_max_price(self) -> int:
    # Market base: star players start at 10 Cr, others at 3 Cr
        if self.player.is_star:
            base_val = 100000000  # 10 Cr
        elif self.player.is_youth:
            base_val = 40000000   # 4 Cr
        else:
            base_val = 30000000   # 3 Cr

        # Star bias adjustment
        if self.player.is_star:
            base_val += int(self.personality["star_bias"] * 100000000)  # up to 10 Cr more

        # Youth bias adjustment
        if self.player.is_youth:
            base_val += int(self.personality["youth_bias"] * 30000000)  # up to 3 Cr more

        # Scarcity adjustment
        if self.scarcity_index < 0.3:
            base_val = int(base_val * 1.2)

        # Squad need adjustment
        squad_need_score = self._get_squad_need_score()
        if squad_need_score > 0.8:
            base_val = int(base_val * 1.5)

        # Aggression and price tolerance cap
        max_price = int(base_val * (1 + (self.personality["aggression"] * 0.5)))
        max_price = min(max_price, int(self.team.remaining_budget * self.personality["price_tolerance"]))
        return max_price
        
    def _get_squad_need_score(self) -> float:
        """Returns 0.0 to 1.0 indicating how badly the squad needs this player's role."""
        role_count = self.team.roles_count.get(self.player.role, 0)
        
        # Simple heuristic: if we have 0, we need them 1.0. If we have > 5 of a role, we need them 0.0
        if role_count == 0:
            return 1.0
        if role_count >= 5:
            return 0.0
            
        return max(0.0, 1.0 - (role_count / 5.0))

    def get_budget_pressure(self) -> float:
        return self.team.remaining_budget / float(self.team.total_budget)

    def should_auto_pass(self, current_bid: int) -> bool:
        """Calculates logic and returns True if the Orchestrator should skip calling the LLM."""
        
        # Budget pressure scaling rule
        pressure = self.get_budget_pressure()
        risk_aversion = self.personality["risk_aversion"]
        
        if pressure < 0.4:
            risk_aversion = min(1.0, risk_aversion * 1.3)
            
        if pressure < 0.2:
            # Only bid for critical squad needs if below 20% budget
            if self._get_squad_need_score() < 0.8:
                return True
                
        # If the bid is already higher than what we calculate is the max tolerable price
        max_price = self.calculate_max_price()
        if current_bid > max_price:
            return True
            
        # If we have no budget left to legally beat the current bid
        if current_bid >= self.team.remaining_budget:
             return True
             
        # If squad is full
        if self.team.squad_size >= self.team.max_squad_size:
             return True

        return False
