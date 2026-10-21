(() => {
  "use strict";

  const GOAL = [1, 2, 3, 4, 5, 6, 7, 8, 0];
  const $ = (id) => document.getElementById(id);
  const boardEl = $("board");

  let state = GOAL.slice();
  let startState = GOAL.slice();
  let userMoves = 0;
  let solution = null;  // array of states from the solver
  let moves = [];       // move descriptions from the solver
  let step = 0;
  let timer = null;
  const tiles = {};

  // ---------- helpers ----------
  const inversions = (s) => {
    const t = s.filter((x) => x);
    let n = 0;
    for (let i = 0; i < t.length; i++) for (let j = i + 1; j < t.length; j++) if (t[i] > t[j]) n++;
    return n;
  };
  const isSolvable = (s) => inversions(s) % 2 === 0;
  const isGoal = (s) => s.every((v, i) => v === GOAL[i]);
  const manhattan = (s) =>
    s.reduce((sum, t, i) => {
      if (!t) return sum;
      const g = t - 1;
      return sum + Math.abs(Math.floor(i / 3) - Math.floor(g / 3)) + Math.abs((i % 3) - (g % 3));
    }, 0);

  function setStatus(text, cls = "") {
    const el = $("status");
    el.textContent = text;
    el.className = "status " + cls;
  }

  // ---------- board rendering ----------
  function buildTiles() {
    for (let n = 1; n <= 8; n++) {
      const el = document.createElement("div");
      el.className = "tile";
      el.textContent = n;
      el.setAttribute("role", "button");
      el.setAttribute("aria-label", "Tile " + n);
      el.addEventListener("click", () => tryMoveTile(n));
      boardEl.appendChild(el);
      tiles[n] = el;
    }
  }

  function render() {
    const gapPx = parseFloat(getComputedStyle(boardEl).paddingLeft);
    const cell = (boardEl.clientWidth - 4 * gapPx) / 3;
    const blank = state.indexOf(0);
    const locked = solution !== null && timer !== null;
    state.forEach((t, i) => {
      if (!t) return;
      const r = Math.floor(i / 3), c = i % 3;
      const el = tiles[t];
      el.style.transform = `translate(${c * (cell + gapPx)}px, ${r * (cell + gapPx)}px)`;
      el.classList.toggle("home", GOAL[i] === t);
      const adj = Math.abs(Math.floor(blank / 3) - r) + Math.abs((blank % 3) - c) === 1;
      el.classList.toggle("movable", adj && !locked);
      el.classList.toggle("locked", locked);
    });
    const solved = isGoal(state);
    boardEl.classList.toggle("solved", solved);
    $("moveCount").textContent = userMoves;
    $("h").textContent = manhattan(state);
    const ok = isSolvable(state);
    $("solvable").textContent = ok ? "yes" : "no";
    $("solvable").className = ok ? "ok" : "no";
  }

  // ---------- manual play ----------
  function tryMoveTile(n) {
    if (timer) return;
    const i = state.indexOf(n), b = state.indexOf(0);
    const adj = Math.abs(Math.floor(i / 3) - Math.floor(b / 3)) + Math.abs((i % 3) - (b % 3)) === 1;
    if (!adj) return;
    [state[i], state[b]] = [state[b], state[i]];
    userMoves++;
    clearSolution();
    render();
    if (isGoal(state)) setStatus(`Solved in ${userMoves} moves! 🎉`, "win");
    else setStatus("Keep going…");
  }

  // Arrow key = direction the tile slides (so ← moves the tile right of the blank into it).
  document.addEventListener("keydown", (e) => {
    if (e.target.tagName === "INPUT") return;
    const b = state.indexOf(0), r = Math.floor(b / 3), c = b % 3;
    const map = { ArrowLeft: [r, c + 1], ArrowRight: [r, c - 1], ArrowUp: [r + 1, c], ArrowDown: [r - 1, c] };
    const t = map[e.key];
    if (!t) return;
    e.preventDefault();
    const [tr, tc] = t;
    if (tr >= 0 && tr < 3 && tc >= 0 && tc < 3) tryMoveTile(state[tr * 3 + tc]);
  });

  function loadBoard(s, msg) {
    stop();
    state = s.slice();
    startState = s.slice();
    userMoves = 0;
    clearSolution();
    render();
    if (!isSolvable(s)) setStatus("This board can't be solved (odd inversions).", "err");
    else setStatus(msg || "Your turn — or hit Solve.");
  }

  function shuffle() {
    let s;
    do {
      s = GOAL.slice();
      for (let i = s.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [s[i], s[j]] = [s[j], s[i]];
      }
    } while (!isSolvable(s) || isGoal(s));
    loadBoard(s, "Shuffled. Your turn — or hit Solve.");
  }

  // ---------- solving ----------
  const algo = () => document.querySelector('input[name="algo"]:checked').value;
  const NAMES = { astar: "A*", bfs: "BFS", greedy: "Greedy" };

  async function callSolve(s, algorithm) {
    const res = await fetch("/api/solve", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ state: s, algorithm }),
    });
    const data = await res.json();
    if (!res.ok || data.error) throw new Error(data.error || "Server error");
    return data;
  }

  function busy(on) {
    ["solveBtn", "compareBtn", "shuffleBtn", "resetBtn"].forEach((id) => ($(id).disabled = on));
  }

  async function solve() {
    if (isGoal(state)) return setStatus("Already solved — shuffle first.", "win");
    if (!isSolvable(state)) return setStatus("This board can't be solved (odd inversions).", "err");
    busy(true);
    setStatus(`Searching with ${NAMES[algo()]}…`);
    try {
      const data = await callSolve(state, algo());
      if (!data.solution) return setStatus(data.message, "err");
      solution = data.solution;
      moves = data.moves;
      step = 0;
      $("rSteps").textContent = data.steps;
      $("rNodes").textContent = data.nodes_expanded.toLocaleString();
      $("rTime").textContent = data.time_ms;
      $("scrub").max = solution.length - 1;
      $("moveList").innerHTML = moves
        .map((m, i) => `<li data-i="${i + 1}">${i + 1}. ${m.tile} ${arrow(m.blank)}</li>`)
        .join("");
      $("result").classList.remove("hidden");
      setStatus(`${NAMES[data.algorithm]} found ${data.steps} moves${data.optimal ? " (optimal)" : ""}.`);
      updateStep();
      play();
    } catch (e) {
      setStatus(e.message, "err");
    } finally {
      busy(false);
    }
  }

  // Tile moves opposite to the blank.
  const arrow = (blank) => ({ up: "↓", down: "↑", left: "→", right: "←" })[blank];

  async function compare() {
    if (!isSolvable(state)) return setStatus("This board can't be solved (odd inversions).", "err");
    busy(true);
    setStatus("Running all three algorithms…");
    try {
      const results = [];
      for (const a of ["astar", "bfs", "greedy"]) results.push(await callSolve(state, a));
      const minSteps = Math.min(...results.map((r) => r.steps));
      const minNodes = Math.min(...results.map((r) => r.nodes_expanded));
      $("compareBody").innerHTML = results
        .map(
          (r) => `<tr><td>${NAMES[r.algorithm]}</td>
            <td class="${r.steps === minSteps ? "best" : ""}">${r.steps}</td>
            <td class="${r.nodes_expanded === minNodes ? "best" : ""}">${r.nodes_expanded.toLocaleString()}</td>
            <td>${r.time_ms} ms</td></tr>`
        )
        .join("");
      $("compare").classList.remove("hidden");
      setStatus("Comparison ready. Green = best.");
    } catch (e) {
      setStatus(e.message, "err");
    } finally {
      busy(false);
    }
  }

  function clearSolution() {
    solution = null;
    moves = [];
    step = 0;
    $("result").classList.add("hidden");
    $("compare").classList.add("hidden");
  }

  function updateStep() {
    state = solution[step].slice();
    $("scrub").value = step;
    $("stepLabel").textContent = `${step} / ${solution.length - 1}`;
    document.querySelectorAll("#moveList li").forEach((li) => {
      const i = +li.dataset.i;
      li.classList.toggle("done", i <= step);
      li.classList.toggle("current", i === step);
    });
    const cur = document.querySelector("#moveList li.current");
    if (cur) cur.scrollIntoView({ block: "nearest" });
    render();
    if (step === solution.length - 1) setStatus("Solved! 🎉", "win");
  }

  function goTo(i) {
    if (!solution) return;
    step = Math.max(0, Math.min(solution.length - 1, i));
    updateStep();
  }

  function play() {
    if (!solution) return;
    if (timer) return stop();
    if (step >= solution.length - 1) step = 0;
    $("playBtn").textContent = "❚❚ Pause";
    timer = setInterval(() => {
      if (step >= solution.length - 1) return stop();
      goTo(step + 1);
    }, +$("speed").value);
    render();
  }

  function stop() {
    if (timer) clearInterval(timer);
    timer = null;
    $("playBtn").textContent = "▶ Play";
    render();
  }

  // ---------- custom board ----------
  function parseBoard(text) {
    const nums = (text.match(/\d/g) || []).map(Number);
    if (nums.length !== 9) throw new Error("Enter exactly 9 digits.");
    if ([...nums].sort().join("") !== "012345678") throw new Error("Use each digit 0–8 exactly once.");
    return nums;
  }

  // ---------- wiring ----------
  $("shuffleBtn").onclick = shuffle;
  $("resetBtn").onclick = () => loadBoard(startState, "Back to the starting board.");
  $("editBtn").onclick = () => {
    $("editForm").classList.toggle("hidden");
    $("editInput").value = state.join(" ");
    $("editInput").focus();
  };
  $("editForm").onsubmit = (e) => {
    e.preventDefault();
    try {
      const s = parseBoard($("editInput").value);
      $("editErr").textContent = "";
      $("editForm").classList.add("hidden");
      loadBoard(s, "Custom board loaded.");
    } catch (err) {
      $("editErr").textContent = err.message;
    }
  };
  $("solveBtn").onclick = solve;
  $("compareBtn").onclick = compare;
  $("playBtn").onclick = play;
  $("firstBtn").onclick = () => { stop(); goTo(0); };
  $("lastBtn").onclick = () => { stop(); goTo(Infinity); };
  $("prevBtn").onclick = () => { stop(); goTo(step - 1); };
  $("nextBtn").onclick = () => { stop(); goTo(step + 1); };
  $("scrub").oninput = (e) => { stop(); goTo(+e.target.value); };
  $("speed").oninput = () => { if (timer) { stop(); play(); } };
  $("moveList").onclick = (e) => { const li = e.target.closest("li"); if (li) { stop(); goTo(+li.dataset.i); } };
  window.addEventListener("resize", render);

  buildTiles();
  shuffle();
})();
