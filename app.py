#!/usr/bin/env python3
"""Meshtastic Local UI (repo-ready)

- Polls `meshtastic --host <RADIO_HOST> --nodes`
- Parses node table (including Lat/Lon + LastHeard + Since)
- Caches latest known nodes to disk, so the map can render even if radio/CLI is temporarily down
- Serves:
  - /        dashboard
  - /map     local-only Leaflet map (no external tiles required; markers still show)
  - /api/nodes  JSON for UI
"""

from __future__ import annotations

import os
import json
import time
import subprocess
import threading
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from flask import Flask, jsonify, render_template, send_from_directory

APP_NAME = "Meshtastic Local UI"
VERSION = "0.2.0"

# ---- Config (env overrides) ----
RADIO_HOST = os.environ.get("RADIO_HOST", "192.168.1.192")
REFRESH_SECONDS = int(os.environ.get("REFRESH_SECONDS", "200"))
LISTEN_HOST = os.environ.get("LISTEN_HOST", "0.0.0.0")
LISTEN_PORT = int(os.environ.get("LISTEN_PORT", "5001"))

# Prefer explicit CLI path (works with systemd user services)
MESHTASTIC_BIN = os.environ.get("MESHTASTIC_BIN", "/home/meshy/meshtastic-venv/bin/meshtastic")

DATA_DIR = os.environ.get("DATA_DIR", os.path.join(os.path.dirname(__file__), "data"))
CACHE_FILE = os.path.join(DATA_DIR, "nodes_cache.json")
HISTORY_FILE = os.path.join(DATA_DIR, "nodes_history.jsonl")  # optional time-series log

ACTIVE_MAX_MIN = int(os.environ.get("ACTIVE_MAX_MIN", "10"))
STALE_MAX_MIN = int(os.environ.get("STALE_MAX_MIN", "60"))

os.makedirs(DATA_DIR, exist_ok=True)

app = Flask(__name__, static_folder="static", template_folder="templates")

def _clean_cell(s: str) -> str:
    return (s or "").strip().replace("\u00a0", " ")

def _parse_float_deg(s: str) -> Optional[float]:
    s = _clean_cell(s)
    if not s or s.upper() == "N/A":
        return None
    s = s.replace("°", "").strip()
    try:
        return float(s)
    except ValueError:
        return None

_SINCE_RE = re.compile(r"(?P<num>\d+)\s*(?P<unit>sec|secs|second|seconds|min|mins|minute|minutes|hour|hours|day|days)\s*ago", re.I)

def since_to_minutes(since: str) -> Optional[float]:
    since = _clean_cell(since)
    if not since or since.upper() == "N/A":
        return None
    if since.lower() in ("now", "just now"):
        return 0.0
    m = _SINCE_RE.search(since)
    if not m:
        return None
    num = float(m.group("num"))
    unit = m.group("unit").lower()
    if unit.startswith("sec"):
        return num / 60.0
    if unit.startswith("min"):
        return num
    if unit.startswith("hour"):
        return num * 60.0
    if unit.startswith("day"):
        return num * 24.0 * 60.0
    return None

def classify(minutes_ago: Optional[float]) -> str:
    if minutes_ago is None:
        return "missing"
    if minutes_ago < ACTIVE_MAX_MIN:
        return "active"
    if minutes_ago <= STALE_MAX_MIN:
        return "stale"
    return "missing"

def run_meshtastic_nodes() -> tuple[bool, str, str]:
    cmd = [MESHTASTIC_BIN, "--host", RADIO_HOST, "--nodes"]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        ok = (p.returncode == 0)
        return ok, (p.stdout or ""), (p.stderr or "")
    except FileNotFoundError as e:
        return False, "", f"Meshtastic CLI not found: {MESHTASTIC_BIN} ({e})"
    except subprocess.TimeoutExpired:
        return False, "", "Meshtastic CLI timed out"
    except Exception as e:
        return False, "", f"Meshtastic CLI error: {e}"

def parse_nodes_table(text: str) -> List[Dict[str, Any]]:
    lines = [ln.rstrip("\n") for ln in (text or "").splitlines()]
    header_idx = None
    for i, ln in enumerate(lines):
        if "User" in ln and "LastHeard" in ln and "│" in ln:
            header_idx = i
            break
    if header_idx is None:
        return []

    headers = [_clean_cell(h) for h in lines[header_idx].split("│")]
    headers = [h for h in headers if h]

    nodes: List[Dict[str, Any]] = []
    for ln in lines[header_idx + 1:]:
        if "╘" in ln:
            break
        if "│" not in ln:
            continue
        if ln.strip().startswith(("╞", "├", "╔", "╟", "╤", "═")):
            continue
        parts = [_clean_cell(p) for p in ln.split("│")]
        parts = [p for p in parts if p]
        if len(parts) < len(headers):
            continue

        row = dict(zip(headers, parts[:len(headers)]))
        lat = _parse_float_deg(row.get("Latitude", ""))
        lon = _parse_float_deg(row.get("Longitude", ""))
        mins = since_to_minutes(row.get("Since", ""))
        row["lat"] = lat
        row["lon"] = lon
        row["minutes_ago"] = mins
        row["status"] = classify(mins)
        row["label"] = row.get("AKA") or row.get("User") or row.get("ID") or "node"
        nodes.append(row)

    return nodes

def google_maps_link(lat: Optional[float], lon: Optional[float]) -> Optional[str]:
    if lat is None or lon is None:
        return None
    return f"https://www.google.com/maps?q={lat},{lon}"

_state_lock = threading.Lock()
_state: Dict[str, Any] = {
    "updated_utc": None,
    "ok": False,
    "error": None,
    "nodes": [],
    "raw": "",
}

def load_cache() -> None:
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            cached = json.load(f)
        with _state_lock:
            _state.update(cached)
    except Exception:
        pass

def save_cache(snapshot: Dict[str, Any]) -> None:
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(snapshot, f, indent=2)
    except Exception:
        pass

def append_history(nodes: List[Dict[str, Any]], updated_utc: str) -> None:
    try:
        rec = {
            "ts": updated_utc,
            "radio": RADIO_HOST,
            "nodes": [
                {
                    "id": n.get("ID"),
                    "aka": n.get("AKA"),
                    "user": n.get("User"),
                    "status": n.get("status"),
                    "minutes_ago": n.get("minutes_ago"),
                    "lat": n.get("lat"),
                    "lon": n.get("lon"),
                    "snr": n.get("SNR"),
                    "hops": n.get("Hops"),
                    "battery": n.get("Battery"),
                }
                for n in nodes
            ],
        }
        with open(HISTORY_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")
    except Exception:
        pass

def poll_loop() -> None:
    load_cache()
    while True:
        ok, out, err = run_meshtastic_nodes()
        updated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        error = None
        nodes: List[Dict[str, Any]] = []

        if ok:
            nodes = parse_nodes_table(out)
            for n in nodes:
                n["gmap"] = google_maps_link(n.get("lat"), n.get("lon"))
        else:
            error = (err or "").strip() or "meshtastic --nodes failed"

        with _state_lock:
            if ok and nodes:
                _state["nodes"] = nodes
                _state["raw"] = out
            _state["ok"] = ok
            _state["error"] = error
            _state["updated_utc"] = updated
            snapshot = dict(_state)

        save_cache(snapshot)
        if nodes:
            append_history(nodes, updated)

        time.sleep(REFRESH_SECONDS)

threading.Thread(target=poll_loop, daemon=True).start()

@app.route("/")
def index():
    with _state_lock:
        s = dict(_state)
    nodes = s.get("nodes", []) or []
    counts = {"active": 0, "stale": 0, "missing": 0}
    for n in nodes:
        counts[n.get("status", "missing")] = counts.get(n.get("status", "missing"), 0) + 1
    return render_template(
        "index.html",
        app_name=APP_NAME,
        version=VERSION,
        radio=RADIO_HOST,
        refresh=REFRESH_SECONDS,
        updated=s.get("updated_utc"),
        ok=s.get("ok"),
        error=s.get("error"),
        nodes=nodes,
        counts=counts,
    )

@app.route("/map")
def map_view():
    with _state_lock:
        s = dict(_state)
    return render_template(
        "map.html",
        app_name=APP_NAME,
        version=VERSION,
        radio=RADIO_HOST,
        refresh=REFRESH_SECONDS,
        updated=s.get("updated_utc"),
        nodes=s.get("nodes", []) or [],
    )

@app.route("/api/nodes")
def api_nodes():
    with _state_lock:
        return jsonify(dict(_state))

@app.route("/leaflet/<path:filename>")
def leaflet_static(filename: str):
    return send_from_directory(os.path.join(app.static_folder, "leaflet"), filename)

if __name__ == "__main__":
    app.run(host=LISTEN_HOST, port=LISTEN_PORT, debug=False)
