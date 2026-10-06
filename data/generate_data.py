"""Validate the maintained India-market catalogue without inventing phone records.

The catalogue is intentionally kept in phones.csv so model details, price references,
and source links can be reviewed before they are added to the app.
"""
import csv
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REQUIRED = {
    "id", "brand", "model", "price", "ram", "storage", "processor", "benchmark",
    "camera_main", "camera_front", "ois", "battery", "charging", "display_type",
    "display_size", "refresh_rate", "five_g", "updates_years", "operating_system",
    "source", "product_url", "last_updated",
}


def main():
    path = os.path.join(HERE, "phones.csv")
    with open(path, newline="", encoding="utf-8") as catalog:
        reader = csv.DictReader(catalog)
        missing = REQUIRED.difference(reader.fieldnames or [])
        if missing:
            raise ValueError(f"India-market catalogue is missing columns: {sorted(missing)}")
        phones = list(reader)
    if not phones:
        raise ValueError("India-market catalogue is empty.")
    print(f"Validated {len(phones)} India-market phone models in data/phones.csv.")
    print("No synthetic phone records were generated.")


if __name__ == "__main__":
    main()
