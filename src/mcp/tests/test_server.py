import json

import pytest
from mcp.server.fastmcp.exceptions import ToolError

from app import neis_client, server
from app.errors import UpstreamError


def _call_tool_json(name: str, arguments: dict):
    """도구 호출 결과(Content 리스트)에서 JSON 페이로드를 파싱해 반환하는 헬퍼 코루틴."""

    async def _run():
        content = await server.mcp.call_tool(name, arguments)
        assert len(content) == 1
        return json.loads(content[0].text)

    return _run()


async def test_list_tools_exposes_search_schools_and_get_meals():
    tools = await server.mcp.list_tools()
    tool_names = {tool.name for tool in tools}

    assert tool_names == {"search_schools", "get_meals"}


async def test_search_schools_tool_success(monkeypatch):
    async def fake_search_schools(school_name, page, size):
        assert school_name == "대구고등학교"
        return (
            [
                {
                    "SD_SCHUL_CODE": "7240059",
                    "ATPT_OFCDC_SC_CODE": "D10",
                    "ATPT_OFCDC_SC_NM": "대구광역시교육청",
                    "SCHUL_NM": "대구고등학교",
                    "SCHUL_KND_SC_NM": "고등학교",
                    "LCTN_SC_NM": "대구광역시",
                    "FOND_SC_NM": "공립",
                }
            ],
            1,
        )

    monkeypatch.setattr(neis_client, "search_schools", fake_search_schools)

    result = await _call_tool_json("search_schools", {"keyword": "대구고등학교"})

    assert result["totalCount"] == 1
    assert result["items"][0]["schoolName"] == "대구고등학교"
    assert result["items"][0]["schoolCode"] == "7240059"


async def test_search_schools_tool_rejects_empty_keyword():
    with pytest.raises(ToolError) as exc_info:
        await server.mcp.call_tool("search_schools", {"keyword": "   "})

    assert "비어 있을 수 없습니다" in str(exc_info.value)


async def test_search_schools_tool_reports_no_results_as_clear_error(monkeypatch):
    async def fake_search_schools(school_name, page, size):
        return ([], 0)

    monkeypatch.setattr(neis_client, "search_schools", fake_search_schools)

    with pytest.raises(ToolError) as exc_info:
        await server.mcp.call_tool("search_schools", {"keyword": "존재하지않는학교"})

    assert "검색 결과가 없습니다" in str(exc_info.value)


async def test_search_schools_tool_wraps_upstream_error_without_leaking_details(monkeypatch):
    async def fake_search_schools(school_name, page, size):
        raise UpstreamError("NEIS 공공데이터 API 호출에 실패했습니다. 잠시 후 다시 시도해주세요.")

    monkeypatch.setattr(neis_client, "search_schools", fake_search_schools)

    with pytest.raises(ToolError) as exc_info:
        await server.mcp.call_tool("search_schools", {"keyword": "대구고등학교"})

    assert "NEIS" in str(exc_info.value)


async def test_get_meals_tool_success(monkeypatch):
    async def fake_get_meals(office_code, school_code, from_date, to_date):
        assert office_code == "D10"
        assert school_code == "7240059"
        return [
            {
                "SCHUL_NM": "대구고등학교",
                "MLSV_YMD": "20260814",
                "DDISH_NM": "쌀밥<br/>미역국",
                "CAL_INFO": "800 Kcal",
            }
        ]

    monkeypatch.setattr(neis_client, "get_meals", fake_get_meals)

    result = await _call_tool_json(
        "get_meals",
        {"school_code": "7240059", "office_code": "D10", "from_date": "2026-08-14", "to_date": "2026-08-14"},
    )

    assert result["schoolName"] == "대구고등학교"
    assert result["meals"][0]["menuItems"] == ["쌀밥", "미역국"]
    assert result["meals"][0]["dayOfWeek"] == "금"


async def test_get_meals_tool_rejects_invalid_date_range():
    with pytest.raises(ToolError) as exc_info:
        await server.mcp.call_tool(
            "get_meals",
            {"school_code": "7240059", "office_code": "D10", "from_date": "2026-08-14", "to_date": "2026-08-01"},
        )

    assert "from_date보다 빠를 수 없습니다" in str(exc_info.value)


async def test_get_meals_tool_rejects_range_over_31_days():
    with pytest.raises(ToolError) as exc_info:
        await server.mcp.call_tool(
            "get_meals",
            {"school_code": "7240059", "office_code": "D10", "from_date": "2026-01-01", "to_date": "2026-03-01"},
        )

    assert "최대 31일" in str(exc_info.value)


async def test_get_meals_tool_reports_no_meals_as_clear_error(monkeypatch):
    async def fake_get_meals(office_code, school_code, from_date, to_date):
        return []

    monkeypatch.setattr(neis_client, "get_meals", fake_get_meals)

    with pytest.raises(ToolError) as exc_info:
        await server.mcp.call_tool(
            "get_meals",
            {"school_code": "7240059", "office_code": "D10", "from_date": "2026-08-14", "to_date": "2026-08-14"},
        )

    assert "급식 정보가 없습니다" in str(exc_info.value)


async def test_get_meals_tool_wraps_upstream_error_without_leaking_details(monkeypatch):
    async def fake_get_meals(office_code, school_code, from_date, to_date):
        raise UpstreamError("NEIS 공공데이터 API 호출에 실패했습니다. 잠시 후 다시 시도해주세요.")

    monkeypatch.setattr(neis_client, "get_meals", fake_get_meals)

    with pytest.raises(ToolError) as exc_info:
        await server.mcp.call_tool(
            "get_meals",
            {"school_code": "7240059", "office_code": "D10", "from_date": "2026-08-14", "to_date": "2026-08-14"},
        )

    assert "NEIS" in str(exc_info.value)
