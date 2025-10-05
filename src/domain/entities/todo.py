# -*- coding: utf-8 -*-
"""Todo Entity - 도메인 핵심 엔티티"""

from dataclasses import dataclass, replace
from datetime import datetime
from typing import Optional

from ..value_objects.todo_id import TodoId
from ..value_objects.content import Content
from ..value_objects.due_date import DueDate


@dataclass
class Todo:
    """Todo 엔티티

    할일 항목의 핵심 비즈니스 로직을 캡슐화합니다.
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
        """TODO를 완료 상태로 변경합니다."""
        self.completed = True

    def uncomplete(self) -> None:
        """TODO를 미완료 상태로 변경합니다."""
        self.completed = False

    def update_content(self, content: Content) -> None:
        """TODO 내용을 수정합니다.

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

    @staticmethod
    def create(
        content: str,
        due_date: Optional[str] = None,
        order: int = 0,
    ) -> 'Todo':
        """새로운 Todo 인스턴스를 생성합니다.

        Args:
            content: TODO 내용 (문자열)
            due_date: 납기일 (ISO 8601 문자열, 선택)
            order: 순서 (기본값: 0)

        Returns:
            Todo: 생성된 Todo 인스턴스

        Raises:
            ValueError: 유효하지 않은 값이 있는 경우
        """
        todo_id = TodoId.generate()
        content_vo = Content(value=content)
        due_date_vo = DueDate.from_string(due_date) if due_date else None
        created_at = datetime.now()

        return Todo(
            id=todo_id,
            content=content_vo,
            completed=False,
            created_at=created_at,
            due_date=due_date_vo,
            order=order,
        )

    def to_dict(self) -> dict:
        """Todo를 딕셔너리로 변환합니다 (JSON 직렬화용).

        Returns:
            dict: Todo 데이터를 담은 딕셔너리
        """
        result = {
            'id': str(self.id),
            'content': str(self.content),
            'completed': self.completed,
            'createdAt': self.created_at.isoformat(),
            'order': self.order,
        }

        # dueDate 추가 (값이 있는 경우에만)
        if self.due_date:
            result['dueDate'] = str(self.due_date)

        return result

    @staticmethod
    def from_dict(data: dict) -> 'Todo':
        """딕셔너리로부터 Todo 인스턴스를 생성합니다 (JSON 역직렬화용).

        Args:
            data: Todo 데이터를 담은 딕셔너리

        Returns:
            Todo: 생성된 Todo 인스턴스

        Raises:
            ValueError: 유효하지 않은 데이터인 경우
        """
        todo_id = TodoId.from_string(data['id'])
        content = Content(value=data['content'])
        completed = data['completed']
        created_at = datetime.fromisoformat(data['createdAt'])
        due_date = DueDate.from_string(data['dueDate']) if data.get('dueDate') else None
        order = data['order']

        return Todo(
            id=todo_id,
            content=content,
            completed=completed,
            created_at=created_at,
            due_date=due_date,
            order=order,
        )

    def __repr__(self) -> str:
        """Todo의 개발자용 문자열 표현을 반환합니다.

        Returns:
            str: Todo 표현 문자열
        """
        return (
            f"Todo(id={self.id!r}, content={self.content!r}, "
            f"completed={self.completed}, created_at={self.created_at.isoformat()}, "
            f"due_date={self.due_date!r}, order={self.order})"
        )
