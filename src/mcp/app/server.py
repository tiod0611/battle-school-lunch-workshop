"""급식배틀 MCP 서버.

NEIS 공개 API를 이용해 학교 검색, 중식 급식 정보 조회 도구를 제공하는
Streamable HTTP 기반 MCP 서버. 기존 backend(FastAPI) API와 완전히 독립적으로
실행되며, 별도 Docker 컨테이너로 기동한다.
"""

from datetime import datetime

from mcp.server.fastmcp import FastMCP

from app import neis_client
from app.config import get_settings
from app.errors import MCPToolError, NotFoundError
from app.formatting import day_of_week_label, parse_menu_items
from app.validators import (
    validate_code,
    validate_date_range,
    validate_keyword,
    validate_page,
    validate_size,
)

settings = get_settings()

mcp = FastMCP(
    "school-lunch-battle",
    host=settings.mcp_host,
    port=settings.mcp_port,
    streamable_http_path="/mcp",
)


@mcp.tool(
    name="search_schools",
    description=(
        "학교 이름 일부를 입력해 후보 학교 목록을 검색합니다. "
        "결과의 schoolCode/officeCode는 get_meals 도구 호출에 그대로 사용합니다."
    ),
)
async def search_schools(keyword: str, page: int = 1, size: int = 20) -> dict:
    """학교명 일부로 학교를 검색한다.

    Args:
        keyword: 검색할 학교 이름의 일부 (예: "대구고등학교").
        page: 조회할 페이지 번호 (1부터 시작).
        size: 페이지당 결과 수 (최대 100).
    """
    try:
        clean_keyword = validate_keyword(keyword)
        page = validate_page(page)
        size = validate_size(size)

        rows, total_count = await neis_client.search_schools(clean_keyword, page, size)
        if not rows:
            raise NotFoundError(f"'{clean_keyword}'에 해당하는 학교 검색 결과가 없습니다. 학교명을 다시 확인해주세요.")

        items = [
            {
                "schoolCode": row["SD_SCHUL_CODE"],
                "officeCode": row["ATPT_OFCDC_SC_CODE"],
                "officeName": row["ATPT_OFCDC_SC_NM"],
                "schoolName": row["SCHUL_NM"],
                "schoolKind": row.get("SCHUL_KND_SC_NM"),
                "region": row.get("LCTN_SC_NM"),
                "foundationType": row.get("FOND_SC_NM"),
            }
            for row in rows
        ]
        return {"items": items, "page": page, "size": size, "totalCount": total_count}
    except MCPToolError:
        raise
    except Exception as exc:  # noqa: BLE001 - 예기치 못한 오류도 안전한 메시지로 변환
        raise MCPToolError("학교 검색 중 알 수 없는 오류가 발생했습니다.") from exc


@mcp.tool(
    name="get_meals",
    description=(
        "선택한 학교(schoolCode, officeCode)와 조회 기간(from_date, to_date)의 "
        "중식 급식 정보를 날짜별로 조회합니다. school_code/office_code는 "
        "search_schools 도구 결과에서 얻은 값을 사용해야 합니다."
    ),
)
async def get_meals(school_code: str, office_code: str, from_date: str, to_date: str) -> dict:
    """학교와 기간을 입력해 중식 급식 정보를 조회한다.

    Args:
        school_code: search_schools 결과의 schoolCode.
        office_code: search_schools 결과의 officeCode.
        from_date: 조회 시작일 (YYYY-MM-DD).
        to_date: 조회 종료일 (YYYY-MM-DD, from_date로부터 최대 31일 이내).
    """
    try:
        clean_school_code = validate_code(school_code, "school_code")
        clean_office_code = validate_code(office_code, "office_code")
        validate_date_range(from_date, to_date)

        rows = await neis_client.get_meals(clean_office_code, clean_school_code, from_date, to_date)
        if not rows:
            raise NotFoundError("해당 기간에 등록된 중식 급식 정보가 없습니다.")

        school_name = ""
        meals = []
        for row in rows:
            school_name = row.get("SCHUL_NM", school_name)
            meal_date = datetime.strptime(row["MLSV_YMD"], "%Y%m%d")
            meals.append(
                {
                    "date": meal_date.date().isoformat(),
                    "dayOfWeek": day_of_week_label(meal_date),
                    "menuItems": parse_menu_items(row.get("DDISH_NM")),
                    "calorie": row.get("CAL_INFO"),
                    "nutritionInfo": row.get("NTR_INFO"),
                }
            )
        return {
            "schoolCode": clean_school_code,
            "officeCode": clean_office_code,
            "schoolName": school_name,
            "meals": meals,
        }
    except MCPToolError:
        raise
    except Exception as exc:  # noqa: BLE001 - 예기치 못한 오류도 안전한 메시지로 변환
        raise MCPToolError("급식 정보 조회 중 알 수 없는 오류가 발생했습니다.") from exc


# uvicorn 등 ASGI 서버로 기동할 때 사용하는 앱 (예: `uvicorn app.server:app`).
app = mcp.streamable_http_app()


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
