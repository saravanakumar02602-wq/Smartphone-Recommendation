"""Price intelligence (Module 7): history, statistics and target-price alerts."""
import datetime as dt
from database import database as db
from config import DEFAULT_USER_ID


def history(pid):
    return db.query("SELECT price, source, recorded_date FROM price_history WHERE phone_id=? ORDER BY recorded_date", (pid,))


def stats(pid):
    h = history(pid)
    if not h:
        return None
    prices = [x["price"] for x in h]
    cur = prices[-1]
    return {"current": cur, "lowest": min(prices), "highest": max(prices), "average": round(sum(prices) / len(prices)),
            "observations": len(prices), "from_peak": cur - max(prices),
            "note": "Historical observations are shown for comparison only; future prices are not predicted."}


def check_alerts(user_id=DEFAULT_USER_ID):
    """Mark alerts whose phone's recorded price is at/below target; return newly triggered ones."""
    fresh = []
    for a in db.list_alerts(user_id):
        if not a["triggered"] and a["current_price"] <= a["target_price"]:
            db.execute("UPDATE alerts SET triggered=1, triggered_price=? WHERE id=?", (a["current_price"], a["id"]))
            fresh.append({**a, "triggered_price": a["current_price"]})
    return fresh
