# train_and_save.py
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, classification_report
import joblib
import os

DATA_PATH = "Crop_recommendation.csv"
MODEL_PATH = "model.pkl"
RANDOM_STATE = 42
TEST_SIZE = 0.20

def load_data(path=DATA_PATH):
    if not os.path.exists(path):
        raise FileNotFoundError(f"{path} not found. Put CSV in project root.")
    df = pd.read_csv(path)
    return df

def prepare_data(df):
    # expected columns: N,P,K,temperature,humidity,ph,rainfall,label
    X = df.drop("label", axis=1)
    y = df["label"]
    le = LabelEncoder()
    y_enc = le.fit_transform(y)
    return X, y_enc, le

def train_and_save(X, y, le, model_path=MODEL_PATH):
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
    )
    model = RandomForestClassifier(n_estimators=100, random_state=RANDOM_STATE)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"Test Accuracy: {acc:.4f}")
    print(classification_report(y_test, y_pred, zero_division=0))

    # Save both model and label encoder together
    joblib.dump({"model": model, "label_encoder": le}, model_path)
    print(f"Saved model and label encoder to: {model_path}")

def main():
    df = load_data()
    X, y, le = prepare_data(df)
    train_and_save(X, y, le)

if __name__ == "__main__":
    main()
