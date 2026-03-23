"""
IPL Auction Simulator — FastAPI Backend
Drop this file into your IPLAuctionSimulator/ root.
Run with: uvicorn backend.main:app --reload --port 8000
"""

import asyncio
import json
import threading
from typing import Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="IPL Auction Simulator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── In-memory auction state (replace with your real AuctionState) ────────────
auction_state = {
    "status": "idle",          # idle | running | paused | finished
    "current_player": None,
    "current_bid": 0,
    "current_bid_team": None,
    "timer_seconds": 15,
    "human_team": None,
    "human_action_pending": False,
}

connected_clients: list[WebSocket] = []
human_action_event = asyncio.Event()
human_action_value: Optional[dict] = None


# ── WebSocket broadcast helper ────────────────────────────────────────────────
async def broadcast(payload: dict):
    dead = []
    for ws in connected_clients:
        try:
            await ws.send_json(payload)
        except Exception:
            dead.append(ws)
    for ws in dead:
        connected_clients.remove(ws)


# ── WebSocket endpoint ────────────────────────────────────────────────────────
@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    connected_clients.append(ws)
    # Send current state immediately on connect
    await ws.send_json({"type": "state_snapshot", "data": await get_full_state()})
    try:
        while True:
            await ws.receive_text()   # keep-alive; client doesn't send over WS
    except WebSocketDisconnect:
        connected_clients.remove(ws)


# ── REST: auction lifecycle ───────────────────────────────────────────────────
class StartRequest(BaseModel):
    human_team: Optional[str] = None


@app.post("/auction/start")
async def start_auction(req: StartRequest):
    """
    Wire this to your Orchestrator.run() in a background thread.
    Replace the stub below with:
        from agents.orchestrator import Orchestrator
        ...
    """
    if auction_state["status"] == "running":
        raise HTTPException(400, "Auction already running")

    auction_state["status"] = "running"
    auction_state["human_team"] = req.human_team

    # TODO: replace stub with real engine call
    # threading.Thread(target=run_real_auction, args=(req.human_team,), daemon=True).start()
    _start_stub_auction()

    await broadcast({"type": "auction_started", "human_team": req.human_team})
    return {"ok": True}


@app.post("/auction/pause")
async def pause_auction():
    auction_state["status"] = "paused"
    await broadcast({"type": "auction_paused"})
    return {"ok": True}


@app.post("/auction/resume")
async def resume_auction():
    auction_state["status"] = "running"
    await broadcast({"type": "auction_resumed"})
    return {"ok": True}


# ── REST: human player action ─────────────────────────────────────────────────
class HumanActionRequest(BaseModel):
    action: str          # "bid" | "pass"
    amount: Optional[int] = None


@app.post("/auction/human-action")
async def human_action(req: HumanActionRequest):
    """
    Called by the frontend when the human player clicks BID or PASS.
    The orchestrator should await human_action_event instead of blocking stdin.
    """
    global human_action_value
    if not auction_state["human_action_pending"]:
        raise HTTPException(400, "No human action currently required")

    human_action_value = {"action": req.action, "amount": req.amount}
    auction_state["human_action_pending"] = False
    human_action_event.set()
    human_action_event.clear()

    await broadcast({"type": "human_action_received", "action": req.action, "amount": req.amount})
    return {"ok": True}


# ── REST: state queries ───────────────────────────────────────────────────────
@app.get("/state")
async def get_full_state():
    """
    Returns the complete serialisable auction state.
    Replace stub data with your real AuctionState fields.
    """
    # TODO: replace with real state pulled from your AuctionState / engine
    return {
        "auction": auction_state,
        "teams": _stub_teams(),
        "players_sold": _stub_sold_players(),
        "players_remaining": _stub_remaining_players(),
        "feed": _stub_feed(),
    }


@app.get("/state/teams")
async def get_teams():
    return _stub_teams()


@app.get("/state/players/remaining")
async def get_remaining_players():
    return _stub_remaining_players()


@app.get("/state/players/sold")
async def get_sold_players():
    return _stub_sold_players()


@app.get("/state/summary")
async def get_summary():
    """End-of-auction summary report."""
    if auction_state["status"] not in ("finished", "running"):
        raise HTTPException(400, "Auction not started")
    teams = _stub_teams()
    summary = []
    for t in teams:
        summary.append({
            "team": t["name"],
            "budget_spent": t["budget_total"] - t["budget_remaining"],
            "budget_remaining": t["budget_remaining"],
            "players_bought": t["players"],
            "role_breakdown": _role_breakdown(t["players"]),
        })
    return summary


# ── Stub data (replace with real engine reads) ────────────────────────────────
def _stub_teams():
    return [
        {"name": "Mumbai Indians", "short": "MI", "color": "#004BA0", "budget_total": 1200, "budget_remaining": 780,
         "players": [{"name": "Rohit Sharma", "role": "BAT", "price": 160}, {"name": "Jasprit Bumrah", "role": "BOWL", "price": 140}, {"name": "Hardik Pandya", "role": "ALL", "price": 120}]},
        {"name": "Chennai Super Kings", "short": "CSK", "color": "#F9CD05", "budget_total": 1200, "budget_remaining": 620,
         "players": [{"name": "MS Dhoni", "role": "WK", "price": 160}, {"name": "Ravindra Jadeja", "role": "ALL", "price": 140}]},
        {"name": "Royal Challengers Bangalore", "short": "RCB", "color": "#EC1C24", "budget_total": 1200, "budget_remaining": 900,
         "players": [{"name": "Virat Kohli", "role": "BAT", "price": 150}, {"name": "Glenn Maxwell", "role": "ALL", "price": 110}]},
        {"name": "Kolkata Knight Riders", "short": "KKR", "color": "#3A225D", "budget_total": 1200, "budget_remaining": 840,
         "players": [{"name": "Andre Russell", "role": "ALL", "price": 120}, {"name": "Sunil Narine", "role": "ALL", "price": 90}]},
        {"name": "Delhi Capitals", "short": "DC", "color": "#282968", "budget_total": 1200, "budget_remaining": 950,
         "players": [{"name": "Rishabh Pant", "role": "WK", "price": 160}]},
        {"name": "Rajasthan Royals", "short": "RR", "color": "#EA1A85", "budget_total": 1200, "budget_remaining": 860,
         "players": [{"name": "Sanju Samson", "role": "WK", "price": 140}, {"name": "Jos Buttler", "role": "BAT", "price": 130}]},
        {"name": "Sunrisers Hyderabad", "short": "SRH", "color": "#F7A721", "budget_total": 1200, "budget_remaining": 880,
         "players": [{"name": "Pat Cummins", "role": "BOWL", "price": 150}]},
        {"name": "Punjab Kings", "short": "PBKS", "color": "#DCDDDF", "budget_total": 1200, "budget_remaining": 920,
         "players": [{"name": "Shikhar Dhawan", "role": "BAT", "price": 80}]},
        {"name": "Gujarat Titans", "short": "GT", "color": "#1C1C3C", "budget_total": 1200, "budget_remaining": 810,
         "players": [{"name": "Shubman Gill", "role": "BAT", "price": 140}, {"name": "Mohammed Shami", "role": "BOWL", "price": 100}]},
        {"name": "Lucknow Super Giants", "short": "LSG", "color": "#A72056", "budget_total": 1200, "budget_remaining": 870,
         "players": [{"name": "KL Rahul", "role": "BAT", "price": 170}]},
    ]


def _stub_remaining_players():
    return [
        {"name": "Mitchell Starc", "role": "BOWL", "base_price": 200, "country": "AUS", "specialist_tags": ["pace", "death-bowling"]},
        {"name": "Sam Curran", "role": "ALL", "base_price": 185, "country": "ENG", "specialist_tags": ["swing", "batting-all-rounder"]},
        {"name": "Cameron Green", "role": "ALL", "base_price": 175, "country": "AUS", "specialist_tags": ["pace", "hard-hitting"]},
        {"name": "David Warner", "role": "BAT", "base_price": 200, "country": "AUS", "specialist_tags": ["opener"]},
        {"name": "Kagiso Rabada", "role": "BOWL", "base_price": 150, "country": "SA", "specialist_tags": ["pace", "powerplay"]},
        {"name": "Rashid Khan", "role": "BOWL", "base_price": 200, "country": "AFG", "specialist_tags": ["leg-spin", "economy"]},
    ]


def _stub_sold_players():
    return [
        {"name": "Rohit Sharma", "role": "BAT", "sold_to": "Mumbai Indians", "sold_price": 160, "base_price": 120},
        {"name": "MS Dhoni", "role": "WK", "sold_to": "Chennai Super Kings", "sold_price": 160, "base_price": 120},
        {"name": "Virat Kohli", "role": "BAT", "sold_to": "RCB", "sold_price": 150, "base_price": 150},
    ]


def _stub_feed():
    return [
        {"time": "10:42", "text": "Rohit Sharma SOLD to Mumbai Indians for ₹16 Cr", "type": "sold"},
        {"time": "10:38", "text": "MS Dhoni SOLD to CSK for ₹16 Cr", "type": "sold"},
        {"time": "10:34", "text": "Virat Kohli SOLD to RCB for ₹15 Cr", "type": "sold"},
    ]


def _role_breakdown(players):
    breakdown = {"BAT": 0, "BOWL": 0, "ALL": 0, "WK": 0}
    for p in players:
        r = p.get("role", "BAT")
        breakdown[r] = breakdown.get(r, 0) + 1
    return breakdown


def _start_stub_auction():
    """Placeholder — replace with real orchestrator threading."""
    pass