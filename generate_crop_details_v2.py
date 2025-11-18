# generate_crop_details_v2.py
"""
Creates crop_details.json for ALL crops in Crop_recommendation.csv,
with auto-generated:
 - desc
 - tips
 - fertilizer link
 - temperature range
 - soil requirements
"""

import pandas as pd
import json
import os
from urllib.parse import quote_plus


CSV_PATH = "Crop_recommendation.csv"
OUT_PATH = "crop_details.json"


# ----------------------------
# TEMPLATES BASED ON CROP TYPE
# ----------------------------
CROP_TYPE_RULES = {
    "rice":      ("Warm humid (20–30 °C)", "Clay/loam soil, high water, pH 5.5–7"),
    "maize":     ("Warm (18–27 °C)", "Well-drained loam, pH 5.5–7"),
    "wheat":     ("Cool (10–25 °C)", "Loam/clay loam, pH 6–7.5"),
    "barley":    ("Cool (12–25 °C)", "Well-drained loam, pH 6–7.5"),
    "cotton":    ("Warm (20–30 °C)", "Black soil/sandy loam, pH 5.5–7.5"),
    "sugarcane": ("Hot humid (20–35 °C)", "Deep loam soil, pH 6–7.5"),
    "millet":    ("Dry warm (20–30 °C)", "Poor sandy soil, drought-tolerant"),
    "sorghum":   ("Dry warm (20–32 °C)", "Loam, sandy loam, drought tolerant"),
    "soy":       ("Warm (20–30 °C)", "Loam soil, pH 6–7"),
    "groundnut": ("Warm (20–30 °C)", "Sandy loam, pH 6–7"),
    "potato":    ("Cool (12–25 °C)", "Light loam soil, pH 5–6.5"),
    "tomato":    ("Warm (20–28 °C)", "Well-drained loam, pH 6–7"),
    "onion":     ("Cool–warm (13–25 °C)", "Loose, sandy loam, pH 6–7"),
    "peas":      ("Cool (10–20 °C)", "Loamy soil, pH 6–7.5"),
    "chili":     ("Warm (20–30 °C)", "Loam, well-drained, pH 6–7"),
    "apple":     ("Cool temperate (5–20 °C)", "Well-drained loam, pH 6–7"),
    "mango":     ("Warm (24–30 °C)", "Deep loam soil, pH 5.5–7.5"),
    "banana":    ("Warm humid (20–35 °C)", "Rich loam, high organic matter, pH 6–7"),
    "papaya":    ("Warm (22–30 °C)", "Well-drained loam, pH 6–7"),
    "orange":    ("Subtropical (12–30 °C)", "Sandy loam, pH 5.5–7"),
    "grape":     ("Warm dry (15–30 °C)", "Well-drained loam, pH 6–7.5"),
    "coconut":   ("Tropical (22–32 °C)", "Sandy loam, pH 5.5–7"),
    "tea":       ("Cool humid (15–25 °C)", "Acidic soil, pH 4.5–5.5"),
    "coffee":    ("Warm highland (15–25 °C)", "Loam soil, pH 5–6.5"),
    "sunflower": ("Warm (20–28 °C)", "Well-drained loam, pH 6–7.5"),
}

# DEFAULTS
DEFAULT_TEMP = "Moderate (18–28 °C)"
DEFAULT_SOIL = "Well-drained loam, pH 6–7"

DEFAULT_TIPS = [
    "Use balanced fertilization based on soil tests.",
    "Ensure proper irrigation scheduling.",
    "Monitor pests and diseases regularly.",
    "Follow recommended spacing and planting guidelines."
]


def make_link(crop):
    return f"https://www.google.com/search?q={quote_plus(crop + ' fertilizer guide')}"


def auto_description(crop):
    return f"{crop.capitalize()} is suitable for cultivation under recommended climate and soil conditions."


def detect_conditions(crop_name):
    name = crop_name.lower()
    for key, (temp, soil) in CROP_TYPE_RULES.items():
        if key in name:
            return temp, soil
    return DEFAULT_TEMP, DEFAULT_SOIL


def main():
    if not os.path.exists(CSV_PATH):
        print("CSV not found:", CSV_PATH)
        return

    df = pd.read_csv(CSV_PATH)
    if "label" not in df.columns:
        print("CSV must contain 'label' column.")
        return

    crops = sorted(df["label"].unique())
    final = {}

    for crop in crops:
        temp, soil = detect_conditions(crop)
        final[crop.lower()] = {
            "name": crop,
            "desc": auto_description(crop),
            "fertilizer_link": make_link(crop),
            "tips": DEFAULT_TIPS,
            "temp_range": temp,
            "soil_requirements": soil
        }

    with open(OUT_PATH, "w", encoding="utf8") as f:
        json.dump(final, f, indent=2)

    print("Created crop_details.json with", len(final), "crops.")


if __name__ == "__main__":
    main()
