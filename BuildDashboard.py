import json
import csv
import os
import re
import subprocess
import argparse
from datetime import datetime

# --- Configuration & Odds ---
GAMES = [
    {
        "key": "club-keno",
        "display": "Club Keno",
        "gameTypeId": 13,
        "main_max": 80,
        "main_count": 20,
        "ticket_cost": 1.0,
    },
    {
        "key": "classic-lotto-47",
        "display": "Classic Lotto 47",
        "gameTypeId": 10,
        "main_max": 47,
        "main_count": 6,
        "ticket_cost": 1.0,
        "odds": 10737573
    },
    {
        "key": "mega-millions",
        "display": "Mega Millions",
        "gameTypeId": 1,
        "main_max": 70,
        "main_count": 5,
        "bonus_label": "Mega Ball",
        "bonus_max": 25,
        "ticket_cost": 5.0,
        "odds": 302575350
    },
    {
        "key": "powerball",
        "display": "Powerball",
        "gameTypeId": 3,
        "main_max": 69,
        "main_count": 5,
        "bonus_label": "Powerball",
        "bonus_max": 26,
        "ticket_cost": 2.0,
        "odds": 292201338
    },
    {
        "key": "millionaire-for-life",
        "display": "Millionaire for Life",
        "gameTypeId": 20,
        "main_max": 58,
        "main_count": 5,
        "bonus_label": "Millionaire Ball",
        "bonus_max": 5,
        "ticket_cost": 5.0,
        "odds": 22910580
    }
]

# --- Constants ---
GQL_URL = "https://www.michiganlottery.com/api"
CASH_OPTION = 0.60
FED_TAX = 0.37
MI_TAX = 0.0425
NET_RATE = (1 - FED_TAX - MI_TAX) * CASH_OPTION  # ~0.3525

# --- Core Logic ---

CURL_CMD = [
    "curl", "-s", "--max-time", "30", "-X", "POST",
    "-H", "Content-Type: application/json",
    "-H", "Origin: https://www.michiganlottery.com",
    "-H", "Referer: https://www.michiganlottery.com/",
    "-H", "User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
]

def _gql_fetch(start_date, end_date):
    def _run(include_jackpot):
        jackpot_fragment = " estimatedJackpot" if include_jackpot else ""
        query = (
            f'{{ winningNumbersForDateRange(dateRange: {{ start: "{start_date}", end: "{end_date}" }}) {{'
            f' id drawDate gameTypeId drawNumber'
            f' winningNumbers {{ drawNumbers millionaireball megaball powerball powerplay }}'
            f'{jackpot_fragment}'
            f' }} }}'
        )
        result = subprocess.run(
            CURL_CMD + ["--data", json.dumps({"query": query}), GQL_URL],
            capture_output=True, text=True, check=True,
        )
        return json.loads(result.stdout)

    data = _run(include_jackpot=True)
    if "errors" in data:
        print("  jackpot field unavailable, fetching without.")
        data = _run(include_jackpot=False)
    return data


CHUNK_DAYS = 90


def fetch_data(game_config, existing_records=None, end_date=None):
    from datetime import date as date_type, timedelta

    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")

    # Incremental: only fetch draws newer than what we already have
    if existing_records:
        last = existing_records[-1]['date']
        start_date = (date_type.fromisoformat(last) + timedelta(days=1)).isoformat()
    else:
        start_date = "2025-01-01"

    if start_date > end_date:
        print(f"{game_config['display']}: already up to date.")
        return existing_records or []

    # Chunk large ranges so the API response never gets too big
    all_raw = []
    chunk_start = date_type.fromisoformat(start_date)
    end_dt = date_type.fromisoformat(end_date)
    while chunk_start <= end_dt:
        chunk_end = min(chunk_start + timedelta(days=CHUNK_DAYS - 1), end_dt)
        cs, ce = chunk_start.isoformat(), chunk_end.isoformat()
        print(f"Fetching {game_config['display']} ({cs} -> {ce})...")
        res = _gql_fetch(cs, ce)
        all_raw.extend(res["data"]["winningNumbersForDateRange"])
        chunk_start = chunk_end + timedelta(days=1)

    filtered = [d for d in all_raw if d["gameTypeId"] == game_config["gameTypeId"]]

    # Deduplicate for Powerball/Lotto47 (Double Play/Kicker returns 2 records per draw)
    seen_dates = {}
    deduped = []
    for d in sorted(filtered, key=lambda x: x['id']):
        date_str = d['drawDate'][:10]
        if date_str not in seen_dates:
            seen_dates[date_str] = True
            deduped.append(d)

    bonus_field = "millionaireball" if game_config['key'] == "millionaire-for-life" else \
                  "megaball" if game_config['key'] == "mega-millions" else \
                  "powerball" if game_config['key'] == "powerball" else None

    new_records = []
    for d in deduped:
        wn = d["winningNumbers"]
        new_records.append({
            "date": d["drawDate"][:10],
            "numbers": sorted(wn["drawNumbers"]),
            "bonus": wn.get(bonus_field) if bonus_field else None,
            "jackpot_usd": int(d["estimatedJackpot"]) // 100 if d.get("estimatedJackpot") else None,
            "powerplay": wn.get("powerplay")
        })

    combined = (existing_records or []) + new_records
    return sorted(combined, key=lambda x: x['date'])


def build_stats(game_config, records):
    if not records:
        return None

    total = len(records)
    freq = {}
    bonus_freq = {}
    sums = []
    # Track draws_since (index from end) and last date seen for each number
    draws_since = {n: total for n in range(1, game_config['main_max'] + 1)}
    last_seen_date = {}
    unpopular_count = 0

    for i, r in enumerate(records):
        s = sum(r['numbers'])
        sums.append(s)

        high_count = len([n for n in r['numbers'] if n >= 32])
        if high_count == game_config['main_count']:
            unpopular_count += 1

        for n in r['numbers']:
            freq[n] = freq.get(n, 0) + 1
            draws_since[n] = total - 1 - i
            last_seen_date[n] = r['date']

        bonus_val = r.get('bonus')
        if bonus_val is not None:
            bonus_freq[bonus_val] = bonus_freq.get(bonus_val, 0) + 1

    gap_analysis = sorted(
        [{"number": n, "last_date": last_seen_date.get(n, "Never"), "draws_since": d}
         for n, d in draws_since.items()],
        key=lambda x: x['draws_since'],
        reverse=True
    )[:5]

    # Recommended: top main_count numbers from 32+ zone by frequency
    rec = sorted(
        [n for n in range(32, game_config['main_max'] + 1)],
        key=lambda n: freq.get(n, 0),
        reverse=True
    )[:game_config['main_count']]

    # EV Analysis — only for games with defined odds
    ev_data = None
    if game_config.get('odds') and game_config['key'] != "millionaire-for-life":
        ev_history = []
        pos_count = 0
        break_even = game_config['ticket_cost'] * game_config['odds'] / NET_RATE

        for r in records:
            if r['jackpot_usd']:
                net = r['jackpot_usd'] * NET_RATE
                ev = (net / game_config['odds']) - game_config['ticket_cost']
                is_pos = ev > 0
                if is_pos:
                    pos_count += 1
                ev_history.append({
                    "date": r['date'],
                    "jackpot_usd": r['jackpot_usd'],
                    "ev": ev,
                    "is_positive": is_pos,
                    "is_win": False
                })

        for i in range(len(ev_history) - 1):
            curr_j = ev_history[i]['jackpot_usd']
            next_j = ev_history[i + 1]['jackpot_usd']
            if curr_j and next_j and next_j < curr_j * 0.5:
                ev_history[i]['is_win'] = True

        ev_data = {
            "break_even_usd": int(break_even),
            "history": ev_history,
            "odds_one_in": game_config['odds'],
            "positive_count": pos_count
        }

    return {
        "available": True,
        "key": game_config['key'],
        "display": game_config['display'],
        "main_max": game_config['main_max'],
        "main_count": game_config['main_count'],
        "bonus_field": "bonus",
        "bonus_label": game_config.get('bonus_label'),
        "bonus_max": game_config.get('bonus_max'),
        "ticket_cost": game_config['ticket_cost'],
        "total_draws": total,
        "first_date": records[0]['date'],
        "last_date": records[-1]['date'],
        "latest_record": records[-1],
        "frequency": freq,
        "bonus_frequency": bonus_freq if bonus_freq else None,
        "sum_min": min(sums),
        "sum_max": max(sums),
        "sum_avg": round(sum(sums) / total, 1),
        "sum_distribution": sorted(sums),
        "gap_analysis": gap_analysis,
        "unpopular": {
            "avg_fraction_32plus": round(unpopular_count / total, 4),
            "draws_all_32plus": unpopular_count
        },
        "recommended_picks": sorted(rec),
        "ev": ev_data
    }


_LEGACY_BONUS_FIELD = {
    "powerball": "powerball",
    "mega-millions": "megaball",
    "millionaire-for-life": "millionaireball",
}

def _normalize(records, game_config):
    """Rename legacy game-specific bonus keys to 'bonus' for consistency."""
    src = _LEGACY_BONUS_FIELD.get(game_config['key'])
    if not src:
        return records
    for r in records:
        if src in r and 'bonus' not in r:
            r['bonus'] = r.pop(src)
    return records


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fetch", action="store_true", help="Pull fresh data from the MI Lottery API")
    parser.add_argument("--output-dir", default=".", help="Directory containing data files and index.html")
    args = parser.parse_args()

    game_stats = []
    jackpot_history = {}
    total_draws = 0

    for game in GAMES:
        records = []
        json_path = os.path.join(args.output_dir, f"lottery-{game['key']}.json")
        csv_path = os.path.join(args.output_dir, f"lottery-{game['key']}.csv")

        if args.fetch:
            existing = []
            if os.path.exists(json_path):
                with open(json_path, "r") as f:
                    existing = _normalize(json.load(f), game)
            records = fetch_data(game, existing_records=existing)
            with open(json_path, "w") as f:
                json.dump(records, f, indent=2)
            # Write CSV
            bonus_label = game.get('bonus_label', 'bonus').lower().replace(' ', '_')
            with open(csv_path, "w", newline="") as f:
                writer = csv.writer(f)
                header = ["date"] + [f"n{i+1}" for i in range(game['main_count'])]
                if game.get('bonus_label'):
                    header.append(bonus_label)
                writer.writerow(header)
                for r in records:
                    row = [r['date']] + r['numbers']
                    if game.get('bonus_label'):
                        row.append(r.get('bonus', ''))
                    writer.writerow(row)
        else:
            if os.path.exists(json_path):
                with open(json_path, "r") as f:
                    records = _normalize(json.load(f), game)

        stats = build_stats(game, records)
        if stats:
            game_stats.append(stats)
            total_draws += stats['total_draws']
            if stats['ev']:
                jackpot_history[game['display']] = stats['ev']['history']

    # Inject fresh data into index.html (treat it as the template)
    html_path = os.path.join(args.output_dir, "index.html")
    template_path = html_path if os.path.exists(html_path) else os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")
    with open(template_path, "r") as f:
        html = f.read()

    json_blob = json.dumps({"games": game_stats, "jackpot_trend": jackpot_history})
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    total_str = f"{total_draws} historical draws across {len(game_stats)} games"

    # Replace the embedded data blob
    html = re.sub(r'const DATA = \{.*?\};', f'const DATA = {json_blob};', html, flags=re.DOTALL)

    # Replace the subtitle timestamp and draw count
    html = re.sub(
        r'Generated [^·<]+·[^<]+',
        f'Generated {timestamp} · Based on {total_str}',
        html
    )

    with open(html_path, "w") as f:
        f.write(html)

    print(f"Dashboard updated: {total_draws} draws across {len(game_stats)} games.")


if __name__ == "__main__":
    main()
