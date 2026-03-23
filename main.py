import json
import argparse
from engine.state import AuctionState, Player, Team
from engine.auction_engine import AuctionEngine
from store.memory import MemoryStore
from agents.team_agent import TeamAgent
from agents.orchestrator import AuctionOrchestrator


def main():
    parser = argparse.ArgumentParser(description="IPL Auction Simulator")
    parser.add_argument(
        "--team",
        type=str,
        default=None,
        help="Team ID to control manually e.g. --team CSK"
    )
    parser.add_argument(
        "--players",
        type=str,
        default="data/mock_players.json",
        help="Path to players JSON file"
    )
    args = parser.parse_args()

    valid_teams = ["MI", "CSK", "RCB", "KKR", "DC", "RR", "SRH", "PBKS", "GT", "LSG"]

    if args.team and args.team.upper() not in valid_teams:
        print(f"Invalid team ID. Choose from: {', '.join(valid_teams)}")
        return

    human_team_id = args.team.upper() if args.team else None

    # 1. Load data
    memory = MemoryStore("data/team_profiles.json")
    with open(args.players, "r") as f:
        unsold_players = [Player(**p) for p in json.load(f)]

    # 2. Build state and agents
    initial_state = AuctionState(unsold_players=unsold_players)
    team_agents = {}

    for t_id, t_prof in memory.team_profiles.items():
        team = Team(id=t_id, name=f"{t_id} Franchise")
        initial_state.teams[t_id] = team
        if t_id != human_team_id:
            team_agents[t_id] = TeamAgent(team=team, personality=t_prof)

    # 3. Build engine and orchestrator
    engine = AuctionEngine(initial_state)
    orchestrator = AuctionOrchestrator(
        engine=engine,
        team_agents=team_agents,
        human_team_id=human_team_id,
        memory=memory
    )

    # 4. Run
    orchestrator.run_auction(test_mode=True)

    # 5. Final summary
    player_lookup = {p.id: p.name for p in unsold_players}
    print("\n\n======== FINAL SQUADS ========")
    final_state = engine.get_state()
    for t_id, t in final_state.teams.items():
        spent = t.total_budget - t.remaining_budget
        marker = " [YOU]" if t_id == human_team_id else ""
        print(f"{t_id}{marker}: Spent {spent / 10000000:.1f} Cr on {t.squad_size} players.")
        named_roster = {
            player_lookup.get(pid, pid): f"{price / 10000000:.1f} Cr"
            for pid, price in t.squad.items()
        }
        print(f"       Roster: {json.dumps(named_roster, indent=2)}")


if __name__ == "__main__":
    main()
