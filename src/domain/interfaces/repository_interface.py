# -*- coding: utf-8 -*-
"""
리포지토리 인터페이스

데이터 영속성 추상화
"""
from abc import ABC, abstractmethod
from typing import List, Optional

# 순환 참조 방지를 위한 TYPE_CHECKING
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..entities.todo import Todo
    from ..value_objects.todo_id import TodoId


class ITodoRepository(ABC):
    """TODO 리포지토리 인터페이스"""

    @abstractmethod
    def find_all(self) -> List['Todo']:
        """
        모든 TODO 조회

        Returns:
            모든 TODO 리스트
        """
        pass

    @abstractmethod
    def find_by_id(self, todo_id: 'TodoId') -> Optional['Todo']:
        """
        ID로 TODO 조회

        Args:
            todo_id: TODO ID

        Returns:
            TODO 엔티티 (없으면 None)
        """
        pass

    @abstractmethod
    def save(self, todo: 'Todo') -> None:
        """
        TODO 저장

        Args:
            todo: TODO 엔티티
        """
        pass

    @abstractmethod
    def save_all(self, todos: List['Todo']) -> None:
        """
        여러 TODO 저장

        Args:
            todos: TODO 리스트
        """
        pass

    @abstractmethod
    def delete(self, todo_id: 'TodoId') -> None:
        """
        TODO 삭제

        Args:
            todo_id: TODO ID
        """
        pass
