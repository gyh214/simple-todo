# -*- coding: utf-8 -*-
"""TodoSearchService - TODO 검색 로직 (재사용 가능)"""

from typing import List
from ..entities.todo import Todo
from ..entities.subtask import SubTask


class TodoSearchService:
    """TODO 검색 로직을 처리하는 도메인 서비스"""

    @staticmethod
    def search_todos(query: str, todos: List[Todo]) -> List[Todo]:
        """내용 기준 검색 (대소문자 무시, 메인 할일 + 하위 할일 모두 검색)

        Args:
            query: 검색어
            todos: 전체 TODO 리스트

        Returns:
            List[Todo]: 검색 결과 (query가 비어있으면 전체 반환)
            - 메인 할일 content에 query가 있는 경우
            - 또는 하위 할일 중 하나라도 query가 있는 경우
        """
        if not query.strip():
            return todos

        query_lower = query.lower()

        result = []
        for todo in todos:
            # 메인 할일 content에서 검색
            if query_lower in todo.content.value.lower():
                result.append(todo)
                continue

            # 하위 할일에서 검색
            if TodoSearchService._search_in_subtasks(todo.subtasks, query_lower):
                result.append(todo)

        return result

    @staticmethod
    def _search_in_subtasks(subtasks: List[SubTask], query: str) -> bool:
        """하위 할일에서 검색

        Args:
            subtasks: 검색 대상 SubTask 리스트
            query: 검색 쿼리 (소문자로 변환된 상태)

        Returns:
            bool: 하나라도 매칭되면 True
        """
        for subtask in subtasks:
            if query in subtask.content.value.lower():
                return True
        return False
