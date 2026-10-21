"""Core 8-puzzle logic: validation, solvability, and search algorithms.

A board is a list/tuple of 9 ints (0-8) read row by row, 0 = blank.
"""
from __future__ import annotations

import heapq
import random
import time
from collections import deque
from itertools import count

GOAL = (1, 2, 3, 4, 5, 6, 7, 8, 0)
GOAL_POS = {tile: divmod(i, 3) for i, tile in enumerate(GOAL)}

# blank moves: (row delta, col delta, name of the direction the BLANK moves)
_MOVES = ((-1, 0, "up"), (1, 0, "down"), (0, -1, "left"), (0, 1, "right"))

ALGORITHMS = ("astar", "bfs", "greedy")
MAX_NODES = 200_000  # 9!/2 = 181,440 reachable states, so this is a safety cap only


class PuzzleError(ValueError):
    """Raised for invalid input boards."""


def validate(state) -> tuple:
    if not isinstance(state, (list, tuple)) or len(state) != 9:
        raise PuzzleError("Board must contain exactly 9 tiles.")
    try:
        tiles = tuple(int(x) for x in state)
    except (TypeError, ValueError):
        raise PuzzleError("Every tile must be a number from 0 to 8.")
    if any(isinstance(x, bool) for x in state):
        raise PuzzleError("Every tile must be a number from 0 to 8.")
    if sorted(tiles) != list(range(9)):
        raise PuzzleError("Use each number 0-8 exactly once (0 is the blank).")
    return tiles


def inversions(state) -> int:
    tiles = [t for t in state if t != 0]
    return sum(1 for i in range(len(tiles)) for j in range(i + 1, len(tiles)) if tiles[i] > tiles[j])


def is_solvable(state) -> bool:
    # On a 3x3 board a state can reach the goal iff its inversion count is even.
    return inversions(state) % 2 == 0


def manhattan(state) -> int:
    total = 0
    for i, tile in enumerate(state):
        if tile:
            r, c = divmod(i, 3)
            gr, gc = GOAL_POS[tile]
            total += abs(r - gr) + abs(c - gc)
    return total


def misplaced(state) -> int:
    return sum(1 for i, t in enumerate(state) if t and t != GOAL[i])


def neighbors(state):
    idx = state.index(0)
    r, c = divmod(idx, 3)
    for dr, dc, name in _MOVES:
        nr, nc = r + dr, c + dc
        if 0 <= nr < 3 and 0 <= nc < 3:
            j = nr * 3 + nc
            s = list(state)
            s[idx], s[j] = s[j], s[idx]
            yield tuple(s), name, s[idx]  # new state, blank direction, tile that slid


def _rebuild(parents, end):
    states, moves = [end], []
    while parents[states[-1]] is not None:
        prev, move = parents[states[-1]]
        moves.append(move)
        states.append(prev)
    states.reverse()
    moves.reverse()
    return states, moves


def _bfs(start):
    parents = {start: None}
    q = deque([start])
    expanded = 0
    while q:
        s = q.popleft()
        expanded += 1
        if s == GOAL:
            return parents, expanded
        for n, name, tile in neighbors(s):
            if n not in parents:
                parents[n] = (s, {"blank": name, "tile": tile})
                q.append(n)
        if expanded > MAX_NODES:
            break
    return None, expanded


def _best_first(start, use_g: bool):
    """A* when use_g is True, greedy best-first otherwise (both use Manhattan)."""
    tie = count()
    parents = {start: None}
    g = {start: 0}
    heap = [(manhattan(start), next(tie), start)]
    closed = set()
    expanded = 0
    while heap:
        _, _, s = heapq.heappop(heap)
        if s in closed:
            continue
        closed.add(s)
        expanded += 1
        if s == GOAL:
            return parents, expanded
        for n, name, tile in neighbors(s):
            ng = g[s] + 1
            if n in closed or (n in g and ng >= g[n]):
                continue
            g[n] = ng
            parents[n] = (s, {"blank": name, "tile": tile})
            f = (ng if use_g else 0) + manhattan(n)
            heapq.heappush(heap, (f, next(tie), n))
        if expanded > MAX_NODES:
            break
    return None, expanded


def solve(state, algorithm: str = "astar") -> dict:
    start = validate(state)
    algorithm = (algorithm or "astar").lower()
    if algorithm not in ALGORITHMS:
        raise PuzzleError(f"Unknown algorithm '{algorithm}'. Choose one of: {', '.join(ALGORITHMS)}.")

    base = {"algorithm": algorithm, "start": list(start), "heuristic": manhattan(start)}
    if not is_solvable(start):
        return {**base, "solvable": False, "solution": None, "moves": [], "steps": 0,
                "nodes_expanded": 0, "time_ms": 0.0,
                "message": "This board is unsolvable (odd number of inversions)."}

    t0 = time.perf_counter()
    if algorithm == "bfs":
        parents, expanded = _bfs(start)
    else:
        parents, expanded = _best_first(start, use_g=(algorithm == "astar"))
    elapsed = (time.perf_counter() - t0) * 1000

    if parents is None:
        return {**base, "solvable": True, "solution": None, "moves": [], "steps": 0,
                "nodes_expanded": expanded, "time_ms": round(elapsed, 2),
                "message": "Search limit reached before finding a solution."}

    states, moves = _rebuild(parents, GOAL)
    return {
        **base,
        "solvable": True,
        "solution": [list(s) for s in states],
        "moves": moves,
        "steps": len(moves),
        "optimal": algorithm in ("astar", "bfs"),
        "nodes_expanded": expanded,
        "time_ms": round(elapsed, 2),
        "message": f"Solved in {len(moves)} moves.",
    }


def random_solvable(moves: int | None = None, rng: random.Random | None = None) -> list:
    """Shuffle by random legal moves from the goal, so the result is always solvable."""
    rng = rng or random.Random()
    if moves is None:
        state = list(range(9))
        while True:
            rng.shuffle(state)
            if is_solvable(state) and tuple(state) != GOAL:
                return state
    state, prev = GOAL, None
    for _ in range(moves):
        options = [n for n, _, _ in neighbors(state) if n != prev]
        prev, state = state, rng.choice(options)
    return list(state)
