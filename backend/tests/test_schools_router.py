from fastapi.testclient import TestClient

from app.main import app
from app.routers import schools


def test_school_search_success(monkeypatch):
    def fake_search_schools(office_code, school_name, page, size):
        return (
            [
                {
                    "SD_SCHUL_CODE": "7010569",
                    "ATPT_OFCDC_SC_CODE": "B10",
                    "ATPT_OFCDC_SC_NM": "서울특별시교육청",
                    "SCHUL_NM": "서울고등학교",
                    "SCHUL_KND_SC_NM": "고등학교",
                    "LCTN_SC_NM": "서울특별시",
                    "FOND_SC_NM": "공립",
                }
            ],
            1,
        )

    monkeypatch.setattr(schools.neis_client, "search_schools", fake_search_schools)
    with TestClient(app) as client:
        response = client.get(
            "/api/schools/search", params={"keyword": "서울", "page": 1, "limit": 30}
        )
    assert response.status_code == 200
    body = response.json()
    assert body["limit"] == 20
    assert body["items"][0]["schoolName"] == "서울고등학교"


def test_school_search_validation():
    with TestClient(app) as client:
        response = client.get("/api/schools/search", params={"keyword": ""})
    assert response.status_code == 422


def test_school_search_neis_error(monkeypatch):
    def fake_search_schools(office_code, school_name, page, size):
        raise schools.neis_client.NeisApiError("ERROR-500", "NEIS 오류")

    monkeypatch.setattr(schools.neis_client, "search_schools", fake_search_schools)
    with TestClient(app) as client:
        response = client.get("/api/schools/search", params={"keyword": "서울"})
    assert response.status_code == 502
