# -*- coding: utf-8 -*-
"""TodoSortUseCase - TODO 정렬 Use Case"""

from typing import List, Tuple
from ...domain.entities.todo import Todo
from ...domain.services.todo_sort_service import TodoSortService, SortOrder
from ...domain.interfaces.repository_interface import ITodoRepository


class TodoSortUseCase:
    """TODO 정렬 Use Case

    비즈니스 규칙:
    - 납기일 빠른순/늦은순 선택 가능
    - 납기일 없는 항목은 항상 맨 뒤
    - 같은 납기일은 order 순서 유지
    - 진행중/완료 섹션 독립적 정렬
    """

    def __init__(self, repository: ITodoRepository):
        """TodoSortUseCase 초기화

        Args:
            repository: TODO 리포지토리
        """
        self.repository = repository

    def execute(self, sort_order: SortOrder) -> Tuple[List[Todo], List[Todo]]:
        """TODO를 정렬합니다.

        Args:
            sort_order: 정렬 순서 ("dueDate_asc" 또는 "dueDate_desc")

        Returns:
            Tuple[List[Todo], List[Todo]]: (진행중 TODO 리스트, 완료 TODO 리스트)

        정렬 규칙:
        - 납기일 없는 항목은 맨 뒤
        - 납기일 있는 항목은 납기일 순서대로
        - 같은 납기일은 order 순

        Raises:
            ValueError: 유효하지 않은 정렬 순서인 경우
        """
        # 1. repository.find_all()로 모든 TODO 조회
        all_todos = self.repository.find_all()

        # 2. TodoSortService.sort_by_section()으로 정렬
        in_progress, completed = TodoSortService.sort_by_section(
            todos=all_todos,
            sort_order=sort_order
        )

        # 3. 정렬된 (진행중, 완료) 튜플 반환
        return in_progress, completed
