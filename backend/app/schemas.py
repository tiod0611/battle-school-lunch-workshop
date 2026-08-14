from datetime import date

from pydantic import BaseModel


class SchoolSummary(BaseModel):
    schoolCode: str
    officeCode: str
    officeName: str
    schoolName: str
    schoolKind: str
    region: str | None = None
    foundationType: str | None = None


class SchoolSearchResponse(BaseModel):
    items: list[SchoolSummary]
    page: int
    limit: int
    totalCount: int


class MealItem(BaseModel):
    date: date
    dayOfWeek: str
    menuItems: list[str]
    calorie: str | None = None
    nutritionInfo: str | None = None


class MealSearchResponse(BaseModel):
    schoolCode: str
    officeCode: str
    schoolName: str
    meals: list[MealItem]
    isEmpty: bool


class ScoreBreakdown(BaseModel):
    base: int
    seasonalIngredient: int
    nutritionBalance: int
    menuVariety: int
    processedFoodPenalty: int
    total: int


class TournamentSchool(BaseModel):
    schoolCode: str
    schoolName: str
    officeName: str
    menuItems: list[str]
    score: ScoreBreakdown


class TournamentMatch(BaseModel):
    matchId: str
    schoolA: TournamentSchool
    schoolB: TournamentSchool | None = None
    winnerSchoolCode: str
    isBye: bool


class TournamentRound(BaseModel):
    roundNumber: int
    roundName: str
    matches: list[TournamentMatch]


class TodayKingResponse(BaseModel):
    date: date
    totalParticipants: int
    champion: TournamentSchool
    bracket: list[TournamentRound]


class ValidationErrorResponse(BaseModel):
    detail: str


class ErrorResponse(BaseModel):
    detail: str
    code: str | None = None