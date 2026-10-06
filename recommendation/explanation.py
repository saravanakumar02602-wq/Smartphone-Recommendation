"""Explainable recommendations (Module 5): reasons are generated from real attributes."""
from config import FEATURES, LABELS, STRONG, WEAK, inr

DESC = {
    "camera": lambda p: f"{p['camera_main']} MP main camera{' with OIS' if p['ois'] else ''}, {p['camera_front']} MP selfie",
    "performance": lambda p: f"{p['processor']} chip, {p['ram']} GB RAM (benchmark {p['benchmark']}K)",
    "battery": lambda p: f"{p['battery']} mAh battery with {p['charging']} W charging",
    "storage": lambda p: f"{p['storage']} GB storage",
    "display": lambda p: f"{p['display_size']}\" {p['display_type']} at {p['refresh_rate']} Hz",
    "software": lambda p: f"{p['updates_years']} years of updates, {'5G ready' if p['five_g'] else 'no 5G'}",
    "value": lambda p: "good capability for the price",
}


def explain(p, params):
    """Return {'reasons': [...], 'warnings': [...]}; each item = {'key', 'text'}."""
    w, b = params["weights"], params["budget"]
    reasons, warns = [], []
    if p["budget_band"] == "within":
        reasons.append({"key": "budget", "text": f"Within your budget ({inr(p['price'])} of {inr(b)})"})
    elif p["budget_band"] == "near":
        warns.append({"key": "budget", "text": f"{inr(p['price'] - b)} above your budget (near-budget option)"})
    for f in FEATURES:
        s = p["s_" + f]
        if s >= STRONG and (w[f] >= 10 or f == "value"):
            reasons.append({"key": f, "text": f"Strong {LABELS[f].lower()}: {DESC[f](p)}"})
        elif s <= WEAK and w[f] >= 12:
            warns.append({"key": f, "text": f"{LABELS[f]} is a weaker area: {DESC[f](p)}"})
    if params.get("min_storage") and p["storage"] >= params["min_storage"]:
        reasons.append({"key": "storage_req", "text": f"Meets your {params['min_storage']} GB storage requirement"})
    if params.get("need_5g") and p["five_g"]:
        reasons.append({"key": "5g", "text": "Supports 5G as requested"})
    if len(reasons) < 2:  # always show the phone's best attribute
        f = max(FEATURES, key=lambda k: p["s_" + k])
        if not any(r["key"] == f for r in reasons):
            reasons.append({"key": f, "text": f"Best attribute is {LABELS[f].lower()}: {DESC[f](p)}"})
    return {"reasons": reasons, "warnings": warns}


def verify(p, params, ex):
    """Check every generated statement against the raw data (used by the evaluation)."""
    ok = 0
    items = [(r, True) for r in ex["reasons"]] + [(x, False) for x in ex["warnings"]]
    for item, positive in items:
        k = item["key"]
        if k == "budget":
            good = (p["price"] <= params["budget"]) if positive else (p["price"] > params["budget"])
        elif k == "storage_req":
            good = p["storage"] >= params["min_storage"]
        elif k == "5g":
            good = p["five_g"] == 1
        elif positive:
            good = p["s_" + k] >= STRONG or ("Best attribute" in item["text"])
        else:
            good = p["s_" + k] <= WEAK
        ok += bool(good)
    return ok, len(items)


def compare_two(a, b, weights):
    """Why does phone A rank above/below phone B? Contribution of each criterion in points."""
    total = float(sum(weights.values())) or 1.0
    diffs = {f: (a["s_" + f] - b["s_" + f]) * weights[f] / total for f in FEATURES}
    adv = sorted([(LABELS[f], round(v, 1)) for f, v in diffs.items() if v > 0.05], key=lambda x: -x[1])
    dis = sorted([(LABELS[f], round(-v, 1)) for f, v in diffs.items() if v < -0.05], key=lambda x: -x[1])
    gap = round(sum(diffs.values()), 1)
    na, nb = f"{a['brand']} {a['model']}", f"{b['brand']} {b['model']}"
    head = f"{na} scores {abs(gap):.1f} points {'higher' if gap >= 0 else 'lower'} than {nb} for your priorities."
    if adv:
        head += " It leads on " + ", ".join(f"{n} (+{v})" for n, v in adv[:3]) + "."
    if dis:
        head += f" {nb} is better on " + ", ".join(f"{n} (+{v})" for n, v in dis[:3]) + "."
    return {"gap": gap, "advantages": adv, "disadvantages": dis, "text": head}
