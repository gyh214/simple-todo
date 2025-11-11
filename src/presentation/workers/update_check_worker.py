# -*- coding: utf-8 -*-
"""UpdateCheckWorker - 백그라운드 업데이트 체크 Worker"""

import logging
from PyQt6.QtCore import QThread, pyqtSignal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...application.use_cases.check_for_updates import CheckForUpdatesUseCase


logger = logging.getLogger(__name__)


class UpdateCheckWorker(QThread):
    """백그라운드에서 업데이트를 확인하는 QThread Worker

    UI 메인 스레드를 차단하지 않고 GitHub API를 통해 업데이트를 확인합니다.
    작업이 완료되면 시그널을 통해 결과를 전달합니다.

    Signals:
        update_available: 업데이트가 있을 때 발생 (Release 객체 전달)
        no_update: 업데이트가 없을 때 발생
        check_failed: 체크 실패 시 발생 (에러 메시지 전달)

    Examples:
        >>> worker = UpdateCheckWorker(check_use_case)
        >>> worker.update_available.connect(on_update_available)
        >>> worker.no_update.connect(on_no_update)
        >>> worker.check_failed.connect(on_check_failed)
        >>> worker.start()
    """

    # 시그널 정의
    update_available = pyqtSignal(object)  # Release 객체
    no_update = pyqtSignal()
    check_failed = pyqtSignal(str)  # 에러 메시지

    def __init__(self, check_use_case: 'CheckForUpdatesUseCase', is_force_check: bool = False):
        """UpdateCheckWorker 초기화

        Args:
            check_use_case: 업데이트 체크 Use Case
            is_force_check: 강제 체크 여부 (True = 24시간 interval 무시)

        Raises:
            TypeError: check_use_case가 CheckForUpdatesUseCase가 아닌 경우
        """
        super().__init__()

        # lazy import로 순환 참조 방지
        from ...application.use_cases.check_for_updates import CheckForUpdatesUseCase

        if not isinstance(check_use_case, CheckForUpdatesUseCase):
            raise TypeError(
                f"check_use_case는 CheckForUpdatesUseCase여야 합니다. "
                f"받은 타입: {type(check_use_case)}"
            )

        self.check_use_case = check_use_case
        self.is_force_check = is_force_check
        logger.info(f"UpdateCheckWorker 초기화 (force_check={is_force_check})")

    def run(self):
        """백그라운드에서 업데이트 체크를 실행합니다.

        QThread의 run() 메서드를 오버라이드합니다.
        이 메서드는 별도의 스레드에서 실행되므로 UI를 차단하지 않습니다.

        작업 흐름:
        1. is_force_check 플래그에 따라 force_check() 또는 execute() 호출
        2. 결과에 따라 적절한 시그널 발생
        3. 예외 발생 시 check_failed 시그널 발생

        Note:
            이 메서드는 직접 호출하지 말고 start()를 호출하세요.
        """
        try:
            logger.info(f"백그라운드 업데이트 체크 시작... (force_check={self.is_force_check})")

            # Use Case 실행 (강제 체크 여부에 따라 다른 메서드 호출)
            if self.is_force_check:
                logger.info("강제 업데이트 체크 실행 (interval 무시)")
                release = self.check_use_case.force_check()
            else:
                logger.info("일반 업데이트 체크 실행 (interval 확인)")
                release = self.check_use_case.execute()

            if release:
                logger.info(f"업데이트 발견: {release.version}")
                self.update_available.emit(release)
            else:
                logger.info("업데이트 없음")
                self.no_update.emit()

        except Exception as e:
            error_msg = f"업데이트 체크 실패: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.check_failed.emit(error_msg)

    def __repr__(self) -> str:
        """개발자용 문자열 표현을 반환합니다."""
        return "UpdateCheckWorker()"
