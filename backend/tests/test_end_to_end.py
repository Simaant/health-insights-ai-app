import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.utils.auth import VALID_TOKEN
from backend.utils.constants import ALL_NORMAL_MSG

client = TestClient(app)

def fake_run_agent(prompt: str) -> str:
    return "- LDL: 150.0 mg/dL (normal: 'max': 100)"

@pytest.fixture(autouse=True)
def patch_agent(monkeypatch):
    monkeypatch.setattr("backend.routes.report.run_agent", fake_run_agent)
    yield

def test_end_to_end_abnormal():
    headers = {"Authorization": f"Bearer {VALID_TOKEN}"}
    r = client.post("/upload", files={"file": ("report.txt", b"LDL: 150 mg/dL")}, headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert "LDL" in data["flagged"]
    assert data["flagged"]["LDL"]["value"] == 150.0

def test_end_to_end_all_normal():
    headers = {"Authorization": f"Bearer {VALID_TOKEN}"}
    r = client.post("/upload", files={"file": ("report.txt", b"LDL: 90 mg/dL")}, headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert data["recommendations"] == ALL_NORMAL_MSG
    assert data["flagged"] == {}
