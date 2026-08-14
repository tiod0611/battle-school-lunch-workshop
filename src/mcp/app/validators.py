"""도구 입력값 검증 유틸리티."""

from __future__ import annotations

from datetime import date, datetime

from app.errors import ValidationError

MAX_RANGE_DAYS = 31
MAX_PAGE_SIZE = 100


def validate_keyword(keyword: str) -> str:
    trimmed = (keyword or "").strip()
    if not trimmed:
        raise ValidationError("학교명(keyword)은 비어 있을 수 없습니다.")
    return trimmed


def validate_page(page: int) -> int:
    if page < 1:
        raise ValidationError("page는 1 이상이어야 합니다.")
    return page


def validate_size(size: int) -> int:
    if size < 1 or size > MAX_PAGE_SIZE:
        raise ValidationError(f"size는 1~{MAX_PAGE_SIZE} 사이여야 합니다.")
    return size


def validate_code(value: str, field_name: str) -> str:
    trimmed = (value or "").strip()
    if not trimmed:
        raise ValidationError(f"{field_name}는 비어 있을 수 없습니다.")
    return trimmed


def validate_date_range(from_date: str, to_date: str) -> tuple[date, date]:
    parsed_from = _parse_date(from_date, "from_date")
    parsed_to = _parse_date(to_date, "to_date")
    if parsed_to < parsed_from:
        raise ValidationError("to_date는 from_date보다 빠를 수 없습니다.")
    if (parsed_to - parsed_from).days > MAX_RANGE_DAYS:
        raise ValidationError(f"조회 기간은 최대 {MAX_RANGE_DAYS}일까지만 가능합니다.")
    return parsed_from, parsed_to


def _parse_date(value: str, field_name: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{field_name}는 YYYY-MM-DD 형식이어야 합니다.") from exc
