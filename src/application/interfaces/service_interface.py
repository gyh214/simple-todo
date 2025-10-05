# -*- coding: utf-8 -*-
"""
애플리케이션 서비스 인터페이스

비즈니스 로직 추상화
"""
from abc import ABC, abstractmethod
from typing import List, Optional

# 순환 참조 방지를 위한 TYPE_CHECKING
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...domain.entities.todo import Todo


class ITodoService(ABC):
    """TODO 서비스 인터페이스"""

    @abstractmethod
    def create_todo(self, content: str, due_date: Optional[str] = None) -> 'Todo':
        """
        새 TODO 생성

        Args:
            content: TODO 내용
            due_date: 납기일 (선택)

        Returns:
            생성된 TODO
        """
        pass

    @abstractmethod
    def update_todo(self, todo_id: str, content: str, due_date: Optional[str] = None) -> None:
        """
        TODO 수정

        Args:
            todo_id: TODO ID
            content: 새 내용
            due_date: 새 납기일 (선택)
        """
        pass

    @abstractmethod
    def delete_todo(self, todo_id: str) -> None:
        """
        TODO 삭제

        Args:
            todo_id: TODO ID
        """
        pass

    @abstractmethod
    def toggle_complete(self, todo_id: str) -> None:
        """
        완료 상태 토글

        Args:
            todo_id: TODO ID
        """
        pass

    @abstractmethod
    def get_all_todos(self) -> List['Todo']:
        """
        모든 TODO 조회

        Returns:
            모든 TODO 리스트
        """
        pass
