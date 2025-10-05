# -*- coding: utf-8 -*-
"""TodoSortService - TODO 정렬 서비스"""

import logging
from typing import List, Literal
from ..entities.todo import Todo


SortOrder = Literal["dueDate_asc", "dueDate_desc", "today_first", "manual"]

# 로깅 설정
logger = logging.getLogger(__name__)


class TodoSortService:
    """Todo 정렬을 담당하는 도메인 서비스

    납기일 기준 정렬 로직을 제공합니다.
    """

    @staticmethod
    def sort_todos(todos: List[Todo], sort_order: SortOrder) -> List[Todo]:
        """Todo 리스트를 정렬합니다.

        정렬 규칙:
        1. manual: order 필드만으로 정렬 (사용자 지정 순서)
        2. dueDate_asc: 납기일 빠른순 → 납기일 없는 항목 (각각 내용순 정렬)
        3. dueDate_desc: 납기일 없는 항목 → 납기일 늦은순 (각각 내용순 정렬)
        4. 같은 납기일을 가진 항목은 내용(content) 순서대로 정렬

        Args:
            todos: 정렬할 Todo 리스트
            sort_order: 정렬 순서 ("dueDate_asc", "dueDate_desc", "manual")

        Returns:
            List[Todo]: 정렬된 Todo 리스트

        Raises:
            ValueError: 유효하지 않은 정렬 순서인 경우
        """
        if sort_order not in ["dueDate_asc", "dueDate_desc", "today_first", "manual"]:
            raise ValueError(f"Invalid sort order: {sort_order}")

        # MANUAL 모드: order 필드만으로 정렬 (납기일 무시)
        if sort_order == "manual":
            sorted_todos = sorted(todos, key=lambda t: t.order)
            logger.debug(f"[Manual Order] Sorted {len(sorted_todos)} todos by order field only")
            return sorted_todos

        # TODAY_FIRST 모드: 오늘 납기 우선 정렬
        if sort_order == "today_first":
            # 1. 납기일이 오늘인 TODO 분리
            from datetime import datetime
            today = datetime.now()
            todos_today = [
                todo for todo in todos
                if todo.due_date is not None and todo.due_date.days_until(today) == 0
            ]
            # 2. 오늘이 아닌 납기일 있는 TODO 분리
            todos_with_due_date = [
                todo for todo in todos
                if todo.due_date is not None and todo.due_date.days_until(today) != 0
            ]
            # 3. 납기일 없는 TODO 분리
            todos_without_due_date = [todo for todo in todos if todo.due_date is None]

            # 4. 각 그룹 정렬 (내용순)
            todos_today.sort(key=lambda t: t.content.value)
            todos_with_due_date.sort(key=lambda t: (t.due_date.value, t.content.value))  # type: ignore
            todos_without_due_date.sort(key=lambda t: t.content.value)

            # 5. 결합: 오늘 → 납기일 있음 → 납기일 없음
            logger.debug(
                f"[Today First] Sorted: today={len(todos_today)}, "
                f"with_due_date={len(todos_with_due_date)}, "
                f"without_due_date={len(todos_without_due_date)}"
            )
            return todos_today + todos_with_due_date + todos_without_due_date

        # 납기일 있는 항목과 없는 항목 분리
        todos_with_due_date = [todo for todo in todos if todo.due_date is not None]
        todos_without_due_date = [todo for todo in todos if todo.due_date is None]

        # 납기일 있는 항목 정렬
        if sort_order == "dueDate_asc":
            # 빠른순: 날짜 오름차순, 같으면 내용 오름차순
            todos_with_due_date.sort(
                key=lambda t: (t.due_date.value, t.content.value)  # type: ignore
            )
            logger.debug(f"[Due Date Asc] Sorted {len(todos_with_due_date)} todos by dueDate, content")
        else:  # dueDate_desc
            # 늦은순: 날짜 내림차순, 같으면 내용 오름차순
            todos_with_due_date.sort(
                key=lambda t: (t.due_date.value, t.content.value),  # type: ignore
                reverse=True
            )
            logger.debug(f"[Due Date Desc] Sorted {len(todos_with_due_date)} todos by dueDate, content")

        # 납기일 없는 항목 정렬 (내용 순)
        todos_without_due_date.sort(key=lambda t: t.content.value)

        # 결합: dueDate_desc일 때는 납기일 없는 항목을 먼저 배치
        if sort_order == "dueDate_desc":
            return todos_without_due_date + todos_with_due_date
        else:
            return todos_with_due_date + todos_without_due_date

    @staticmethod
    def sort_by_section(
        todos: List[Todo],
        sort_order: SortOrder
    ) -> tuple[List[Todo], List[Todo]]:
        """Todo 리스트를 섹션(진행중/완료)별로 분리하고 정렬합니다.

        Args:
            todos: 정렬할 Todo 리스트
            sort_order: 정렬 순서 ("dueDate_asc", "dueDate_desc")

        Returns:
            tuple[List[Todo], List[Todo]]: (진행중 Todo 리스트, 완료 Todo 리스트)
        """
        # 진행중/완료 분리
        in_progress = [todo for todo in todos if not todo.completed]
        completed = [todo for todo in todos if todo.completed]

        # 각 섹션 정렬
        in_progress_sorted = TodoSortService.sort_todos(in_progress, sort_order)
        completed_sorted = TodoSortService.sort_todos(completed, sort_order)

        return in_progress_sorted, completed_sorted

    @staticmethod
    def sync_order_with_current_sort(todos: List[Todo]) -> List[Todo]:
        """현재 정렬 순서에 맞게 order 값을 동기화합니다.

        정렬 드롭다운 변경 시 또는 드래그 시작 전에 호출되어,
        현재 표시 순서를 order 필드에 저장합니다.

        Args:
            todos: 현재 정렬된 TODO 리스트

        Returns:
            List[Todo]: order가 동기화된 TODO 리스트
        """
        if not todos:
            logger.debug("[Order Sync] Empty list, returning as-is")
            return todos

        logger.debug(f"[Order Sync] Starting sync for {len(todos)} todos")

        updated_count = 0

        for new_order, todo in enumerate(todos):
            if todo.order != new_order:
                old_order = todo.order
                # order 변경 (mutable 방식)
                todo.change_order(new_order)
                updated_count += 1
                logger.debug(
                    f"[Order Sync] Updated: {str(todo.id)[:8]}... "
                    f"{old_order} -> {new_order}"
                )

        if updated_count == 0:
            logger.debug("[Order Sync] No changes needed")
        else:
            logger.info(f"[Order Sync] Completed: {updated_count} todos updated")

        return todos
