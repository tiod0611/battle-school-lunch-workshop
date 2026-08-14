from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.database import Base, SessionLocal, engine
from app.neis_client import NeisApiError
from app.routers import meals, schools, tournament
from app.scheduler import ensure_today_tournament, start_scheduler, stop_scheduler

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        ensure_today_tournament(db)
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(title="급식배틀 백엔드 API", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)
app.include_router(schools.router)
app.include_router(meals.router)
app.include_router(tournament.router)


@app.exception_handler(NeisApiError)
async def handle_neis_error(_: Request, exc: NeisApiError) -> JSONResponse:
    return JSONResponse(status_code=502, content={"detail": exc.message, "code": exc.code})