"""Smartphone data management (Module 2): loading, caching and lookup."""
import numpy as np
import pandas as pd
from database import database as db
from recommendation.scoring import compute_feature_scores
from config import FEATURES, LEGACY_SAMPLE_SOURCE

_cache = {"scored": None}


def invalidate():
    _cache["scored"] = None


def get_scored():
    if _cache["scored"] is None:
        df = db.phones_df().dropna(subset=["price", "battery", "storage"])  # basic data cleaning
        df = df[df["source"] != LEGACY_SAMPLE_SOURCE]
        df = df.drop_duplicates(subset=["brand", "model"])
        _cache["scored"] = compute_feature_scores(df)
    return _cache["scored"]


def catalogue_means():
    d = get_scored()
    return {f: float(d["s_" + f].mean()) for f in FEATURES}


def get_phone(pid):
    d = get_scored()
    r = d[d.id == pid]
    return None if r.empty else r.iloc[0].to_dict()


def get_phones(ids):
    d = get_scored().set_index("id")
    return [dict(d.loc[i], id=i) for i in ids if i in d.index]


def similar_phones(pid, n=4):
    """k-nearest phones in sub-score space within +/-25% price (scikit-learn)."""
    from sklearn.neighbors import NearestNeighbors
    d = get_scored()
    base = d[d.id == pid]
    if base.empty:
        return []
    price = float(base.price.iloc[0])
    pool = d[(d.price.between(price * 0.75, price * 1.25))]
    cols = ["s_" + f for f in FEATURES]
    if len(pool) < 2:
        return []
    nn = NearestNeighbors(n_neighbors=min(n + 1, len(pool))).fit(pool[cols].values)
    _, idx = nn.kneighbors(base[cols].values)
    out = pool.iloc[idx[0]]
    return [r.to_dict() for _, r in out.iterrows() if r["id"] != pid][:n]
