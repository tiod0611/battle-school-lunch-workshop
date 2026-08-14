"""NEIS 응답 필드 가공 유틸리티 (backend/app/services/scoring.py 의 파싱 로직과 동일)."""

from __future__ import annotations

import re
from datetime import datetime

DAY_OF_WEEK = ["월", "화", "수", "목", "금", "토", "일"]


def parse_menu_items(ddish_nm: str | None) -> list[str]:
    if not ddish_nm:
        return []
    return [item.strip() for item in re.split(r"<br\s*/?>", ddish_nm) if item.strip()]


def day_of_week_label(date_value: datetime) -> str:
    return DAY_OF_WEEK[date_value.weekday()]
