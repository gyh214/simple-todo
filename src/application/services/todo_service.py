# -*- coding: utf-8 -*-
"""TodoService - TODO CRUD 비즈니스 로직"""

from typing import List, Optional
import logging
from ...domain.entities.todo import Todo
from ...domain.value_objects.todo_id import TodoId
from ...domain.value_objects.content import Content
from ...domain.value_objects.due_date import DueDate
from ...domain.interfaces.repository_interface import ITodoRepository

# 로깅 설정
logger = logging.getLogger(__name__)


class TodoService:
    """Todo 비즈니스 로직을 처리하는 애플리케이션 서비스"""

    def __init__(self, repository: ITodoRepository):
        """TodoService 초기화

        Args:
            repository: TODO 리포지토리 구현체
        """
        self.repository = repository

    def _calculate_next_order(self) -> int:
        """진행중 TODO의 다음 order 값을 계산합니다 (공통 메서드).

        Returns:
            int: 다음 order 값
        """
        all_todos = self.repository.find_all()
        incomplete_todos = [todo for todo in all_todos if not todo.completed]

        if incomplete_todos:
            max_order = max(todo.order for todo in incomplete_todos)
            return max_order + 1
        return 0

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
        # 다음 order 계산 (공통 메서드 재사용)
        next_order = self._calculate_next_order()

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

    def delete_completed_todos(self) -> int:
        """완료된 TODO만 일괄 삭제

        Returns:
            int: 삭제된 개수
        """
        all_todos = self.repository.find_all()
        completed = [t for t in all_todos if t.completed]

        for todo in completed:
            self.repository.delete(todo.id)

        return len(completed)

    def delete_selected_todos(self, todo_ids: List[str]) -> int:
        """선택된 TODO 일괄 삭제

        Args:
            todo_ids: 삭제할 TODO ID 리스트 (문자열)

        Returns:
            int: 삭제된 개수
        """
        count = 0
        for todo_id in todo_ids:
            try:
                self.delete_todo(todo_id)  # 기존 메서드 재사용
                count += 1
            except ValueError:
                # TODO를 찾을 수 없는 경우 건너뛰기
                pass

        return count

    def restore_selected_todos(self, todos: List[Todo]) -> int:
        """선택된 TODO들을 현재 목록에 복구합니다.

        Args:
            todos: 복구할 TODO 리스트

        Returns:
            int: 실제로 복구된 개수
        """
        # 1. 현재 TODO 목록 조회
        all_todos = self.repository.find_all()

        # 2. 기존 ID 목록 (중복 체크용)
        existing_ids = {todo.id for todo in all_todos}

        # 3. 다음 order 계산 (공통 메서드 재사용)
        next_order = self._calculate_next_order()

        # 4. TODO 복구
        restored_count = 0
        for todo in todos:
            # 중복 체크
            if todo.id in existing_ids:
                logger.warning(f"TODO already exists, skipping: {todo.id}")
                continue

            # order 재조정 (진행중 TODO만)
            if not todo.completed:
                todo.change_order(next_order)
                next_order += 1

            # 저장 (repository.save 재사용)
            self.repository.save(todo)
            restored_count += 1

        logger.info(f"Restored {restored_count} TODOs from backup")
        return restored_count
