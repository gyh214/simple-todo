# -*- coding: utf-8 -*-
"""DataPreservationService - 데이터 무결성 보장 서비스"""

from typing import List
from datetime import datetime
from ...domain.entities.todo import Todo


class DataPreservationService:
    """데이터 무결성을 보장하는 서비스

    저장 전 데이터를 검증하고 필요시 수정합니다.
    """

    @staticmethod
    def validate_and_fix(todos: List[Todo]) -> List[Todo]:
        """TODO 리스트를 검증하고 수정합니다.

        Args:
            todos: 검증할 TODO 리스트

        Returns:
            List[Todo]: 검증 및 수정된 TODO 리스트

        검증 규칙:
        1. 모든 TODO는 유효한 ID 보유 (TodoId Value Object가 보장)
        2. order는 중복 없이 연속적 (섹션별)
        3. completed 상태와 섹션 일치
        4. createdAt 필드 보존 (누락 시 현재 시간)

        수정 사항:
        - order 중복 시 재계산
        - createdAt 누락 시 현재 시간으로 설정

        Raises:
            ValueError: 중복 ID가 있는 경우
        """
        # 1. ID 중복 검증 (예외 발생)
        DataPreservationService.validate_unique_ids(todos)

        # 2. createdAt 보장
        todos = DataPreservationService.ensure_created_at(todos)

        # 3. order 일관성 보장
        todos = DataPreservationService.ensure_order_consistency(todos)

        return todos

    @staticmethod
    def ensure_order_consistency(todos: List[Todo]) -> List[Todo]:
        """order 필드의 일관성을 보장합니다.

        Args:
            todos: TODO 리스트

        Returns:
            List[Todo]: order가 재계산된 TODO 리스트

        로직:
        - 진행중/완료 섹션별로 order를 0부터 순차적으로 설정
        - 중복 방지
        """
        # 1. 진행중(completed=False)과 완료(completed=True) 분리
        in_progress = [todo for todo in todos if not todo.completed]
        completed = [todo for todo in todos if todo.completed]

        # 2. 각 섹션의 order를 0부터 순차적으로 재설정
        for index, todo in enumerate(in_progress):
            todo.change_order(index)

        for index, todo in enumerate(completed):
            todo.change_order(index)

        # 3. 합쳐서 반환
        return in_progress + completed

    @staticmethod
    def ensure_created_at(todos: List[Todo]) -> List[Todo]:
        """createdAt 필드를 보장합니다.

        Args:
            todos: TODO 리스트

        Returns:
            List[Todo]: createdAt이 보장된 TODO 리스트

        로직:
        - createdAt이 None이거나 유효하지 않으면 현재 시간으로 설정
        """
        current_time = datetime.now()

        for todo in todos:
            # createdAt이 None이면 현재 시간으로 설정
            if todo.created_at is None:
                todo.created_at = current_time

        return todos

    @staticmethod
    def validate_unique_ids(todos: List[Todo]) -> bool:
        """ID 중복을 검사합니다.

        Args:
            todos: TODO 리스트

        Returns:
            bool: 중복이 없으면 True

        Raises:
            ValueError: 중복 ID가 있는 경우
        """
        # 1. 모든 TODO의 ID 추출
        ids = [str(todo.id) for todo in todos]

        # 2. set으로 중복 검사
        unique_ids = set(ids)

        # 3. 중복 시 ValueError 발생
        if len(ids) != len(unique_ids):
            # 중복된 ID 찾기
            seen = set()
            duplicates = set()
            for todo_id in ids:
                if todo_id in seen:
                    duplicates.add(todo_id)
                seen.add(todo_id)

            raise ValueError(f"Duplicate IDs found: {duplicates}")

        return True
