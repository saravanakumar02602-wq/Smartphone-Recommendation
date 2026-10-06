"""Evaluation (Module 8): recommendation profiles, quality checks, and R exports."""
import os, time
import pandas as pd
from config import FEATURES, BASE_DIR
from database import database as db
from recommendation import recommend
from recommendation.explanation import verify
from recommendation.preferences import build_params
from services import phone_data

PROFILES = {
    "Student":        dict(budget=15000, w=dict(camera=30, battery=20, performance=20, storage=15, display=10, value=5), min_storage=128),
    "Gamer":          dict(budget=25000, w=dict(performance=40, display=20, battery=20, storage=10, camera=5, software=5), min_ram=8),
    "Photographer":   dict(budget=30000, w=dict(camera=45, display=15, storage=15, performance=10, battery=10, software=5), min_storage=128),
    "Business user":  dict(budget=35000, w=dict(software=25, battery=25, display=15, performance=15, camera=10, storage=10), need_5g=True),
    "Heavy battery":  dict(budget=15000, w=dict(battery=45, performance=15, display=10, storage=10, camera=10, value=10)),
    "Budget user":    dict(budget=12000, w=dict(value=35, battery=25, storage=15, camera=10, performance=10, display=5), include_near=False),
}


def _params(cfg, weights=None):
    kw = {k: v for k, v in cfg.items() if k != "w"}
    return build_params(weights=weights or cfg["w"], **kw)


def run_evaluation(export=True):
    scored = phone_data.get_scored()
    means = phone_data.catalogue_means()
    summary, recs = [], []
    for name, cfg in PROFILES.items():
        p = _params(cfg)
        t0 = time.perf_counter()
        for _ in range(5):
            out = recommend(scored, p)
        ms = (time.perf_counter() - t0) / 5 * 1000
        res = out["results"]
        top = pd.DataFrame(res)
        dom = max(FEATURES, key=lambda f: p["weights"][f])
        # 1) constraint accuracy
        viol = 0
        for r in res:
            bad = (r["storage"] < p["min_storage"]) or (r["ram"] < p["min_ram"]) or (p["need_5g"] and not r["five_g"]) \
                or r["price"] > p["budget"] * (1.10 if p["include_near"] else 1.0)
            viol += int(bad)
        # 2) relevance: weighted score of top-10 relative to catalogue average
        mean_match = float(top["match"].mean()) if len(top) else 0.0
        base = float((scored[["s_" + f for f in FEATURES]].mul([p["weights"][f] for f in FEATURES]).sum(axis=1) / 100).mean())
        lift = round(mean_match - base, 1)
        # 3) score consistency: raising the dominant priority must not lower its average in the Top-10
        boosted = dict(p["weights"]); boosted[dom] += 25
        out2 = recommend(scored, _params(cfg, boosted))
        before = float(top["s_" + dom].mean()) if len(top) else 0.0
        after = float(pd.DataFrame(out2["results"])["s_" + dom].mean()) if out2["results"] else 0.0
        consistent = bool(after >= before - 1e-9)
        # 4) explanation consistency
        ok = tot = 0
        for r in res:
            a, b = verify(r, p, r["explain"]); ok += a; tot += b
        summary.append(dict(profile=name, budget=p["budget"], candidates=out["stats"]["candidates"], top_n=len(res),
                            mean_match=round(mean_match, 1), lift_vs_catalogue=lift, constraint_violations=viol,
                            priority_consistent=int(consistent), explanation_accuracy=round(ok / tot, 3) if tot else 1.0,
                            avg_response_ms=round(ms, 2), dominant=dom, **{"w_" + f: p["weights"][f] for f in FEATURES}))
        for r in res:
            recs.append(dict(profile=name, rank=r["rank"], phone_id=r["id"], brand=r["brand"], model=r["model"],
                             price=r["price"], match=r["match"], **{"s_" + f: r["s_" + f] for f in FEATURES}))
    result = {"summary": summary,
              "overall": {"constraint_violations": int(sum(s["constraint_violations"] for s in summary)),
                          "priority_consistency": f"{sum(s['priority_consistent'] for s in summary)}/{len(summary)}",
                          "explanation_accuracy": round(sum(s["explanation_accuracy"] for s in summary) / len(summary), 3),
                          "avg_response_ms": round(sum(s["avg_response_ms"] for s in summary) / len(summary), 2)}}
    if export:
        export_for_r(summary, recs)
    return result


def export_for_r(summary=None, recs=None):
    d = os.path.join(BASE_DIR, "data")
    if summary is not None:
        pd.DataFrame(summary).to_csv(os.path.join(d, "eval_summary.csv"), index=False)
        pd.DataFrame(recs).to_csv(os.path.join(d, "eval_recommendations.csv"), index=False)
    hist = db.query("SELECT id, user_id, budget, usage, recommendation_date, selected_phone_id FROM recommendation_history")
    pd.DataFrame(hist, columns=["id", "user_id", "budget", "usage", "recommendation_date", "selected_phone_id"]) \
        .to_csv(os.path.join(d, "export_history.csv"), index=False)
    inter = db.query("SELECT user_id, phone_id, action, timestamp FROM interactions")
    pd.DataFrame(inter, columns=["user_id", "phone_id", "action", "timestamp"]).to_csv(os.path.join(d, "export_interactions.csv"), index=False)


if __name__ == "__main__":
    db.init_db()
    r = run_evaluation()
    print(pd.DataFrame(r["summary"])[["profile", "candidates", "mean_match", "constraint_violations",
                                      "priority_consistent", "explanation_accuracy", "avg_response_ms"]].to_string(index=False))
    print(r["overall"])
