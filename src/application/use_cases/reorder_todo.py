# -*- coding: utf-8 -*-
"""ReorderTodoUseCase - TODO 순서 변경 Use Case"""

import logging
from typing import Literal, List
from ...domain.entities.todo import Todo
from ...domain.value_objects.todo_id import TodoId
from ...domain.interfaces.repository_interface import ITodoRepository
from ...domain.services.todo_sort_service import TodoSortService


SectionType = Literal["in_progress", "completed"]

# 로깅 설정
logger = logging.getLogger(__name__)


class ReorderTodoUseCase:
    """TODO 순서 변경 Use Case

    비즈니스 규칙:
    - 같은 섹션 내에서만 이동 가능
    - 섹션 간 이동은 불가 (완료 처리로만 섹션 이동)
    - 드래그 시작 시: 현재 표시 순서를 order 필드에 동기화
    - 드롭 시: order 필드를 0부터 순차적으로 재계산
    - 모든 변경사항 즉시 저장
    """

    def __init__(self, repository: ITodoRepository):
        """ReorderTodoUseCase 초기화

        Args:
            repository: TODO 리포지토리
        """
        self.repository = repository

    def execute(self, todo_id: str, new_position: int, section: SectionType) -> None:
        """TODO 순서를 변경합니다 (order 업데이트).

        Args:
            todo_id: 이동할 TODO ID (UUID 문자열)
            new_position: 새 위치 (0부터 시작)
            section: "in_progress" 또는 "completed"

        Raises:
            ValueError: TODO를 찾을 수 없거나 다른 섹션에 있는 경우
            ValueError: 유효하지 않은 UUID 문자열인 경우
            ValueError: new_position이 음수인 경우

        로직:
        1. 드래그 시작 시: 현재 표시 순서를 order에 동기화
        2. 해당 섹션의 TODO들만 조회
        3. 이동할 TODO를 찾아 리스트에서 제거
        4. new_position에 삽입
        5. 모든 TODO의 order를 0부터 순차적으로 재설정
        6. repository.save_all()로 일괄 저장
        """
        # 유효성 검증
        self._validate_inputs(new_position)

        # Order 동기화
        self._sync_order_with_current_sort(section)

        # TODO 찾기 및 검증
        target_todo, target_index, section_todos = self._find_and_validate_todo(
            todo_id, section
        )

        # 재정렬
        reordered_todos = self._reorder_in_section(
            section_todos, target_todo, target_index, new_position
        )

        # 저장 및 설정 업데이트
        self._save_reordered_todos(reordered_todos, section)

    def _validate_inputs(self, new_position: int) -> None:
        """입력 유효성 검증

        Args:
            new_position: 새 위치

        Raises:
            ValueError: new_position이 음수인 경우
        """
        if new_position < 0:
            raise ValueError(f"new_position must be non-negative, got {new_position}")

    def _sync_order_with_current_sort(self, section: SectionType) -> None:
        """드래그 시작 시 order 동기화

        현재 표시 순서를 order 필드에 저장합니다.

        Args:
            section: 대상 섹션
        """
        all_todos = self.repository.find_all()

        # 현재 섹션 TODO 조회
        current_section_todos = self._get_section_todos(all_todos, section)

        # Order 동기화
        synced_todos = TodoSortService.sync_order_with_current_sort(current_section_todos)

        # 다른 섹션 TODO 가져오기
        other_section_todos = self._get_section_todos(all_todos, self._get_opposite_section(section))

        # 저장
        all_todos_merged = synced_todos + other_section_todos
        self.repository.save_all(all_todos_merged)
        logger.info(f"[Reorder] Order synchronized before drag in '{section}' section")

    def _find_and_validate_todo(
        self, todo_id: str, section: SectionType
    ) -> tuple[Todo, int, List[Todo]]:
        """TODO 찾기 및 섹션 검증

        Args:
            todo_id: 찾을 TODO ID (UUID 문자열)
            section: 대상 섹션

        Returns:
            (타겟 TODO, 타겟 인덱스, 섹션 TODO 리스트) 튜플

        Raises:
            ValueError: TODO를 찾을 수 없거나 다른 섹션에 있는 경우
        """
        target_todo_id = TodoId.from_string(todo_id)
        all_todos = self.repository.find_all()

        # 현재 섹션 TODO 조회
        section_todos = self._get_section_todos(all_todos, section)

        # 타겟 TODO 찾기
        target_todo: Todo | None = None
        target_index: int = -1

        for idx, todo in enumerate(section_todos):
            if todo.id.value == target_todo_id.value:
                target_todo = todo
                target_index = idx
                break

        # 검증
        if target_todo is None:
            self._raise_todo_not_found_error(todo_id, section, all_todos, target_todo_id)

        return target_todo, target_index, section_todos

    def _reorder_in_section(
        self,
        section_todos: List[Todo],
        target_todo: Todo,
        target_index: int,
        new_position: int
    ) -> List[Todo]:
        """섹션 내에서 TODO 재정렬

        Args:
            section_todos: 섹션 TODO 리스트
            target_todo: 이동할 TODO
            target_index: 이동할 TODO의 현재 인덱스
            new_position: 새 위치

        Returns:
            재정렬된 TODO 리스트
        """
        # 리스트에서 제거 후 new_position에 삽입
        section_todos.pop(target_index)
        insert_position = min(new_position, len(section_todos))
        section_todos.insert(insert_position, target_todo)

        # Order 재계산
        for idx, todo in enumerate(section_todos):
            todo.change_order(idx)
            logger.debug(f"Updated order: {str(todo.id)[:8]}... -> order={idx}")

        logger.info(
            f"Reordered TODO '{str(target_todo.id)[:8]}...' to position {insert_position}"
        )

        return section_todos

    def _save_reordered_todos(self, section_todos: List[Todo], section: SectionType) -> None:
        """재정렬된 TODO 저장 및 설정 업데이트

        Args:
            section_todos: 재정렬된 섹션 TODO 리스트
            section: 대상 섹션
        """
        all_todos = self.repository.find_all()

        # 다른 섹션 TODO 가져오기
        other_section_todos = self._get_section_todos(all_todos, self._get_opposite_section(section))

        # 전체 TODO 병합 후 저장
        all_todos_final = section_todos + other_section_todos
        self.repository.save_all(all_todos_final)

        # MANUAL 모드로 전환
        self.repository.update_settings({"sortOrder": "manual"})
        logger.info("[Reorder] Automatically switched to MANUAL mode after drag & drop")

    def _get_section_todos(self, all_todos: List[Todo], section: SectionType) -> List[Todo]:
        """섹션별 TODO 조회

        Args:
            all_todos: 전체 TODO 리스트
            section: 대상 섹션

        Returns:
            해당 섹션의 TODO 리스트
        """
        if section == "in_progress":
            return [todo for todo in all_todos if not todo.completed]
        else:
            return [todo for todo in all_todos if todo.completed]

    def _get_opposite_section(self, section: SectionType) -> SectionType:
        """반대 섹션 반환

        Args:
            section: 현재 섹션

        Returns:
            반대 섹션
        """
        return "completed" if section == "in_progress" else "in_progress"

    def _raise_todo_not_found_error(
        self, todo_id: str, section: SectionType, all_todos: List[Todo], target_todo_id: TodoId
    ) -> None:
        """TODO를 찾을 수 없을 때 에러 발생

        Args:
            todo_id: 찾을 TODO ID (UUID 문자열)
            section: 대상 섹션
            all_todos: 전체 TODO 리스트
            target_todo_id: 변환된 TODO ID

        Raises:
            ValueError: TODO를 찾을 수 없거나 다른 섹션에 있는 경우
        """
        # 다른 섹션에 있는지 확인
        other_section = self._get_opposite_section(section)
        other_section_todos = self._get_section_todos(all_todos, other_section)

        for todo in other_section_todos:
            if todo.id.value == target_todo_id.value:
                raise ValueError(
                    f"TODO '{todo_id}' is in '{other_section}' section, "
                    f"not in '{section}' section"
                )

        # 완전히 존재하지 않는 경우
        raise ValueError(f"TODO not found: {todo_id}")
