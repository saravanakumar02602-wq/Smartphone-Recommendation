"""Personalized recommendation engine: ties filtering, scoring, explanation, trade-offs, conflicts."""
import json
from config import NEAR_BUDGET_PENALTY, TOP_N
from .scoring import compute_feature_scores, personal_score
from .filtering import classify_budget, apply_constraints
from .explanation import explain, compare_two
from .tradeoff import analyze
from .conflict import detect_conflicts


def recommend(scored, params, top_n=TOP_N):
    """`scored` = catalogue DataFrame that already has s_* columns."""
    d = classify_budget(personal_score(scored, params["weights"]), params["budget"])
    cands, stats = apply_constraints(d, params)
    cands = cands.copy()
    cands["match"] = (cands.score - (cands.budget_band == "near") * NEAR_BUDGET_PENALTY).clip(lower=0).round(1)
    top = cands.sort_values(["match", "price"], ascending=[False, True]).head(top_n)
    rows = json.loads(top.to_json(orient="records"))
    for i, r in enumerate(rows):
        r["rank"] = i + 1
        r["explain"] = explain(r, params)
        r["tradeoff"] = analyze(r, params["weights"])
        r["vs_next"] = compare_two(r, rows[i + 1], params["weights"]) if i + 1 < len(rows) else None
    return {"results": rows, "stats": stats, "conflict": detect_conflicts(d, params), "params": params}
