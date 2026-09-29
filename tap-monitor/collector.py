import math
import random
from datetime import datetime, timedelta, timezone

import requests

import config
import db

SERP_URL = "https://serpapi.com/search.json"


def _serpapi(dest, depart, ret):
    params = {
        "engine": "google_flights", "departure_id": config.ORIGIN, "arrival_id": dest,
        "outbound_date": depart, "currency": config.CURRENCY, "hl": "pt",
        "include_airlines": "TP", "type": 1 if ret else 2, "api_key": config.SERPAPI_KEY,
    }
    if ret:
        params["return_date"] = ret
    r = requests.get(SERP_URL, params=params, timeout=60)
    r.raise_for_status()
    data = r.json()
    if data.get("error"):
        raise RuntimeError(data["error"])
    options = (data.get("best_flights") or []) + (data.get("other_flights") or [])
    options = [o for o in options if o.get("price")]
    if not options:
        return None
    best = min(options, key=lambda o: o["price"])
    return {"price": best["price"], "stops": max(len(best.get("flights", [])) - 1, 0),
            "duration": best.get("total_duration")}


def _demo(dest, days_ahead, now):
    # Preço sintético estável por destino + sazonalidade + ruído
    seed = sum(ord(c) for c in dest) * 97
    base = 3800 + (seed % 2500)
    t = now.timestamp() / 86400
    wave = math.sin(t / 6 + seed) * 350 + math.sin(t * 2 * math.pi) * 60
    urgency = max(0, 45 - days_ahead) * 25
    noise = random.Random(int(now.timestamp() // 3600) + seed + days_ahead).uniform(-120, 120)
    return {"price": round(base + wave + urgency + noise, 2), "stops": 1, "duration": 900 + seed % 300}


def fetch(dest, days_ahead, now=None):
    now = now or datetime.now(timezone.utc)
    depart = (now + timedelta(days=days_ahead)).date()
    ret = depart + timedelta(days=config.TRIP_LENGTH_DAYS) if config.TRIP_LENGTH_DAYS else None
    if config.PROVIDER == "serpapi":
        res = _serpapi(dest, depart.isoformat(), ret.isoformat() if ret else None)
    else:
        res = _demo(dest, days_ahead, now)
    return depart, res


def collect_once():
    if config.PROVIDER == "serpapi" and not config.SERPAPI_KEY:
        msg = "SERPAPI_KEY não configurada"
        with db.conn() as c:
            c.execute("INSERT INTO runs(ts,ok,message) VALUES(?,?,?)",
                      (datetime.now(timezone.utc).isoformat(), 0, msg))
        return {"ok": 0, "errors": [msg]}
    ok, errors = 0, []
    now = datetime.now(timezone.utc)
    for dest in config.DESTINATIONS:
        for da in config.DAYS_AHEAD:
            try:
                depart, res = fetch(dest, da, now)
                if not res:
                    errors.append(f"{dest}/{da}d: sem voos TAP")
                    continue
                with db.conn() as c:
                    c.execute("INSERT INTO prices(ts,dest,days_ahead,depart_date,price,currency,stops,duration_min,source)"
                              " VALUES(?,?,?,?,?,?,?,?,?)",
                              (now.isoformat(), dest, da, depart.isoformat(), res["price"], config.CURRENCY,
                               res["stops"], res["duration"], config.PROVIDER))
                ok += 1
            except Exception as e:  # uma falha não derruba as demais
                errors.append(f"{dest}/{da}d: {e}")
    with db.conn() as c:
        c.execute("INSERT INTO runs(ts,ok,message) VALUES(?,?,?)",
                  (now.isoformat(), ok, "; ".join(errors)[:1000]))
    return {"ok": ok, "errors": errors}


def backfill_demo(days=90):
    """Gera 3 meses de histórico sintético (apenas modo demo, banco vazio)."""
    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    rows = []
    for h in range(days * 24, 0, -6):  # a cada 6h para ficar leve
        t = now - timedelta(hours=h)
        for dest in config.DESTINATIONS:
            for da in config.DAYS_AHEAD:
                r = _demo(dest, da, t)
                rows.append((t.isoformat(), dest, da, (t + timedelta(days=da)).date().isoformat(),
                             r["price"], config.CURRENCY, r["stops"], r["duration"], "demo"))
    with db.conn() as c:
        c.executemany("INSERT INTO prices(ts,dest,days_ahead,depart_date,price,currency,stops,duration_min,source)"
                      " VALUES(?,?,?,?,?,?,?,?,?)", rows)
