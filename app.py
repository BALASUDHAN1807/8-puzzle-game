from flask import Flask, jsonify, render_template, request
from flask_cors import CORS

from solver import ALGORITHMS, PuzzleError, is_solvable, random_solvable, solve, validate

# Static assets live in public/ so Vercel serves them from its CDN;
# locally Flask serves the same folder at the site root.
app = Flask(__name__, static_folder="public", static_url_path="")
CORS(app)


@app.get("/")
def home():
    return render_template("index.html")


@app.get("/api/health")
def health():
    return jsonify({"status": "ok", "algorithms": list(ALGORITHMS)})


@app.post("/api/solve")
@app.post("/solve")  # kept for backward compatibility with the original endpoint
def api_solve():
    data = request.get_json(silent=True) or {}
    if "state" not in data:
        return jsonify({"error": "Request body must be JSON with a 'state' array of 9 numbers."}), 400
    try:
        return jsonify(solve(data["state"], data.get("algorithm", "astar")))
    except PuzzleError as e:
        return jsonify({"error": str(e)}), 400


@app.post("/api/check")
def api_check():
    data = request.get_json(silent=True) or {}
    try:
        state = validate(data.get("state"))
    except PuzzleError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify({"state": list(state), "solvable": is_solvable(state)})


@app.get("/api/random")
def api_random():
    moves = request.args.get("moves", type=int)
    if moves is not None:
        moves = max(1, min(moves, 200))
    return jsonify({"state": random_solvable(moves)})


@app.errorhandler(404)
def not_found(_):
    if request.path.startswith("/api/"):
        return jsonify({"error": "Not found"}), 404
    return render_template("index.html"), 404


if __name__ == "__main__":
    app.run(debug=True)
