# -*- coding: utf-8 -*-
"""ChangeSortOrderUseCase - 정렬 순서 변경 Use Case"""

import logging
from typing import Literal
from ...domain.services.todo_sort_service import TodoSortService, SortOrder
from ...domain.interfaces.repository_interface import ITodoRepository

# 로깅 설정
logger = logging.getLogger(__name__)


class ChangeSortOrderUseCase:
    """정렬 순서 변경 Use Case

    비즈니스 규칙:
    - 정렬 드롭다운 변경 시 호출
    - 현재 표시 순서를 order 필드에 동기화
    - 새로운 정렬 적용
    """

    def __init__(self, repository: ITodoRepository):
        """ChangeSortOrderUseCase 초기화

        Args:
            repository: TODO 리포지토리
        """
        self.repository = repository

    def execute(self, sort_order: SortOrder) -> None:
        """정렬 순서를 변경하고 order를 동기화합니다.

        Args:
            sort_order: 새로운 정렬 순서 ("dueDate_asc", "dueDate_desc", "manual")

        로직:
        1. 모든 TODO 조회
        2. 섹션별로 분리 (in_progress, completed)
        3. 새로운 정렬 적용
        4. order 동기화 (현재 표시 순서를 order에 저장)
        5. 저장
        """
        logger.info(f"[ChangeSortOrder] Changing sort order to: {sort_order}")

        # 1. 모든 TODO 조회
        all_todos = self.repository.find_all()

        # 2. 섹션별로 분리 및 정렬
        in_progress_sorted, completed_sorted = TodoSortService.sort_by_section(
            all_todos, sort_order
        )

        # 3. order 동기화 (진행중 섹션)
        synced_in_progress = []
        if in_progress_sorted:
            synced_in_progress = TodoSortService.sync_order_with_current_sort(
                in_progress_sorted
            )
            logger.debug(f"[ChangeSortOrder] Synced {len(synced_in_progress)} in_progress todos")

        # 4. order 동기화 (완료 섹션)
        synced_completed = []
        if completed_sorted:
            synced_completed = TodoSortService.sync_order_with_current_sort(
                completed_sorted
            )
            logger.debug(f"[ChangeSortOrder] Synced {len(synced_completed)} completed todos")

        # 5. 병합 후 일괄 저장 (데이터 손실 방지)
        all_todos_merged = synced_in_progress + synced_completed
        self.repository.save_all(all_todos_merged)

        logger.info(f"[ChangeSortOrder] Sort order changed and orders synchronized")
