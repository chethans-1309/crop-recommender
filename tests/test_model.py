# tests/test_model.py
import joblib
import numpy as np
import os

MODEL_PATH = "model.pkl"

def test_model_file_exists():
    assert os.path.exists(MODEL_PATH), f"{MODEL_PATH} not found. Run training script."

def test_model_predicts():
    data = joblib.load(MODEL_PATH)
    model = data["model"]
    label_encoder = data["label_encoder"]
    # sample input in the expected order (N,P,K,temperature,humidity,ph,rainfall)
    sample = np.array([[90, 40, 40, 25, 80, 6.5, 200]])
    pred_idx = model.predict(sample)[0]
    crop = label_encoder.inverse_transform([pred_idx])[0]
    assert isinstance(crop, (str,)), "Prediction not a string label"
