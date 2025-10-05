# -*- coding: utf-8 -*-
"""TodoId Value Object - UUID 기반 불변 식별자"""

from dataclasses import dataclass
from uuid import UUID, uuid4


@dataclass(frozen=True)
class TodoId:
    """Todo의 고유 식별자를 나타내는 Value Object

    UUID를 기반으로 하며, 불변성을 보장합니다.
    """

    value: UUID

    @staticmethod
    def generate() -> 'TodoId':
        """새로운 UUID를 생성하여 TodoId 인스턴스를 반환합니다.

        Returns:
            TodoId: 새로 생성된 TodoId 인스턴스
        """
        return TodoId(value=uuid4())

    @staticmethod
    def from_string(id_str: str) -> 'TodoId':
        """문자열로부터 TodoId 인스턴스를 생성합니다.

        Args:
            id_str: UUID 문자열

        Returns:
            TodoId: 생성된 TodoId 인스턴스

        Raises:
            ValueError: 유효하지 않은 UUID 문자열인 경우
        """
        try:
            return TodoId(value=UUID(id_str))
        except ValueError as e:
            raise ValueError(f"Invalid UUID string: {id_str}") from e

    def __str__(self) -> str:
        """TodoId를 문자열로 변환합니다.

        Returns:
            str: UUID 문자열
        """
        return str(self.value)

    def __repr__(self) -> str:
        """TodoId의 개발자용 문자열 표현을 반환합니다.

        Returns:
            str: TodoId 표현 문자열
        """
        return f"TodoId('{self.value}')"
