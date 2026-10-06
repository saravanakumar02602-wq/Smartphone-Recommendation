"""Requirement analyzer (rule-based NLP), weight handling and preference learning (Module 1)."""
import re
from config import FEATURES, LABELS, DEFAULT_WEIGHTS

KEYWORDS = {
    "camera": ["camera", "photo", "photography", "selfie", "vlog", "portrait", "video"],
    "performance": ["gaming", "game", "games", "pubg", "bgmi", "performance", "fast", "multitask",
                    "processor", "editing", "lag"],
    "battery": ["battery", "charging", "charge", "travel", "all day", "long lasting", "backup"],
    "storage": ["storage", "memory", "files", "store", "gb"],
    "display": ["display", "screen", "amoled", "movies", "netflix", "watching", "120 hz", "120hz", "reels"],
    "software": ["software", "updates", "clean", "android", "security", "long term", "long-term", "smooth ui"],
    "value": ["cheap", "value", "affordable", "money", "saving"],
}
PROFILE_BOOSTS = {
    "student": {"value": 1.0}, "gamer": {"performance": 2.5, "display": 1.0, "battery": 0.5},
    "business": {"software": 2.0, "battery": 1.0}, "professional": {"software": 1.5, "battery": 1.0},
    "social media": {"camera": 0.8, "display": 0.8, "battery": 0.5},
    "youtube": {"display": 1.2, "battery": 1.2}, "photographer": {"camera": 3.0},
}
STRONG_MODS = ("good", "main", "mainly", "mostly", "very", "excellent", "best", "high", "great", "top", "priority", "important", "amazing", "flagship", "highest")
SOFT_MODS = ("decent", "occasional", "occasionally", "some", "average", "okay", "basic", "little")


def normalize_weights(w):
    """Scale any positive weights to integers that sum to exactly 100."""
    raw = {f: max(0.0, float(w.get(f, 0) or 0)) for f in FEATURES}
    total = sum(raw.values())
    if total <= 0:
        return dict(DEFAULT_WEIGHTS)
    out = {f: int(round(raw[f] / total * 100)) for f in FEATURES}
    diff = 100 - sum(out.values())
    out[max(out, key=out.get)] += diff
    return out


def level(weight):
    return "High" if weight >= 20 else "Medium" if weight >= 12 else "Low"


def _num(txt):
    return float(txt.replace(",", ""))


def parse_requirements(text):
    """Extract weights, budget and constraints from free text."""
    t = (text or "").lower()
    pts = {f: 1.0 for f in FEATURES}
    pts["value"] = 0.6
    detected = []
    for f, words in KEYWORDS.items():
        for w in words:
            for m in re.finditer(r"\b" + re.escape(w) + r"\b", t):
                window = t[max(0, m.start() - 28):m.start()]
                bump = 3.0
                if any(s in window for s in STRONG_MODS):
                    bump += 1.5
                if any(s in window for s in SOFT_MODS):
                    bump -= 1.0
                pts[f] += bump
                detected.append(f)
    for name, boosts in PROFILE_BOOSTS.items():
        if name in t:
            for f, b in boosts.items():
                pts[f] += b
    out = {
        "weights": normalize_weights(pts), "budget": None, "min_storage": 0, "min_ram": 0,
        "need_5g": "5g" in t, "display_pref": "amoled" if "amoled" in t else "any",
    }
    m = re.search(r"(?:₹|rs\.?|inr|budget(?:\s+of|\s+is)?|under|within)\s*([\d,]+(?:\.\d+)?)\s*(k)?\b", t)
    if not m:
        m = re.search(r"\b(\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)\s*(k)\b", t)
    if m:
        val = _num(m.group(1)) * (1000 if m.group(2) else 1)
        if val >= 3000:
            out["budget"] = int(val)
    ram = re.search(r"(\d+)\s*gb\s*ram|ram\s*(?:of\s*)?(\d+)", t)
    if ram:
        out["min_ram"] = int(ram.group(1) or ram.group(2))
    t_no_ram = re.sub(r"\d+\s*gb\s*ram", "", t)
    sto = re.search(r"\b(64|128|256|512|1024)\s*gb\b", t_no_ram)
    if sto:
        out["min_storage"] = int(sto.group(1))
    out["levels"] = {f: level(out["weights"][f]) for f in FEATURES}
    out["detected"] = sorted(set(detected), key=FEATURES.index)
    return out


def build_params(budget=15000, weights=None, include_near=True, min_storage=0, min_ram=0,
                 need_5g=False, display_pref="any", usage=""):
    def to_int(v, d=0):
        try:
            return int(float(str(v).replace(",", "")))
        except (TypeError, ValueError):
            return d
    weights = weights or {}
    w = normalize_weights(weights) if sum(float(weights.get(f, 0) or 0) for f in FEATURES) > 0 \
        else (parse_requirements(usage)["weights"] if usage else dict(DEFAULT_WEIGHTS))
    return {"budget": max(3000, to_int(budget, 15000)), "weights": w, "include_near": bool(include_near),
            "min_storage": to_int(min_storage), "min_ram": to_int(min_ram), "need_5g": bool(need_5g),
            "display_pref": display_pref if display_pref in ("any", "amoled") else "any", "usage": (usage or "")[:600]}


def default_params():
    return build_params(15000, DEFAULT_WEIGHTS, min_storage=128)


ACTION_WEIGHT = {"save": 3.0, "select": 4.0, "compare": 2.0, "view": 1.0, "reject": -1.5}


def learn_weights(events, catalogue_means, current):
    """Suggest weights from interactions. `events` = [{action, s_camera, ...}, ...]."""
    pos = [e for e in events if ACTION_WEIGHT.get(e["action"], 0) > 0]
    if not pos:
        return None
    tw = sum(ACTION_WEIGHT[e["action"]] for e in pos)
    profile = {f: sum(ACTION_WEIGHT[e["action"]] * e["s_" + f] for e in pos) / tw for f in FEATURES}
    for e in events:  # rejected phones pull emphasis away from their strong areas
        if e["action"] == "reject":
            for f in FEATURES:
                profile[f] -= 0.15 * (e["s_" + f] - catalogue_means[f]) / max(1, len(events))
    learned = normalize_weights({f: max(profile[f] - catalogue_means[f], 0) + 5 for f in FEATURES})
    confidence = round(min(1.0, len(events) / 12), 2)
    blend = normalize_weights({f: (1 - 0.5 * confidence) * current[f] + 0.5 * confidence * learned[f] for f in FEATURES})
    top = sorted(FEATURES, key=lambda f: -learned[f])[:2]
    msg = (f"Your past selections indicate that {LABELS[top[0]].lower()} and {LABELS[top[1]].lower()} "
           f"have usually been important to you.")
    return {"learned": learned, "suggested": blend, "confidence": confidence, "message": msg, "events": len(events)}
