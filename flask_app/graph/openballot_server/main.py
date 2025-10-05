# main.py — OpenBallot API
# - /api/graph: force-directed graph data (House JSON you already generated)
# - /api/indiv_percentiles: percent-of-funds from Individuals, aggregated from new_data CSVs
# - /api/healthz: quick status + counts

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, Dict, Any, List
import os, json, csv, statistics

APP_NAME = "OpenBallot"


HERE = os.path.abspath(os.path.dirname(__file__))

DATA_PATH = os.environ.get(
    "OPENBALLOT_GRAPH_PATH",
    os.path.abspath(os.path.join(HERE, "..", "graph_house.json"))
)

DATA_DIR = os.environ.get(
    "OPENBALLOT_DATA_DIR",
    os.path.abspath(os.path.join(HERE, "..", "new_data"))
)

HOUSE_CSV = os.path.join(DATA_DIR, "house_candidates_indiv_percentiles.csv")
SEN_CSV   = os.path.join(DATA_DIR, "senate_candidates_indiv_percentiles.csv")

# -----------------------------
# App
# -----------------------------
app = FastAPI(title=f"{APP_NAME} API", version="0.3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

# -----------------------------
# Load Graph JSON (tolerant)
# -----------------------------
GRAPH: Dict[str, Any] = {"nodes": [], "links": [], "meta": {"app": APP_NAME}}
if os.path.exists(DATA_PATH):
    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            GRAPH = json.load(f)
    except Exception as e:
        GRAPH = {"nodes": [], "links": [], "meta": {"app": APP_NAME, "error": str(e)}}

FUNDING_GROUP_IDS = {n.get("id") for n in GRAPH.get("nodes", []) if n.get("type") == "FundingGroup"}
POLITICIAN_IDS    = {n.get("id") for n in GRAPH.get("nodes", []) if n.get("type") == "Politician"}
POLITICIANS       = {n.get("id"): n for n in GRAPH.get("nodes", []) if n.get("type") == "Politician"}

# -----------------------------
# Helpers for CSV reading
# -----------------------------
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
    """
    Reads either House or Senate CSV and returns rows with:
      name, party (D/R/Other), state, pct_indiv (0-100), plus some totals (if present).
    Supports columns 'Pct_Individual' or 'PCT_INDIV_CONTRIB'.
    """
    out: List[Dict[str, Any]] = []
    if not os.path.exists(path):
        return out

    with open(path, newline="", encoding="utf-8") as f:
        rdr = csv.DictReader(f)
        for r in rdr:
            name  = (r.get("CAND_NAME") or "").strip()
            if not name:
                # Some rows may be totals/blank; skip
                continue
            party = _slim_party(r.get("CAND_PTY_AFFILIATION") or r.get("CAND_PTY") or "")
            state = (r.get("CAND_OFFICE_ST") or r.get("STATE") or "").strip() or "NA"

            # Individual share % — try multiple keys; coerce to [0,100]
            pct_raw = r.get("Pct_Individual", "")
            if pct_raw == "" and "PCT_INDIV_CONTRIB" in r:
                pct_raw = r.get("PCT_INDIV_CONTRIB")

            pct = _to_float(pct_raw, 0.0)
            # Heuristic: if looks like 0..1, treat as fraction; else assume already a percent
            if 0.0 <= pct <= 1.0:
                pct *= 100.0
            pct = max(0.0, min(100.0, pct))

            out.append({
                "name": name,
                "party": party,
                "state": state,
                "pct_indiv": pct,
                # Optional extras if present (won't be required by charts)
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

def _group_p50(rows: List[Dict[str, Any]], key: str) -> List[Dict[str, Any]]:
    buckets: Dict[str, List[float]] = {}
    for r in rows:
        k = r.get(key) or "NA"
        buckets.setdefault(k, []).append(r["pct_indiv"])
    out = [{"%s" % key: k, "p50": round(_p50(vs), 2), "n": len(vs)} for k, vs in buckets.items()]
    out.sort(key=lambda x: x[key])
    return out

# Load once at startup
ALL_ROWS: List[Dict[str, Any]] = _read_percentile_csv(HOUSE_CSV) + _read_percentile_csv(SEN_CSV)

# -----------------------------
# Endpoints
# -----------------------------
@app.get("/api/graph")
def get_graph(
    party: Optional[str] = Query(None, description="Filter by party code (D/R/Other or raw in JSON)"),
    state: Optional[str] = Query(None, description="Filter by state code (e.g., MA, TX)"),
    min_amount: int = Query(0, ge=0, description="Keep donation links with amount >= min_amount"),
) -> Dict[str, Any]:
    """
    Returns a subgraph with the three FundingGroup nodes and filtered Politicians + inbound donation links.
    """
    nodes: List[Dict[str, Any]] = GRAPH.get("nodes", [])
    links: List[Dict[str, Any]] = GRAPH.get("links", [])

    keep_pols = set()
    for pid, p in POLITICIANS.items():
        ok = True
        if party is not None:
            # accept D/R/Other or the raw codes from your JSON
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
        "app": GRAPH.get("meta", {}).get("app", APP_NAME),
        "currency": GRAPH.get("meta", {}).get("currency", "USD"),
        "filters": {"party": party, "state": state, "min_amount": min_amount},
        "counts": {"nodes": len(kept_nodes), "links": len(kept_links), "politicians": len(keep_pols)},
        "note": "Funding mix → Politician (House). STATE/PARTY may be missing in this dataset.",
    }
    return {"meta": meta, "nodes": kept_nodes, "links": kept_links}

@app.get("/api/indiv_percentiles")
def indiv_percentiles(
    party: str = Query("All", description="One of: All | D | R | Other"),
    state: Optional[str] = Query(None, description="State code (e.g., CA)"),
    topn: int = Query(15, ge=1, le=100),
    include_rows: bool = Query(True, description="Always include rows used by charts"),
) -> Dict[str, Any]:
    """
    Returns percent-of-funds-from-Individuals stats merged across House + Senate CSVs.
      - summary: overall and party medians
      - by_party: p50 per party
      - by_state: p50 per state (within current filter)
      - leaders_low / leaders_high: bottom/top N by pct_indiv (within current filter)
      - rows: slim list [{name, party, state, pct_indiv}] ALWAYS included for charts.
    """
    if not ALL_ROWS:
        return {
            "summary": {"n": 0, "p50_overall": 0, "p50_D": 0, "p50_R": 0, "unit": "percent"},
            "by_party": [], "by_state": [], "leaders_low": [], "leaders_high": [], "rows": []
        }

    rows = ALL_ROWS
    if party and party != "All":
        rows = [r for r in rows if r["party"] == party]
    if state:
        rows = [r for r in rows if r["state"] == state]

    n = len(rows)
    overall_p50 = round(_p50([r["pct_indiv"] for r in rows]), 2)

    # Party medians (use ALL_ROWS so comparison is stable even when filtering by party)
    by_party = []
    for p in ["D", "R", "Other"]:
        pr = [r["pct_indiv"] for r in ALL_ROWS if r["party"] == p and (not state or r["state"] == state)]
        by_party.append({"party": p, "p50": round(_p50(pr), 2), "n": len(pr)})

    # States (within current filter)
    by_state = _group_p50(rows, "state")

    # Leaderboards (within current filter)
    sorted_rows = sorted(rows, key=lambda r: r["pct_indiv"])
    leaders_low  = sorted_rows[:topn]
    leaders_high = list(reversed(sorted_rows[-topn:]))

    rows_slim = [{"name": r["name"], "party": r["party"], "state": r["state"], "pct_indiv": r["pct_indiv"]} for r in rows]

    return {
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
    }

@app.get("/api/healthz")
def healthz():
    return {
        "status": "ok",
        "data_path": DATA_PATH,
        "data_dir": DATA_DIR,
        "nodes": len(GRAPH.get("nodes", [])),
        "links": len(GRAPH.get("links", [])),
        "rows_loaded": len(ALL_ROWS),
        "has_house_csv": os.path.exists(HOUSE_CSV),
        "has_senate_csv": os.path.exists(SEN_CSV),
    }
