"""Requirement-conflict detection (Module 3)."""
import math
import numpy as np
from config import FEATURES, LABELS, STRONG_REQUIREMENT, inr
from .filtering import apply_hard


def detect_conflicts(scored, params):
    """`scored` = full catalogue with s_* columns. Returns warnings and adjustable options."""
    w, budget = params["weights"], params["budget"]
    hard = apply_hard(scored, params)
    pool = hard[hard.price <= budget]
    res = {"has_conflict": False, "messages": [], "options": []}
    if pool.empty:
        res["has_conflict"] = True
        res["messages"].append(f"No phone meets your hard requirements within {inr(budget)}.")
        if not hard.empty:
            need = int(math.ceil(hard.price.min() / 500.0) * 500)
            res["options"].append({"label": f"Increase budget to {inr(need)}", "apply": {"budget": need}})
        if params.get("min_storage", 0) > 64:
            res["options"].append({"label": "Reduce storage requirement to 128 GB",
                                   "apply": {"min_storage": 128}})
        if params.get("need_5g"):
            res["options"].append({"label": "Allow non-5G phones", "apply": {"need_5g": 0}})
        return res

    demanded = [f for f in FEATURES if f != "value" and w[f] >= 20]
    gaps = [(f, float(pool["s_" + f].max())) for f in demanded if pool["s_" + f].max() < STRONG_REQUIREMENT]

    def satisfying(frame):
        if not demanded:
            return frame
        mask = np.ones(len(frame), dtype=bool)
        for f in demanded:
            mask &= frame["s_" + f].values >= STRONG_REQUIREMENT
        return frame[mask]

    together = len(demanded) < 2 or not satisfying(pool).empty
    for f, best in gaps:
        res["messages"].append(f"No phone within {inr(budget)} reaches a strong {LABELS[f].lower()} score "
                               f"(best available: {best:.0f}/100).")
    if not together:
        res["messages"].append("No phone within budget is strong in all of: "
                               + ", ".join(LABELS[f] for f in demanded) + ".")
    if res["messages"]:
        res["has_conflict"] = True
        better = satisfying(hard)
        if not better.empty and better.price.min() > budget:
            need = int(math.ceil(better.price.min() / 500.0) * 500)
            res["options"].append({"label": f"Increase budget to {inr(need)}", "apply": {"budget": need}})
        for f in sorted(demanded, key=lambda k: pool["s_" + k].max())[:2]:
            res["options"].append({"label": f"Reduce {LABELS[f].lower()} priority to 15%",
                                   "apply": {"weights": {f: 15}}})
        if params.get("min_storage", 0) > 128:
            res["options"].append({"label": "Reduce storage requirement to 128 GB", "apply": {"min_storage": 128}})
    return res
