import random

import pytest

from app import app
from solver import GOAL, PuzzleError, is_solvable, neighbors, random_solvable, solve, validate


def apply_moves(start, moves):
    s = list(start)
    delta = {"up": -3, "down": 3, "left": -1, "right": 1}
    for m in moves:
        b = s.index(0)
        j = b + delta[m["blank"]]
        assert s[j] == m["tile"]
        s[b], s[j] = s[j], s[b]
    return s


def test_validate_rejects_bad_boards():
    for bad in ([1, 2, 3], [1, 1, 2, 3, 4, 5, 6, 7, 8], [1, 2, 3, 4, 5, 6, 7, 8, 9], "123456780", None):
        with pytest.raises(PuzzleError):
            validate(bad)


def test_solvability():
    assert is_solvable(GOAL)
    assert not is_solvable([2, 1, 3, 4, 5, 6, 7, 8, 0])


def test_goal_is_zero_steps():
    for algo in ("astar", "bfs", "greedy"):
        r = solve(list(GOAL), algo)
        assert r["steps"] == 0 and r["solution"] == [list(GOAL)]


def test_unsolvable_reported():
    r = solve([1, 2, 3, 4, 5, 6, 8, 7, 0])
    assert r["solvable"] is False and r["solution"] is None


def test_hardest_board_is_31_moves():
    hardest = [8, 6, 7, 2, 5, 4, 3, 0, 1]  # known 31-move instance
    assert solve(hardest, "astar")["steps"] == 31
    assert solve(hardest, "bfs")["steps"] == 31


@pytest.mark.parametrize("seed", range(15))
def test_astar_matches_bfs_and_moves_are_valid(seed):
    start = random_solvable(rng=random.Random(seed))
    a, b, g = (solve(start, x) for x in ("astar", "bfs", "greedy"))
    assert a["steps"] == b["steps"]
    assert g["steps"] >= a["steps"]
    for r in (a, b, g):
        assert apply_moves(start, r["moves"]) == list(GOAL)
        for s1, s2 in zip(r["solution"], r["solution"][1:]):
            assert tuple(s2) in {n for n, _, _ in neighbors(tuple(s1))}


def test_random_solvable_with_moves():
    for _ in range(20):
        assert is_solvable(random_solvable(30))


@pytest.fixture
def client():
    app.config["TESTING"] = True
    return app.test_client()


def test_api_solve(client):
    r = client.post("/api/solve", json={"state": [1, 2, 3, 4, 5, 6, 7, 0, 8], "algorithm": "bfs"})
    assert r.status_code == 200 and r.json["steps"] == 1


def test_api_legacy_route(client):
    r = client.post("/solve", json={"state": [1, 2, 3, 4, 5, 6, 0, 7, 8]})
    assert r.status_code == 200 and r.json["steps"] == 2


def test_api_errors(client):
    assert client.post("/api/solve", json={}).status_code == 400
    assert client.post("/api/solve", json={"state": [1, 2]}).status_code == 400
    assert client.post("/api/solve", json={"state": list(GOAL), "algorithm": "dfs"}).status_code == 400


def test_pages(client):
    assert client.get("/").status_code == 200
    assert client.get("/app.js").status_code == 200
    assert client.get("/api/health").json["status"] == "ok"
    assert client.get("/api/random").status_code == 200
    assert client.post("/api/check", json={"state": [2, 1, 3, 4, 5, 6, 7, 8, 0]}).json["solvable"] is False
