# -*- coding: utf-8 -*-
"""AppVersion Value Object - Semantic Versioning 지원"""

from dataclasses import dataclass
from typing import Union
import re


@dataclass(frozen=True)
class AppVersion:
    """애플리케이션 버전을 나타내는 Value Object

    Semantic Versioning(major.minor.patch)을 지원하며, 불변성을 보장합니다.
    버전 간 비교 연산을 지원합니다.

    Examples:
        >>> v1 = AppVersion.from_string("2.4")
        >>> v2 = AppVersion.from_string("2.5.1")
        >>> v1 < v2
        True
        >>> str(v1)
        '2.4.0'
    """

    major: int
    minor: int
    patch: int = 0

    def __post_init__(self):
        """생성 후 검증을 수행합니다."""
        if self.major < 0 or self.minor < 0 or self.patch < 0:
            raise ValueError(
                f"버전 숫자는 0 이상이어야 합니다: {self.major}.{self.minor}.{self.patch}"
            )

    @classmethod
    def from_string(cls, version_str: str) -> 'AppVersion':
        """문자열로부터 AppVersion 인스턴스를 생성합니다.

        지원 형식:
        - "major.minor.patch" (예: "2.4.1")
        - "major.minor" (예: "2.4") - patch는 0으로 설정
        - "vX.Y.Z" 형식도 지원 (v 접두사 제거)

        Args:
            version_str: 버전 문자열

        Returns:
            AppVersion: 생성된 AppVersion 인스턴스

        Raises:
            ValueError: 유효하지 않은 버전 문자열인 경우
        """
        if not version_str or not isinstance(version_str, str):
            raise ValueError(f"버전 문자열이 필요합니다: {version_str}")

        # "v" 접두사 제거
        clean_version = version_str.strip().lower()
        if clean_version.startswith('v'):
            clean_version = clean_version[1:]

        # 정규식으로 버전 파싱 (major.minor 또는 major.minor.patch)
        pattern = r'^(\d+)\.(\d+)(?:\.(\d+))?$'
        match = re.match(pattern, clean_version)

        if not match:
            raise ValueError(
                f"유효하지 않은 버전 형식입니다: {version_str} "
                f"(형식: 'major.minor.patch' 또는 'major.minor')"
            )

        major = int(match.group(1))
        minor = int(match.group(2))
        patch = int(match.group(3)) if match.group(3) else 0

        return cls(major=major, minor=minor, patch=patch)

    def __str__(self) -> str:
        """버전을 문자열로 변환합니다.

        Returns:
            str: "major.minor.patch" 형식의 문자열
        """
        return f"{self.major}.{self.minor}.{self.patch}"

    def __repr__(self) -> str:
        """개발자용 문자열 표현을 반환합니다.

        Returns:
            str: AppVersion 표현 문자열
        """
        return f"AppVersion('{self.major}.{self.minor}.{self.patch}')"

    def _as_tuple(self) -> tuple:
        """비교를 위한 튜플 표현을 반환합니다.

        Returns:
            tuple: (major, minor, patch) 튜플
        """
        return (self.major, self.minor, self.patch)

    def __lt__(self, other: 'AppVersion') -> bool:
        """작음(less than) 비교 연산자.

        Args:
            other: 비교할 다른 AppVersion

        Returns:
            bool: self < other인 경우 True

        Raises:
            TypeError: AppVersion이 아닌 객체와 비교 시
        """
        if not isinstance(other, AppVersion):
            raise TypeError(
                f"AppVersion은 AppVersion과만 비교 가능합니다. "
                f"받은 타입: {type(other)}"
            )
        return self._as_tuple() < other._as_tuple()

    def __le__(self, other: 'AppVersion') -> bool:
        """작거나 같음(less than or equal) 비교 연산자.

        Args:
            other: 비교할 다른 AppVersion

        Returns:
            bool: self <= other인 경우 True
        """
        if not isinstance(other, AppVersion):
            raise TypeError(
                f"AppVersion은 AppVersion과만 비교 가능합니다. "
                f"받은 타입: {type(other)}"
            )
        return self._as_tuple() <= other._as_tuple()

    def __eq__(self, other: object) -> bool:
        """같음(equal) 비교 연산자.

        Args:
            other: 비교할 다른 객체

        Returns:
            bool: self == other인 경우 True
        """
        if not isinstance(other, AppVersion):
            return False
        return self._as_tuple() == other._as_tuple()

    def __ne__(self, other: object) -> bool:
        """같지 않음(not equal) 비교 연산자.

        Args:
            other: 비교할 다른 객체

        Returns:
            bool: self != other인 경우 True
        """
        return not self.__eq__(other)

    def __gt__(self, other: 'AppVersion') -> bool:
        """큼(greater than) 비교 연산자.

        Args:
            other: 비교할 다른 AppVersion

        Returns:
            bool: self > other인 경우 True
        """
        if not isinstance(other, AppVersion):
            raise TypeError(
                f"AppVersion은 AppVersion과만 비교 가능합니다. "
                f"받은 타입: {type(other)}"
            )
        return self._as_tuple() > other._as_tuple()

    def __ge__(self, other: 'AppVersion') -> bool:
        """크거나 같음(greater than or equal) 비교 연산자.

        Args:
            other: 비교할 다른 AppVersion

        Returns:
            bool: self >= other인 경우 True
        """
        if not isinstance(other, AppVersion):
            raise TypeError(
                f"AppVersion은 AppVersion과만 비교 가능합니다. "
                f"받은 타입: {type(other)}"
            )
        return self._as_tuple() >= other._as_tuple()

    def __hash__(self) -> int:
        """해시값을 반환합니다 (딕셔너리 키로 사용 가능).

        Returns:
            int: 버전의 해시값
        """
        return hash(self._as_tuple())
