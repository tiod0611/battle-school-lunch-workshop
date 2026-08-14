from __future__ import annotations

import time
from collections.abc import Callable
from datetime import date
from typing import Any

import httpx

from app.config import get_settings

settings = get_settings()

BASE_URL = "https://open.neis.go.kr"
SUCCESS_CODES = {"INFO-000", "INFO-100", "INFO-300"}
EMPTY_CODE = "INFO-200"
RETRY_BACKOFFS = [0.5, 1.0]
DEFAULT_TIMEOUT = httpx.Timeout(connect=3.0, read=7.0, write=7.0, pool=7.0)


class NeisApiError(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")


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
        raise NeisApiError("NEIS_INVALID_RESPONSE", "NEIS 응답 형식이 올바르지 않습니다.")
    code = result.get("CODE", "")
    message = result.get("MESSAGE", "NEIS 응답 오류")
    if code == EMPTY_CODE:
        return [], 0
    if code not in SUCCESS_CODES:
        raise NeisApiError(code, message)
    rows: list[dict] = next((entry.get("row", []) for entry in data if "row" in entry), [])
    return rows, total_count


def _request(
    path: str, params: dict, root_key: str, client_factory: Callable[[], httpx.Client] | None = None
) -> tuple[list[dict], int]:
    client_factory = client_factory or (
        lambda: httpx.Client(base_url=BASE_URL, timeout=DEFAULT_TIMEOUT)
    )
    attempts = len(RETRY_BACKOFFS) + 1
    for attempt in range(attempts):
        try:
            with client_factory() as client:
                response = client.get(
                    path, params={"KEY": settings.neis_api_key, "Type": "json", **params}
                )
                if response.status_code >= 500:
                    raise httpx.HTTPStatusError(
                        "NEIS server error", request=response.request, response=response
                    )
                response.raise_for_status()
                return _extract_payload(response.json(), root_key)
        except (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError) as exc:
            retryable = isinstance(exc, (httpx.TimeoutException, httpx.NetworkError)) or (
                isinstance(exc, httpx.HTTPStatusError)
                and exc.response is not None
                and exc.response.status_code >= 500
            )
            if retryable and attempt < len(RETRY_BACKOFFS):
                time.sleep(RETRY_BACKOFFS[attempt])
                continue
            raise NeisApiError("NEIS_UPSTREAM_ERROR", "NEIS API 호출에 실패했습니다.") from exc
    raise NeisApiError("NEIS_UPSTREAM_ERROR", "NEIS API 호출에 실패했습니다.")


def search_schools(
    office_code: str | None, school_name: str | None, page: int, size: int
) -> tuple[list[dict], int]:
    params: dict[str, Any] = {"pIndex": page, "pSize": size}
    if office_code:
        params["ATPT_OFCDC_SC_CODE"] = office_code
    if school_name:
        params["SCHUL_NM"] = school_name
    return _request("/hub/schoolInfo", params, "schoolInfo")


def search_high_schools_by_office(office_code: str, page: int, size: int) -> tuple[list[dict], int]:
    params = {
        "pIndex": page,
        "pSize": size,
        "ATPT_OFCDC_SC_CODE": office_code,
        "SCHUL_KND_SC_NM": "고등학교",
    }
    return _request("/hub/schoolInfo", params, "schoolInfo")


def get_meals(office_code: str, school_code: str, from_date: str, to_date: str) -> list[dict]:
    params = {
        "pIndex": 1,
        "pSize": 1000,
        "ATPT_OFCDC_SC_CODE": office_code,
        "SD_SCHUL_CODE": school_code,
        "MMEAL_SC_CODE": "2",
        "MLSV_FROM_YMD": _to_yyyymmdd(from_date),
        "MLSV_TO_YMD": _to_yyyymmdd(to_date),
    }
    rows, _ = _request("/hub/mealServiceDietInfo", params, "mealServiceDietInfo")
    return rows


def _to_yyyymmdd(value: str | date) -> str:
    if isinstance(value, date):
        return value.strftime("%Y%m%d")
    return value.replace("-", "")
