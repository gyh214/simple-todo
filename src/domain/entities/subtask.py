# -*- coding: utf-8 -*-
"""SubTask Entity - 하위 할일 엔티티 (1-depth만 지원)"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from ..value_objects.todo_id import TodoId
from ..value_objects.content import Content
from ..value_objects.due_date import DueDate
from .base_task import BaseTask


@dataclass
class SubTask(BaseTask):
    """SubTask 엔티티

    메인 할일(Todo)과 동일한 필드 구조를 가지지만,
    자체적으로 하위 할일을 가질 수 없음 (1-depth만 지원).
    BaseTask의 모든 공통 메서드를 상속받습니다.
    """

    @staticmethod
    def create(
        content: str,
        due_date: Optional[str] = None,
        order: int = 0,
    ) -> 'SubTask':
        """새로운 SubTask 인스턴스를 생성합니다 (팩토리 메서드).

        Args:
            content: SubTask 내용 (문자열)
            due_date: 납기일 (ISO 8601 문자열, 선택)
            order: 순서 (기본값: 0)

        Returns:
            SubTask: 생성된 SubTask 인스턴스

        Raises:
            ValueError: 유효하지 않은 값이 있는 경우
        """
        subtask_id = TodoId.generate()
        content_vo = Content(value=content)
        due_date_vo = DueDate.from_string(due_date) if due_date else None
        created_at = datetime.now()

        return SubTask(
            id=subtask_id,
            content=content_vo,
            completed=False,
            created_at=created_at,
            due_date=due_date_vo,
            order=order,
        )

    def to_dict(self) -> dict:
        """SubTask를 딕셔너리로 변환합니다 (JSON 직렬화용).

        Returns:
            dict: SubTask 데이터를 담은 딕셔너리
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
    def from_dict(data: dict) -> 'SubTask':
        """딕셔너리로부터 SubTask 인스턴스를 생성합니다 (JSON 역직렬화용).

        Args:
            data: SubTask 데이터를 담은 딕셔너리

        Returns:
            SubTask: 생성된 SubTask 인스턴스

        Raises:
            ValueError: 유효하지 않은 데이터인 경우
        """
        subtask_id = TodoId.from_string(data['id'])
        content = Content(value=data['content'])
        completed = data['completed']
        created_at = datetime.fromisoformat(data['createdAt'])
        due_date = DueDate.from_string(data['dueDate']) if data.get('dueDate') else None
        order = data['order']

        return SubTask(
            id=subtask_id,
            content=content,
            completed=completed,
            created_at=created_at,
            due_date=due_date,
            order=order,
        )

    def __repr__(self) -> str:
        """SubTask의 개발자용 문자열 표현을 반환합니다.

        Returns:
            str: SubTask 표현 문자열
        """
        return (
            f"SubTask(id={self.id!r}, content={self.content!r}, "
            f"completed={self.completed}, created_at={self.created_at.isoformat()}, "
            f"due_date={self.due_date!r}, order={self.order})"
        )
