# tests/test_flask_api.py
import pytest
from app import app as flask_app

@pytest.fixture
def client():
    flask_app.config['TESTING'] = True
    with flask_app.test_client() as client:
        yield client

def test_ping_root(client):
    res = client.get('/')
    assert res.status_code == 200

def test_predict_json(client):
    payload = {
        "N": 90, "P": 40, "K": 40,
        "temperature": 25, "humidity": 80, "ph": 6.5, "rainfall": 200
    }
    res = client.post('/predict', json=payload)
    assert res.status_code == 200
    data = res.get_json()
    assert "recommended_crop" in data
