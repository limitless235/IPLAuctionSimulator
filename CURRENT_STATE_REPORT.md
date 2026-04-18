# IPL Auction Simulator Current State Report

## Overview

This repository is an IPL auction simulation project with three main runtime layers:

- A Python auction engine and orchestration layer
- A FastAPI backend that exposes state and live events
- A React/Vite frontend that renders the auction UI

The branch `codex/current-state-audit` includes a focused stabilization pass on top of the existing project. The goal of this report is to document how the project currently works, what was verified, what was fixed in this pass, and what risks still remain.

## Architecture Map

### CLI Flow

- [`main.py`](/Users/limitless/Documents/IPLAuctionSimulator-audit/main.py) is the local entrypoint for a terminal-driven auction run.
- It loads team personalities from `data/team_profiles.json`.
- It loads players from `data/mock_players.json`.
- It creates an `AuctionState`, team records, AI agents, an `AuctionEngine`, and an `AuctionOrchestrator`.
- It runs the auction loop and prints a final squad summary.

### Simulation Core

- [`engine/state.py`](/Users/limitless/Documents/IPLAuctionSimulator-audit/engine/state.py) defines the core domain models:
  - `Player`
  - `Team`
  - `AuctionState`
  - `BidAction`
- [`engine/auction_engine.py`](/Users/limitless/Documents/IPLAuctionSimulator-audit/engine/auction_engine.py) handles:
  - auction ordering
  - bid increment rules
  - bid/pass validation
  - player sale or unsold resolution
  - team budget and squad updates

### Agent and Memory Layer

- [`agents/team_agent.py`](/Users/limitless/Documents/IPLAuctionSimulator-audit/agents/team_agent.py) decides whether an AI franchise should bid or pass.
- [`tools/valuation_filter.py`](/Users/limitless/Documents/IPLAuctionSimulator-audit/tools/valuation_filter.py) applies budget and valuation guardrails before a bid goes through.
- [`store/memory.py`](/Users/limitless/Documents/IPLAuctionSimulator-audit/store/memory.py) holds team profiles plus runtime scarcity and rivalry memory.
- [`agents/orchestrator.py`](/Users/limitless/Documents/IPLAuctionSimulator-audit/agents/orchestrator.py) drives the live auction loop and coordinates AI teams, human turns, and backend broadcasts.

### Backend and Frontend

- [`backend/main.py`](/Users/limitless/Documents/IPLAuctionSimulator-audit/backend/main.py) exposes:
  - REST routes for auction start, pause, resume, speed changes, and human actions
  - a WebSocket for live updates
  - snapshot endpoints for teams and players
- [`frontend/src/App.jsx`](/Users/limitless/Documents/IPLAuctionSimulator-audit/frontend/src/App.jsx) contains the main application UI:
  - setup screen
  - live bid panel
  - teams tab
  - queue tab
  - summary tab
  - feed updates from WebSocket messages

## Runtime Flow

### Backend-Led Auction Run

1. The frontend calls `POST /auction/start`.
2. The backend loads players and teams, creates the engine and orchestrator, and starts the auction in a background thread.
3. The orchestrator loops through active bidders for each player.
4. The backend publishes snapshots and live bid/sale events over WebSocket.
5. The frontend fetches `/state` initially and then applies live WebSocket updates.

### Human Turn Flow

1. When the human-controlled franchise is reached in the bidding loop, [`agents/human_agent.py`](/Users/limitless/Documents/IPLAuctionSimulator-audit/agents/human_agent.py) sets `human_action_pending`.
2. The backend broadcasts a state update.
3. The frontend shows `Bid` and `Pass` controls.
4. The frontend submits `POST /auction/human-action`.
5. The orchestrator resumes after the backend event is set.

## Verified Issues From Audit

The initial audit identified these concrete issues:

- Pause and resume changed backend status but did not actually pause the orchestrator loop.
- The frontend displayed the next bid amount using a percentage bump instead of the engine's actual increment rules.
- Team highlighting used mismatched identity shapes:
  - some paths used full team names
  - some used short IDs like `MI` or `CSK`
- The human custom-bid control was misleading because custom amounts were not honored end-to-end.
- `/state/teams`, `/state/players/remaining`, and `/state/players/sold` returned stub data instead of live auction data once an auction started.
- The setup screen claimed `228 players`, but the current dataset contains `221`.
- `test_mock.py` used only 9 teams and omitted `LSG`.

## Fixes Implemented In This Branch

### Backend Consistency

- Added shared serialization helpers in [`backend/main.py`](/Users/limitless/Documents/IPLAuctionSimulator-audit/backend/main.py).
- Updated `/state`, `/state/teams`, `/state/players/remaining`, and `/state/players/sold` to use real live state when an auction exists.
- Added `meta.player_pool_size` to the `/state` payload so the frontend can show the actual dataset size.

### Orchestrator Pause/Resume

- Added pause polling to [`agents/orchestrator.py`](/Users/limitless/Documents/IPLAuctionSimulator-audit/agents/orchestrator.py).
- The auction loop now waits while backend status is `paused`, which makes the existing pause/resume API meaningful during backend-driven runs.

### Frontend State Alignment

- Replaced the frontend's incorrect `10%` bid bump logic with a helper that mirrors the engine's bid increment rules in lakhs.
- Standardized team selection and highlight comparisons around team short IDs in the UI layer.
- Replaced the incorrect hardcoded player count with the backend-provided dataset count.
- Removed the misleading custom bid amount control from the live human-action panel and clarified that the simulator currently follows official increment rules only.

### Test Harness Alignment

- Updated [`test_mock.py`](/Users/limitless/Documents/IPLAuctionSimulator-audit/test_mock.py) to include all 10 teams, including `LSG`.

## Validation Performed

### Repository and Data Inspection

- Confirmed the project structure and major runtime entrypoints.
- Confirmed `data/mock_players.json` currently contains 221 players.
- Confirmed `data/team_profiles.json` contains 10 team profiles.

### Python Verification

- Verified major Python modules import successfully in the local environment.
- Performed a bounded mock-auction run earlier in the audit to confirm the simulation flow executes and produces auction output.

### Test Coverage Reality

- `python3 -m pytest -q` reported that no tests were discovered.
- The repository currently relies more on smoke testing and manual verification than on formal automated tests.

### Frontend/Build Validation

- The frontend has dependency and tooling wiring in place, but previous broad `npm run build` and `npm run lint` attempts in this environment did not complete within the time bounds used during the audit.
- Those commands should still be rerun after this branch is checked in to confirm there are no environment-specific hangs.

## Remaining Risks

- The project still has light automated coverage.
- The frontend is concentrated in a large single `App.jsx` file, which makes future changes harder to isolate and test.
- The backend keeps runtime state in globals, which is workable for local/demo usage but fragile for multi-session or production-style deployment.
- The live feed remains partly event-driven and partly snapshot-driven, so reconnect behavior could still use a more deliberate design.
- The human-action API still accepts an optional `amount`, but the current UI now intentionally uses standard increments only.

## Recommended Next Steps

- Add targeted tests for:
  - bid increment rules
  - pause/resume orchestration behavior
  - `/state` versus `/state/*` consistency
  - human-action flow
- Move frontend state helpers into smaller modules or components once correctness work is stable.
- Consider decoupling the simulation core from `backend.main` globals to make CLI and backend runs cleaner and easier to test.
