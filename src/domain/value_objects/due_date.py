# -*- coding: utf-8 -*-
"""DueDate Value Object - 납기일"""

from dataclasses import dataclass
from datetime import datetime, date
from typing import Literal


DueDateStatus = Literal["overdue_severe", "overdue_moderate", "overdue_mild", "today", "upcoming", "normal"]


@dataclass(frozen=True)
class DueDate:
    """Todo의 납기일을 나타내는 Value Object

    datetime을 래핑하며, 날짜 상태 계산 기능을 제공합니다.
    """

    value: datetime

    def calculate_status(self, current_date: datetime | None = None) -> DueDateStatus:
        """현재 날짜 기준으로 납기일 상태를 계산합니다.

        Args:
            current_date: 기준 날짜 (None일 경우 현재 시각 사용)

        Returns:
            DueDateStatus: "overdue_severe", "overdue_moderate", "overdue_mild", "today", "upcoming", "normal" 중 하나
        """
        if current_date is None:
            current_date = datetime.now()

        # 날짜만 비교 (시간 제외)
        due_date_only = self.value.date()
        current_date_only = current_date.date()

        days_diff = (due_date_only - current_date_only).days

        if days_diff < 0:
            # 만료: 3단계로 세분화
            days_overdue = abs(days_diff)
            if days_overdue >= 14:
                return "overdue_severe"      # 14일 이상 지남
            elif days_overdue >= 7:
                return "overdue_moderate"    # 7-13일 지남
            else:
                return "overdue_mild"        # 1-6일 지남
        elif days_diff == 0:
            return "today"
        elif days_diff <= 10:
            return "upcoming"                # 1-10일 남음
        else:
            return "normal"                  # 11일 이상 남음

    def days_until(self, current_date: datetime | None = None) -> int:
        """현재 날짜로부터 납기일까지의 일수를 계산합니다.

        Args:
            current_date: 기준 날짜 (None일 경우 현재 시각 사용)

        Returns:
            int: 남은 일수 (음수: 지남, 0: 오늘, 양수: 남음)
        """
        if current_date is None:
            current_date = datetime.now()

        # 날짜만 비교 (시간 제외)
        due_date_only = self.value.date()
        current_date_only = current_date.date()

        return (due_date_only - current_date_only).days

    def format_display_text(self, current_date: datetime | None = None) -> str:
        """사용자에게 표시할 납기일 텍스트를 생성합니다.

        Args:
            current_date: 기준 날짜 (None일 경우 현재 시각 사용)

        Returns:
            str: "X일 남음", "오늘", "X일 지남" 형식의 문자열
        """
        days = self.days_until(current_date)

        if days < 0:
            return f"{abs(days)}일 지남"
        elif days == 0:
            return "오늘"
        else:
            return f"{days}일 남음"

    @staticmethod
    def from_string(date_str: str) -> 'DueDate':
        """문자열로부터 DueDate 인스턴스를 생성합니다.

        Args:
            date_str: ISO 8601 형식의 날짜 문자열

        Returns:
            DueDate: 생성된 DueDate 인스턴스

        Raises:
            ValueError: 유효하지 않은 날짜 형식인 경우
        """
        try:
            # ISO 8601 형식 파싱 시도
            dt = datetime.fromisoformat(date_str)
            return DueDate(value=dt)
        except ValueError:
            # YYYY-MM-DD 형식 시도
            try:
                dt = datetime.strptime(date_str, "%Y-%m-%d")
                return DueDate(value=dt)
            except ValueError as e:
                raise ValueError(f"Invalid date string: {date_str}. Expected ISO 8601 or YYYY-MM-DD format") from e

    @staticmethod
    def from_date(date_obj: date) -> 'DueDate':
        """date 객체로부터 DueDate 인스턴스를 생성합니다.

        Args:
            date_obj: datetime.date 객체

        Returns:
            DueDate: 생성된 DueDate 인스턴스
        """
        dt = datetime.combine(date_obj, datetime.min.time())
        return DueDate(value=dt)

    def __str__(self) -> str:
        """DueDate를 ISO 8601 문자열로 변환합니다.

        Returns:
            str: ISO 8601 형식 날짜 문자열
        """
        return self.value.isoformat()

    def __repr__(self) -> str:
        """DueDate의 개발자용 문자열 표현을 반환합니다.

        Returns:
            str: DueDate 표현 문자열
        """
        return f"DueDate('{self.value.isoformat()}')"
