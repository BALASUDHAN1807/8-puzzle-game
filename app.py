from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from collections import deque

app = Flask(__name__)
CORS(app)

GOAL = [1, 2, 3, 4, 5, 6, 7, 8, 0]
GOAL_KEY = tuple(GOAL)

def get_neighbors(state):
    neighbors = []
    idx = state.index(0)
    x, y = divmod(idx, 3)

    moves = [(-1,0),(1,0),(0,-1),(0,1)]

    for dx, dy in moves:
        nx, ny = x + dx, y + dy
        if 0 <= nx < 3 and 0 <= ny < 3:
            new_idx = nx * 3 + ny
            new_state = state[:]
            new_state[idx], new_state[new_idx] = new_state[new_idx], new_state[idx]
            neighbors.append(new_state)

    return neighbors


def bfs(start):
    queue = deque([(start, [])])
    visited = set()
    visited.add(tuple(start))

    while queue:
        state, path = queue.popleft()

        if tuple(state) == GOAL_KEY:
            return path + [state]

        for neighbor in get_neighbors(state):
            key = tuple(neighbor)
            if key not in visited:
                visited.add(key)
                queue.append((neighbor, path + [state]))

    return None


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/solve', methods=['POST'])
def solve():
    try:
        data = request.json
        start = data['state']

        result = bfs(start)

        if result:
            return jsonify({"solution": result})
        else:
            return jsonify({"solution": "No solution"})

    except Exception as e:
        return jsonify({"error": str(e)})


if __name__ == "__main__":
    app.run(debug=True)
