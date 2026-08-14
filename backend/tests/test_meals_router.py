from fastapi.testclient import TestClient

from app.main import app
from app.routers import meals


def test_meals_success(monkeypatch):
    def fake_get_meals(office_code, school_code, from_date, to_date):
        return [
            {
                "SCHUL_NM": "서울고등학교",
                "MLSV_YMD": "20260814",
                "DDISH_NM": "현미밥<br/>미역국",
                "CAL_INFO": "800 Kcal",
                "NTR_INFO": "탄수화물(g) 80 단백질(g) 20 지방(g) 15",
            }
        ]

    monkeypatch.setattr(meals.neis_client, "get_meals", fake_get_meals)
    with TestClient(app) as client:
        response = client.get(
            "/api/meals",
            params={
                "schoolCode": "7010569",
                "officeCode": "B10",
                "from": "2026-08-14",
                "to": "2026-08-14",
            },
        )
    assert response.status_code == 200
    assert response.json()["meals"][0]["menuItems"] == ["현미밥", "미역국"]


def test_meals_invalid_date_range():
    with TestClient(app) as client:
        response = client.get(
            "/api/meals",
            params={
                "schoolCode": "7010569",
                "officeCode": "B10",
                "from": "2026-08-15",
                "to": "2026-08-14",
            },
        )
    assert response.status_code == 422


def test_meals_neis_error(monkeypatch):
    def fake_get_meals(office_code, school_code, from_date, to_date):
        raise meals.neis_client.NeisApiError("ERROR-500", "NEIS 오류")

    monkeypatch.setattr(meals.neis_client, "get_meals", fake_get_meals)
    with TestClient(app) as client:
        response = client.get(
            "/api/meals",
            params={
                "schoolCode": "7010569",
                "officeCode": "B10",
                "from": "2026-08-14",
                "to": "2026-08-14",
            },
        )
    assert response.status_code == 502
