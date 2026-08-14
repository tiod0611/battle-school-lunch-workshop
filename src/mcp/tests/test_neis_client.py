import httpx
import pytest
import respx

from app import neis_client
from app.errors import UpstreamError

SEARCH_URL = "https://open.neis.go.kr/hub/schoolInfo"
MEALS_URL = "https://open.neis.go.kr/hub/mealServiceDietInfo"


def _school_info_payload(rows: list[dict], total_count: int) -> dict:
    return {
        "schoolInfo": [
            {"head": [{"list_total_count": total_count}, {"RESULT": {"CODE": "INFO-000", "MESSAGE": "정상"}}]},
            {"row": rows},
        ]
    }


def _empty_payload(root_key: str) -> dict:
    return {root_key: [{"RESULT": {"CODE": "INFO-200", "MESSAGE": "해당하는 데이터가 없습니다."}}]}


@respx.mock
async def test_search_schools_returns_rows_and_total_count():
    respx.get(SEARCH_URL).mock(
        return_value=httpx.Response(
            200,
            json=_school_info_payload(
                [
                    {
                        "SD_SCHUL_CODE": "7240059",
                        "ATPT_OFCDC_SC_CODE": "D10",
                        "ATPT_OFCDC_SC_NM": "대구광역시교육청",
                        "SCHUL_NM": "대구고등학교",
                        "SCHUL_KND_SC_NM": "고등학교",
                    }
                ],
                1,
            ),
        )
    )

    rows, total_count = await neis_client.search_schools("대구고등학교", 1, 20)

    assert total_count == 1
    assert rows[0]["SCHUL_NM"] == "대구고등학교"


@respx.mock
async def test_search_schools_empty_result_returns_empty_list():
    respx.get(SEARCH_URL).mock(return_value=httpx.Response(200, json=_empty_payload("schoolInfo")))

    rows, total_count = await neis_client.search_schools("존재하지않는학교이름", 1, 20)

    assert rows == []
    assert total_count == 0


@respx.mock
async def test_search_schools_neis_error_code_raises_upstream_error():
    respx.get(SEARCH_URL).mock(
        return_value=httpx.Response(
            200,
            json={
                "schoolInfo": [
                    {"head": [{"RESULT": {"CODE": "ERROR-300", "MESSAGE": "필수 값이 누락되어 있습니다."}}]}
                ]
            },
        )
    )

    with pytest.raises(UpstreamError) as exc_info:
        await neis_client.search_schools("대구고등학교", 1, 20)

    # 원본 NEIS 오류 메시지가 아니라 고정된 안전 메시지만 노출되어야 한다.
    assert "NEIS" in str(exc_info.value)
    assert "ERROR-300" not in str(exc_info.value)


@respx.mock
async def test_search_schools_http_5xx_retries_then_raises_upstream_error():
    route = respx.get(SEARCH_URL).mock(return_value=httpx.Response(500))

    with pytest.raises(UpstreamError):
        await neis_client.search_schools("대구고등학교", 1, 20)

    # 최초 시도 + 재시도 2회 = 3회 호출되어야 한다.
    assert route.call_count == 3


@respx.mock
async def test_search_schools_timeout_raises_upstream_error_without_leaking_details():
    respx.get(SEARCH_URL).mock(side_effect=httpx.ConnectTimeout("connect timed out"))

    with pytest.raises(UpstreamError) as exc_info:
        await neis_client.search_schools("대구고등학교", 1, 20)

    assert "connect timed out" not in str(exc_info.value)


@respx.mock
async def test_get_meals_returns_rows():
    respx.get(MEALS_URL).mock(
        return_value=httpx.Response(
            200,
            json={
                "mealServiceDietInfo": [
                    {"head": [{"list_total_count": 1}, {"RESULT": {"CODE": "INFO-000", "MESSAGE": "정상"}}]},
                    {
                        "row": [
                            {
                                "SCHUL_NM": "대구고등학교",
                                "MLSV_YMD": "20260814",
                                "DDISH_NM": "쌀밥<br/>미역국",
                                "CAL_INFO": "800 Kcal",
                            }
                        ]
                    },
                ]
            },
        )
    )

    rows = await neis_client.get_meals("D10", "7240059", "2026-08-14", "2026-08-14")

    assert len(rows) == 1
    assert rows[0]["MLSV_YMD"] == "20260814"


@respx.mock
async def test_get_meals_empty_result_returns_empty_list():
    respx.get(MEALS_URL).mock(return_value=httpx.Response(200, json=_empty_payload("mealServiceDietInfo")))

    rows = await neis_client.get_meals("D10", "7240059", "2026-08-14", "2026-08-14")

    assert rows == []
