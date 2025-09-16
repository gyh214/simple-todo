"""
날짜 처리 및 만료 확인 유틸리티 모듈
"""

from datetime import datetime, date
from typing import Optional, Union
import re


class DateUtils:
    """날짜 관련 유틸리티 클래스"""

    # 기본 생성일 (기존 데이터 마이그레이션용)
    DEFAULT_CREATED_DATE = "2025-09-01"

    @staticmethod
    def get_current_date() -> str:
        """현재 날짜를 ISO 형식 문자열로 반환"""
        return datetime.now().date().isoformat()

    @staticmethod
    def get_current_datetime() -> str:
        """현재 날짜시간을 ISO 형식 문자열로 반환"""
        return datetime.now().isoformat()

    @staticmethod
    def parse_date(date_str: str) -> Optional[date]:
        """
        날짜 문자열을 date 객체로 파싱

        Args:
            date_str: 날짜 문자열 (ISO 형식: YYYY-MM-DD 또는 YYYY-MM-DD HH:MM:SS)

        Returns:
            date 객체 또는 None (파싱 실패시)
        """
        if not date_str:
            return None

        try:
            # ISO 날짜 형식들 시도
            date_patterns = [
                r'^\d{4}-\d{2}-\d{2}$',  # YYYY-MM-DD
                r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}',  # ISO datetime
            ]

            for pattern in date_patterns:
                if re.match(pattern, date_str):
                    if 'T' in date_str:
                        # datetime 형식
                        return datetime.fromisoformat(date_str.split('T')[0]).date()
                    else:
                        # date 형식
                        return datetime.fromisoformat(date_str).date()

            # 다른 형식들도 시도
            return datetime.strptime(date_str[:10], '%Y-%m-%d').date()

        except (ValueError, TypeError):
            return None

    @staticmethod
    def is_date_expired(due_date: Optional[str]) -> bool:
        """
        납기일이 만료되었는지 확인

        Args:
            due_date: 납기일 문자열 (ISO 형식)

        Returns:
            만료 여부 (True: 만료됨, False: 아직 안 만료됨 또는 납기일 없음)
        """
        if not due_date:
            return False

        parsed_due = DateUtils.parse_date(due_date)
        if not parsed_due:
            return False

        current_date = date.today()
        return current_date > parsed_due

    @staticmethod
    def is_date_today(check_date: Optional[str]) -> bool:
        """
        주어진 날짜가 오늘인지 확인

        Args:
            check_date: 확인할 날짜 문자열

        Returns:
            오늘 여부
        """
        if not check_date:
            return False

        parsed_date = DateUtils.parse_date(check_date)
        if not parsed_date:
            return False

        return parsed_date == date.today()

    @staticmethod
    def is_date_upcoming(due_date: Optional[str], days_ahead: int = 3) -> bool:
        """
        납기일이 곧 다가오는지 확인 (기본 3일 이내)

        Args:
            due_date: 납기일 문자열
            days_ahead: 미리 알림할 일수

        Returns:
            곧 다가올 납기일 여부
        """
        if not due_date:
            return False

        parsed_due = DateUtils.parse_date(due_date)
        if not parsed_due:
            return False

        current_date = date.today()
        days_diff = (parsed_due - current_date).days

        return 0 <= days_diff <= days_ahead

    @staticmethod
    def format_date_for_display(date_str: Optional[str]) -> str:
        """
        날짜를 표시용으로 포맷

        Args:
            date_str: 날짜 문자열

        Returns:
            포맷된 날짜 문자열 (예: "2025-09-20")
        """
        if not date_str:
            return ""

        parsed_date = DateUtils.parse_date(date_str)
        if not parsed_date:
            return date_str  # 파싱 실패시 원본 반환

        return parsed_date.strftime("%Y-%m-%d")

    @staticmethod
    def format_date_korean(date_str: Optional[str]) -> str:
        """
        날짜를 한국식으로 포맷

        Args:
            date_str: 날짜 문자열

        Returns:
            한국식 날짜 문자열 (예: "2025년 9월 20일")
        """
        if not date_str:
            return ""

        parsed_date = DateUtils.parse_date(date_str)
        if not parsed_date:
            return date_str

        return f"{parsed_date.year}년 {parsed_date.month}월 {parsed_date.day}일"

    @staticmethod
    def get_days_until_due(due_date: Optional[str]) -> Optional[int]:
        """
        납기일까지 남은 일수 계산

        Args:
            due_date: 납기일 문자열

        Returns:
            남은 일수 (음수면 만료된 일수, None이면 계산 불가)
        """
        if not due_date:
            return None

        parsed_due = DateUtils.parse_date(due_date)
        if not parsed_due:
            return None

        current_date = date.today()
        return (parsed_due - current_date).days

    @staticmethod
    def validate_date_string(date_str: str) -> bool:
        """
        날짜 문자열이 유효한지 검증

        Args:
            date_str: 검증할 날짜 문자열

        Returns:
            유효성 여부
        """
        return DateUtils.parse_date(date_str) is not None

    @staticmethod
    def get_date_status_info(due_date: Optional[str]) -> dict:
        """
        날짜 상태 정보를 종합적으로 반환

        Args:
            due_date: 납기일 문자열

        Returns:
            상태 정보 딕셔너리
        """
        if not due_date:
            return {
                'has_due_date': False,
                'is_expired': False,
                'is_today': False,
                'is_upcoming': False,
                'days_until_due': None,
                'display_text': "",
                'status_color': 'normal'
            }

        days_until = DateUtils.get_days_until_due(due_date)
        is_expired = DateUtils.is_date_expired(due_date)
        is_today = DateUtils.is_date_today(due_date)
        is_upcoming = DateUtils.is_date_upcoming(due_date)

        # 상태에 따른 색상 결정
        if is_expired:
            status_color = 'expired'  # 빨간색
        elif is_today:
            status_color = 'today'    # 주황색
        elif is_upcoming:
            status_color = 'upcoming' # 노란색
        else:
            status_color = 'normal'   # 기본색

        return {
            'has_due_date': True,
            'is_expired': is_expired,
            'is_today': is_today,
            'is_upcoming': is_upcoming,
            'days_until_due': days_until,
            'display_text': DateUtils.format_date_for_display(due_date),
            'status_color': status_color
        }