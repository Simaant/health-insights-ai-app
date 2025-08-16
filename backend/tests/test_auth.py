from fastapi.testclient import TestClient
from backend.main import app
from backend.utils.auth import VALID_TOKEN
from backend.utils.constants import (
    ERROR_MISSING_TOKEN,
    ERROR_INVALID_TOKEN,
    NO_MARKERS_FOUND_MSG,
    ALL_NORMAL_MSG,
)

client = TestClient(app)

def test_upload_without_auth():
    response = client.post("/upload", files={"file": ("test.txt", b"LDL: 150 mg/dL")})
    assert response.status_code == 401
    assert ERROR_MISSING_TOKEN in response.text

def test_upload_with_bad_auth():
    headers = {"Authorization": "Bearer wrong-token"}
    response = client.post(
        "/upload",
        files={"file": ("test.txt", b"LDL: 150 mg/dL")},
        headers=headers
    )
    assert response.status_code == 401
    assert ERROR_INVALID_TOKEN in response.text

def test_upload_with_good_auth_abnormal_markers():
    headers = {"Authorization": f"Bearer {VALID_TOKEN}"}
    response = client.post(
        "/upload",
        files={"file": ("test.txt", b"LDL: 150 mg/dL")},
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "LDL" in data["flagged"]
    assert data["flagged"]["LDL"]["value"] == 150.0

def test_upload_with_good_auth_all_normal():
    headers = {"Authorization": f"Bearer {VALID_TOKEN}"}
    response = client.post(
        "/upload",
        files={"file": ("test.txt", b"LDL: 90 mg/dL")},
        headers=headers
    )
    data = response.json()
    assert response.status_code == 200
    assert data["recommendations"] == ALL_NORMAL_MSG
    assert data["flagged"] == {}

def test_upload_with_good_auth_no_markers():
    headers = {"Authorization": f"Bearer {VALID_TOKEN}"}
    response = client.post(
        "/upload",
        files={"file": ("test.txt", b"Completely unrelated text")},
        headers=headers
    )
    data = response.json()
    assert response.status_code == 200
    assert data["recommendations"] == NO_MARKERS_FOUND_MSG
    assert data["flagged"] == {}
