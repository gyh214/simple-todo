# -*- coding: utf-8 -*-
"""RecurrenceService - 반복 할일 비즈니스 로직"""

from datetime import timedelta
from dateutil.relativedelta import relativedelta
from typing import Optional

from ..value_objects.due_date import DueDate
from ..value_objects.recurrence_rule import RecurrenceRule


class RecurrenceService:
    """반복 할일 비즈니스 로직 처리 서비스

    책임:
    - 다음 반복 날짜 계산
    - 반복 생성 여부 판단
    """

    @staticmethod
    def calculate_next_occurrence(
        current_due_date: DueDate,
        recurrence_rule: RecurrenceRule
    ) -> DueDate:
        """다음 반복 날짜 계산

        Args:
            current_due_date: 현재 납기일
            recurrence_rule: 반복 규칙

        Returns:
            다음 반복 날짜 (DueDate)

        Examples:
            # 매일 반복
            current: 2025-01-01
            next: 2025-01-02

            # 매주 반복 (요일 선택 없음)
            current: 2025-01-01 (수요일)
            next: 2025-01-08 (다음 수요일)

            # 매주 반복 (월수금 선택)
            current: 2025-01-01 (수요일)
            next: 2025-01-03 (금요일)

            # 매달 반복
            current: 2025-01-15
            next: 2025-02-15
        """
        current_dt = current_due_date.value

        if recurrence_rule.frequency == "daily":
            # 매일 반복: 하루 추가
            next_dt = current_dt + timedelta(days=1)

        elif recurrence_rule.frequency == "weekly":
            # 요일 선택이 있는 경우
            if recurrence_rule.weekdays:
                # 현재 요일 (0=월요일, 6=일요일)
                current_weekday = current_dt.weekday()

                # 다음 선택된 요일 찾기 (최대 7일 탐색)
                next_weekday = None
                days_ahead = 0
                for i in range(1, 8):
                    candidate_weekday = (current_weekday + i) % 7
                    if candidate_weekday in recurrence_rule.weekdays:
                        next_weekday = candidate_weekday
                        days_ahead = i
                        break

                if next_weekday is None:
                    # 선택된 요일이 없으면 7일 추가 (fallback, 실제로는 발생하지 않아야 함)
                    next_dt = current_dt + timedelta(weeks=1)
                else:
                    # 다음 선택된 요일로 이동
                    next_dt = current_dt + timedelta(days=days_ahead)
            else:
                # 요일 선택 없으면 7일 추가 (기존 로직)
                next_dt = current_dt + timedelta(weeks=1)

        elif recurrence_rule.frequency == "monthly":
            # 매달 반복: 1개월 추가 (dateutil.relativedelta 사용)
            next_dt = current_dt + relativedelta(months=1)

        else:
            raise ValueError(f"Unsupported frequency: {recurrence_rule.frequency}")

        return DueDate(next_dt)

    @staticmethod
    def should_create_next_instance(
        current_due_date: Optional[DueDate],
        recurrence_rule: RecurrenceRule
    ) -> bool:
        """다음 반복 인스턴스를 생성해야 하는지 판단

        Args:
            current_due_date: 현재 납기일 (None이면 생성하지 않음)
            recurrence_rule: 반복 규칙

        Returns:
            True: 다음 인스턴스 생성해야 함
            False: 생성하지 않음 (다음 조건 중 하나)
                - current_due_date가 None
                - 다음 날짜가 end_date를 초과

        로직:
        - current_due_date가 None이면 False (납기 없는 반복 할일은 불가)
        - end_date가 있으면 다음 날짜가 end_date를 초과하는지 확인
        - 그 외에는 True (무한 반복)
        """
        # 납기일이 없으면 반복 불가
        if current_due_date is None:
            return False

        # 종료일이 있으면 확인
        if recurrence_rule.end_date is not None:
            # 다음 날짜 계산
            next_date = RecurrenceService.calculate_next_occurrence(
                current_due_date,
                recurrence_rule
            )

            # 다음 날짜가 종료일을 초과하면 생성하지 않음
            # 시간 정보를 제거하고 날짜만 비교
            next_date_only = next_date.value.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date_only = recurrence_rule.end_date.replace(hour=0, minute=0, second=0, microsecond=0)

            if next_date_only > end_date_only:
                return False

        # 그 외에는 생성 (무한 반복 또는 종료일 내)
        return True
