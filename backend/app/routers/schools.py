from fastapi import APIRouter, HTTPException, Query

from app import neis_client
from app.schemas import ErrorResponse, SchoolSearchResponse, SchoolSummary, ValidationErrorResponse

router = APIRouter(prefix="/api/schools", tags=["schools"])


@router.get(
    "/search",
    response_model=SchoolSearchResponse,
    responses={422: {"model": ValidationErrorResponse}, 502: {"model": ErrorResponse}},
)
def search_schools(
    keyword: str = Query(..., min_length=1),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1),
) -> SchoolSearchResponse:
    if not keyword.strip():
        raise HTTPException(status_code=422, detail="keyword는 비어 있을 수 없습니다.")
    try:
        rows, total_count = neis_client.search_schools(None, keyword.strip(), page, min(limit, 20))
    except neis_client.NeisApiError as exc:
        raise HTTPException(status_code=502, detail=exc.message) from exc
    items = [
        SchoolSummary(
            schoolCode=row["SD_SCHUL_CODE"],
            officeCode=row["ATPT_OFCDC_SC_CODE"],
            officeName=row["ATPT_OFCDC_SC_NM"],
            schoolName=row["SCHUL_NM"],
            schoolKind=row["SCHUL_KND_SC_NM"],
            region=row.get("LCTN_SC_NM"),
            foundationType=row.get("FOND_SC_NM"),
        )
        for row in rows
    ]
    return SchoolSearchResponse(items=items, page=page, limit=min(limit, 20), totalCount=total_count)