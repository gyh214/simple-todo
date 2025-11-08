# -*- coding: utf-8 -*-
"""RecurrenceRule Value Object - 반복 규칙"""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Optional, List, FrozenSet


@dataclass(frozen=True)
class RecurrenceRule:
    """반복 규칙 Value Object (불변)

    기본 반복만 지원:
    - daily: 매일 반복
    - weekly: 매주 반복
    - monthly: 매달 반복

    종료일 옵션:
    - end_date: 특정 날짜까지만 반복 (None이면 무한 반복)

    주간 반복 시 요일 선택 가능:
    - weekdays: 0=월요일, 1=화요일, ..., 6=일요일
    - 예: frozenset({0, 2, 4}) = 월, 수, 금요일만 반복

    하위 할일 복사 옵션:
    - copy_subtasks: 반복 시 하위 할일도 함께 복사 (기본: False)

    Examples:
        RecurrenceRule(frequency="daily")  # 매일 반복 (무한)
        RecurrenceRule(frequency="weekly", end_date=datetime(2025, 12, 31))  # 2025년까지만 매주 반복
        RecurrenceRule(frequency="weekly", weekdays=frozenset({0, 2, 4}))  # 월수금만 반복
        RecurrenceRule(frequency="daily", copy_subtasks=True)  # 하위 할일 복사
    """

    frequency: Literal["daily", "weekly", "monthly"]
    end_date: Optional[datetime] = None
    weekdays: Optional[FrozenSet[int]] = None
    copy_subtasks: bool = False

    @staticmethod
    def create(
        frequency: str,
        end_date: Optional[datetime] = None,
        weekdays: Optional[List[int]] = None,
        copy_subtasks: bool = False
    ) -> 'RecurrenceRule':
        """RecurrenceRule 생성 (팩토리 메서드)

        Args:
            frequency: 반복 빈도 ("daily", "weekly", "monthly")
            end_date: 종료일 (optional, None이면 무한 반복)
            weekdays: 주간 반복 시 요일 선택 (0-6, 0=월요일, optional)
            copy_subtasks: 반복 시 하위 할일 복사 여부 (기본: False)

        Returns:
            RecurrenceRule 인스턴스

        Raises:
            ValueError: frequency가 유효하지 않거나 end_date가 과거이거나 weekdays가 잘못된 경우

        Examples:
            RecurrenceRule.create("daily")
            RecurrenceRule.create("weekly", weekdays=[0, 2, 4])  # 월수금
            RecurrenceRule.create("monthly", end_date=datetime(2025, 12, 31))
            RecurrenceRule.create("daily", copy_subtasks=True)  # 하위 할일 복사
        """
        # frequency 검증
        if frequency not in ("daily", "weekly", "monthly"):
            raise ValueError(f"Invalid frequency: {frequency}. Must be 'daily', 'weekly', or 'monthly'")

        # end_date 검증 (과거 날짜는 안됨)
        if end_date is not None:
            # 시간 정보를 제거하고 날짜만 비교
            end_date_only = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
            now_date_only = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

            if end_date_only < now_date_only:
                raise ValueError("end_date cannot be in the past")

        # weekdays 검증
        weekdays_set = None
        if weekdays is not None:
            # weekdays는 weekly에서만 사용 가능
            if frequency != "weekly":
                raise ValueError("weekdays can only be used with weekly frequency")

            # 0-6 범위 체크
            if not all(0 <= day <= 6 for day in weekdays):
                raise ValueError("weekdays must be between 0 (Monday) and 6 (Sunday)")

            # 빈 리스트 체크
            if not weekdays:
                raise ValueError("weekdays cannot be empty")

            # FrozenSet으로 변환 (중복 제거 + 불변)
            weekdays_set = frozenset(weekdays)

        return RecurrenceRule(
            frequency=frequency,
            end_date=end_date,
            weekdays=weekdays_set,
            copy_subtasks=copy_subtasks
        )

    @staticmethod
    def from_dict(data: dict) -> 'RecurrenceRule':
        """딕셔너리에서 RecurrenceRule 생성

        Args:
            data: {
                "frequency": "daily"|"weekly"|"monthly",
                "endDate": "ISO 8601 문자열" (optional),
                "weekdays": [0, 1, 2, ...] (optional),
                "copySubtasks": boolean (optional, 기본: False)
            }

        Returns:
            RecurrenceRule 인스턴스

        Raises:
            ValueError: frequency가 없거나 유효하지 않은 경우
        """
        frequency = data.get('frequency')
        if not frequency:
            raise ValueError("Missing 'frequency' in RecurrenceRule data")

        # end_date 파싱 (optional)
        end_date = None
        end_date_str = data.get('endDate')
        if end_date_str:
            try:
                # ISO 8601 형식 파싱 (Z 제거)
                end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                # 파싱 실패 시 무시 (None으로 유지)
                pass

        # weekdays 파싱 (optional, List[int])
        weekdays = data.get('weekdays')

        # copy_subtasks 파싱 (optional, 기본값 False - Zero Migration 지원)
        copy_subtasks = data.get('copySubtasks', False)

        return RecurrenceRule.create(frequency, end_date, weekdays, copy_subtasks)

    def to_dict(self) -> dict:
        """RecurrenceRule을 딕셔너리로 변환

        Returns:
            {
                "frequency": "daily"|"weekly"|"monthly",
                "endDate": "ISO 8601 문자열" (end_date가 있을 경우),
                "weekdays": [0, 1, 2, ...] (weekdays가 있을 경우),
                "copySubtasks": boolean (항상 포함)
            }
        """
        result = {
            'frequency': self.frequency,
            'copySubtasks': self.copy_subtasks  # 항상 포함 (기본값 False)
        }

        # end_date가 있으면 포함
        if self.end_date:
            result['endDate'] = self.end_date.isoformat()

        # weekdays가 있으면 포함 (정렬된 리스트로 변환)
        if self.weekdays is not None:
            result['weekdays'] = sorted(list(self.weekdays))

        return result

    def __str__(self) -> str:
        """사람이 읽기 쉬운 문자열 표현"""
        frequency_map = {
            "daily": "매일",
            "weekly": "매주",
            "monthly": "매달"
        }
        text = frequency_map.get(self.frequency, self.frequency)

        # 주간 반복이고 요일 선택이 있으면 표시
        if self.frequency == "weekly" and self.weekdays:
            weekday_names = ["월", "화", "수", "목", "금", "토", "일"]
            selected_days = [weekday_names[d] for d in sorted(self.weekdays)]
            text += f" ({', '.join(selected_days)})"

        # 종료일이 있으면 추가
        if self.end_date:
            end_date_str = self.end_date.strftime("%Y-%m-%d")
            text += f" ({end_date_str}까지)"

        # 하위 할일 복사 여부 표시
        if self.copy_subtasks:
            text += " [하위 할일 복사]"

        return text

    def __repr__(self) -> str:
        """RecurrenceRule의 개발자용 문자열 표현을 반환합니다.

        Returns:
            str: RecurrenceRule 표현 문자열
        """
        parts = [f"frequency='{self.frequency}'"]
        if self.end_date:
            parts.append(f"end_date='{self.end_date.isoformat()}'")
        if self.weekdays:
            parts.append(f"weekdays={set(self.weekdays)}")
        parts.append(f"copy_subtasks={self.copy_subtasks}")
        return f"RecurrenceRule({', '.join(parts)})"
