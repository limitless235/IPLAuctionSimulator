import os
import json
import yaml

# Ensure we have our pydantic models and engines imported
from engine.state import AuctionState, Player, Team
from engine.auction_engine import AuctionEngine
from store.memory import MemoryStore
from agents.team_agent import TeamAgent
from agents.orchestrator import AuctionOrchestrator
from agents.llm_client import LocalLLMClient

def load_llm_config(path: str = "config/llm.yaml"):
    try:
        with open(path, "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Warning: Could not load {path}, using defaults. Error: {e}")
        return {
            "provider": "local",
            "endpoint": "http://localhost:11434/api/generate",
            "model": "mistral",
            "temperature": 0.2,
            "max_tokens": 120
        }

def main():
    llm_conf = load_llm_config()
    if llm_conf.get("provider") == "local":
        client = LocalLLMClient(
            endpoint=llm_conf.get("endpoint", "http://localhost:11434/api/generate"),
            model=llm_conf.get("model", "mistral"),
            temperature=llm_conf.get("temperature", 0.2),
            max_tokens=llm_conf.get("max_tokens", 120)
        )
    else:
        # Fallback to base or extensible clients here
        raise NotImplementedError("Only local provider is supported in this example.")

    # 1. Load Data
    memory = MemoryStore("data/team_profiles.json")
    
    with open("data/mock_players.json", "r") as f:
        mock_players_data = json.load(f)
        unsold_players = [Player(**p) for p in mock_players_data]

    # 2. Init State & Teams
    initial_state = AuctionState()
    initial_state.unsold_players = unsold_players
    
    team_agents = {}
    for t_id, t_prof in memory.team_profiles.items():
        team = Team(id=t_id, name=f"{t_id} Franchise")
        initial_state.teams[t_id] = team
        
        # We assign CSK as the human team for the demo if desired, 
        # otherwise we can just run a full bot simulation.
        # Here we setup Agents for all of them; Orchestrator will selectively use human agent if needed.
        team_agents[t_id] = TeamAgent(team=team, personality=t_prof, client=client)

    # 3. Create Engine & Orchestrator
    engine = AuctionEngine(initial_state)
    
    # Optional: assign "CSK" as the Human
    # human_team_id = "CSK" 
    human_team_id = None # Set to None for fully automatic headless simulation
    
    orchestrator = AuctionOrchestrator(
        engine=engine,
        team_agents=team_agents,
        human_team_id=human_team_id,
        memory=memory
    )

    # 4. Run Loop
    # test_mode = True enables verbose logging of heuristics and skipped turns
    orchestrator.run_auction(test_mode=True)
    
    # 5. Output Summary
    print("\n\n======== FINAL SQUADS ========")
    final_state = engine.get_state()
    for t_id, t in final_state.teams.items():
        print(f"{t_id}: Spent {t.total_budget - t.remaining_budget} on {t.squad_size} players.")
        print(f"       Roster: {json.dumps(t.squad, indent=2)}")

if __name__ == "__main__":
    main()
