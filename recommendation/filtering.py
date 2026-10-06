"""Budget bands and hard-constraint filtering (Module 3)."""
import numpy as np
from config import NEAR_BUDGET_TOLERANCE


def classify_budget(df, budget, tolerance=NEAR_BUDGET_TOLERANCE):
    d = df.copy()
    d["budget_band"] = np.where(d.price <= budget, "within",
                                np.where(d.price <= budget * (1 + tolerance), "near", "above"))
    return d


def apply_hard(df, params):
    """Hard constraints that ignore budget: storage, RAM, 5G, display type."""
    d = df[(df.storage >= params.get("min_storage", 0)) & (df.ram >= params.get("min_ram", 0))]
    if params.get("need_5g"):
        d = d[d.five_g == 1]
    if params.get("display_pref") == "amoled":
        d = d[d.display_type.str.contains("AMOLED|OLED", regex=True)]
    return d


def apply_constraints(df, params):
    """Return (candidates, stats). `df` must already carry budget_band."""
    hard = apply_hard(df, params)
    allowed = ["within", "near"] if params.get("include_near", True) else ["within"]
    cands = hard[hard.budget_band.isin(allowed)]
    stats = {
        "catalogue": int(len(df)),
        "after_constraints": int(len(hard)),
        "within": int((hard.budget_band == "within").sum()),
        "near": int((hard.budget_band == "near").sum()),
        "above": int((hard.budget_band == "above").sum()),
        "candidates": int(len(cands)),
    }
    return cands, stats
