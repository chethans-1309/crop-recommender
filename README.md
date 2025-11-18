# Crop Recommender (local)

Steps:
1. Create venv and install dependencies (see below).
2. Put `Crop_recommendation.csv` in project root.
3. Run `python train_and_save.py` to train and create `model.pkl`.
4. Run `python app.py` to start Flask backend on http://127.0.0.1:5000
5. Run `streamlit run streamlit_app.py` to start Streamlit UI.

Run tests:
- `pytest` from project root.
