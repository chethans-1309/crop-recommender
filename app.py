# app.py
import os
import json
import sqlite3
from datetime import datetime
import io
import csv

from flask import Flask, request, render_template, jsonify, send_file
import joblib
import numpy as np

# ---------------- CONFIG ----------------
MODEL_PATH = "model.pkl"
DB_PATH = "predictions.db"
CROP_DETAILS_PATH = "crop_details.json"

# The feature order your model expects:
FEATURE_NAMES = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]
# ----------------------------------------

app = Flask(__name__)

# ----- Load model and label encoder -----
if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(f"{MODEL_PATH} not found. Run train_and_save.py to create it.")

saved = joblib.load(MODEL_PATH)
model = saved.get("model")
label_encoder = saved.get("label_encoder")

if model is None or label_encoder is None:
    raise ValueError("model.pkl must contain both 'model' and 'label_encoder' saved as a dict.")

# ----- Load crop details JSON (if available) -----
CROP_DETAILS = {}
if os.path.exists(CROP_DETAILS_PATH):
    try:
        with open(CROP_DETAILS_PATH, "r", encoding="utf8") as f:
            CROP_DETAILS = json.load(f)
    except Exception as e:
        print("Failed to load crop_details.json:", e)
        CROP_DETAILS = {}
# Fallback default
if "default" not in CROP_DETAILS:
    CROP_DETAILS["default"] = {
        "desc": "No extended info available for this crop.",
        "fertilizer_link": "https://www.google.com/search?q=fertilizer+guide",
        "tips": ["Maintain proper irrigation and nutrient levels."]
    }

# ----- Initialize (or create) SQLite DB -----
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            N REAL, P REAL, K REAL,
            temperature REAL, humidity REAL, ph REAL, rainfall REAL,
            recommended_crop TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

def log_prediction(values: dict, crop_name: str):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            INSERT INTO predictions (timestamp, N, P, K, temperature, humidity, ph, rainfall, recommended_crop)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.utcnow().isoformat(),
            values.get("N"), values.get("P"), values.get("K"),
            values.get("temperature"), values.get("humidity"), values.get("ph"), values.get("rainfall"),
            crop_name
        ))
        conn.commit()
    except Exception as e:
        print("Failed to log prediction to DB:", e)
    finally:
        try:
            conn.close()
        except Exception:
            pass

# ----- Routes -----
@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/predict", methods=["POST"])
def api_predict():
    try:
        js = request.get_json(force=True)
        if not isinstance(js, dict):
            return jsonify({"error": "Invalid JSON body"}), 400

        # validate and collect values in model order
        vals = {}
        for k in FEATURE_NAMES:
            if k not in js:
                return jsonify({"error": f"Missing field: {k}"}), 400
            try:
                vals[k] = float(js.get(k))
            except Exception:
                return jsonify({"error": f"Field {k} must be numeric"}), 400

        # prepare input array and predict
        arr = np.array([vals[k] for k in FEATURE_NAMES]).reshape(1, -1)
        pred_idx = model.predict(arr)[0]
        crop = label_encoder.inverse_transform([pred_idx])[0]

        # feature importances (if available)
        try:
            fi = model.feature_importances_
            fi_list = [{"name": FEATURE_NAMES[i], "importance": float(fi[i])} for i in range(len(FEATURE_NAMES))]
            fi_list = sorted(fi_list, key=lambda x: x["importance"], reverse=True)
        except Exception:
            fi_list = [{"name": n, "importance": 0.0} for n in FEATURE_NAMES]

        # crop details from JSON (case-insensitive match)
        crop_key = str(crop).lower()
        crop_details = CROP_DETAILS.get(crop_key, CROP_DETAILS.get("default", {}))

        # log prediction (best-effort)
        try:
            log_prediction(vals, crop)
        except Exception as e:
            print("Log error:", e)

        return jsonify({
            "recommended_crop": str(crop),
            "feature_importances": fi_list,
            "crop_details": crop_details
        })

    except Exception as e:
        print("Server error in /predict:", e)
        return jsonify({"error": str(e)}), 500

@app.route("/recent", methods=["GET"])
def recent():
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT id, timestamp, N, P, K, temperature, humidity, ph, rainfall, recommended_crop FROM predictions ORDER BY id DESC LIMIT 100")
        rows = c.fetchall()
        columns = ["id","timestamp","N","P","K","temperature","humidity","ph","rainfall","recommended_crop"]
        results = [dict(zip(columns, r)) for r in rows]
        conn.close()
        return jsonify({"recent": results})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/download_predictions", methods=["GET"])
def download_predictions():
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT id, timestamp, N, P, K, temperature, humidity, ph, rainfall, recommended_crop FROM predictions ORDER BY id DESC")
        rows = c.fetchall()
        conn.close()

        si = io.StringIO()
        cw = csv.writer(si)
        cw.writerow(["id","timestamp","N","P","K","temperature","humidity","ph","rainfall","recommended_crop"])
        cw.writerows(rows)
        output = io.BytesIO()
        output.write(si.getvalue().encode('utf-8'))
        output.seek(0)
        return send_file(output, mimetype="text/csv", as_attachment=True, download_name="predictions.csv")
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ----------------- Run -----------------
if __name__ == "__main__":
    app.run(debug=True, port=5000)
