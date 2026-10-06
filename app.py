"""Phone Nexora - personalized smartphone recommendations (Flask entry point).

Run:  python app.py      then open http://127.0.0.1:5000
"""
import glob, json, os, shutil, subprocess
import pandas as pd
from flask import Flask, abort, jsonify, redirect, render_template, request, url_for

import config as C
from analytics.evaluation import run_evaluation, export_for_r
from database import database as db
from recommendation import recommend
from recommendation.explanation import compare_two
from recommendation.preferences import (build_params, default_params, learn_weights, parse_requirements,
                                        normalize_weights)
from recommendation.tradeoff import analyze
from services import phone_data, price_tracker, source_manager

app = Flask(__name__)
app.config["SECRET_KEY"] = C.SECRET_KEY
app.jinja_env.filters["inr"] = C.inr
app.jinja_env.globals.update(FEATURES=C.FEATURES, LABELS=C.LABELS, COLORS=C.COLORS)
db.init_db()
UID = C.DEFAULT_USER_ID


# ----------------------------------------------------------------------------- helpers
def run(params, top_n=C.TOP_N):
    return recommend(phone_data.get_scored(), params, top_n)


def params_from_form(f):
    weights = {k: f.get("w_" + k, 0) for k in C.FEATURES}
    return build_params(f.get("budget", 15000), weights, f.get("include_near") == "on", f.get("min_storage", 0),
                        f.get("min_ram", 0), f.get("need_5g") == "on", f.get("display_pref", "any"), f.get("usage", ""))


def params_from_json(d):
    return build_params(d.get("budget", 15000), d.get("weights"), d.get("include_near", True), d.get("min_storage", 0),
                        d.get("min_ram", 0), d.get("need_5g", False), d.get("display_pref", "any"), d.get("usage", ""))


def params_for_hid(hid):
    h = db.get_history(hid) if hid else db.latest_history()
    return (json.loads(h["params_json"]), h["id"]) if h else (default_params(), None)


def apply_overrides(params, args):
    p = json.loads(json.dumps(params))
    if args.get("budget"):
        p["budget"] = int(float(args["budget"]))
    if args.get("min_storage") not in (None, ""):
        p["min_storage"] = int(args["min_storage"])
    if args.get("need_5g") not in (None, ""):
        p["need_5g"] = args["need_5g"] in ("1", "true", "on")
    changed = {f: float(args["w_" + f]) for f in C.FEATURES if args.get("w_" + f)}
    if changed:
        raw = dict(p["weights"]); raw.update(changed)
        p["weights"] = normalize_weights(raw)
    return p


def slim(out):
    return [{"id": r["id"], "rank": r["rank"], "name": f"{r['brand']} {r['model']}", "price": r["price"],
             "match": r["match"], "band": r["budget_band"]} for r in out["results"]]


def learned_info():
    ev = []
    for i in db.interactions(UID):
        ph = phone_data.get_phone(i["phone_id"])
        if ph:
            ev.append({"action": i["action"], **{"s_" + f: ph["s_" + f] for f in C.FEATURES}})
    params, _ = params_for_hid(None)
    return learn_weights(ev, phone_data.catalogue_means(), params["weights"])


def find_rscript():
    exe = shutil.which("Rscript")
    if exe:
        return exe
    if os.name == "nt":
        root = os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), "R")
        candidates = glob.glob(os.path.join(root, "R-*", "bin", "Rscript.exe"))
        candidates += glob.glob(os.path.join(root, "R-*", "bin", "x64", "Rscript.exe"))
        if candidates:
            return max(candidates, key=os.path.getmtime)
    return None


# ----------------------------------------------------------------------------- pages
@app.route("/")
def index():
    base, _ = params_for_hid(None)
    p = apply_overrides(base, request.args)
    return render_template("index.html", p=p, recent=db.list_history(UID, 3), n_phones=len(phone_data.get_scored()))


@app.route("/recommend", methods=["POST"])
def recommend_route():
    params = params_from_form(request.form)
    out = run(params)
    hid = db.save_history(UID, params, [r["id"] for r in out["results"]])
    db.save_preferences(UID, params["weights"])
    return redirect(url_for("results", hid=hid))


@app.route("/results/<int:hid>")
def results(hid):
    h = db.get_history(hid) or abort(404)
    params = json.loads(h["params_json"])
    out = run(params)
    states = db.phone_actions(UID, [r["id"] for r in out["results"]])
    for r in out["results"]:
        r["state"] = states.get(r["id"]); r["source"] = source_manager.describe(r)
    return render_template("results.html", out=out, hid=hid, selected=h["selected_phone_id"])


@app.route("/phone/<int:pid>")
def phone_details(pid):
    p = phone_data.get_phone(pid) or abort(404)
    params, hid = params_for_hid(request.args.get("hid", type=int))
    db.log_interaction(UID, pid, "view")
    return render_template("phone_details.html", p=p, hid=hid, src=source_manager.describe(p),
                           stats=price_tracker.stats(pid), hist=price_tracker.history(pid),
                           trade=analyze(p, params["weights"]), similar=phone_data.similar_phones(pid))


@app.route("/compare")
def compare():
    ids = [int(x) for x in request.args.get("ids", "").split(",") if x.strip().isdigit()][:3]
    if len(ids) < 2:
        return redirect(url_for("index"))
    params, hid = params_for_hid(request.args.get("hid", type=int))
    d = phone_data.get_scored()
    from recommendation.scoring import personal_score
    d = personal_score(d, params["weights"])
    phones = [r.iloc[0].to_dict() for i in ids for r in [d[d.id == i]] if not r.empty]
    if len(phones) < 2:
        return redirect(url_for("index"))
    for p in phones:
        db.log_interaction(UID, p["id"], "compare")
    rows = [("Price", "price", "low"), ("Personal match", "score", "high"), ("Main camera (MP)", "camera_main", "high"),
            ("Front camera (MP)", "camera_front", "high"), ("RAM (GB)", "ram", "high"), ("Storage (GB)", "storage", "high"),
            ("Battery (mAh)", "battery", "high"), ("Charging (W)", "charging", "high"), ("Processor", "processor", None),
            ("Benchmark (K)", "benchmark", "high"), ("Display", "display_type", None), ("Refresh rate (Hz)", "refresh_rate", "high"),
            ("5G", "five_g", "high"), ("Updates (years)", "updates_years", "high")]
    why = compare_two(phones[0], phones[1], params["weights"]) if len(phones) > 1 else None
    return render_template("compare.html", phones=phones, rows=rows, hid=hid, why=why)


@app.route("/what-if")
def what_if():
    base, hid = params_for_hid(request.args.get("hid", type=int))
    scenario = apply_overrides(base, request.args)
    return render_template("what_if.html", base=base, scenario=scenario, hid=hid)


@app.route("/history")
def history():
    learned = learned_info()
    apply_url = url_for("index", **{"w_" + f: learned["suggested"][f] for f in C.FEATURES}) if learned else None
    return render_template("history.html", sessions=db.list_history(UID), inter=db.interactions(UID, 25),
                           learned=learned, apply_url=apply_url, alerts=db.list_alerts(UID))


@app.route("/analytics")
def analytics():
    imgs = sorted(os.path.basename(p) for p in glob.glob(os.path.join(C.R_OUTPUT_DIR, "*.png")))
    return render_template("analytics.html", imgs=imgs, has_r=find_rscript() is not None)


# ----------------------------------------------------------------------------- JSON APIs
@app.route("/api/parse", methods=["POST"])
def api_parse():
    return jsonify(parse_requirements((request.get_json(silent=True) or {}).get("text", "")))


@app.route("/api/whatif", methods=["POST"])
def api_whatif():
    d = request.get_json(silent=True) or {}
    base, scen = params_from_json(d.get("base", {})), params_from_json(d.get("scenario", {}))
    b, s = run(base), run(scen)
    old = {r["id"]: r["rank"] for r in b["results"]}
    rows = slim(s)
    for r in rows:
        r["was"] = old.get(r["id"])
        r["move"] = (old[r["id"]] - r["rank"]) if r["id"] in old else None
    dropped = [x for x in slim(b) if x["id"] not in {r["id"] for r in rows}]
    return jsonify({"base": slim(b), "scenario": rows, "dropped": dropped, "conflict": s["conflict"], "stats": s["stats"]})


@app.route("/api/budget-sim", methods=["POST"])
def api_budget_sim():
    d = request.get_json(silent=True) or {}
    base = params_from_json(d.get("base", {}))
    b0 = run(base)
    base_ids = {r["id"] for r in b0["results"]}
    sims = []
    for amount in d.get("budgets") or [base["budget"] + k for k in (1000, 2000, 3000, 5000)]:
        p = dict(base, budget=int(amount))
        o = run(p)
        top = slim(o)
        sims.append({"budget": p["budget"], "within": o["stats"]["within"], "extra_within": o["stats"]["within"] - b0["stats"]["within"],
                     "top3": top[:3], "new_in_top10": [x for x in top if x["id"] not in base_ids][:4],
                     "best_match": top[0]["match"] if top else None})
    return jsonify({"current": {"budget": base["budget"], "within": b0["stats"]["within"], "top3": slim(b0)[:3]},
                    "sims": sims, "caveat": "Scenario analysis only - spending more does not always give a better choice for you."})


@app.route("/api/interact", methods=["POST"])
def api_interact():
    d = request.get_json(silent=True) or {}
    action, pid = d.get("action"), d.get("phone_id")
    if action not in ("view", "compare", "save", "reject", "select") or not phone_data.get_phone(pid):
        return jsonify({"ok": False}), 400
    db.log_interaction(UID, pid, "save" if action == "select" else action)
    if action == "select" and d.get("hid"):
        db.select_phone(d["hid"], pid)
    return jsonify({"ok": True})


@app.route("/api/alerts", methods=["POST"])
def api_alert():
    d = request.get_json(silent=True) or {}
    ph = phone_data.get_phone(d.get("phone_id"))
    try:
        target = int(d.get("target_price"))
    except (TypeError, ValueError):
        target = 0
    if not ph or target <= 0:
        return jsonify({"ok": False, "error": "Enter a valid target price."}), 400
    if ph["source"] == C.INDIA_CATALOG_SOURCE:
        return jsonify({"ok": False, "error": "Price alerts need live seller-price data; this catalogue price is indicative only."}), 400
    db.add_alert(UID, ph["id"], target)
    hit = price_tracker.check_alerts(UID)
    return jsonify({"ok": True, "triggered": len(hit) > 0})


@app.route("/api/alerts/check")
def api_alert_check():
    fresh = price_tracker.check_alerts(UID)
    unseen = db.query("SELECT a.id, p.brand, p.model, a.triggered_price FROM alerts a JOIN phones p ON p.id=a.phone_id "
                      "WHERE a.user_id=? AND a.triggered=1 AND a.seen=0 AND p.source != ?",
                      (UID, C.LEGACY_SAMPLE_SOURCE))
    for u in unseen:
        db.execute("UPDATE alerts SET seen=1 WHERE id=?", (u["id"],))
    return jsonify({"triggered": [{"name": f"{u['brand']} {u['model']}", "price": u["triggered_price"]} for u in unseen]})


@app.route("/api/evaluation")
def api_evaluation():
    return jsonify(run_evaluation())


@app.route("/api/run-r", methods=["POST"])
def api_run_r():
    exe = find_rscript()
    if not exe:
        return jsonify({"ok": False, "error": "Rscript was not found. Install R, then run: Rscript R/analysis.R"}), 400
    run_evaluation()
    export_for_r()
    try:
        proc = subprocess.run([exe, os.path.join("R", "analysis.R")], cwd=C.BASE_DIR, capture_output=True,
                              text=True, timeout=240)
    except subprocess.TimeoutExpired:
        return jsonify({"ok": False, "error": "R analysis exceeded the 4-minute time limit."}), 504
    except OSError as exc:
        return jsonify({"ok": False, "error": f"Could not start Rscript: {exc}"}), 500
    return jsonify({"ok": proc.returncode == 0, "log": (proc.stdout + proc.stderr)[-1500:]})


@app.errorhandler(404)
def not_found(_):
    return render_template("base.html", page_404=True), 404


if __name__ == "__main__":
    app.run(debug=True)
