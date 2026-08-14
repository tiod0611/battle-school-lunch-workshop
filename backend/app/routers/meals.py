from datetime import date, datetime

from fastapi import APIRouter, HTTPException, Query

from app import neis_client
from app.schemas import ErrorResponse, MealItem, MealSearchResponse, ValidationErrorResponse
from app.services.scoring import day_of_week_label, parse_menu_items

router = APIRouter(tags=["meals"])


@router.get(
    "/api/meals",
    response_model=MealSearchResponse,
    responses={422: {"model": ValidationErrorResponse}, 502: {"model": ErrorResponse}},
)
def get_meals(
    schoolCode: str = Query(...),
    officeCode: str = Query(...),
    from_: date = Query(..., alias="from"),
    to: date = Query(...),
) -> MealSearchResponse:
    if to < from_:
        raise HTTPException(status_code=422, detail="종료일은 시작일보다 빠를 수 없습니다.")
    if (to - from_).days > 31:
        raise HTTPException(status_code=422, detail="날짜 범위는 최대 31일까지 조회할 수 있습니다.")
    try:
        rows = neis_client.get_meals(officeCode, schoolCode, from_.isoformat(), to.isoformat())
    except neis_client.NeisApiError as exc:
        raise HTTPException(status_code=502, detail=exc.message) from exc
    meals = []
    school_name = ""
    for row in rows:
        school_name = row.get("SCHUL_NM", school_name)
        meal_date = datetime.strptime(row["MLSV_YMD"], "%Y%m%d")
        meals.append(
            MealItem(
                date=meal_date.date(),
                dayOfWeek=day_of_week_label(meal_date),
                menuItems=parse_menu_items(row.get("DDISH_NM")),
                calorie=row.get("CAL_INFO"),
                nutritionInfo=row.get("NTR_INFO"),
            )
        )
    return MealSearchResponse(
        schoolCode=schoolCode,
        officeCode=officeCode,
        schoolName=school_name,
        meals=meals,
        isEmpty=len(meals) == 0,
    )
