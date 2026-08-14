"""MCP 도구 오류 타입.

모든 예외는 사용자에게 그대로 노출해도 안전한 메시지만 담는다.
(NEIS API 키, 요청 URL, 원본 예외 스택 등 민감 정보는 절대 포함하지 않는다.)
"""

from __future__ import annotations


class MCPToolError(Exception):
    """MCP 도구 호출 중 발생하는 모든 사용자 대면 오류의 기반 클래스."""


class ValidationError(MCPToolError):
    """도구 입력값이 유효하지 않을 때 발생한다."""


class NotFoundError(MCPToolError):
    """검색/조회 결과가 없을 때 발생한다."""


class UpstreamError(MCPToolError):
    """NEIS 공공데이터 API 호출 실패(오류 응답, 타임아웃 등) 시 발생한다."""
