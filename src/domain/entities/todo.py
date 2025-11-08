# -*- coding: utf-8 -*-
"""Todo Entity - 도메인 핵심 엔티티"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List

from ..value_objects.todo_id import TodoId
from ..value_objects.content import Content
from ..value_objects.due_date import DueDate
from ..value_objects.recurrence_rule import RecurrenceRule
from .base_task import BaseTask
from .subtask import SubTask


@dataclass
class Todo(BaseTask):
    """Todo 엔티티

    할일 항목의 핵심 비즈니스 로직을 캡슐화합니다.
    하위 할일(SubTask)을 포함할 수 있으며, 자동 정렬을 지원합니다.
    반복 규칙(RecurrenceRule)을 통해 반복 할일을 생성할 수 있습니다.
    """

    subtasks: List[SubTask] = field(default_factory=list)
    recurrence: Optional[RecurrenceRule] = None

    def set_recurrence(self, recurrence_rule: Optional[RecurrenceRule]) -> None:
        """반복 규칙을 설정합니다.

        Args:
            recurrence_rule: 설정할 반복 규칙 (None이면 반복 제거)
        """
        self.recurrence = recurrence_rule

    def remove_recurrence(self) -> None:
        """반복 규칙을 제거합니다."""
        self.recurrence = None

    def is_recurring(self) -> bool:
        """반복 할일인지 확인합니다.

        Returns:
            True: 반복 규칙이 있고 납기일이 있는 경우
            False: 반복 규칙이 없거나 납기일이 없는 경우
        """
        return self.recurrence is not None and self.due_date is not None

    def add_subtask(self, subtask: SubTask) -> None:
        """하위 할일을 추가하고 자동 정렬합니다.

        Args:
            subtask: 추가할 하위 할일
        """
        self.subtasks.append(subtask)
        self.subtasks = self._sort_subtasks(self.subtasks)

    def remove_subtask(self, subtask_id: TodoId) -> None:
        """하위 할일을 제거합니다.

        Args:
            subtask_id: 제거할 하위 할일의 ID
        """
        self.subtasks = [st for st in self.subtasks if st.id != subtask_id]

    def update_subtask(self, subtask_id: TodoId, updated_subtask: SubTask) -> None:
        """하위 할일을 수정하고 재정렬합니다.

        Args:
            subtask_id: 수정할 하위 할일의 ID
            updated_subtask: 수정된 하위 할일 인스턴스
        """
        self.subtasks = [
            updated_subtask if st.id == subtask_id else st
            for st in self.subtasks
        ]
        self.subtasks = self._sort_subtasks(self.subtasks)

    def toggle_subtask_complete(self, subtask_id: TodoId) -> None:
        """하위 할일의 완료 상태를 토글합니다.

        Args:
            subtask_id: 토글할 하위 할일의 ID
        """
        for subtask in self.subtasks:
            if subtask.id == subtask_id:
                subtask.toggle_complete()
                break

    def get_subtask(self, subtask_id: TodoId) -> Optional[SubTask]:
        """ID로 하위 할일을 조회합니다.

        Args:
            subtask_id: 조회할 하위 할일의 ID

        Returns:
            SubTask | None: 찾은 하위 할일 또는 None
        """
        for subtask in self.subtasks:
            if subtask.id == subtask_id:
                return subtask
        return None

    def _sort_subtasks(self, subtasks: List[SubTask]) -> List[SubTask]:
        """하위 할일을 자동 정렬합니다.

        정렬 우선순위:
        1. 납기일이 있는 것이 먼저 (빠른 순)
        2. 납기일이 같으면 생성시간 순
        3. 납기일이 없는 것은 맨 뒤 (생성시간 순)

        Args:
            subtasks: 정렬할 하위 할일 리스트

        Returns:
            List[SubTask]: 정렬된 하위 할일 리스트
        """
        def sort_key(subtask: SubTask) -> tuple:
            # 납기일이 있으면 (False, 납기일, 생성시간)
            # 납기일이 없으면 (True, 최대 datetime, 생성시간)
            if subtask.due_date:
                return (False, subtask.due_date.value, subtask.created_at)
            else:
                # 납기일 없는 것은 맨 뒤로
                return (True, datetime.max, subtask.created_at)

        return sorted(subtasks, key=sort_key)

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
            subtasks=[],
            recurrence=None,
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
            'subtasks': [st.to_dict() for st in self.subtasks],
        }

        # dueDate 추가 (값이 있는 경우에만)
        if self.due_date:
            result['dueDate'] = str(self.due_date)

        # recurrence 추가 (값이 있는 경우에만)
        if self.recurrence:
            result['recurrence'] = self.recurrence.to_dict()

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

        # 하위 할일 (optional, 기본값: [])
        subtasks_data = data.get('subtasks', [])
        subtasks = [SubTask.from_dict(st) for st in subtasks_data]

        # 반복 규칙 (optional, 기본값: None)
        recurrence_data = data.get('recurrence')
        recurrence = RecurrenceRule.from_dict(recurrence_data) if recurrence_data else None

        return Todo(
            id=todo_id,
            content=content,
            completed=completed,
            created_at=created_at,
            due_date=due_date,
            order=order,
            subtasks=subtasks,
            recurrence=recurrence,
        )

    def __repr__(self) -> str:
        """Todo의 개발자용 문자열 표현을 반환합니다.

        Returns:
            str: Todo 표현 문자열
        """
        return (
            f"Todo(id={self.id!r}, content={self.content!r}, "
            f"completed={self.completed}, created_at={self.created_at.isoformat()}, "
            f"due_date={self.due_date!r}, order={self.order}, "
            f"subtasks={len(self.subtasks)} items, "
            f"recurrence={self.recurrence!r})"
        )
