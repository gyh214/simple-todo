# -*- coding: utf-8 -*-
"""BaseTask Abstract Entity - Todo와 SubTask의 공통 추상 클래스"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from ..value_objects.todo_id import TodoId
from ..value_objects.content import Content
from ..value_objects.due_date import DueDate


@dataclass
class BaseTask(ABC):
    """BaseTask 추상 엔티티

    Todo와 SubTask의 공통 필드 및 메서드를 정의합니다.
    모든 할일 관련 엔티티는 이 클래스를 상속받아야 합니다.
    """

    id: TodoId
    content: Content
    completed: bool
    created_at: datetime
    due_date: Optional[DueDate]
    order: int

    def __post_init__(self) -> None:
        """인스턴스 생성 후 검증을 수행합니다.

        Raises:
            ValueError: 유효하지 않은 값이 있는 경우
        """
        if self.order < 0:
            raise ValueError(f"Order must be non-negative, got {self.order}")

    def complete(self) -> None:
        """할일을 완료 상태로 변경합니다."""
        self.completed = True

    def uncomplete(self) -> None:
        """할일을 미완료 상태로 변경합니다."""
        self.completed = False

    def toggle_complete(self) -> None:
        """완료 상태를 토글합니다."""
        self.completed = not self.completed

    def update_content(self, content: Content) -> None:
        """할일 내용을 수정합니다.

        Args:
            content: 새로운 내용 (Content Value Object)

        Raises:
            ValueError: 유효하지 않은 내용인 경우 (Content에서 검증)
        """
        self.content = content

    def set_due_date(self, due_date: Optional[DueDate]) -> None:
        """납기일을 설정합니다.

        Args:
            due_date: 새로운 납기일 (None일 경우 납기일 제거)
        """
        self.due_date = due_date

    def change_order(self, new_order: int) -> None:
        """순서를 변경합니다.

        Args:
            new_order: 새로운 순서 (0 이상)

        Raises:
            ValueError: 순서가 음수인 경우
        """
        if new_order < 0:
            raise ValueError(f"Order must be non-negative, got {new_order}")
        self.order = new_order

    @abstractmethod
    def to_dict(self) -> dict:
        """할일을 딕셔너리로 변환합니다 (JSON 직렬화용).

        하위 클래스에서 반드시 구현해야 합니다.

        Returns:
            dict: 할일 데이터를 담은 딕셔너리
        """
        pass

    @staticmethod
    @abstractmethod
    def from_dict(data: dict):
        """딕셔너리로부터 할일 인스턴스를 생성합니다 (JSON 역직렬화용).

        하위 클래스에서 반드시 구현해야 합니다.

        Args:
            data: 할일 데이터를 담은 딕셔너리

        Returns:
            BaseTask: 생성된 할일 인스턴스

        Raises:
            ValueError: 유효하지 않은 데이터인 경우
        """
        pass

    @abstractmethod
    def __repr__(self) -> str:
        """할일의 개발자용 문자열 표현을 반환합니다.

        하위 클래스에서 반드시 구현해야 합니다.

        Returns:
            str: 할일 표현 문자열
        """
        pass
