import os
import sys

from fastapi.testclient import TestClient

# Ensure app and chunking are importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app

client = TestClient(app)




def test_restart_server():
    """Test the restart server endpoint"""
    response = client.post("/restart_server")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "Server is restarting"}





def test_speech_endpoint_v1_audio_speech():
    """Test the speech endpoint"""
    # Short text (no batching)
    response = client.post("/v1/audio/speech", json={"input": "Hello world!", "voice": "default"})
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("audio/")

    # Long text (should trigger batching)
    long_text = "Hello world! " * 100
    response = client.post("/v1/audio/speech", json={"input": long_text, "voice": "default"})
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("audio/")


def test_speech_endpoint_legacy():
    """Test the legacy speech endpoint"""
    # Short text
    response = client.post("/speak", json={"text": "Legacy endpoint test.", "voice": "default"})
    assert response.status_code == 200
    # Should return JSON with output_file
    data = response.json()
    assert data["status"] == "ok"
    assert "output_file" in data

    # # Long text (should trigger batching)
    # long_text = "Legacy endpoint test. " * 100
    # response = client.post("/speak", json={"text": long_text, "voice": "default"})
    # assert response.status_code == 200
    # # Should return a file (joined wav)
    # assert response.headers["content-type"].startswith("audio/") 