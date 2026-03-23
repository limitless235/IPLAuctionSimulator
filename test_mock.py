import json
import random
from typing import List

from engine.state import AuctionState, Player, Team
from engine.auction_engine import AuctionEngine
from agents.team_agent import TeamAgent, AgentDecision
from agents.llm_client import BaseLLMClient
from agents.orchestrator import AuctionOrchestrator
from store.memory import MemoryStore


class MockClient(BaseLLMClient):
    """Mock LLM client for deterministic testing without network calls."""

    def generate_json(self, prompt: str) -> str:
        """Generate mock JSON response based on random decision."""
        if random.random() < 0.6:
            bid_amount = random.randint(20000000, 50000000)
            return json.dumps({"decision": "BID", "bid_amount": bid_amount})
        else:
            return json.dumps({"decision": "PASS", "bid_amount": None})


def build_mock_state() -> AuctionState:
    """Build a mock auction state with 60 players and 9 teams."""
    team_ids = ["MI", "CSK", "RCB", "KKR", "DC", "PBKS", "RR", "SRH", "GT"]
    teams = {}
    for team_id in team_ids:
        teams[team_id] = Team(
            id=team_id,
            name=team_id,
            remaining_budget=1000000000,
            squad={},
        )
    players = [Player(**p) for p in json.load(open("data/mock_players.json"))]
    return AuctionState(unsold_players=players, teams=teams)
def build_agents(state: AuctionState, client: MockClient) -> dict:
    agents = {}
    for team_id in state.teams.keys():
        agents[team_id] = TeamAgent(
            team=state.teams[team_id],
            personality = {
    "aggression": 0.7,
    "risk_aversion": 0.3,
    "star_bias": 0.8,
    "role_need": 0.5,
    "price_tolerance": 0.8,
    "youth_bias": 0.5
},
            client=client
        )
    return agents


if __name__ == "__main__":
    print("Running Mock Auction Engine Test...")

    state = build_mock_state()
    client = MockClient()
    memory = MemoryStore()
    agents = build_agents(state, client)
    orchestrator = AuctionOrchestrator(engine=AuctionEngine(state), team_agents=agents, memory=memory)
    print("Starting IPL Auction Simulator...")
    orchestrator.run_auction(test_mode=True)

    print("\n======== FINAL MOCK SQUADS =========")
    for team_id, team in state.teams.items():
        spent = 1000000000 - team.remaining_budget
        print(f"{team_id}: Spent {spent} on {len(team.squad)} players.")
