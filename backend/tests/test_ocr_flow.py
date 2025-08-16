import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.utils.auth import VALID_TOKEN
from backend.utils.constants import ALL_NORMAL_MSG, NO_MARKERS_FOUND_MSG

client = TestClient(app)

@pytest.fixture(autouse=True)
def patch_agent(monkeypatch):
    def fake_run_agent(prompt: str) -> str:
        return "- LDL: 150.0 mg/dL (normal: 'max': 100)"
    monkeypatch.setattr("backend.routes.report.run_agent", fake_run_agent)
    yield

def test_pdf_upload_with_abnormal_marker(monkeypatch):
    def fake_ocr_any(file_bytes, filename, content_type):
        return "LDL: 150 mg/dL"
    monkeypatch.setattr("backend.routes.report.ocr_any", fake_ocr_any)

    headers = {"Authorization": f"Bearer {VALID_TOKEN}"}
    files = {"file": ("report.pdf", b"%PDF-FAKE", "application/pdf")}
    r = client.post("/upload", files=files, headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert "LDL" in data["flagged"]
    assert data["flagged"]["LDL"]["value"] == 150.0

def test_image_upload_all_normal(monkeypatch):
    def fake_ocr_any(file_bytes, filename, content_type):
        return "LDL: 90 mg/dL"
    monkeypatch.setattr("backend.routes.report.ocr_any", fake_ocr_any)

    headers = {"Authorization": f"Bearer {VALID_TOKEN}"}
    files = {"file": ("photo.jpg", b"\xff\xd8\xff\xdbFAKEJPEG", "image/jpeg")}
    r = client.post("/upload", files=files, headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert data["recommendations"] == ALL_NORMAL_MSG
    assert data["flagged"] == {}

def test_pdf_upload_no_markers(monkeypatch):
    def fake_ocr_any(file_bytes, filename, content_type):
        return "Random text with no labs."
    monkeypatch.setattr("backend.routes.report.ocr_any", fake_ocr_any)

    headers = {"Authorization": f"Bearer {VALID_TOKEN}"}
    files = {"file": ("something.pdf", b"%PDF-FAKE", "application/pdf")}
    r = client.post("/upload", files=files, headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert data["recommendations"] == NO_MARKERS_FOUND_MSG
    assert data["flagged"] == {}
