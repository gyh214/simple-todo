# -*- coding: utf-8 -*-
"""TodoSearchService - TODO 검색 로직 (재사용 가능)"""

from typing import List
from ..entities.todo import Todo


class TodoSearchService:
    """TODO 검색 로직을 처리하는 도메인 서비스"""

    @staticmethod
    def search_todos(query: str, todos: List[Todo]) -> List[Todo]:
        """내용 기준 검색 (대소문자 무시)

        Args:
            query: 검색어
            todos: 전체 TODO 리스트

        Returns:
            List[Todo]: 검색 결과 (query가 비어있으면 전체 반환)
        """
        if not query.strip():
            return todos

        query_lower = query.lower()
        return [
            todo for todo in todos
            if query_lower in todo.content.value.lower()
        ]
