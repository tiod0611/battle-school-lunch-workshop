import random
from datetime import date

from app.services import tournament_service


def test_allocate_quota_sums_to_128():
    quotas = tournament_service.allocate_quota()
    assert len(quotas) == 17
    assert sum(quotas) == 128
    assert quotas.count(8) == 9
    assert quotas.count(7) == 8


def test_draw_schools_replaces_and_shrinks(monkeypatch):
    office_rows = {
        code: [
            {
                "SD_SCHUL_CODE": f"{code}{index:03d}",
                "SCHUL_NM": f"{code}-학교-{index}",
                "ATPT_OFCDC_SC_NM": f"{code}-교육청",
            }
            for index in range(4)
        ]
        for code in tournament_service.OFFICE_CODES
    }

    def fake_search_high_schools_by_office(office_code, page, size):
        return office_rows[office_code], len(office_rows[office_code])

    def fake_get_meals(office_code, school_code, from_date, to_date):
        if school_code.endswith("000"):
            return []
        return [
            {
                "DDISH_NM": "현미밥<br/>시금치국",
                "NTR_INFO": "탄수화물(g) 80 단백질(g) 20 지방(g) 15",
                "MLSV_YMD": "20260814",
            }
        ]

    monkeypatch.setattr(
        tournament_service.neis_client,
        "search_high_schools_by_office",
        fake_search_high_schools_by_office,
    )
    monkeypatch.setattr(tournament_service.neis_client, "get_meals", fake_get_meals)

    result = tournament_service.draw_schools_for_today(date(2026, 8, 14), random.Random(1))
    assert len(result) == 32
    assert all(not school["schoolCode"].endswith("000") for school in result)
