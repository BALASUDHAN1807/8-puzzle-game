# 8 Puzzle Solver

An interactive 8-puzzle game and solver. Play the puzzle yourself, or let **A\***, **BFS** or **Greedy best-first search** solve it and watch the solution animate step by step.

**Live demo:** https://8-puzzle-game-nu.vercel.app

## Features

- Playable sliding board — click tiles or use arrow keys
- Random shuffle that always produces a solvable board
- Custom board input with validation
- Solvability check using inversion parity (unsolvable boards are rejected instantly)
- Three search algorithms with live stats: moves, nodes expanded, time
- Solution playback: play/pause, step forward/back, scrub, adjustable speed, clickable move list
- "Compare all" table to see the trade-offs between algorithms on the same board
- Responsive layout for phones and desktop

## Algorithms

| Algorithm | Strategy | Optimal? | Notes |
|-----------|----------|----------|-------|
| **A\*** | `f = g + h`, h = Manhattan distance | Yes | Manhattan is admissible, so A\* finds the shortest path while expanding far fewer nodes than BFS |
| **BFS** | Explores level by level | Yes | Uninformed; may visit all 181,440 reachable states |
| **Greedy** | Orders by `h` only | No | Very fast, but solutions are often longer |

On the hardest 8-puzzle board (31 moves), A\* expands ~20k nodes vs. BFS's ~181k.

**Solvability:** a 3×3 board can reach the goal only if the number of inversions (pairs of tiles in the wrong relative order, ignoring the blank) is even.

## Tech stack

- **Backend:** Python, Flask (`solver.py` holds all search logic, `app.py` the API)
- **Frontend:** HTML, CSS, vanilla JavaScript (`templates/`, `public/`)
- **Deployment:** Vercel (zero-config Flask)

## API

| Method | Route | Body / Query | Returns |
|--------|-------|--------------|---------|
| `POST` | `/api/solve` | `{"state": [1,2,3,4,5,6,7,0,8], "algorithm": "astar" \| "bfs" \| "greedy"}` | solution states, moves, steps, nodes_expanded, time_ms |
| `POST` | `/api/check` | `{"state": [...]}` | `{"solvable": true/false}` |
| `GET`  | `/api/random` | `?moves=N` (optional) | a random solvable board |
| `GET`  | `/api/health` | — | status |

`POST /solve` is kept as an alias of `/api/solve` for backward compatibility.

## Run locally

```bash
pip install -r requirements.txt
python app.py
# open http://127.0.0.1:5000
```

## Tests

```bash
pip install pytest
python -m pytest -q
```

The suite checks validation, solvability, that A\* and BFS agree on optimal length, that every returned move is legal, the 31-move hardest case, and all API routes.

## Project structure

```
app.py              Flask routes
solver.py           Search algorithms, heuristics, solvability
templates/index.html
public/style.css    Served by Vercel's CDN (and by Flask locally)
public/app.js
tests/test_solver.py
```

## Author

Balasudhan R — B.Tech CSE, SRM Institute of Science and Technology
