from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, jsonify, render_template, request

import collector
import config
import db

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html", origin=config.ORIGIN, provider=config.PROVIDER,
                           currency=config.CURRENCY, catalog=config.CATALOG,
                           dests=config.DESTINATIONS, days_ahead=config.DAYS_AHEAD,
                           interval=config.INTERVAL_MIN)


@app.route("/api/series")
def series():
    days = int(request.args.get("days", 90))
    gran = request.args.get("gran", "day")  # day | hour
    da = int(request.args.get("da", config.DAYS_AHEAD[0]))
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    fmt = "%Y-%m-%d" if gran == "day" else "%Y-%m-%dT%H:00"
    q = f"""SELECT dest, strftime('{fmt}', ts) AS t, MIN(price) AS min, ROUND(AVG(price),2) AS avg
            FROM prices WHERE ts >= ? AND days_ahead = ? GROUP BY dest, t ORDER BY t"""
    out = {}
    with db.conn() as c:
        for r in c.execute(q, (since, da)):
            out.setdefault(r["dest"], []).append({"t": r["t"], "min": r["min"], "avg": r["avg"]})
    return jsonify(out)


@app.route("/api/summary")
def summary():
    days = int(request.args.get("days", 90))
    da = int(request.args.get("da", config.DAYS_AHEAD[0]))
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    rows = []
    with db.conn() as c:
        for d in config.DESTINATIONS:
            s = c.execute("SELECT MIN(price) mn, MAX(price) mx, AVG(price) av, COUNT(*) n FROM prices"
                          " WHERE dest=? AND days_ahead=? AND ts>=?", (d, da, since)).fetchone()
            last = c.execute("SELECT price, ts, depart_date, stops FROM prices WHERE dest=? AND days_ahead=?"
                             " ORDER BY ts DESC LIMIT 1", (d, da)).fetchone()
            if not last:
                continue
            rows.append({"dest": d, "city": config.CATALOG.get(d, d), "last": last["price"], "ts": last["ts"],
                         "depart": last["depart_date"], "stops": last["stops"],
                         "min": s["mn"], "max": s["mx"], "avg": round(s["av"], 2), "n": s["n"]})
    return jsonify(sorted(rows, key=lambda r: r["last"]))


@app.route("/api/status")
def status():
    with db.conn() as c:
        r = c.execute("SELECT ts, ok, message FROM runs ORDER BY id DESC LIMIT 1").fetchone()
    return jsonify(dict(r) if r else {})


@app.route("/api/collect", methods=["POST"])
def collect_now():
    return jsonify(collector.collect_once())


if __name__ == "__main__":
    db.init()
    with db.conn() as c:
        empty = c.execute("SELECT COUNT(*) FROM prices").fetchone()[0] == 0
    if empty and config.PROVIDER == "demo":
        collector.backfill_demo(90)
    sched = BackgroundScheduler()
    sched.add_job(collector.collect_once, "interval", minutes=config.INTERVAL_MIN,
                  next_run_time=datetime.now())
    sched.start()
    print(f"→ http://127.0.0.1:5050  (provider={config.PROVIDER})")
    app.run(host="127.0.0.1", port=5050, debug=False)
