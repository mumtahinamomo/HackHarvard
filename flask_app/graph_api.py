"""
Graph API endpoints for Flask application.
Provides graph data and visualization endpoints adapted from the OpenBallot FastAPI server.
"""

import os
import json
import csv
import statistics
from typing import Dict, Any, List, Optional
from flask import jsonify, request
from . import app

# Graph data paths
HERE = os.path.abspath(os.path.dirname(__file__))
GRAPH_PATH = os.path.join(HERE, "graph", "graph_house.json")
DATA_DIR = os.path.join(HERE, "new_data")
HOUSE_CSV = os.path.join(DATA_DIR, "house_candidates_indiv_percentiles.csv")
SEN_CSV = os.path.join(DATA_DIR, "senate_candidates_indiv_percentiles.csv")

# Load graph data once at startup
GRAPH: Dict[str, Any] = {"nodes": [], "links": [], "meta": {"app": "OpenBallot"}}
if os.path.exists(GRAPH_PATH):
    try:
        with open(GRAPH_PATH, "r", encoding="utf-8") as f:
            GRAPH = json.load(f)
    except Exception as e:
        GRAPH = {"nodes": [], "links": [], "meta": {"app": "OpenBallot", "error": str(e)}}

# Extract node collections for quick lookup
FUNDING_GROUP_IDS = {n.get("id") for n in GRAPH.get("nodes", []) if n.get("type") == "FundingGroup"}
POLITICIAN_IDS = {n.get("id") for n in GRAPH.get("nodes", []) if n.get("type") == "Politician"}
POLITICIANS = {n.get("id"): n for n in GRAPH.get("nodes", []) if n.get("type") == "Politician"}

def _slim_party(raw: str) -> str:
    """Normalize party codes to D / R / Other."""
    if not raw:
        return "Other"
    r = raw.strip().upper()
    if r.startswith("DEM"): return "D"
    if r.startswith("REP"): return "R"
    if r in {"D", "R"}:     return r
    return "Other"

def _to_float(x, default=0.0) -> float:
    try:
        return float(x)
    except Exception:
        return default

def _read_percentile_csv(path: str) -> List[Dict[str, Any]]:
    """Read House or Senate CSV and return rows with normalized data."""
    out: List[Dict[str, Any]] = []
    if not os.path.exists(path):
        return out

    with open(path, newline="", encoding="utf-8") as f:
        rdr = csv.DictReader(f)
        for r in rdr:
            name = (r.get("CAND_NAME") or "").strip()
            if not name:
                continue
            party = _slim_party(r.get("CAND_PTY_AFFILIATION") or r.get("CAND_PTY") or "")
            state = (r.get("CAND_OFFICE_ST") or r.get("STATE") or "").strip() or "NA"

            # Individual share % — try multiple keys; coerce to [0,100]
            pct_raw = r.get("Pct_Individual", "")
            if pct_raw == "" and "PCT_INDIV_CONTRIB" in r:
                pct_raw = r.get("PCT_INDIV_CONTRIB")

            pct = _to_float(pct_raw, 0.0)
            if 0.0 <= pct <= 1.0:
                pct *= 100.0
            pct = max(0.0, min(100.0, pct))

            out.append({
                "name": name,
                "party": party,
                "state": state,
                "pct_indiv": pct,
                "ttl_indiv": _to_float(r.get("TTL_INDIV_CONTRIB", 0.0)),
                "ttl_rcpts": _to_float(r.get("TTL_RECEIPTS", 0.0)),
            })
    return out

def _p50(vals: List[float]) -> float:
    vals = [v for v in vals if v is not None]
    if not vals:
        return 0.0
    try:
        return float(statistics.median(vals))
    except Exception:
        vals = sorted(vals)
        n = len(vals)
        mid = n // 2
        return float(vals[mid] if n % 2 == 1 else (vals[mid-1] + vals[mid]) / 2)

# Load CSV data once at startup
ALL_ROWS: List[Dict[str, Any]] = _read_percentile_csv(HOUSE_CSV) + _read_percentile_csv(SEN_CSV)

@app.route('/api/graph')
def get_graph():
    """Returns graph data with optional filtering."""
    party = request.args.get('party', None)
    state = request.args.get('state', None)
    min_amount = int(request.args.get('min_amount', 0))
    
    nodes: List[Dict[str, Any]] = GRAPH.get("nodes", [])
    links: List[Dict[str, Any]] = GRAPH.get("links", [])

    keep_pols = set()
    for pid, p in POLITICIANS.items():
        ok = True
        if party is not None:
            want = party
            have = p.get("party", "")
            ok = ok and (have == want)
        if state is not None:
            ok = ok and (p.get("state", "") == state)
        if ok:
            keep_pols.add(pid)

    if party is None and state is None:
        keep_pols = set(POLITICIAN_IDS)

    kept_links: List[Dict[str, Any]] = []
    for l in links:
        if l.get("type") != "donation":
            continue
        if l.get("target") in keep_pols and float(l.get("amount", 0) or 0) >= float(min_amount):
            kept_links.append(l)

    used_ids = set(FUNDING_GROUP_IDS) | {l["target"] for l in kept_links} | {l["source"] for l in kept_links}
    kept_nodes = [n for n in nodes if n.get("id") in used_ids]

    meta = {
        "app": GRAPH.get("meta", {}).get("app", "OpenBallot"),
        "currency": GRAPH.get("meta", {}).get("currency", "USD"),
        "filters": {"party": party, "state": state, "min_amount": min_amount},
        "counts": {"nodes": len(kept_nodes), "links": len(kept_links), "politicians": len(keep_pols)},
        "note": "Funding mix → Politician (House). STATE/PARTY may be missing in this dataset.",
    }
    return jsonify({"meta": meta, "nodes": kept_nodes, "links": kept_links})

@app.route('/api/politician/<politician_id>/graph')
def get_politician_graph(politician_id: str):
    """Returns graph data focused on a specific politician."""
    # Find the politician in the graph data
    politician_node = None
    for node in GRAPH.get("nodes", []):
        if node.get("type") == "Politician" and node.get("id") == f"pol_{politician_id}":
            politician_node = node
            break
    
    if not politician_node:
        return jsonify({"error": "Politician not found in graph data"}), 404

    nodes: List[Dict[str, Any]] = GRAPH.get("nodes", [])
    links: List[Dict[str, Any]] = GRAPH.get("links", [])

    # Include all funding groups and the specific politician
    politician_id_full = f"pol_{politician_id}"
    kept_nodes = [n for n in nodes if n.get("id") in FUNDING_GROUP_IDS or n.get("id") == politician_id_full]
    
    # Include links connected to this politician
    kept_links = []
    for l in links:
        if l.get("type") == "donation" and l.get("target") == politician_id_full:
            kept_links.append(l)

    meta = {
        "app": "OpenBallot",
        "currency": "USD",
        "politician_id": politician_id,
        "politician_name": politician_node.get("name", "Unknown"),
        "counts": {"nodes": len(kept_nodes), "links": len(kept_links)},
        "note": f"Funding connections for {politician_node.get('name', 'Unknown')}",
    }
    
    return jsonify({"meta": meta, "nodes": kept_nodes, "links": kept_links})

@app.route('/api/indiv_percentiles')
def indiv_percentiles():
    """Returns individual contribution percentile statistics."""
    party = request.args.get('party', 'All')
    state = request.args.get('state', None)
    topn = int(request.args.get('topn', 15))
    
    if not ALL_ROWS:
        return jsonify({
            "summary": {"n": 0, "p50_overall": 0, "p50_D": 0, "p50_R": 0, "unit": "percent"},
            "by_party": [], "by_state": [], "leaders_low": [], "leaders_high": [], "rows": []
        })

    rows = ALL_ROWS
    if party and party != "All":
        rows = [r for r in rows if r["party"] == party]
    if state:
        rows = [r for r in rows if r["state"] == state]

    n = len(rows)
    overall_p50 = round(_p50([r["pct_indiv"] for r in rows]), 2)

    # Party medians
    by_party = []
    for p in ["D", "R", "Other"]:
        pr = [r["pct_indiv"] for r in ALL_ROWS if r["party"] == p and (not state or r["state"] == state)]
        by_party.append({"party": p, "p50": round(_p50(pr), 2), "n": len(pr)})

    # States
    buckets: Dict[str, List[float]] = {}
    for r in rows:
        k = r.get("state") or "NA"
        buckets.setdefault(k, []).append(r["pct_indiv"])
    by_state = [{"state": k, "p50": round(_p50(vs), 2), "n": len(vs)} for k, vs in buckets.items()]
    by_state.sort(key=lambda x: x["state"])

    # Leaderboards
    sorted_rows = sorted(rows, key=lambda r: r["pct_indiv"])
    leaders_low = sorted_rows[:topn]
    leaders_high = list(reversed(sorted_rows[-topn:]))

    rows_slim = [{"name": r["name"], "party": r["party"], "state": r["state"], "pct_indiv": r["pct_indiv"]} for r in rows]

    return jsonify({
        "summary": {
            "n": n,
            "p50_overall": overall_p50,
            "p50_D": next((x["p50"] for x in by_party if x["party"]=="D"), 0.0),
            "p50_R": next((x["p50"] for x in by_party if x["party"]=="R"), 0.0),
            "unit": "percent",
        },
        "by_party": by_party,
        "by_state": by_state,
        "leaders_low": leaders_low,
        "leaders_high": leaders_high,
        "rows": rows_slim, 
    })

@app.route('/api/graph/health')
def graph_health():
    """Health check endpoint for graph data."""
    return jsonify({
        "status": "ok",
        "graph_path": GRAPH_PATH,
        "data_dir": DATA_DIR,
        "nodes": len(GRAPH.get("nodes", [])),
        "links": len(GRAPH.get("links", [])),
        "rows_loaded": len(ALL_ROWS),
        "has_house_csv": os.path.exists(HOUSE_CSV),
        "has_senate_csv": os.path.exists(SEN_CSV),
    })
