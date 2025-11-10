# -*- coding: utf-8 -*-
"""DownloadUpdateUseCase - 업데이트 다운로드 Use Case"""

import logging
from pathlib import Path
from typing import Optional, Callable

from ...domain.entities.release import Release
from ...infrastructure.services.update_downloader_service import UpdateDownloaderService


logger = logging.getLogger(__name__)


class DownloadUpdateUseCase:
    """업데이트 파일 다운로드를 관리하는 Use Case

    비즈니스 규칙:
    - 다운로드 후 파일 크기 검증 수행
    - 진행률을 콜백으로 전달 (UI 업데이트)
    - 실패 시 임시 파일 자동 정리
    - 최종 파일 경로 반환

    Attributes:
        downloader: 업데이트 다운로더 서비스
        filename: 저장할 파일명

    Examples:
        >>> use_case = DownloadUpdateUseCase(downloader, "SimpleTodo_new.exe")
        >>> def progress(downloaded, total):
        ...     print(f"진행률: {downloaded}/{total}")
        >>> file_path = use_case.execute(release, progress_callback=progress)
        >>> if file_path:
        ...     print(f"다운로드 완료: {file_path}")
    """

    def __init__(
        self,
        downloader: UpdateDownloaderService,
        filename: str = "SimpleTodo_new.exe"
    ):
        """DownloadUpdateUseCase 초기화

        Args:
            downloader: 업데이트 다운로더 서비스
            filename: 저장할 파일명 (기본값: "SimpleTodo_new.exe")

        Raises:
            TypeError: downloader가 UpdateDownloaderService가 아닌 경우
            ValueError: filename이 비어있거나 .exe 확장자가 아닌 경우
        """
        if not isinstance(downloader, UpdateDownloaderService):
            raise TypeError(
                f"downloader는 UpdateDownloaderService여야 합니다. "
                f"받은 타입: {type(downloader)}"
            )

        if not filename or not isinstance(filename, str):
            raise ValueError(f"filename이 유효하지 않습니다: {filename}")

        if not filename.lower().endswith('.exe'):
            raise ValueError(
                f"filename은 .exe 확장자를 가져야 합니다: {filename}"
            )

        self.downloader = downloader
        self.filename = filename

        logger.info(f"DownloadUpdateUseCase 초기화: filename={filename}")

    def execute(
        self,
        release: Release,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Optional[Path]:
        """업데이트 파일을 다운로드하고 검증합니다.

        비즈니스 흐름:
        1. Release에서 다운로드 URL과 파일 크기 추출
        2. UpdateDownloaderService.download() 호출
        3. 진행률 콜백 전달 (UI 업데이트)
        4. 다운로드 완료 후 파일 크기 검증
        5. 성공 시 파일 경로 반환, 실패 시 None

        Args:
            release: 다운로드할 릴리스 정보
            progress_callback: 진행률 콜백 함수 (downloaded_bytes, total_bytes)
                - 주기적으로 호출됨 (100KB마다)
                - UI 업데이트에 사용

        Returns:
            Optional[Path]: 다운로드된 파일 경로 또는 None (실패 시)

        Raises:
            TypeError: release가 Release가 아닌 경우

        Note:
            다음 경우에 None을 반환합니다:
            - 네트워크 오류
            - 다운로드 실패 (HTTP 오류, 타임아웃 등)
            - 파일 크기 검증 실패
        """
        if not isinstance(release, Release):
            raise TypeError(
                f"release는 Release여야 합니다. "
                f"받은 타입: {type(release)}"
            )

        try:
            logger.info(
                f"다운로드 시작: {release.asset_name} "
                f"({release.format_file_size()})"
            )
            logger.info(f"다운로드 URL: {release.download_url}")

            # 1. 다운로드 수행
            downloaded_path = self.downloader.download(
                url=release.download_url,
                filename=self.filename,
                progress_callback=progress_callback
            )

            if not downloaded_path:
                logger.error("다운로드 실패")
                return None

            logger.info(f"다운로드 완료: {downloaded_path}")

            # 2. 파일 검증
            is_valid = self.verify_download(downloaded_path, release.asset_size)

            if not is_valid:
                logger.error("파일 검증 실패")
                # 검증 실패 시 파일 삭제
                self._cleanup_failed_download(downloaded_path)
                return None

            logger.info(f"파일 검증 성공: {downloaded_path}")
            return downloaded_path

        except Exception as e:
            logger.error(f"다운로드 중 예상치 못한 오류 발생: {e}", exc_info=True)
            return None

    def verify_download(self, file_path: Path, expected_size: int) -> bool:
        """다운로드된 파일을 검증합니다.

        파일 크기를 검증하여 다운로드가 올바르게 완료되었는지 확인합니다.

        Args:
            file_path: 다운로드된 파일 경로
            expected_size: 예상 파일 크기 (bytes)

        Returns:
            bool: 검증 성공 시 True

        Note:
            이 메서드는 UpdateDownloaderService.verify_download()를 호출합니다.
        """
        try:
            return self.downloader.verify_download(file_path, expected_size)
        except Exception as e:
            logger.error(f"파일 검증 중 오류: {e}", exc_info=True)
            return False

    def cancel(self) -> bool:
        """진행 중인 다운로드를 취소합니다.

        Note:
            현재 구현에서는 다운로드 취소가 완전히 지원되지 않습니다.
            다운로드 스레드를 강제 종료할 수 없기 때문입니다.
            이 메서드는 향후 확장을 위해 예약되어 있습니다.

        Returns:
            bool: 항상 False (취소 미지원)

        TODO:
            - 다운로드 취소 기능 구현 (스레드 인터럽트)
            - 임시 파일 정리
        """
        logger.warning("다운로드 취소 기능은 현재 지원되지 않습니다")
        return False

    def cleanup_temp_files(self):
        """임시 파일들을 정리합니다.

        다운로드 디렉토리의 .tmp 파일들을 삭제합니다.
        다운로드 실패 시 남은 임시 파일들을 정리하는 데 사용됩니다.
        """
        try:
            self.downloader.cleanup_temp_files()
            logger.info("임시 파일 정리 완료")
        except Exception as e:
            logger.error(f"임시 파일 정리 중 오류: {e}", exc_info=True)

    def _cleanup_failed_download(self, file_path: Path):
        """실패한 다운로드 파일을 정리합니다.

        Args:
            file_path: 삭제할 파일 경로
        """
        try:
            if file_path.exists():
                file_path.unlink()
                logger.info(f"실패한 다운로드 파일 삭제: {file_path}")
        except Exception as e:
            logger.warning(f"파일 삭제 실패: {file_path} - {e}")

    def __repr__(self) -> str:
        """개발자용 문자열 표현을 반환합니다."""
        return f"DownloadUpdateUseCase(filename='{self.filename}')"
