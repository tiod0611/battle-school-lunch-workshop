from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime

from app.schemas import ScoreBreakdown

BASE_SCORE = 20
SEASONAL_KEYWORDS = {
    "spring": ["딸기", "냉이", "두릅", "봄동", "취나물", "죽순", "완두콩", "마늘종", "도다리"],
    "summer": ["수박", "참외", "옥수수", "애호박", "감자", "오이", "가지", "열무", "복숭아"],
    "autumn": ["사과", "배", "감", "밤", "고구마", "버섯", "전어", "갈치", "단호박"],
    "winter": ["귤", "굴", "시금치", "배추", "무", "호박", "방어", "대구", "냉이"],
}
PROCESSED_FOOD_KEYWORDS = [
    "소시지",
    "햄",
    "베이컨",
    "스팸",
    "맛살",
    "어묵",
    "통조림",
    "냉동",
    "즉석",
    "라면",
    "핫도그",
    "너겟",
]
NUTRITION_TARGETS = {"carb": 60.0, "protein": 13.5, "fat": 22.5}
NUTRITION_RANGES = {"carb": (55.0, 65.0), "protein": (7.0, 20.0), "fat": (15.0, 30.0)}
DAY_OF_WEEK = ["월", "화", "수", "목", "금", "토", "일"]


@dataclass
class NutritionRatios:
    carb: float
    protein: float
    fat: float


@dataclass
class ScoreResult:
    breakdown: ScoreBreakdown
    menu_count: int
    nutrition_distance: float
    ratios: NutritionRatios | None


def parse_menu_items(ddish_nm: str | None) -> list[str]:
    if not ddish_nm:
        return []
    return [item.strip() for item in re.split(r"<br\s*/?>", ddish_nm) if item.strip()]


def determine_season(meal_date: str) -> str | None:
    try:
        month = datetime.strptime(meal_date, "%Y%m%d").month
    except (TypeError, ValueError):
        return None
    if 3 <= month <= 5:
        return "spring"
    if 6 <= month <= 8:
        return "summer"
    if 9 <= month <= 11:
        return "autumn"
    return "winter"


def score_seasonal_ingredients(menu_items: list[str], meal_date: str | None) -> int:
    season = determine_season(meal_date or "")
    if not season:
        return 0
    menu_text = " ".join(menu_items)
    matches = sum(1 for keyword in SEASONAL_KEYWORDS[season] if keyword in menu_text)
    if matches == 0:
        return 0
    if matches == 1:
        return 10
    if matches == 2:
        return 18
    return 25


def parse_nutrition_info(ntr_info: str | None) -> NutritionRatios | None:
    if not ntr_info:
        return None

    def extract(label: str) -> float | None:
        patterns = [
            rf"{label}\s*[:：]?\s*([\d.]+)\s*g",
            rf"{label}\s*\(g\)\s*[:：]?\s*([\d.]+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, ntr_info, re.IGNORECASE)
            if match:
                return float(match.group(1))
        return None

    carb_g = extract("탄수화물")
    protein_g = extract("단백질")
    fat_g = extract("지방")
    if carb_g is None or protein_g is None or fat_g is None:
        return None
    total_kcal = carb_g * 4 + protein_g * 4 + fat_g * 9
    if total_kcal <= 0:
        return None
    return NutritionRatios(
        carb=(carb_g * 4 / total_kcal) * 100,
        protein=(protein_g * 4 / total_kcal) * 100,
        fat=(fat_g * 9 / total_kcal) * 100,
    )


def _score_ratio(value: float, lower: float, upper: float) -> int:
    if lower <= value <= upper:
        return 10
    deviation = lower - value if value < lower else value - upper
    return max(0, int(round(10 - deviation * 2)))


def score_nutrition_balance(ntr_info: str | None) -> tuple[int, NutritionRatios | None, float]:
    ratios = parse_nutrition_info(ntr_info)
    if ratios is None:
        return 0, None, float("inf")
    score = (
        _score_ratio(ratios.carb, *NUTRITION_RANGES["carb"])
        + _score_ratio(ratios.protein, *NUTRITION_RANGES["protein"])
        + _score_ratio(ratios.fat, *NUTRITION_RANGES["fat"])
    )
    distance = (
        abs(ratios.carb - NUTRITION_TARGETS["carb"])
        + abs(ratios.protein - NUTRITION_TARGETS["protein"])
        + abs(ratios.fat - NUTRITION_TARGETS["fat"])
    )
    return score, ratios, distance


def score_menu_variety(menu_items: list[str]) -> tuple[int, int]:
    count = len(menu_items)
    if count == 0:
        return 0, 0
    if count <= 3:
        return 5, count
    if count <= 5:
        return 15, count
    if count <= 7:
        return 20, count
    return 25, count


def score_processed_food_penalty(menu_items: list[str]) -> int:
    menu_text = " ".join(menu_items)
    matches = sum(1 for keyword in PROCESSED_FOOD_KEYWORDS if keyword in menu_text)
    return -min(matches, 4) * 5


def calculate_meal_score(meal_row: dict) -> ScoreResult:
    menu_items = parse_menu_items(meal_row.get("DDISH_NM"))
    seasonal_score = score_seasonal_ingredients(menu_items, meal_row.get("MLSV_YMD"))
    nutrition_score, ratios, nutrition_distance = score_nutrition_balance(meal_row.get("NTR_INFO"))
    menu_variety, menu_count = score_menu_variety(menu_items)
    processed_penalty = score_processed_food_penalty(menu_items)
    total = max(
        0,
        min(100, BASE_SCORE + seasonal_score + nutrition_score + menu_variety + processed_penalty),
    )
    breakdown = ScoreBreakdown(
        base=BASE_SCORE,
        seasonalIngredient=seasonal_score,
        nutritionBalance=nutrition_score,
        menuVariety=menu_variety,
        processedFoodPenalty=processed_penalty,
        total=total,
    )
    return ScoreResult(
        breakdown=breakdown,
        menu_count=menu_count,
        nutrition_distance=nutrition_distance,
        ratios=ratios,
    )


def compare_score_results(first: dict, second: dict) -> dict:
    first_total = first["score"]["total"]
    second_total = second["score"]["total"]
    if first_total != second_total:
        return first if first_total > second_total else second
    if first["menuCount"] != second["menuCount"]:
        return first if first["menuCount"] > second["menuCount"] else second
    if first["nutritionDistance"] != second["nutritionDistance"]:
        return first if first["nutritionDistance"] < second["nutritionDistance"] else second
    return first if first["schoolCode"] <= second["schoolCode"] else second


def day_of_week_label(date_value: datetime) -> str:
    return DAY_OF_WEEK[date_value.weekday()]
