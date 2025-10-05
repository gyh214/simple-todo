# -*- coding: utf-8 -*-
"""Content Value Object - TODO 내용"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Content:
    """Todo의 내용을 나타내는 Value Object

    1-1000자 제한, 빈 문자열 불가, 앞뒤 공백 자동 제거
    """

    value: str

    MIN_LENGTH = 1
    MAX_LENGTH = 1000

    def __post_init__(self) -> None:
        """인스턴스 생성 후 검증을 수행합니다.

        Raises:
            ValueError: 내용이 유효하지 않은 경우
        """
        # frozen=True이므로 object.__setattr__ 사용
        trimmed_value = self.value.strip()

        if not trimmed_value:
            raise ValueError("Content cannot be empty or whitespace only")

        if len(trimmed_value) < self.MIN_LENGTH:
            raise ValueError(f"Content must be at least {self.MIN_LENGTH} character(s)")

        if len(trimmed_value) > self.MAX_LENGTH:
            raise ValueError(f"Content must not exceed {self.MAX_LENGTH} characters")

        # 공백이 제거된 값으로 업데이트
        if trimmed_value != self.value:
            object.__setattr__(self, 'value', trimmed_value)

    def __str__(self) -> str:
        """Content를 문자열로 변환합니다.

        Returns:
            str: 내용 문자열
        """
        return self.value

    def __repr__(self) -> str:
        """Content의 개발자용 문자열 표현을 반환합니다.

        Returns:
            str: Content 표현 문자열
        """
        return f"Content('{self.value}')"
