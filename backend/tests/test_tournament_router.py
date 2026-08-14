from contextlib import asynccontextmanager
from datetime import date

from fastapi.testclient import TestClient

from app.database import Base, SessionLocal, engine
from app.main import app
from app.models import TournamentRun


@asynccontextmanager
async def noop_lifespan(app):
    yield


def setup_function():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def test_tournament_not_ready():
    app.router.lifespan_context = noop_lifespan
    with TestClient(app) as client:
        response = client.get("/api/tournament/today")
    assert response.status_code == 404
    assert response.json()["code"] == "TOURNAMENT_NOT_READY"


def test_tournament_today_success():
    payload = {
        "date": date.today().isoformat(),
        "totalParticipants": 2,
        "champion": {
            "schoolCode": "001",
            "schoolName": "우승고",
            "officeName": "서울특별시교육청",
            "menuItems": ["현미밥"],
            "score": {
                "base": 20,
                "seasonalIngredient": 10,
                "nutritionBalance": 30,
                "menuVariety": 5,
                "processedFoodPenalty": 0,
                "total": 65,
            },
        },
        "bracket": [
            {
                "roundNumber": 1,
                "roundName": "결승",
                "matches": [
                    {
                        "matchId": "R1-M1",
                        "schoolA": {
                            "schoolCode": "001",
                            "schoolName": "우승고",
                            "officeName": "서울특별시교육청",
                            "menuItems": ["현미밥"],
                            "score": {
                                "base": 20,
                                "seasonalIngredient": 10,
                                "nutritionBalance": 30,
                                "menuVariety": 5,
                                "processedFoodPenalty": 0,
                                "total": 65,
                            },
                        },
                        "schoolB": {
                            "schoolCode": "002",
                            "schoolName": "준우승고",
                            "officeName": "부산광역시교육청",
                            "menuItems": ["백미밥"],
                            "score": {
                                "base": 20,
                                "seasonalIngredient": 0,
                                "nutritionBalance": 20,
                                "menuVariety": 5,
                                "processedFoodPenalty": -5,
                                "total": 40,
                            },
                        },
                        "winnerSchoolCode": "001",
                        "isBye": False,
                    }
                ],
            }
        ],
    }
    with SessionLocal() as db:
        db.add(
            TournamentRun(run_date=date.today(), champion_school_code="001", result_json=payload)
        )
        db.commit()
    app.router.lifespan_context = noop_lifespan
    with TestClient(app) as client:
        response = client.get("/api/tournament/today")
    assert response.status_code == 200
    assert response.json()["champion"]["schoolName"] == "우승고"
