# generate_crop_details.py
"""
Generate crop_details.json from Crop_recommendation.csv

Outputs:
  - crop_details.json : mapping crop_name_lower -> {desc, fertilizer_link, tips: [..]}

Usage:
  python generate_crop_details.py
"""

import pandas as pd
import json
import os
from urllib.parse import quote_plus

CSV_PATH = "Crop_recommendation.csv"
OUT_PATH = "crop_details.json"


# keyword-based templates: for crop names containing any of the keywords, use that template
TEMPLATES = {
    "rice": {
        "desc": "Rice thrives in flooded or saturated soils with good nitrogen availability.",
        "tips": [
            "Maintain shallow flooding during early growth stages.",
            "Split nitrogen application: basal + top-dressing after tillering.",
            "Control weeds during the first 30 days for better yields.",
            "Monitor and manage pests and diseases in wet conditions."
        ]
    },
    "maize": {
        "desc": "Maize (corn) prefers well-drained soils and balanced NPK fertilization.",
        "tips": [
            "Use starter fertilizer at sowing and side-dress nitrogen during active growth.",
            "Plant at recommended spacing to improve airflow and reduce disease.",
            "Irrigate during tasseling and grain fill for best yields.",
            "Rotate with legumes to help maintain soil nitrogen."
        ]
    },
    "wheat": {
        "desc": "Wheat grows best in well-drained loamy soils with moderate moisture.",
        "tips": [
            "Apply nitrogen in split doses: at sowing and during tillering.",
            "Sow at recommended seeding rates and depth for your region.",
            "Monitor for rusts and fungal diseases and treat promptly.",
            "Use crop rotation to reduce soil-borne disease pressure."
        ]
    },
    "sugarcane": {
        "desc": "Sugarcane is a heavy feeder that needs regular nutrients and water.",
        "tips": [
            "Apply organic matter and balanced NPK; top-dress as crop grows.",
            "Ensure uniform irrigation and good drainage.",
            "Use disease-free setts at planting.",
            "Keep fields weed-free especially during the early months."
        ]
    },
    "cotton": {
        "desc": "Cotton prefers well-drained soils and benefits from balanced nutrients.",
        "tips": [
            "Ensure proper spacing and timely irrigation.",
            "Apply phosphorus at planting and side-dress nitrogen carefully.",
            "Scout regularly for bollworms and aphids.",
            "Use integrated pest management to reduce pesticide use."
        ]
    },
    "soy": {"desc": "Soybean (soy) fixes nitrogen and grows well in warm conditions.", "tips": [
        "Inoculate seed with rhizobia if soil lacks soybean history.",
        "Ensure even planting and maintain good soil moisture during flowering.",
        "Rotate with non-legume crops to break pest cycles.",
        "Apply potassium and phosphorus based on soil test."
    ]},
    "groundnut": {"desc": "Groundnut (peanut) prefers sandy loam and warm conditions.", "tips": [
        "Avoid waterlogging; ensure good drainage.",
        "Apply calcium and potassium for pod development.",
        "Use proper row spacing and timely weeding.",
        "Harvest when pods reach maturity to avoid quality loss."
    ]},
    "potato": {"desc": "Potato prefers cool climate and well-drained soils rich in organic matter.", "tips": [
        "Use certified seed tubers to avoid diseases.",
        "Maintain soil moisture especially during tuber formation.",
        "Hill up soil around stems to protect tubers.",
        "Apply balanced NPK with focus on potassium for tuber quality."
    ]},
    "tomato": {"desc": "Tomato grows well in fertile, well-drained soil with regular watering.", "tips": [
        "Provide staking or cages to support plants and reduce disease.",
        "Regularly remove lower leaves and monitor for blight.",
        "Feed with balanced fertilizer and additional potassium during fruiting.",
        "Ensure consistent irrigation to avoid blossom end rot."
    ]},
    "onion": {"desc": "Onion prefers well-drained soil and consistent moisture early on.", "tips": [
        "Avoid overwatering as bulbs form to prevent rot.",
        "Apply nitrogen during early growth, reduce towards bulb formation.",
        "Use raised beds for better drainage.",
        "Harvest when tops begin to fall and cure bulbs properly."
    ]},
    "orange": {"desc": "Orange (citrus) needs well-drained soil and steady irrigation.", "tips": [
        "Mulch to conserve soil moisture and suppress weeds.",
        "Apply micronutrients (Zn, Mn) when deficiency appears.",
        "Use drip irrigation for consistent water supply.",
        "Thin fruits if trees are overloaded to improve size."
    ]},
    "banana": {"desc": "Banana needs high humidity, rich soil and regular feeding.", "tips": [
        "Apply high potassium fertilizers during fruit development.",
        "Use mulch and maintain consistent soil moisture.",
        "Provide wind protection for bunches.",
        "Remove suckers to manage planting density."
    ]},
    "papaya": {"desc": "Papaya requires warm climate, well-drained soil and regular watering.", "tips": [
        "Protect young plants from strong winds.",
        "Feed regularly with balanced NPK during fruiting.",
        "Maintain even soil moisture to avoid fruit drop.",
        "Prune damaged or diseased branches promptly."
    ]},
    "banana": {"desc": "Banana needs high humidity and rich soil.", "tips": [
        "Maintain high K levels for fruit quality.",
        "Ensure regular irrigation and mulching.",
        "Control nematodes and fungal diseases.",
        "Plant disease-free suckers."
    ]},
    "grape": {"desc": "Grapes prefer well-drained soils and sunshine for ripening.", "tips": [
        "Train vines for good airflow and sunlight penetration.",
        "Control fungal disease with timely sprays.",
        "Register pruning time to balance growth and fruiting.",
        "Monitor soil fertility and apply potassium for sugar accumulation."
    ]},
    "mango": {"desc": "Mango prefers tropical/subtropical climate and deep well-drained soils.", "tips": [
        "Protect flowers from heavy rain and strong winds.",
        "Apply balanced fertilizer and micronutrients annually.",
        "Thin fruits if crop load is very heavy.",
        "Use mulch to conserve moisture in dry seasons."
    ]},
    "apple": {"desc": "Apple grows best in temperate climates with chilling hours.", "tips": [
        "Ensure correct rootstock-scion compatibility.",
        "Prune annually to maintain shape and light penetration.",
        "Manage pests like codling moth and diseases like scab.",
        "Apply potassium during fruit enlargement."
    ]},
    "coconut": {"desc": "Coconut thrives in coastal tropics with deep, well-drained soils.", "tips": [
        "Maintain regular irrigation in dry seasons.",
        "Apply balanced fertilization and mulch.",
        "Control pests like rhinoceros beetle and coconut mite.",
        "Intercrop with compatible short-duration crops."
    ]},
    "tea": {"desc": "Tea prefers acidic soils and high humidity, usually grown in hilly regions.", "tips": [
        "Maintain soil acidity (pH 4.5–5.5) for best growth.",
        "Regular pruning and plucking maintain yield.",
        "Use organic matter and mulching to protect roots.",
        "Control pests and diseases using integrated management."
    ]},
    "coffee": {"desc": "Coffee prefers shaded, well-drained soils in tropical highlands.", "tips": [
        "Provide shade for young plants and maintain humidity.",
        "Apply fertilizer based on soil tests.",
        "Prune regularly to maintain production canopy.",
        "Monitor for coffee berry borer and other pests."
    ]},
    "sunflower": {"desc": "Sunflower prefers full sun and well-drained soils.", "tips": [
        "Plant in full sunlight and good spacing.",
        "Manage weeds early to reduce competition.",
        "Ensure adequate phosphorus for root development.",
        "Harvest at the correct moisture level for seeds."
    ]},
    "millet": {"desc": "Millets are hardy cereals suited to dry conditions and low fertility soils.", "tips": [
        "Use recommended spacing and timely weed control.",
        "Apply phosphorus at sowing for better establishment.",
        "Millets usually need less water—avoid over-irrigation.",
        "Rotate with legumes to improve soil fertility."
    ]},
}

# fallback generic template
DEFAULT_TEMPLATE = {
    "desc": "A recommended crop. Follow local extension service guidance for best practices.",
    "tips": [
        "Use balanced fertilization based on soil test results.",
        "Ensure proper irrigation scheduling appropriate to the crop.",
        "Monitor pests and diseases and act early.",
        "Follow local recommended spacing and planting dates."
    ]
}


def make_fertilizer_link(crop_name: str) -> str:
    # simple Google search URL for fertilizer guide
    q = quote_plus(f"{crop_name} fertilizer guide")
    return f"https://www.google.com/search?q={q}"


def choose_template_for(crop_name: str):
    lower = crop_name.lower()
    for key, tpl in TEMPLATES.items():
        if key in lower:
            # copy so we don't mutate the original
            return {"desc": tpl["desc"], "tips": list(tpl["tips"])}
    # if nothing matched, return default
    return {"desc": DEFAULT_TEMPLATE["desc"], "tips": list(DEFAULT_TEMPLATE["tips"])}


def main():
    if not os.path.exists(CSV_PATH):
        print(f"ERROR: {CSV_PATH} not found. Put the dataset in project root.")
        return

    df = pd.read_csv(CSV_PATH)
    if "label" not in df.columns:
        print("ERROR: CSV must have column named 'label' containing crop names.")
        return

    crops = sorted(df["label"].dropna().unique())
    output = {}

    for crop in crops:
        tpl = choose_template_for(crop)
        output[crop.lower()] = {
            "name": crop,
            "desc": tpl["desc"],
            "fertilizer_link": make_fertilizer_link(crop),
            "tips": tpl["tips"]
        }

    # write JSON
    with open(OUT_PATH, "w", encoding="utf8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"Wrote {len(output)} crop entries to {OUT_PATH}")
    print("You can now edit the JSON file to refine descriptions and tips.")


if __name__ == "__main__":
    main()
