from typing import Dict, List, Optional, Literal
from pydantic import BaseModel, Field

# ---------------------------------------------------------
# CORE DOMAIN MODELS
# ---------------------------------------------------------

class Player(BaseModel):
    id: str
    name: str
    role: Literal["batter", "bowler", "all_rounder", "wicket_keeper"]
    base_price: int
    is_star: bool = False
    is_youth: bool = False
    
class Team(BaseModel):
    id: str
    name: str
    total_budget: int = 1000000000  # Default 100 Cr
    remaining_budget: int = 1000000000
    squad_size: int = 0
    max_squad_size: int = 25
    min_squad_size: int = 18
    roles_count: Dict[str, int] = Field(
        default_factory=lambda: {
            "batter": 0,
            "bowler": 0,
            "all_rounder": 0,
            "wicket_keeper": 0
        }
    )
    # Roster mapping player_id -> purchase_price
    squad: Dict[str, int] = Field(default_factory=dict)

# ---------------------------------------------------------
# AUCTION STATE & ACTIONS
# ---------------------------------------------------------

class BidAction(BaseModel):
    action_type: Literal["START", "BID", "PASS", "NEXT"]
    team_id: str
    bid_amount: Optional[int] = None

class ActionResponse(BaseModel):
    status: Literal["OK", "ERROR"]
    error_msg: Optional[str] = None

class AuctionState(BaseModel):
    current_player: Optional[Player] = None
    current_bid: int = 0
    highest_bidder: Optional[str] = None
    
    # Track current active active bidders for the current player
    active_bidders: List[str] = Field(default_factory=list)
    bidding_rounds: int = 0
    
    # Master records of teams and sold players
    teams: Dict[str, Team] = Field(default_factory=dict)
    unsold_players: List[Player] = Field(default_factory=list)
    sold_players: List[Player] = Field(default_factory=list)
    truly_unsold_players: List[Player] = Field(default_factory=list)
    
    is_auction_complete: bool = False
