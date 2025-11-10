# -*- coding: utf-8 -*-
"""VersionComparisonService - 버전 비교 비즈니스 로직"""

from typing import Optional

from ..value_objects.app_version import AppVersion


class VersionComparisonService:
    """버전 비교 관련 비즈니스 로직을 담당하는 도메인 서비스

    상태를 가지지 않으며, 순수한 버전 비교 로직만 제공합니다.
    모든 메서드는 static method로 구현됩니다.
    """

    @staticmethod
    def compare(v1: AppVersion, v2: AppVersion) -> int:
        """두 버전을 비교합니다.

        Args:
            v1: 첫 번째 버전
            v2: 두 번째 버전

        Returns:
            int:
                - -1: v1 < v2
                - 0: v1 == v2
                - 1: v1 > v2

        Raises:
            TypeError: 인자가 AppVersion이 아닌 경우

        Examples:
            >>> v1 = AppVersion.from_string("2.4.0")
            >>> v2 = AppVersion.from_string("2.5.1")
            >>> VersionComparisonService.compare(v1, v2)
            -1
        """
        if not isinstance(v1, AppVersion):
            raise TypeError(f"v1은 AppVersion이어야 합니다. 받은 타입: {type(v1)}")
        if not isinstance(v2, AppVersion):
            raise TypeError(f"v2는 AppVersion이어야 합니다. 받은 타입: {type(v2)}")

        if v1 < v2:
            return -1
        elif v1 > v2:
            return 1
        else:
            return 0

    @staticmethod
    def is_update_available(current: AppVersion, latest: AppVersion) -> bool:
        """업데이트가 가능한지 확인합니다.

        최신 버전이 현재 버전보다 높으면 업데이트가 가능합니다.

        Args:
            current: 현재 설치된 버전
            latest: 최신 릴리스 버전

        Returns:
            bool: 업데이트가 가능하면 True

        Raises:
            TypeError: 인자가 AppVersion이 아닌 경우

        Examples:
            >>> current = AppVersion.from_string("2.4.0")
            >>> latest = AppVersion.from_string("2.5.0")
            >>> VersionComparisonService.is_update_available(current, latest)
            True
        """
        if not isinstance(current, AppVersion):
            raise TypeError(
                f"current는 AppVersion이어야 합니다. 받은 타입: {type(current)}"
            )
        if not isinstance(latest, AppVersion):
            raise TypeError(
                f"latest는 AppVersion이어야 합니다. 받은 타입: {type(latest)}"
            )

        return latest > current

    @staticmethod
    def should_notify_user(
        current: AppVersion,
        latest: AppVersion,
        skipped: Optional[AppVersion] = None
    ) -> bool:
        """사용자에게 업데이트 알림을 표시해야 하는지 결정합니다.

        다음 조건을 모두 만족하면 알림을 표시합니다:
        1. 업데이트가 가능한 경우 (latest > current)
        2. 사용자가 건너뛴 버전이 아닌 경우

        Args:
            current: 현재 설치된 버전
            latest: 최신 릴리스 버전
            skipped: 사용자가 건너뛴 버전 (선택사항)

        Returns:
            bool: 알림을 표시해야 하면 True

        Raises:
            TypeError: 인자가 AppVersion이 아닌 경우

        Examples:
            >>> current = AppVersion.from_string("2.4.0")
            >>> latest = AppVersion.from_string("2.5.0")
            >>> skipped = AppVersion.from_string("2.5.0")
            >>> VersionComparisonService.should_notify_user(current, latest, skipped)
            False  # 건너뛴 버전이므로 알림 표시 안 함
        """
        if not isinstance(current, AppVersion):
            raise TypeError(
                f"current는 AppVersion이어야 합니다. 받은 타입: {type(current)}"
            )
        if not isinstance(latest, AppVersion):
            raise TypeError(
                f"latest는 AppVersion이어야 합니다. 받은 타입: {type(latest)}"
            )
        if skipped is not None and not isinstance(skipped, AppVersion):
            raise TypeError(
                f"skipped는 AppVersion이거나 None이어야 합니다. "
                f"받은 타입: {type(skipped)}"
            )

        # 업데이트가 없으면 알림 표시 안 함
        if not VersionComparisonService.is_update_available(current, latest):
            return False

        # 사용자가 건너뛴 버전이면 알림 표시 안 함
        if skipped is not None and latest == skipped:
            return False

        # 그 외의 경우 알림 표시
        return True

    @staticmethod
    def is_major_update(current: AppVersion, latest: AppVersion) -> bool:
        """메이저 버전 업데이트인지 확인합니다.

        메이저 버전이 변경된 경우 True를 반환합니다.

        Args:
            current: 현재 설치된 버전
            latest: 최신 릴리스 버전

        Returns:
            bool: 메이저 버전 업데이트인 경우 True

        Raises:
            TypeError: 인자가 AppVersion이 아닌 경우

        Examples:
            >>> current = AppVersion.from_string("2.4.0")
            >>> latest = AppVersion.from_string("3.0.0")
            >>> VersionComparisonService.is_major_update(current, latest)
            True
        """
        if not isinstance(current, AppVersion):
            raise TypeError(
                f"current는 AppVersion이어야 합니다. 받은 타입: {type(current)}"
            )
        if not isinstance(latest, AppVersion):
            raise TypeError(
                f"latest는 AppVersion이어야 합니다. 받은 타입: {type(latest)}"
            )

        return latest.major > current.major

    @staticmethod
    def is_minor_update(current: AppVersion, latest: AppVersion) -> bool:
        """마이너 버전 업데이트인지 확인합니다.

        메이저 버전은 같지만 마이너 버전이 변경된 경우 True를 반환합니다.

        Args:
            current: 현재 설치된 버전
            latest: 최신 릴리스 버전

        Returns:
            bool: 마이너 버전 업데이트인 경우 True

        Raises:
            TypeError: 인자가 AppVersion이 아닌 경우

        Examples:
            >>> current = AppVersion.from_string("2.4.0")
            >>> latest = AppVersion.from_string("2.5.0")
            >>> VersionComparisonService.is_minor_update(current, latest)
            True
        """
        if not isinstance(current, AppVersion):
            raise TypeError(
                f"current는 AppVersion이어야 합니다. 받은 타입: {type(current)}"
            )
        if not isinstance(latest, AppVersion):
            raise TypeError(
                f"latest는 AppVersion이어야 합니다. 받은 타입: {type(latest)}"
            )

        return (
            latest.major == current.major and
            latest.minor > current.minor
        )

    @staticmethod
    def is_patch_update(current: AppVersion, latest: AppVersion) -> bool:
        """패치 버전 업데이트인지 확인합니다.

        메이저와 마이너 버전은 같지만 패치 버전이 변경된 경우 True를 반환합니다.

        Args:
            current: 현재 설치된 버전
            latest: 최신 릴리스 버전

        Returns:
            bool: 패치 버전 업데이트인 경우 True

        Raises:
            TypeError: 인자가 AppVersion이 아닌 경우

        Examples:
            >>> current = AppVersion.from_string("2.4.0")
            >>> latest = AppVersion.from_string("2.4.1")
            >>> VersionComparisonService.is_patch_update(current, latest)
            True
        """
        if not isinstance(current, AppVersion):
            raise TypeError(
                f"current는 AppVersion이어야 합니다. 받은 타입: {type(current)}"
            )
        if not isinstance(latest, AppVersion):
            raise TypeError(
                f"latest는 AppVersion이어야 합니다. 받은 타입: {type(latest)}"
            )

        return (
            latest.major == current.major and
            latest.minor == current.minor and
            latest.patch > current.patch
        )

    @staticmethod
    def get_update_type(current: AppVersion, latest: AppVersion) -> str:
        """업데이트 타입을 문자열로 반환합니다.

        Args:
            current: 현재 설치된 버전
            latest: 최신 릴리스 버전

        Returns:
            str: 업데이트 타입
                - "major": 메이저 업데이트
                - "minor": 마이너 업데이트
                - "patch": 패치 업데이트
                - "none": 업데이트 없음
                - "downgrade": 다운그레이드

        Raises:
            TypeError: 인자가 AppVersion이 아닌 경우

        Examples:
            >>> current = AppVersion.from_string("2.4.0")
            >>> latest = AppVersion.from_string("3.0.0")
            >>> VersionComparisonService.get_update_type(current, latest)
            'major'
        """
        if not isinstance(current, AppVersion):
            raise TypeError(
                f"current는 AppVersion이어야 합니다. 받은 타입: {type(current)}"
            )
        if not isinstance(latest, AppVersion):
            raise TypeError(
                f"latest는 AppVersion이어야 합니다. 받은 타입: {type(latest)}"
            )

        if latest < current:
            return "downgrade"
        elif latest == current:
            return "none"
        elif VersionComparisonService.is_major_update(current, latest):
            return "major"
        elif VersionComparisonService.is_minor_update(current, latest):
            return "minor"
        else:  # is_patch_update
            return "patch"
