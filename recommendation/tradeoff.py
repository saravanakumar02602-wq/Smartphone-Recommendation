"""Trade-off analyzer (Module 5): strengths, weaknesses and a plain-language summary."""
from config import FEATURES, LABELS, COLORS, STRONG, WEAK


def _join(names):
    names = [n.lower() for n in names]
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]


def analyze(p, weights):
    bars = [{"key": f, "label": LABELS[f], "score": p["s_" + f], "weight": weights[f], "color": COLORS[f]}
            for f in FEATURES]
    strong = sorted([b for b in bars if b["score"] >= STRONG], key=lambda b: -b["score"])
    weak = sorted([b for b in bars if b["score"] <= WEAK or (b["weight"] >= 15 and b["score"] < 55)],
                  key=lambda b: b["score"])
    if strong and weak:
        s = (f"This phone scores strongly for {_join([b['label'] for b in strong[:3]])} but has "
             f"comparatively lower {_join([b['label'] for b in weak[:2]])}.")
    elif strong:
        s = f"A well-rounded choice that stands out for {_join([b['label'] for b in strong[:3]])}."
    elif weak:
        s = f"Mid-range overall, with lower {_join([b['label'] for b in weak[:2]])}."
    else:
        s = "A balanced phone without major strengths or weaknesses."
    return {"bars": bars, "strengths": [b["label"] for b in strong], "weaknesses": [b["label"] for b in weak], "summary": s}
