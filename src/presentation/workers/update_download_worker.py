# -*- coding: utf-8 -*-
"""UpdateDownloadWorker - 백그라운드 다운로드 Worker"""

import logging
from pathlib import Path
from PyQt6.QtCore import QThread, pyqtSignal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...application.use_cases.download_update import DownloadUpdateUseCase
    from ...domain.entities.release import Release


logger = logging.getLogger(__name__)


class UpdateDownloadWorker(QThread):
    """백그라운드에서 업데이트 파일을 다운로드하는 QThread Worker

    UI 메인 스레드를 차단하지 않고 대용량 파일을 다운로드합니다.
    진행률을 주기적으로 시그널을 통해 전달합니다.

    Signals:
        progress_changed: 다운로드 진행률 변경 시 발생 (downloaded, total)
        download_complete: 다운로드 완료 시 발생 (파일 경로 전달)
        download_failed: 다운로드 실패 시 발생 (에러 메시지 전달)

    Examples:
        >>> worker = UpdateDownloadWorker(download_use_case, release)
        >>> worker.progress_changed.connect(on_progress)
        >>> worker.download_complete.connect(on_complete)
        >>> worker.download_failed.connect(on_failed)
        >>> worker.start()
    """

    # 시그널 정의
    progress_changed = pyqtSignal(int, int)  # (downloaded_bytes, total_bytes)
    download_complete = pyqtSignal(object)  # Path 객체
    download_failed = pyqtSignal(str)  # 에러 메시지

    def __init__(
        self,
        download_use_case: 'DownloadUpdateUseCase',
        release: 'Release'
    ):
        """UpdateDownloadWorker 초기화

        Args:
            download_use_case: 다운로드 Use Case
            release: 다운로드할 릴리스 정보

        Raises:
            TypeError: 인자 타입이 유효하지 않은 경우
        """
        super().__init__()

        # lazy import로 순환 참조 방지
        from ...application.use_cases.download_update import DownloadUpdateUseCase
        from ...domain.entities.release import Release

        if not isinstance(download_use_case, DownloadUpdateUseCase):
            raise TypeError(
                f"download_use_case는 DownloadUpdateUseCase여야 합니다. "
                f"받은 타입: {type(download_use_case)}"
            )

        if not isinstance(release, Release):
            raise TypeError(
                f"release는 Release여야 합니다. "
                f"받은 타입: {type(release)}"
            )

        self.download_use_case = download_use_case
        self.release = release

        logger.info(f"UpdateDownloadWorker 초기화: {release.version}")

    def run(self):
        """백그라운드에서 다운로드를 실행합니다.

        QThread의 run() 메서드를 오버라이드합니다.
        이 메서드는 별도의 스레드에서 실행되므로 UI를 차단하지 않습니다.

        작업 흐름:
        1. DownloadUpdateUseCase.execute() 호출
        2. 진행률 콜백을 통해 progress_changed 시그널 발생
        3. 다운로드 완료 시 download_complete 시그널 발생
        4. 실패 시 download_failed 시그널 발생

        Note:
            이 메서드는 직접 호출하지 말고 start()를 호출하세요.
        """
        try:
            logger.info(f"백그라운드 다운로드 시작: {self.release.asset_name}")

            # 진행률 콜백 정의
            def progress_callback(downloaded: int, total: int):
                """다운로드 진행률을 시그널로 전달합니다."""
                self.progress_changed.emit(downloaded, total)

            # Use Case 실행
            file_path = self.download_use_case.execute(
                release=self.release,
                progress_callback=progress_callback
            )

            if file_path and file_path.exists():
                logger.info(f"다운로드 완료: {file_path}")
                self.download_complete.emit(file_path)
            else:
                error_msg = "다운로드 실패: 파일이 생성되지 않았습니다"
                logger.error(error_msg)
                self.download_failed.emit(error_msg)

        except Exception as e:
            error_msg = f"다운로드 중 오류 발생: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.download_failed.emit(error_msg)

    def __repr__(self) -> str:
        """개발자용 문자열 표현을 반환합니다."""
        return f"UpdateDownloadWorker(release={self.release.version})"
