from __future__ import annotations

import math
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import neis_client
from app.models import TournamentRun
from app.schemas import TodayKingResponse, TournamentMatch, TournamentRound, TournamentSchool
from app.services.scoring import calculate_meal_score, compare_score_results, parse_menu_items

OFFICE_CODES = [
    "B10",
    "C10",
    "D10",
    "E10",
    "F10",
    "G10",
    "H10",
    "I10",
    "J10",
    "K10",
    "L10",
    "M10",
    "N10",
    "P10",
    "Q10",
    "R10",
    "S10",
]

# 방학/주말처럼 급식 데이터가 있는 학교가 드문 날에는 학교를 하나씩 순차 조회하면
# 수백~수천 건의 NEIS 호출이 직렬로 쌓여 서버 기동/배치가 수 분씩 걸릴 수 있다.
# 배치 단위로 동시 조회하되, 목표 인원(quota)을 채우면 즉시 중단해 불필요한 호출은 늘리지 않는다.
MEAL_LOOKUP_BATCH_SIZE = 20
MEAL_LOOKUP_MAX_WORKERS = 20


def allocate_quota(total: int = 128, offices: int = 17) -> list[int]:
    base = total // offices
    remainder = total % offices
    return [base + (1 if index < remainder else 0) for index in range(offices)]


def _previous_power_of_two(number: int) -> int:
    if number < 2:
        return number
    return 2 ** int(math.log2(number))


def draw_schools_for_today(
    target_date: date | None = None, rng: random.Random | None = None
) -> list[dict]:
    target_date = target_date or date.today()
    rng = rng or random.Random()
    quotas = dict(zip(OFFICE_CODES, allocate_quota(), strict=True))
    selected: list[dict] = []
    remaining_pool: dict[str, list[dict]] = {}

    with ThreadPoolExecutor(max_workers=MEAL_LOOKUP_MAX_WORKERS) as executor:
        for office_code in OFFICE_CODES:
            rows, _ = neis_client.search_high_schools_by_office(office_code, page=1, size=1000)
            shuffled = rows[:]
            rng.shuffle(shuffled)
            remaining_pool[office_code] = shuffled

            office_selected = _select_for_office(
                office_code, quotas[office_code], target_date, remaining_pool, executor
            )
            selected.extend(office_selected)

        if len(selected) < 128:
            selected.extend(
                _fill_from_other_offices(
                    128 - len(selected), target_date, remaining_pool, rng, executor
                )
            )

    target_size = _previous_power_of_two(len(selected))
    return selected[:target_size]


def _fetch_meals_batch(
    office_code: str,
    school_rows: list[dict],
    target_date: date,
    executor: ThreadPoolExecutor,
) -> list[tuple[dict, dict]]:
    """급식 조회를 배치 단위로 동시 실행해 학교를 순차 호출하는 것보다 빠르게 결과를 모은다."""
    futures = {
        executor.submit(
            neis_client.get_meals,
            office_code,
            school["SD_SCHUL_CODE"],
            target_date.isoformat(),
            target_date.isoformat(),
        ): school
        for school in school_rows
    }
    hits: list[tuple[dict, dict]] = []
    for future in as_completed(futures):
        school = futures[future]
        meals = future.result()
        if meals:
            hits.append((school, meals[0]))
    return hits


def _select_for_office(
    office_code: str,
    quota: int,
    target_date: date,
    remaining_pool: dict[str, list[dict]],
    executor: ThreadPoolExecutor,
) -> list[dict]:
    selected: list[dict] = []
    pool = remaining_pool[office_code]
    while pool and len(selected) < quota:
        batch_size = min(MEAL_LOOKUP_BATCH_SIZE, len(pool))
        batch = pool[:batch_size]
        del pool[:batch_size]
        for school, meal in _fetch_meals_batch(office_code, batch, target_date, executor):
            if len(selected) >= quota:
                break
            selected.append(_build_candidate_school(school, meal))
    return selected


def _fill_from_other_offices(
    needed: int,
    target_date: date,
    remaining_pool: dict[str, list[dict]],
    rng: random.Random,
    executor: ThreadPoolExecutor,
) -> list[dict]:
    selected: list[dict] = []
    office_order = OFFICE_CODES[:]
    rng.shuffle(office_order)
    for office_code in office_order:
        if len(selected) == needed:
            break
        pool = remaining_pool[office_code]
        while pool and len(selected) < needed:
            batch_size = min(MEAL_LOOKUP_BATCH_SIZE, len(pool))
            batch = pool[:batch_size]
            del pool[:batch_size]
            for school, meal in _fetch_meals_batch(office_code, batch, target_date, executor):
                if len(selected) >= needed:
                    break
                selected.append(_build_candidate_school(school, meal))
    return selected


def _build_candidate_school(school_row: dict, meal_row: dict) -> dict:
    score_result = calculate_meal_score(meal_row)
    return {
        "schoolCode": school_row["SD_SCHUL_CODE"],
        "schoolName": school_row["SCHUL_NM"],
        "officeName": school_row["ATPT_OFCDC_SC_NM"],
        "menuItems": parse_menu_items(meal_row.get("DDISH_NM")),
        "score": score_result.breakdown.model_dump(),
        "menuCount": score_result.menu_count,
        "nutritionDistance": score_result.nutrition_distance,
    }


def build_bracket(schools: list[dict]) -> list[TournamentRound]:
    rounds: list[TournamentRound] = []
    current = schools[:]
    round_number = 1

    while len(current) > 1:
        matches = []
        winners = []
        round_name = "결승" if len(current) == 2 else f"{len(current)}강"
        for index in range(0, len(current), 2):
            school_a = current[index]
            school_b = current[index + 1] if index + 1 < len(current) else None
            winner = school_a if school_b is None else compare_score_results(school_a, school_b)
            winners.append(winner)
            matches.append(
                TournamentMatch(
                    matchId=f"R{round_number}-M{index // 2 + 1}",
                    schoolA=_to_tournament_school(school_a),
                    schoolB=_to_tournament_school(school_b) if school_b is not None else None,
                    winnerSchoolCode=winner["schoolCode"],
                    isBye=school_b is None,
                )
            )
        rounds.append(
            TournamentRound(roundNumber=round_number, roundName=round_name, matches=matches)
        )
        current = winners
        round_number += 1
    return rounds


def _to_tournament_school(candidate: dict) -> TournamentSchool:
    payload = {
        key: candidate[key]
        for key in ("schoolCode", "schoolName", "officeName", "menuItems", "score")
    }
    return TournamentSchool.model_validate(payload)


def run_daily_tournament(
    db: Session, run_date: date | None = None, rng: random.Random | None = None
) -> TodayKingResponse:
    run_date = run_date or date.today()
    existing = db.query(TournamentRun).filter(TournamentRun.run_date == run_date).one_or_none()
    if existing:
        return TodayKingResponse.model_validate(existing.result_json)

    schools = draw_schools_for_today(target_date=run_date, rng=rng)
    if not schools:
        raise ValueError("토너먼트 참가 학교를 확보하지 못했습니다.")
    bracket = build_bracket(schools)
    final_match = bracket[-1].matches[0]
    assert final_match.schoolB is not None, "결승전은 항상 두 학교가 대결해야 합니다."
    champion = (
        final_match.schoolA
        if final_match.winnerSchoolCode == final_match.schoolA.schoolCode
        else final_match.schoolB
    )
    result = TodayKingResponse(
        date=run_date,
        totalParticipants=len(schools),
        champion=champion,
        bracket=bracket,
    )
    tournament_run = TournamentRun(
        run_date=run_date,
        champion_school_code=result.champion.schoolCode,
        result_json=result.model_dump(mode="json"),
    )
    db.add(tournament_run)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = db.query(TournamentRun).filter(TournamentRun.run_date == run_date).one()
        return TodayKingResponse.model_validate(existing.result_json)
    db.refresh(tournament_run)
    return result
