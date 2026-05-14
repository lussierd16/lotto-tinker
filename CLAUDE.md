# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

**Fetch data and rebuild dashboard (full pipeline):**
```bash
python3 BuildDashboard.py --fetch
```

**Rebuild dashboard from cached JSON only (no API call):**
```bash
python3 BuildDashboard.py
```

**Fetch into a specific output directory:**
```bash
python3 BuildDashboard.py --fetch --output-dir .
```

**Quick API test:**
```bash
curl -s -X POST "https://www.michiganlottery.com/api" \
  -H "Content-Type: application/json" \
  -H "Origin: https://www.michiganlottery.com" \
  -d '{"query": "{ winningNumbersForDateRange(dateRange: { start: \"2026-01-01\", end: \"2026-01-01\" }) { drawDate gameTypeId winningNumbers { drawNumbers } } }"}' | python3 -m json.tool
```

No `pip` dependencies — `BuildDashboard.py` uses Python 3 stdlib only.

## Architecture

This is a **single-file pipeline**: `BuildDashboard.py` is both the data fetcher and dashboard builder. It has no framework, no build step, no package manager.

**Data flow:**
1. `fetch_data()` — POSTs a GraphQL query to `https://www.michiganlottery.com/api`, filters by `gameTypeId`, deduplicates (Powerball and Classic Lotto 47 return 2 records per draw), returns sorted records.
2. `build_stats()` — Computes frequency maps, sum distributions, gap analysis, EV history, and recommended picks from the record list.
3. `main()` — Iterates all 4 games, writes `lottery-{key}.json` and `lottery-{key}.csv`, then renders `index.html` by injecting a `JSON.dumps()` blob into the HTML template string (`TEMPLATE`).

**Output files:**
- `index.html` — the entire dashboard, self-contained; served via Cloudflare Pages
- `lottery-{key}.json` / `lottery-{key}.csv` — raw draw history, committed to git by CI

**Frontend:**
`index.html` is a single-file Vanilla JS + Chart.js app. All data is embedded as a JSON literal in a `const DATA = ...` block. No server, no API calls at runtime. The smart number generator runs entirely client-side.

**Automation:**
GitHub Actions (`.github/workflows/update-lottery.yml`) runs daily at 6 AM EST, calls `python3 BuildDashboard.py --fetch --output-dir .`, commits changed JSON/CSV/HTML, then Cloudflare Pages auto-deploys from the `main` branch.

## Key Design Decisions

- **No dependencies**: The data layer uses only `urllib.request`, `json`, `csv`, `os`. Intentional — CI needs no `pip install`.
- **Deduplication**: The GraphQL API returns two records per Powerball and Classic Lotto 47 draw (Double Play / Kicker variant). The script deduplicates by keeping the first record per calendar date (lowest `id`).
- **EV model constants**: `CASH_OPTION = 0.60`, `FED_TAX = 0.37`, `MI_TAX = 0.0425` → `NET_RATE ≈ 0.3525`. Break-even jackpot = `ticket_cost × odds / NET_RATE`.
- **The TEMPLATE string**: The HTML dashboard is a Python string literal in `BuildDashboard.py`, not a separate file. Edits to the dashboard go there.
- **PAI skill**: The `_MILottery` PAI skill (`~/.claude/skills/_MILottery/`) wraps this pipeline for conversational invocation. Use the skill for routine data updates; edit `BuildDashboard.py` for pipeline changes.

## API Reference

**Endpoint:** `POST https://www.michiganlottery.com/api`  
**Auth:** None (public GraphQL)  
**Required headers:** `Content-Type: application/json`, `Origin: https://www.michiganlottery.com`

Game type IDs tracked: Mega Millions (1), Powerball (3), Classic Lotto 47 (10), Millionaire for Life (20). See `SCRAPING-GUIDE.md` for the full game ID table and field-level API notes.
