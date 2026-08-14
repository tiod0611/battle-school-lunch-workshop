"""NEIS 공개 API(`data/openapi.json`) 호출 클라이언트.

backend/app/neis_client.py 와 동일한 응답 파싱/재시도 정책을 따르되,
MCP 도구는 비동기로 동작하므로 httpx.AsyncClient 기반으로 재작성했다.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from datetime import date

import httpx

from app.config import get_settings
from app.errors import UpstreamError

BASE_URL = "https://open.neis.go.kr"
SUCCESS_CODES = {"INFO-000", "INFO-100", "INFO-300"}
EMPTY_CODE = "INFO-200"
RETRY_BACKOFFS = [0.5, 1.0]
DEFAULT_TIMEOUT = httpx.Timeout(connect=3.0, read=7.0, write=7.0, pool=7.0)

# 실패 시 사용자에게 노출할 고정 메시지. 원본 예외 메시지는 절대 포함하지 않는다.
UPSTREAM_ERROR_MESSAGE = "NEIS 공공데이터 API 호출에 실패했습니다. 잠시 후 다시 시도해주세요."


def _extract_payload(payload: dict, root_key: str) -> tuple[list[dict], int]:
    data = payload.get(root_key)
    if not data:
        return [], 0
    head = next((entry.get("head") for entry in data if "head" in entry), None)
    if not head:
        return [], 0
    result = None
    total_count = 0
    for item in head:
        if "RESULT" in item:
            result = item["RESULT"]
        if "list_total_count" in item:
            total_count = item["list_total_count"]
    if result is None:
        raise UpstreamError(UPSTREAM_ERROR_MESSAGE)
    code = result.get("CODE", "")
    if code == EMPTY_CODE:
        return [], 0
    if code not in SUCCESS_CODES:
        raise UpstreamError(UPSTREAM_ERROR_MESSAGE)
    rows = next((entry.get("row", []) for entry in data if "row" in entry), [])
    return rows, total_count


async def _request(
    path: str,
    params: dict,
    root_key: str,
    client_factory: Callable[[], httpx.AsyncClient] | None = None,
    sleep: Callable[[float], Awaitable[None]] | None = None,
) -> tuple[list[dict], int]:
    settings = get_settings()
    client_factory = client_factory or (lambda: httpx.AsyncClient(base_url=BASE_URL, timeout=DEFAULT_TIMEOUT))
    if sleep is None:
        import anyio

        sleep = anyio.sleep
    attempts = len(RETRY_BACKOFFS) + 1
    for attempt in range(attempts):
        try:
            async with client_factory() as client:
                response = await client.get(path, params={"KEY": settings.neis_api_key, "Type": "json", **params})
                if response.status_code >= 500:
                    raise httpx.HTTPStatusError("NEIS server error", request=response.request, response=response)
                response.raise_for_status()
                return _extract_payload(response.json(), root_key)
        except (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError) as exc:
            retryable = isinstance(exc, (httpx.TimeoutException, httpx.NetworkError)) or (
                isinstance(exc, httpx.HTTPStatusError) and exc.response is not None and exc.response.status_code >= 500
            )
            if retryable and attempt < len(RETRY_BACKOFFS):
                await sleep(RETRY_BACKOFFS[attempt])
                continue
            raise UpstreamError(UPSTREAM_ERROR_MESSAGE) from exc


async def search_schools(school_name: str, page: int, size: int) -> tuple[list[dict], int]:
    params = {"pIndex": page, "pSize": size, "SCHUL_NM": school_name}
    return await _request("/hub/schoolInfo", params, "schoolInfo")


async def get_meals(office_code: str, school_code: str, from_date: str, to_date: str) -> list[dict]:
    params = {
        "pIndex": 1,
        "pSize": 1000,
        "ATPT_OFCDC_SC_CODE": office_code,
        "SD_SCHUL_CODE": school_code,
        "MMEAL_SC_CODE": "2",
        "MLSV_FROM_YMD": _to_yyyymmdd(from_date),
        "MLSV_TO_YMD": _to_yyyymmdd(to_date),
    }
    rows, _ = await _request("/hub/mealServiceDietInfo", params, "mealServiceDietInfo")
    return rows


def _to_yyyymmdd(value: str | date) -> str:
    if isinstance(value, date):
        return value.strftime("%Y%m%d")
    return value.replace("-", "")
