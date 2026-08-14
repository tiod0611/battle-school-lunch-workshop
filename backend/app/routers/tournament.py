from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import TournamentRun
from app.schemas import ErrorResponse, TodayKingResponse

router = APIRouter(prefix="/api/tournament", tags=["tournament"])


@router.get("/today", response_model=TodayKingResponse, responses={404: {"model": ErrorResponse}})
def get_today_tournament(db: Session = Depends(get_db)) -> TodayKingResponse:
    today = date.today()
    tournament_run = db.query(TournamentRun).filter(TournamentRun.run_date == today).one_or_none()
    if tournament_run is None:
        return JSONResponse(
            status_code=404,
            content={"detail": "오늘의 왕 준비 중", "code": "TOURNAMENT_NOT_READY"},
        )
    return TodayKingResponse.model_validate(tournament_run.result_json)