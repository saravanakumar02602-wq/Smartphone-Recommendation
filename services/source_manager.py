"""Source & last-updated management, authorized feed ingestion (Module 7)."""
import datetime as dt
import pandas as pd
from database import database as db
from services import phone_data
from config import STALE_AFTER_DAYS, INDIA_CATALOG_SOURCE

REQUIRED = ["brand", "model", "price", "ram", "storage", "processor", "benchmark", "camera_main", "camera_front",
            "ois", "battery", "charging", "display_type", "display_size", "refresh_rate", "five_g",
            "updates_years", "operating_system", "source", "product_url"]

POLICY = ("Use only authorized product feeds, official APIs or permitted affiliate feeds. "
          "Do not scrape sites whose terms prohibit it.")


def describe(phone):
    last = dt.date.fromisoformat(str(phone["last_updated"])[:10])
    age = (dt.date.today() - last).days
    indicative = phone["source"] == INDIA_CATALOG_SOURCE
    return {"source": phone["source"], "url": phone["product_url"], "last_updated": last.strftime("%d-%m-%Y"),
            "age_days": age, "stale": age > STALE_AFTER_DAYS, "indicative": indicative,
            "note": "Indicative India-market reference, not a live quote. Confirm specifications, price and availability with a seller."
            if indicative else
            "Prices and availability change frequently - verify on the product page." if age > STALE_AFTER_DAYS
            else "Recently updated."}


def ingest_feed(csv_path):
    """Upsert an authorized CSV feed. Records a price-history row whenever a price changed."""
    feed = pd.read_csv(csv_path)
    missing = [c for c in REQUIRED if c not in feed.columns]
    if missing:
        raise ValueError(f"Feed is missing columns: {missing}")
    today = dt.date.today().isoformat()
    added = updated = 0
    for rec in feed.to_dict("records"):
        found = db.query("SELECT id, price FROM phones WHERE brand=? AND model=?", (rec["brand"], rec["model"]))
        cols = REQUIRED + ["last_updated"]
        rec["last_updated"] = today
        if found:
            pid = found[0]["id"]
            db.execute("UPDATE phones SET " + ",".join(f"{c}=?" for c in cols) + " WHERE id=?",
                       [rec[c] for c in cols] + [pid])
            if int(found[0]["price"]) != int(rec["price"]):
                db.execute("INSERT INTO price_history (phone_id, price, source, recorded_date) VALUES (?,?,?,?)",
                           (pid, int(rec["price"]), rec["source"], today))
            updated += 1
        else:
            pid = db.execute("INSERT INTO phones (" + ",".join(cols) + ") VALUES (" + ",".join("?" * len(cols)) + ")",
                             [rec[c] for c in cols])
            db.execute("INSERT INTO price_history (phone_id, price, source, recorded_date) VALUES (?,?,?,?)",
                       (pid, int(rec["price"]), rec["source"], today))
            added += 1
    phone_data.invalidate()
    return {"added": added, "updated": updated}
