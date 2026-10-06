"""Central configuration for Phone Nexora."""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database", "smartphone.db")
PHONES_CSV = os.path.join(BASE_DIR, "data", "phones.csv")
PRICE_CSV = os.path.join(BASE_DIR, "data", "price_history.csv")
R_OUTPUT_DIR = os.path.join(BASE_DIR, "static", "r_output")
SECRET_KEY = os.environ.get("SECRET_KEY", "change-me-in-production")

# The seven decision criteria (order = spectrum order in the UI)
FEATURES = ["camera", "performance", "battery", "storage", "display", "software", "value"]
LABELS = {
    "camera": "Camera", "performance": "Performance", "battery": "Battery",
    "storage": "Storage", "display": "Display", "software": "Software", "value": "Value",
}
COLORS = {
    "camera": "#C65C7A", "performance": "#5D6FC4", "battery": "#2E9A76",
    "storage": "#3F8CAD", "display": "#C28A30", "software": "#C16D4F", "value": "#178B84",
}
DEFAULT_WEIGHTS = {"camera": 25, "performance": 20, "battery": 20, "storage": 10,
                   "display": 10, "software": 5, "value": 10}

NEAR_BUDGET_TOLERANCE = 0.10   # up to 10% above budget = "near budget"
NEAR_BUDGET_PENALTY = 4.0      # rank penalty (points) for near-budget phones
STRONG = 70                    # sub-score treated as a strength
WEAK = 45                      # sub-score treated as a weakness
STRONG_REQUIREMENT = 65        # used by the conflict engine
TOP_N = 10
DEFAULT_USER_ID = 1
STALE_AFTER_DAYS = 30
LEGACY_SAMPLE_SOURCE = "Sample dataset (replace with authorized feed)"
INDIA_CATALOG_SOURCE = "India-market reference; indicative launch price not a live retailer quote"


def inr(n):
    """Indian-grouped rupees, e.g. 1234567 -> ₹12,34,567."""
    try:
        s = str(int(round(float(n))))
    except (TypeError, ValueError):
        return "₹–"
    if len(s) <= 3:
        return "₹" + s
    head, tail = s[:-3], s[-3:]
    parts = []
    while len(head) > 2:
        parts.insert(0, head[-2:])
        head = head[:-2]
    if head:
        parts.insert(0, head)
    return "₹" + ",".join(parts + [tail])
