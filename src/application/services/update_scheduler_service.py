# -*- coding: utf-8 -*-
"""UpdateSchedulerService - 업데이트 체크 스케줄링 및 조율 서비스"""

import logging
from typing import Optional

from ...domain.entities.release import Release
from ...domain.value_objects.app_version import AppVersion
from ...infrastructure.repositories.update_settings_repository import UpdateSettingsRepository
from ..use_cases.check_for_updates import CheckForUpdatesUseCase


logger = logging.getLogger(__name__)


class UpdateSchedulerService:
    """업데이트 체크 스케줄링 및 조율을 담당하는 Application 서비스

    앱 시작 시 업데이트 체크 여부를 결정하고, 사용자의 업데이트 설정을 관리합니다.
    Use Case와 Repository 사이의 조율자 역할을 합니다.

    비즈니스 규칙:
    - 자동 체크가 비활성화된 경우 체크하지 않음
    - 사용자가 건너뛴 버전은 알림 표시 안 함
    - 건너뛴 버전 초기화 기능 제공

    Attributes:
        check_use_case: 업데이트 확인 use case
        settings_repo: 업데이트 설정 repository

    Examples:
        >>> scheduler = UpdateSchedulerService(check_use_case, settings_repo)
        >>> if scheduler.should_check_on_startup():
        ...     release = scheduler.check_and_notify()
        ...     if release:
        ...         print(f"업데이트 가능: {release.version}")
    """

    def __init__(
        self,
        check_use_case: CheckForUpdatesUseCase,
        settings_repo: UpdateSettingsRepository
    ):
        """UpdateSchedulerService 초기화

        Args:
            check_use_case: 업데이트 확인 use case
            settings_repo: 업데이트 설정 repository

        Raises:
            TypeError: 인자 타입이 유효하지 않은 경우
        """
        if not isinstance(check_use_case, CheckForUpdatesUseCase):
            raise TypeError(
                f"check_use_case는 CheckForUpdatesUseCase여야 합니다. "
                f"받은 타입: {type(check_use_case)}"
            )

        if not isinstance(settings_repo, UpdateSettingsRepository):
            raise TypeError(
                f"settings_repo는 UpdateSettingsRepository여야 합니다. "
                f"받은 타입: {type(settings_repo)}"
            )

        self.check_use_case = check_use_case
        self.settings_repo = settings_repo

        logger.info("UpdateSchedulerService 초기화")

    def should_check_on_startup(self) -> bool:
        """앱 시작 시 업데이트를 체크해야 하는지 결정합니다.

        다음 조건을 모두 만족하면 체크를 수행합니다:
        1. 자동 체크가 활성화되어 있음 (settings_repo.is_auto_check_enabled())
        2. check_interval_hours가 경과함 (내부적으로 CheckForUpdatesUseCase에서 확인)

        Returns:
            bool: 체크해야 하면 True

        Note:
            이 메서드는 앱 시작 시 호출되며, False를 반환하면 체크를 건너뜁니다.

        Examples:
            >>> if scheduler.should_check_on_startup():
            ...     release = scheduler.check_and_notify()
        """
        try:
            # 1. 자동 체크 활성화 여부 확인
            is_auto_check_enabled = self.settings_repo.is_auto_check_enabled()

            if not is_auto_check_enabled:
                logger.info("자동 업데이트 체크가 비활성화되어 있습니다")
                return False

            logger.info("자동 업데이트 체크가 활성화되어 있습니다")

            # 2. check_interval_hours 경과 여부는 CheckForUpdatesUseCase에서 확인
            # (should_check_on_startup은 자동 체크 활성화 여부만 확인)
            return True

        except Exception as e:
            logger.error(f"업데이트 체크 여부 확인 중 오류: {e}", exc_info=True)
            # 오류 발생 시 안전하게 체크 건너뛰기
            return False

    def check_and_notify(self) -> Optional[Release]:
        """업데이트를 확인하고 알림이 필요한 릴리스를 반환합니다.

        내부적으로 CheckForUpdatesUseCase.execute()를 호출합니다.

        Returns:
            Optional[Release]: 알림이 필요한 릴리스 또는 None
                - None: 업데이트 없음 또는 건너뛴 버전 또는 체크 간격 미경과

        Note:
            이 메서드는 check_interval_hours를 존중합니다.
            강제 체크를 원하면 check_use_case.force_check()를 직접 호출하세요.

        Examples:
            >>> release = scheduler.check_and_notify()
            >>> if release:
            ...     # UI에서 업데이트 다이얼로그 표시
            ...     show_update_dialog(release)
        """
        try:
            logger.info("업데이트 확인 및 알림 체크...")
            release = self.check_use_case.execute()

            if release:
                logger.info(f"업데이트 알림 필요: {release.version}")
            else:
                logger.info("업데이트 알림 불필요")

            return release

        except Exception as e:
            logger.error(f"업데이트 확인 중 오류: {e}", exc_info=True)
            return None

    def skip_version(self, version: AppVersion) -> bool:
        """특정 버전을 건너뛰도록 설정합니다.

        사용자가 "이 버전 건너뛰기" 버튼을 클릭했을 때 호출됩니다.

        Args:
            version: 건너뛸 버전

        Returns:
            bool: 성공 여부

        Raises:
            TypeError: version이 AppVersion이 아닌 경우

        Examples:
            >>> release = scheduler.check_and_notify()
            >>> if release and user_clicked_skip:
            ...     scheduler.skip_version(release.version)
        """
        if not isinstance(version, AppVersion):
            raise TypeError(
                f"version은 AppVersion이어야 합니다. "
                f"받은 타입: {type(version)}"
            )

        try:
            logger.info(f"버전 건너뛰기 설정: {version}")
            success = self.settings_repo.set_skipped_version(version)

            if success:
                logger.info(f"버전 {version} 건너뛰기 설정 완료")
            else:
                logger.error(f"버전 {version} 건너뛰기 설정 실패")

            return success

        except Exception as e:
            logger.error(f"버전 건너뛰기 설정 중 오류: {e}", exc_info=True)
            return False

    def reset_skipped_version(self) -> bool:
        """건너뛴 버전 설정을 초기화합니다.

        사용자가 수동으로 "업데이트 확인" 버튼을 클릭했을 때,
        이전에 건너뛴 버전을 다시 알림 받을 수 있도록 초기화합니다.

        Returns:
            bool: 성공 여부

        Examples:
            >>> # 사용자가 "업데이트 확인" 버튼 클릭
            >>> scheduler.reset_skipped_version()
            >>> release = check_use_case.force_check()
        """
        try:
            logger.info("건너뛴 버전 초기화")
            success = self.settings_repo.set_skipped_version(None)

            if success:
                logger.info("건너뛴 버전 초기화 완료")
            else:
                logger.error("건너뛴 버전 초기화 실패")

            return success

        except Exception as e:
            logger.error(f"건너뛴 버전 초기화 중 오류: {e}", exc_info=True)
            return False

    def enable_auto_check(self, enabled: bool) -> bool:
        """자동 업데이트 체크를 활성화/비활성화합니다.

        사용자가 설정에서 "자동 업데이트 체크" 옵션을 변경했을 때 호출됩니다.

        Args:
            enabled: 활성화 여부 (True: 활성화, False: 비활성화)

        Returns:
            bool: 성공 여부

        Raises:
            TypeError: enabled가 bool이 아닌 경우

        Examples:
            >>> # 사용자가 설정에서 자동 체크 비활성화
            >>> scheduler.enable_auto_check(False)
        """
        if not isinstance(enabled, bool):
            raise TypeError(
                f"enabled는 bool이어야 합니다. "
                f"받은 타입: {type(enabled)}"
            )

        try:
            logger.info(f"자동 업데이트 체크 {'활성화' if enabled else '비활성화'}")
            success = self.settings_repo.set_auto_check_enabled(enabled)

            if success:
                logger.info(
                    f"자동 업데이트 체크 {'활성화' if enabled else '비활성화'} 완료"
                )
            else:
                logger.error(
                    f"자동 업데이트 체크 {'활성화' if enabled else '비활성화'} 실패"
                )

            return success

        except Exception as e:
            logger.error(
                f"자동 업데이트 체크 설정 중 오류: {e}",
                exc_info=True
            )
            return False

    def get_auto_check_status(self) -> bool:
        """자동 업데이트 체크 활성화 여부를 조회합니다.

        Returns:
            bool: 활성화 여부 (기본값: True)

        Examples:
            >>> is_enabled = scheduler.get_auto_check_status()
            >>> print(f"자동 체크: {'활성화' if is_enabled else '비활성화'}")
        """
        try:
            return self.settings_repo.is_auto_check_enabled()
        except Exception as e:
            logger.error(f"자동 체크 상태 조회 중 오류: {e}", exc_info=True)
            # 오류 발생 시 기본값 True 반환
            return True

    def get_skipped_version(self) -> Optional[AppVersion]:
        """현재 건너뛴 버전을 조회합니다.

        Returns:
            Optional[AppVersion]: 건너뛴 버전 또는 None

        Examples:
            >>> skipped = scheduler.get_skipped_version()
            >>> if skipped:
            ...     print(f"건너뛴 버전: {skipped}")
        """
        try:
            return self.settings_repo.get_skipped_version()
        except Exception as e:
            logger.error(f"건너뛴 버전 조회 중 오류: {e}", exc_info=True)
            return None

    def __repr__(self) -> str:
        """개발자용 문자열 표현을 반환합니다."""
        return "UpdateSchedulerService()"
