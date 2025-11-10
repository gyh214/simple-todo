# -*- coding: utf-8 -*-
"""CheckForUpdatesUseCase - 업데이트 확인 Use Case"""

import logging
from typing import Optional
from datetime import datetime, timedelta

from ...domain.entities.release import Release
from ...domain.value_objects.app_version import AppVersion
from ...domain.services.version_comparison_service import VersionComparisonService
from ...infrastructure.repositories.github_release_repository import GitHubReleaseRepository
from ...infrastructure.repositories.update_settings_repository import UpdateSettingsRepository


logger = logging.getLogger(__name__)


class CheckForUpdatesUseCase:
    """업데이트 확인 비즈니스 로직을 담당하는 Use Case

    비즈니스 규칙:
    - check_interval_hours 경과 시에만 체크 수행
    - 건너뛴 버전은 알림 표시 안 함
    - 체크 시간을 자동으로 기록
    - 현재 버전보다 높은 릴리스만 반환

    Attributes:
        github_repo: GitHub 릴리스 repository
        settings_repo: 업데이트 설정 repository
        version_service: 버전 비교 서비스
        current_version: 현재 설치된 버전
        check_interval_hours: 체크 간격 (시간)

    Examples:
        >>> use_case = CheckForUpdatesUseCase(
        ...     github_repo,
        ...     settings_repo,
        ...     version_service,
        ...     AppVersion.from_string("2.4.0"),
        ...     check_interval_hours=24
        ... )
        >>> release = use_case.execute()
        >>> if release:
        ...     print(f"업데이트 가능: {release.version}")
    """

    def __init__(
        self,
        github_repo: GitHubReleaseRepository,
        settings_repo: UpdateSettingsRepository,
        version_service: VersionComparisonService,
        current_version: AppVersion,
        check_interval_hours: int = 24
    ):
        """CheckForUpdatesUseCase 초기화

        Args:
            github_repo: GitHub 릴리스 repository
            settings_repo: 업데이트 설정 repository
            version_service: 버전 비교 서비스
            current_version: 현재 설치된 버전
            check_interval_hours: 체크 간격 (시간, 기본값: 24)

        Raises:
            TypeError: 인자 타입이 유효하지 않은 경우
            ValueError: check_interval_hours가 0 이하인 경우
        """
        if not isinstance(github_repo, GitHubReleaseRepository):
            raise TypeError(
                f"github_repo는 GitHubReleaseRepository여야 합니다. "
                f"받은 타입: {type(github_repo)}"
            )

        if not isinstance(settings_repo, UpdateSettingsRepository):
            raise TypeError(
                f"settings_repo는 UpdateSettingsRepository여야 합니다. "
                f"받은 타입: {type(settings_repo)}"
            )

        if not isinstance(current_version, AppVersion):
            raise TypeError(
                f"current_version은 AppVersion이어야 합니다. "
                f"받은 타입: {type(current_version)}"
            )

        if check_interval_hours <= 0:
            raise ValueError(
                f"check_interval_hours는 0보다 커야 합니다: {check_interval_hours}"
            )

        self.github_repo = github_repo
        self.settings_repo = settings_repo
        self.version_service = version_service
        self.current_version = current_version
        self.check_interval_hours = check_interval_hours

        logger.info(
            f"CheckForUpdatesUseCase 초기화: "
            f"current_version={current_version}, "
            f"check_interval={check_interval_hours}시간"
        )

    def execute(self) -> Optional[Release]:
        """업데이트를 확인하고 가능한 릴리스를 반환합니다.

        비즈니스 흐름:
        1. 마지막 체크 시간 확인 (check_interval_hours 경과 여부)
        2. 경과하지 않았으면 None 반환 (체크 생략)
        3. GitHub에서 최신 릴리스 조회
        4. 현재 버전과 비교하여 업데이트 가능 여부 확인
        5. 건너뛴 버전 확인 (사용자가 건너뛴 버전이면 알림 안 함)
        6. 체크 시간 저장
        7. 업데이트 가능하면 Release 반환, 아니면 None

        Returns:
            Optional[Release]: 업데이트 가능한 릴리스 또는 None
                - None: 업데이트 없음 또는 건너뛴 버전 또는 체크 시간 미경과

        Note:
            이 메서드는 자동 체크 시 호출되며, check_interval_hours를 존중합니다.
            강제 체크를 원하면 force_check()를 사용하세요.
        """
        try:
            # 1. 체크 시간 확인
            if not self._should_check_now():
                logger.info("업데이트 체크 간격이 아직 경과하지 않았습니다")
                return None

            logger.info("업데이트 확인 시작...")

            # 2. GitHub에서 최신 릴리스 조회
            latest_release = self.github_repo.get_latest_release()

            if not latest_release:
                logger.info("최신 릴리스를 찾을 수 없습니다")
                # 체크 시간 저장 (실패해도 다음 체크까지 대기)
                self.settings_repo.save_last_check_time(datetime.now())
                return None

            logger.info(f"최신 릴리스 조회: {latest_release.version}")

            # 3. 현재 버전과 비교
            is_update_available = self.version_service.is_update_available(
                current=self.current_version,
                latest=latest_release.version
            )

            if not is_update_available:
                logger.info(
                    f"업데이트 없음: 현재 {self.current_version} == "
                    f"최신 {latest_release.version}"
                )
                self.settings_repo.save_last_check_time(datetime.now())
                return None

            # 4. 건너뛴 버전 확인
            skipped_version = self.settings_repo.get_skipped_version()
            should_notify = self.version_service.should_notify_user(
                current=self.current_version,
                latest=latest_release.version,
                skipped=skipped_version
            )

            if not should_notify:
                logger.info(
                    f"건너뛴 버전입니다: {latest_release.version} "
                    f"(skipped: {skipped_version})"
                )
                self.settings_repo.save_last_check_time(datetime.now())
                return None

            # 5. 체크 시간 저장
            self.settings_repo.save_last_check_time(datetime.now())

            # 6. 업데이트 타입 로깅
            update_type = self.version_service.get_update_type(
                current=self.current_version,
                latest=latest_release.version
            )
            logger.info(
                f"업데이트 가능: {self.current_version} -> {latest_release.version} "
                f"({update_type} update)"
            )

            return latest_release

        except Exception as e:
            logger.error(f"업데이트 확인 중 오류 발생: {e}", exc_info=True)
            # 오류 발생 시에도 체크 시간 저장 (무한 재시도 방지)
            try:
                self.settings_repo.save_last_check_time(datetime.now())
            except Exception:
                pass
            return None

    def force_check(self) -> Optional[Release]:
        """강제로 업데이트를 확인합니다 (check_interval_hours 무시).

        사용자가 수동으로 "업데이트 확인" 버튼을 클릭한 경우 사용됩니다.
        check_interval_hours를 무시하고 즉시 체크를 수행합니다.

        Returns:
            Optional[Release]: 업데이트 가능한 릴리스 또는 None

        Note:
            나머지 로직은 execute()와 동일합니다.
        """
        logger.info("강제 업데이트 확인 (check_interval 무시)")

        try:
            # 1. GitHub에서 최신 릴리스 조회
            latest_release = self.github_repo.get_latest_release()

            if not latest_release:
                logger.info("최신 릴리스를 찾을 수 없습니다")
                # 체크 시간 저장
                self.settings_repo.save_last_check_time(datetime.now())
                return None

            logger.info(f"최신 릴리스 조회: {latest_release.version}")

            # 2. 현재 버전과 비교
            is_update_available = self.version_service.is_update_available(
                current=self.current_version,
                latest=latest_release.version
            )

            if not is_update_available:
                logger.info(
                    f"업데이트 없음: 현재 {self.current_version} >= "
                    f"최신 {latest_release.version}"
                )
                self.settings_repo.save_last_check_time(datetime.now())
                return None

            # 3. 건너뛴 버전 확인
            skipped_version = self.settings_repo.get_skipped_version()
            should_notify = self.version_service.should_notify_user(
                current=self.current_version,
                latest=latest_release.version,
                skipped=skipped_version
            )

            if not should_notify:
                logger.info(
                    f"건너뛴 버전입니다: {latest_release.version} "
                    f"(skipped: {skipped_version})"
                )
                self.settings_repo.save_last_check_time(datetime.now())
                return None

            # 4. 체크 시간 저장
            self.settings_repo.save_last_check_time(datetime.now())

            # 5. 업데이트 타입 로깅
            update_type = self.version_service.get_update_type(
                current=self.current_version,
                latest=latest_release.version
            )
            logger.info(
                f"업데이트 가능: {self.current_version} -> {latest_release.version} "
                f"({update_type} update)"
            )

            return latest_release

        except Exception as e:
            logger.error(f"강제 업데이트 확인 중 오류 발생: {e}", exc_info=True)
            # 오류 발생 시에도 체크 시간 저장
            try:
                self.settings_repo.save_last_check_time(datetime.now())
            except Exception:
                pass
            return None

    def _should_check_now(self) -> bool:
        """지금 업데이트를 체크해야 하는지 확인합니다.

        마지막 체크 시간 + check_interval_hours < 현재 시간이면 True 반환.

        Returns:
            bool: 체크해야 하면 True
        """
        last_check_time = self.settings_repo.get_last_check_time()

        if last_check_time is None:
            # 한 번도 체크하지 않았으면 체크 수행
            logger.info("첫 업데이트 체크입니다")
            return True

        # 현재 시간
        now = datetime.now()

        # 다음 체크 시간 계산
        next_check_time = last_check_time + timedelta(hours=self.check_interval_hours)

        if now >= next_check_time:
            logger.info(
                f"체크 간격 경과: 마지막 체크 {last_check_time.isoformat()}, "
                f"다음 체크 {next_check_time.isoformat()}"
            )
            return True
        else:
            remaining_hours = (next_check_time - now).total_seconds() / 3600
            logger.debug(
                f"다음 체크까지 {remaining_hours:.1f}시간 남음 "
                f"(마지막 체크: {last_check_time.isoformat()})"
            )
            return False

    def __repr__(self) -> str:
        """개발자용 문자열 표현을 반환합니다."""
        return (
            f"CheckForUpdatesUseCase("
            f"current_version={self.current_version}, "
            f"check_interval={self.check_interval_hours}h)"
        )
