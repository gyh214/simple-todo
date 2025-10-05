# -*- coding: utf-8 -*-
"""TodoService - TODO CRUD 비즈니스 로직"""

from typing import List, Optional
from ...domain.entities.todo import Todo
from ...domain.value_objects.todo_id import TodoId
from ...domain.value_objects.content import Content
from ...domain.value_objects.due_date import DueDate
from ...domain.interfaces.repository_interface import ITodoRepository


class TodoService:
    """Todo 비즈니스 로직을 처리하는 애플리케이션 서비스"""

    def __init__(self, repository: ITodoRepository):
        """TodoService 초기화

        Args:
            repository: TODO 리포지토리 구현체
        """
        self.repository = repository

    def create_todo(self, content: str, due_date: Optional[str] = None) -> Todo:
        """새 TODO 생성

        Args:
            content: TODO 내용
            due_date: 납기일 (ISO 8601 문자열, 선택)

        Returns:
            Todo: 생성된 TODO

        Raises:
            ValueError: 유효하지 않은 입력인 경우
        """
        # 현재 모든 TODO 조회
        all_todos = self.repository.find_all()

        # 진행중(completed=False) TODO들 필터링
        incomplete_todos = [todo for todo in all_todos if not todo.completed]

        # 마지막 order 계산 (없으면 0)
        next_order = 0
        if incomplete_todos:
            max_order = max(todo.order for todo in incomplete_todos)
            next_order = max_order + 1

        # 새 TODO 생성
        new_todo = Todo.create(
            content=content,
            due_date=due_date,
            order=next_order
        )

        # 저장
        self.repository.save(new_todo)

        return new_todo

    def update_todo(self, todo_id: str, content: str, due_date: Optional[str] = None) -> None:
        """TODO 수정

        Args:
            todo_id: TODO ID (문자열)
            content: 새 내용
            due_date: 새 납기일 (ISO 8601 문자열, 선택)

        Raises:
            ValueError: TODO를 찾을 수 없는 경우
        """
        # ID 변환
        todo_id_vo = TodoId.from_string(todo_id)

        # TODO 조회
        todo = self.repository.find_by_id(todo_id_vo)
        if todo is None:
            raise ValueError(f"TODO not found: {todo_id}")

        # 내용 수정
        content_vo = Content(value=content)
        todo.update_content(content_vo)

        # 납기일 수정
        due_date_vo = DueDate.from_string(due_date) if due_date else None
        todo.set_due_date(due_date_vo)

        # 저장
        self.repository.save(todo)

    def delete_todo(self, todo_id: str) -> None:
        """TODO 삭제

        Args:
            todo_id: TODO ID (문자열)

        Raises:
            ValueError: TODO를 찾을 수 없는 경우
        """
        # ID 변환
        todo_id_vo = TodoId.from_string(todo_id)

        # 존재 확인
        todo = self.repository.find_by_id(todo_id_vo)
        if todo is None:
            raise ValueError(f"TODO not found: {todo_id}")

        # 삭제
        self.repository.delete(todo_id_vo)

    def toggle_complete(self, todo_id: str) -> None:
        """완료 상태 토글

        Args:
            todo_id: TODO ID (문자열)

        Raises:
            ValueError: TODO를 찾을 수 없는 경우
        """
        # ID 변환
        todo_id_vo = TodoId.from_string(todo_id)

        # TODO 조회
        todo = self.repository.find_by_id(todo_id_vo)
        if todo is None:
            raise ValueError(f"TODO not found: {todo_id}")

        # 완료 상태 토글
        if todo.completed:
            todo.uncomplete()
        else:
            todo.complete()

        # 저장
        self.repository.save(todo)

    def get_all_todos(self) -> List[Todo]:
        """전체 TODO 조회

        Returns:
            List[Todo]: 모든 TODO 리스트
        """
        return self.repository.find_all()
