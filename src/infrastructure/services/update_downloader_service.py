# -*- coding: utf-8 -*-
"""Update Downloader Service - HTTP로 exe 파일 다운로드 및 진행률 추적"""

import logging
import tempfile
from pathlib import Path
from typing import Optional, Callable
import time

try:
    import requests
except ImportError:
    requests = None


logger = logging.getLogger(__name__)


class UpdateDownloaderService:
    """업데이트 파일을 다운로드하고 진행률을 추적하는 서비스

    HTTP를 통해 exe 파일을 다운로드하며, 청크 단위로 진행률을 추적합니다.
    임시 파일로 다운로드한 후 완료 시 최종 파일명으로 변경합니다.

    Attributes:
        download_dir: 다운로드 디렉토리 경로

    Examples:
        >>> service = UpdateDownloaderService()
        >>> def progress(downloaded, total):
        ...     print(f"{downloaded}/{total} bytes")
        >>> path = service.download(
        ...     "https://example.com/app.exe",
        ...     "app_new.exe",
        ...     progress_callback=progress
        ... )
    """

    # 청크 크기 (8KB)
    CHUNK_SIZE = 8 * 1024

    # 진행률 콜백 호출 간격 (100KB마다)
    PROGRESS_CALLBACK_INTERVAL = 100 * 1024

    # 타임아웃 (초)
    DOWNLOAD_TIMEOUT = 60

    # 최대 재시도 횟수
    MAX_RETRIES = 3

    def __init__(self, download_dir: Optional[Path] = None):
        """UpdateDownloaderService 초기화

        Args:
            download_dir: 다운로드 디렉토리 (None: 시스템 임시 디렉토리)

        Raises:
            ImportError: requests 라이브러리가 설치되지 않은 경우
        """
        if requests is None:
            raise ImportError(
                "requests 라이브러리가 설치되지 않았습니다. "
                "'pip install requests'를 실행하세요."
            )

        if download_dir is None:
            # 시스템 임시 디렉토리 사용
            self.download_dir = Path(tempfile.gettempdir())
        else:
            self.download_dir = Path(download_dir)

        # 디렉토리 생성
        self.download_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"UpdateDownloaderService 초기화: {self.download_dir}")

    def download(
        self,
        url: str,
        filename: str,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Optional[Path]:
        """파일을 다운로드하고 경로를 반환합니다.

        Args:
            url: 다운로드 URL
            filename: 저장할 파일명 (예: "SimpleTodo_new.exe")
            progress_callback: 진행률 콜백 함수 (downloaded_bytes, total_bytes)

        Returns:
            Optional[Path]: 다운로드된 파일 경로 (실패 시 None)

        Note:
            다음 경우에 None을 반환합니다:
            - 네트워크 오류
            - 디스크 공간 부족
            - 타임아웃
            - HTTP 오류 (4xx, 5xx)
        """
        if not url or not isinstance(url, str):
            logger.error(f"유효하지 않은 URL: {url}")
            return None

        if not filename or not isinstance(filename, str):
            logger.error(f"유효하지 않은 파일명: {filename}")
            return None

        # 최종 파일 경로
        dest_path = self.download_dir / filename

        # 재시도 로직
        for attempt in range(1, self.MAX_RETRIES + 1):
            logger.info(f"다운로드 시도 {attempt}/{self.MAX_RETRIES}: {url}")

            try:
                success = self._download_with_progress(
                    url,
                    dest_path,
                    progress_callback
                )

                if success:
                    logger.info(f"다운로드 완료: {dest_path}")
                    return dest_path
                else:
                    logger.warning(f"다운로드 실패 (시도 {attempt}/{self.MAX_RETRIES})")

            except Exception as e:
                logger.error(
                    f"다운로드 중 오류 (시도 {attempt}/{self.MAX_RETRIES}): {e}",
                    exc_info=True
                )

            # 재시도 전 대기 (지수 백오프: 1초, 2초, 4초)
            if attempt < self.MAX_RETRIES:
                wait_time = 2 ** (attempt - 1)
                logger.info(f"{wait_time}초 후 재시도...")
                time.sleep(wait_time)

        logger.error(f"최대 재시도 횟수 초과: {url}")
        return None

    def _download_with_progress(
        self,
        url: str,
        dest_path: Path,
        progress_callback: Optional[Callable[[int, int], None]]
    ) -> bool:
        """진행률을 추적하며 파일을 다운로드합니다.

        Args:
            url: 다운로드 URL
            dest_path: 저장할 파일 경로
            progress_callback: 진행률 콜백 함수

        Returns:
            bool: 성공 여부
        """
        # 임시 파일 경로 (dest_path.tmp)
        temp_path = dest_path.with_suffix(dest_path.suffix + '.tmp')

        try:
            # HTTP 요청 (스트리밍 모드)
            headers = {
                'User-Agent': 'SimpleTodo-AutoUpdater/1.0'
            }

            response = requests.get(
                url,
                headers=headers,
                stream=True,
                timeout=self.DOWNLOAD_TIMEOUT
            )

            # HTTP 상태 코드 확인
            if response.status_code != 200:
                logger.error(f"HTTP 오류: {response.status_code} - {url}")
                return False

            # 파일 크기 (Content-Length 헤더)
            total_size = int(response.headers.get('Content-Length', 0))

            if total_size == 0:
                logger.warning("파일 크기를 알 수 없습니다 (Content-Length 헤더 없음)")

            logger.info(f"다운로드 시작: {total_size:,} bytes")

            # 임시 파일에 쓰기
            downloaded_size = 0
            last_callback_size = 0

            with open(temp_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=self.CHUNK_SIZE):
                    if chunk:  # 빈 청크 필터링
                        f.write(chunk)
                        downloaded_size += len(chunk)

                        # 진행률 콜백 호출 (100KB마다)
                        if progress_callback and (
                            downloaded_size - last_callback_size >= self.PROGRESS_CALLBACK_INTERVAL
                            or downloaded_size == total_size
                        ):
                            progress_callback(downloaded_size, total_size)
                            last_callback_size = downloaded_size

            # 최종 진행률 콜백 (100% 완료 보장)
            if progress_callback and downloaded_size > 0:
                progress_callback(downloaded_size, total_size)

            # 파일 크기 검증
            if total_size > 0 and downloaded_size != total_size:
                logger.error(
                    f"다운로드 크기 불일치: {downloaded_size} != {total_size}"
                )
                temp_path.unlink(missing_ok=True)
                return False

            # 임시 파일을 최종 파일로 이동 (원자적 교체)
            if dest_path.exists():
                dest_path.unlink()

            temp_path.rename(dest_path)

            logger.info(f"파일 저장 완료: {dest_path} ({downloaded_size:,} bytes)")
            return True

        except requests.exceptions.Timeout:
            logger.error(f"다운로드 타임아웃 ({self.DOWNLOAD_TIMEOUT}초): {url}")
            temp_path.unlink(missing_ok=True)
            return False

        except requests.exceptions.ConnectionError as e:
            logger.error(f"네트워크 연결 오류: {e}")
            temp_path.unlink(missing_ok=True)
            return False

        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP 요청 오류: {e}")
            temp_path.unlink(missing_ok=True)
            return False

        except OSError as e:
            logger.error(f"파일 쓰기 오류 (디스크 공간 부족?): {e}")
            temp_path.unlink(missing_ok=True)
            return False

        except Exception as e:
            logger.error(f"예상치 못한 오류: {e}", exc_info=True)
            temp_path.unlink(missing_ok=True)
            return False

    def verify_download(self, file_path: Path, expected_size: int) -> bool:
        """다운로드된 파일을 검증합니다.

        Args:
            file_path: 파일 경로
            expected_size: 예상 파일 크기 (bytes)

        Returns:
            bool: 검증 성공 여부
        """
        if not file_path.exists():
            logger.error(f"파일이 존재하지 않습니다: {file_path}")
            return False

        try:
            actual_size = file_path.stat().st_size

            if actual_size != expected_size:
                logger.error(
                    f"파일 크기 불일치: {actual_size:,} != {expected_size:,} bytes"
                )
                return False

            logger.info(f"파일 검증 성공: {file_path} ({actual_size:,} bytes)")
            return True

        except Exception as e:
            logger.error(f"파일 검증 중 오류: {e}", exc_info=True)
            return False

    def cleanup_temp_files(self):
        """임시 파일들을 정리합니다.

        download_dir 내의 .tmp 파일들을 삭제합니다.
        """
        try:
            temp_files = list(self.download_dir.glob('*.tmp'))

            for temp_file in temp_files:
                try:
                    temp_file.unlink()
                    logger.info(f"임시 파일 삭제: {temp_file}")
                except Exception as e:
                    logger.warning(f"임시 파일 삭제 실패: {temp_file} - {e}")

            if temp_files:
                logger.info(f"임시 파일 {len(temp_files)}개 정리 완료")

        except Exception as e:
            logger.error(f"임시 파일 정리 중 오류: {e}", exc_info=True)

    def __repr__(self) -> str:
        """개발자용 문자열 표현을 반환합니다."""
        return f"UpdateDownloaderService(download_dir='{self.download_dir}')"
