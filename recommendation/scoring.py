"""Feature normalization and personalized scoring (Modules 4).

Every phone gets seven 0-100 sub-scores (min-max normalised over the WHOLE catalogue so
scores stay stable when the user changes filters). The personal score is the weighted
average of the sub-scores using the user's weights.
"""
import numpy as np
import pandas as pd
from config import FEATURES

SCORE_CURVE = 0.6
DISPLAY_QUALITY = {
    "LTPO AMOLED": 1.0, "Dynamic AMOLED 2X": 1.0, "Super AMOLED": 1.0,
    "AMOLED": 1.0, "OLED": 0.95, "pOLED": 0.95, "IPS LCD": 0.45, "LCD": 0.4,
}


def _norm(s, lo=None, hi=None):
    s = pd.to_numeric(s, errors="coerce").astype(float)
    lo = s.min() if lo is None else lo
    hi = s.max() if hi is None else hi
    if hi <= lo:
        return pd.Series(0.5, index=s.index)
    return ((s - lo) / (hi - lo)).clip(0, 1)


def compute_feature_scores(df):
    """Return a copy of df with s_camera ... s_value columns (0-100)."""
    d = df.copy()
    camera = 0.45 * _norm(np.log(d.camera_main)) + 0.30 * d.ois.astype(float) + 0.25 * _norm(d.camera_front)
    performance = 0.80 * _norm(d.benchmark) + 0.20 * _norm(d.ram)
    battery = 0.65 * _norm(d.battery) + 0.35 * _norm(d.charging)
    storage = _norm(np.log2(d.storage))
    display = (0.45 * d.display_type.map(DISPLAY_QUALITY).fillna(0.4)
               + 0.35 * _norm(d.refresh_rate) + 0.20 * _norm(d.display_size))
    software = 0.75 * _norm(d.updates_years) + 0.25 * d.five_g.astype(float)
    composite = (camera + performance + battery + storage + display + software) / 6
    value = _norm(np.log(composite.clip(lower=0.01) / d.price))
    parts = dict(camera=camera, performance=performance, battery=battery, storage=storage,
                 display=display, software=software, value=value)
    for k, v in parts.items():
        # concave transform (documented): lifts mid-range phones so scores use the full 0-100 range
        d["s_" + k] = (v.clip(0, 1) ** SCORE_CURVE * 100).round(1)
    return d


def personal_score(df, weights):
    """Weighted 0-100 score: sum(sub_score * weight) / sum(weights)."""
    total = float(sum(weights.get(f, 0) for f in FEATURES)) or 1.0
    d = df.copy()
    d["score"] = sum(d["s_" + f] * weights.get(f, 0) for f in FEATURES) / total
    d["score"] = d["score"].round(1)
    return d
