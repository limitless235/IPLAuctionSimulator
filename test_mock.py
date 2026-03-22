import json
from engine.state import AuctionState, Player, Team
from engine.auction_engine import AuctionEngine
from store.memory import MemoryStore
from agents.team_agent import TeamAgent
from agents.orchestrator import AuctionOrchestrator

class MockMessage:
    def __init__(self, content):
        self.content = content

class MockChoice:
    def __init__(self, content):
        self.message = MockMessage(content)

class MockResponse:
    def __init__(self, content):
        self.choices = [MockChoice(content)]

class MockChatCompletions:
    def create(self, **kwargs):
        # Find current bid from prompt to bid legally higher
        prompt = kwargs.get("messages", [{}])[0].get("content", "")
        current_bid_line = [m for m in prompt.split('\n') if "Current bid:" in m]
        if current_bid_line:
            current_bid = int(current_bid_line[0].split(":")[1].strip())
            return MockResponse(json.dumps({"decision": "BID", "bid_amount": current_bid + 500000}))
        return MockResponse(json.dumps({"decision": "PASS", "bid_amount": None}))

class MockChat:
    def __init__(self):
        self.completions = MockChatCompletions()

class MockClient:
    def __init__(self, api_key=None):
        self.chat = MockChat()

def test_mock_auction():
    client = MockClient()
    memory = MemoryStore("data/team_profiles.json")
    
    with open("data/mock_players.json", "r") as f:
        mock_players_data = json.load(f)
        unsold_players = [Player(**p) for p in mock_players_data[:3]]

    initial_state = AuctionState()
    initial_state.unsold_players = unsold_players
    
    team_agents = {}
    for t_id, t_prof in memory.team_profiles.items():
        team = Team(id=t_id, name=f"{t_id} Franchise")
        initial_state.teams[t_id] = team
        team_agents[t_id] = TeamAgent(team=team, personality=t_prof, client=client)

    engine = AuctionEngine(initial_state)
    orchestrator = AuctionOrchestrator(
        engine=engine,
        team_agents=team_agents,
        human_team_id=None,
        memory=memory
    )

    print("Running Mock Auction Engine Test...")
    orchestrator.run_auction(test_mode=True)
    
    final_state = engine.get_state()
    print("\n\n======== FINAL MOCK SQUADS ========")
    for t_id, t in final_state.teams.items():
        print(f"{t_id}: Spent {t.total_budget - t.remaining_budget} on {t.squad_size} players.")

if __name__ == "__main__":
    test_mock_auction()
