# -*- coding: utf-8 -*-
"""UpdateManager - 전체 업데이트 프로세스 조율"""

import logging
from pathlib import Path
from PyQt6.QtWidgets import QMainWindow, QMessageBox
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QCloseEvent
from typing import TYPE_CHECKING, Optional

from ..workers.update_check_worker import UpdateCheckWorker
from ..workers.update_download_worker import UpdateDownloadWorker
from ..dialogs.update_available_dialog import UpdateAvailableDialog
from ..dialogs.update_progress_dialog import UpdateProgressDialog

if TYPE_CHECKING:
    from ...application.services.update_scheduler_service import UpdateSchedulerService
    from ...application.use_cases.check_for_updates import CheckForUpdatesUseCase
    from ...application.use_cases.download_update import DownloadUpdateUseCase
    from ...application.use_cases.install_update import InstallUpdateUseCase
    from ...domain.entities.release import Release
    from ...domain.value_objects.app_version import AppVersion


logger = logging.getLogger(__name__)


class UpdateManager:
    """전체 업데이트 프로세스를 조율하는 Manager

    앱 시작 시 자동 체크, 수동 체크, 다운로드, 설치까지 전체 흐름을 관리합니다.
    Worker와 Dialog를 조율하여 비동기 업데이트 프로세스를 구현합니다.

    프로세스 흐름:
    1. check_for_updates_on_startup() - 앱 시작 시 자동 체크
    2. UpdateCheckWorker 실행 (백그라운드)
    3. update_available 시 UpdateAvailableDialog 표시
    4. 사용자가 "업데이트" 선택 시 다운로드 시작
    5. UpdateDownloadWorker 실행 (백그라운드)
    6. UpdateProgressDialog로 진행률 표시
    7. 다운로드 완료 시 설치 시작
    8. InstallUpdateUseCase로 앱 재시작

    Examples:
        >>> manager = UpdateManager(
        ...     parent_window,
        ...     scheduler,
        ...     check_use_case,
        ...     download_use_case,
        ...     install_use_case,
        ...     current_version
        ... )
        >>> manager.check_for_updates_on_startup()
    """

    def __init__(
        self,
        parent_window: QMainWindow,
        scheduler: 'UpdateSchedulerService',
        check_use_case: 'CheckForUpdatesUseCase',
        download_use_case: 'DownloadUpdateUseCase',
        install_use_case: 'InstallUpdateUseCase',
        current_version: 'AppVersion'
    ):
        """UpdateManager 초기화

        Args:
            parent_window: 메인 윈도우
            scheduler: 업데이트 스케줄러 서비스
            check_use_case: 업데이트 확인 Use Case
            download_use_case: 다운로드 Use Case
            install_use_case: 설치 Use Case
            current_version: 현재 앱 버전
        """
        self.parent_window = parent_window
        self.scheduler = scheduler
        self.check_use_case = check_use_case
        self.download_use_case = download_use_case
        self.install_use_case = install_use_case
        self.current_version = current_version

        # Worker 및 Dialog 참조
        self.check_worker: Optional[UpdateCheckWorker] = None
        self.download_worker: Optional[UpdateDownloadWorker] = None
        self.progress_dialog: Optional[UpdateProgressDialog] = None

        logger.info(
            f"UpdateManager 초기화: current_version={current_version}"
        )

    def check_for_updates_on_startup(self):
        """앱 시작 시 자동 업데이트 체크를 수행합니다.

        앱 시작 3초 후에 백그라운드에서 체크를 수행합니다.
        UpdateSchedulerService로 체크 여부를 확인한 후 실행합니다.

        Note:
            QTimer를 사용하여 앱 시작 후 3초 뒤에 체크를 수행합니다.
            이는 앱 초기화가 완료된 후 체크하기 위함입니다.
        """
        # 자동 체크가 활성화되어 있는지 확인
        if not self.scheduler.should_check_on_startup():
            logger.info("자동 업데이트 체크 건너뛰기")
            return

        # 3초 후 체크 시작
        logger.info("앱 시작 3초 후 자동 업데이트 체크 예약")
        QTimer.singleShot(3000, self._start_auto_check)

    def check_for_updates_manual(self):
        """수동으로 업데이트를 확인합니다.

        사용자가 "업데이트 확인" 버튼을 클릭했을 때 호출됩니다.
        check_interval_hours를 무시하고 즉시 체크를 수행합니다.

        Note:
            is_force_check=True를 사용하여 interval을 무시하고 강제 체크를 수행합니다.
        """
        logger.info("수동 업데이트 체크 시작")

        # 건너뛴 버전 초기화 (수동 체크 시 모든 버전 알림)
        self.scheduler.reset_skipped_version()

        # Worker 생성 및 시작 (is_force_check=True로 interval 무시)
        self.check_worker = UpdateCheckWorker(self.check_use_case, is_force_check=True)
        self.check_worker.update_available.connect(self._on_update_available)
        self.check_worker.no_update.connect(self._on_no_update_manual)
        self.check_worker.check_failed.connect(self._on_check_failed)
        self.check_worker.start()

        logger.info("수동 업데이트 체크 Worker 시작 (강제 체크 모드)")

    def _start_auto_check(self):
        """자동 업데이트 체크를 시작합니다 (내부 메서드).

        앱 시작 3초 후에 호출되며, 백그라운드에서 체크를 수행합니다.
        """
        logger.info("자동 업데이트 체크 시작")

        # Worker 생성 및 시작
        self.check_worker = UpdateCheckWorker(self.check_use_case)
        self.check_worker.update_available.connect(self._on_update_available)
        self.check_worker.no_update.connect(self._on_no_update_auto)
        self.check_worker.check_failed.connect(self._on_check_failed)
        self.check_worker.start()

        logger.info("자동 업데이트 체크 Worker 시작")

    def _on_update_available(self, release: 'Release'):
        """업데이트가 발견되었을 때 호출됩니다.

        UpdateAvailableDialog를 표시하고 사용자의 선택을 받습니다.

        Args:
            release: 발견된 새 릴리스
        """
        logger.info(f"업데이트 발견: v{release.version}")

        # Worker 정리
        if self.check_worker:
            self.check_worker.deleteLater()
            self.check_worker = None

        # 업데이트 다이얼로그 표시
        self._show_update_dialog(release)

    def _on_no_update_auto(self):
        """업데이트가 없을 때 호출됩니다 (자동 체크).

        자동 체크에서는 별도의 메시지를 표시하지 않습니다.
        """
        logger.info("업데이트 없음 (자동 체크)")

        # Worker 정리
        if self.check_worker:
            self.check_worker.deleteLater()
            self.check_worker = None

    def _on_no_update_manual(self):
        """업데이트가 없을 때 호출됩니다 (수동 체크).

        수동 체크에서는 "최신 버전입니다" 메시지를 표시합니다.
        """
        logger.info("업데이트 없음 (수동 체크)")

        # Worker 정리
        if self.check_worker:
            self.check_worker.deleteLater()
            self.check_worker = None

        # 메시지 박스 표시
        QMessageBox.information(
            self.parent_window,
            "업데이트 확인",
            f"현재 최신 버전(v{self.current_version})을 사용 중입니다."
        )

    def _on_check_failed(self, error_message: str):
        """업데이트 체크 실패 시 호출됩니다.

        Args:
            error_message: 에러 메시지
        """
        logger.error(f"업데이트 체크 실패: {error_message}")

        # Worker 정리
        if self.check_worker:
            self.check_worker.deleteLater()
            self.check_worker = None

        # 에러 메시지 표시 (선택적)
        # 자동 체크에서는 에러 메시지를 표시하지 않음 (사용자 방해 최소화)
        # 수동 체크에서만 표시하려면 플래그 추가 필요

    def _show_update_dialog(self, release: 'Release'):
        """업데이트 알림 다이얼로그를 표시합니다.

        Args:
            release: 표시할 릴리스 정보
        """
        try:
            dialog = UpdateAvailableDialog(
                self.parent_window,
                release,
                self.current_version
            )
            dialog.exec()

            # 사용자 선택 처리
            choice = dialog.get_user_choice()

            if choice == "update":
                # 업데이트 시작
                self._start_download(release)
            elif choice == "skip":
                # 이 버전 건너뛰기
                logger.info(f"버전 {release.version} 건너뛰기 설정")
                self.scheduler.skip_version(release.version)
            else:
                # 나중에
                logger.info("업데이트 나중에")

        except Exception as e:
            logger.error(f"업데이트 알림 다이얼로그 표시 실패: {e}", exc_info=True)
            QMessageBox.critical(
                self.parent_window,
                "업데이트 오류",
                f"업데이트 알림을 표시할 수 없습니다.\n\n{str(e)}"
            )

    def _start_download(self, release: 'Release'):
        """다운로드를 시작합니다.

        Args:
            release: 다운로드할 릴리스
        """
        logger.info(f"다운로드 시작: {release.asset_name}")

        # 진행률 다이얼로그 생성
        self.progress_dialog = UpdateProgressDialog(
            self.parent_window,
            release
        )
        self.progress_dialog.show()

        # Worker 생성 및 시작
        self.download_worker = UpdateDownloadWorker(
            self.download_use_case,
            release
        )
        self.download_worker.progress_changed.connect(
            self._on_download_progress
        )
        self.download_worker.download_complete.connect(
            self._on_download_complete
        )
        self.download_worker.download_failed.connect(
            self._on_download_failed
        )
        self.download_worker.start()

        logger.info("다운로드 Worker 시작")

    def _on_download_progress(self, downloaded: int, total: int):
        """다운로드 진행률 업데이트.

        Args:
            downloaded: 다운로드된 바이트 수
            total: 전체 파일 크기
        """
        if self.progress_dialog:
            self.progress_dialog.update_progress(downloaded, total)

    def _on_download_complete(self, file_path: Path):
        """다운로드 완료 시 호출됩니다.

        Args:
            file_path: 다운로드된 파일 경로
        """
        logger.info(f"다운로드 완료: {file_path}")

        # Worker 정리
        if self.download_worker:
            self.download_worker.deleteLater()
            self.download_worker = None

        # 진행률 다이얼로그 완료 표시
        if self.progress_dialog:
            self.progress_dialog.set_complete()

        # 업데이트 설치 시작
        self._install_update(file_path)

    def _on_download_failed(self, error_message: str):
        """다운로드 실패 시 호출됩니다.

        Args:
            error_message: 에러 메시지
        """
        logger.error(f"다운로드 실패: {error_message}")

        # Worker 정리
        if self.download_worker:
            self.download_worker.deleteLater()
            self.download_worker = None

        # 진행률 다이얼로그 닫기
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None

        # 에러 메시지 표시
        QMessageBox.critical(
            self.parent_window,
            "다운로드 실패",
            f"업데이트 파일 다운로드에 실패했습니다.\n\n{error_message}"
        )

    def _install_update(self, file_path: Path):
        """업데이트를 설치합니다.

        Args:
            file_path: 새 버전 exe 파일 경로
        """
        logger.info(f"업데이트 설치 시작: {file_path}")

        # 진행률 다이얼로그 닫기
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None

        # 확인 메시지
        reply = QMessageBox.question(
            self.parent_window,
            "업데이트 설치",
            "업데이트를 설치하려면 애플리케이션을 종료하고 재시작해야 합니다.\n\n"
            "지금 설치하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )

        if reply != QMessageBox.StandardButton.Yes:
            logger.info("사용자가 설치를 취소했습니다")
            return

        # 설치 시작
        try:
            # 설치 전 준비 (데이터 저장 등)
            self.install_use_case.prepare_for_shutdown()

            # 설치 실행 (앱 종료됨)
            success = self.install_use_case.execute(file_path)

            if success:
                logger.info("업데이트 설치 시작됨. 앱 종료 중...")
                # 앱 종료 (Batch script가 재시작함)
                from PyQt6.QtWidgets import QApplication
                QApplication.quit()
            else:
                raise Exception("설치 스크립트 실행 실패")

        except Exception as e:
            logger.error(f"업데이트 설치 실패: {e}", exc_info=True)
            QMessageBox.critical(
                self.parent_window,
                "설치 실패",
                f"업데이트 설치에 실패했습니다.\n\n{str(e)}"
            )

    def __repr__(self) -> str:
        """개발자용 문자열 표현을 반환합니다."""
        return f"UpdateManager(current_version={self.current_version})"
