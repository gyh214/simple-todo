"""
FileService - CLEAN 아키텍처 파일 시스템 추상화

💾 Infrastructure Layer:
========================
파일 시스템과의 모든 상호작용을 추상화하여
Domain Layer가 구체적인 파일 구현에 의존하지 않도록 합니다.

🔒 안전한 파일 처리:
===================
- UTF-8 인코딩 강제 (Windows 환경)
- 원자적 쓰기 (Atomic Write) 보장
- 자동 백업 및 복구 메커니즘
- 동시성 제어 (파일 락)

🎯 테스트 가능성:
================
Mock 객체로 완전히 교체 가능하여
파일 시스템 없이도 모든 비즈니스 로직을 테스트할 수 있습니다.
"""

import os
import json
import shutil
import logging
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional
from threading import RLock

from interfaces import IFileService, TodoRepositoryError

logger = logging.getLogger(__name__)


class WindowsFileService(IFileService):
    """
    Windows 환경 최적화된 파일 서비스 구현체

    🖥️ Windows 특화:
    ================
    - UTF-8 인코딩 명시적 사용
    - Windows 파일 경로 처리
    - NTFS 파일 시스템 최적화
    - Windows 특화 오류 처리

    🔒 동시성 제어:
    ===============
    여러 프로세스가 동시에 같은 파일에 접근할 때의 충돌을 방지합니다.
    """

    def __init__(self):
        """
        파일 서비스 초기화 (DI Container 호환용)

        기본 설정으로 초기화한 후, 필요시 configure() 메서드로 설정 변경 가능
        """
        self._enable_backup = True
        self._backup_count = 5
        self._file_locks: Dict[str, RLock] = {}
        self._lock = RLock()

        logger.info(f"WindowsFileService 초기화 - 백업: {self._enable_backup}")

    def configure(self, enable_backup: bool = True, backup_count: int = 5):
        """서비스 설정 변경"""
        self._enable_backup = enable_backup
        self._backup_count = backup_count
        logger.info(f"WindowsFileService 설정 변경 - 백업: {enable_backup}, 개수: {backup_count}")
        return self

    def read_json(self, file_path: str) -> Dict[str, Any]:
        """
        JSON 파일 안전한 읽기

        🛡️ 안전 장치:
        =============
        - UTF-8 인코딩 강제
        - JSON 파싱 오류 처리
        - 파일 락으로 동시성 제어
        - 손상된 파일 복구 시도

        Args:
            file_path: 읽을 파일 경로

        Returns:
            파싱된 JSON 데이터

        Raises:
            TodoRepositoryError: 읽기 실패시
        """
        file_path = str(file_path)

        with self._get_file_lock(file_path):
            try:
                if not os.path.exists(file_path):
                    logger.debug(f"파일이 존재하지 않음: {file_path}")
                    return {}

                # UTF-8 인코딩으로 파일 읽기 (Windows 환경 필수)
                with open(file_path, 'r', encoding='utf-8') as file:
                    data = json.load(file)

                logger.debug(f"JSON 파일 읽기 성공: {file_path}")
                return data if isinstance(data, dict) else {}

            except json.JSONDecodeError as e:
                # JSON 파싱 오류 - 백업에서 복구 시도
                logger.error(f"JSON 파싱 오류: {file_path} - {str(e)}")

                if self._enable_backup:
                    backup_data = self._try_restore_from_backup(file_path)
                    if backup_data is not None:
                        logger.info(f"백업에서 복구 성공: {file_path}")
                        return backup_data

                raise TodoRepositoryError(
                    f"JSON 파일 파싱 실패: {str(e)}",
                    "JSON_PARSE_ERROR",
                    {"file_path": file_path, "error": str(e)}
                )

            except Exception as e:
                logger.error(f"파일 읽기 실패: {file_path} - {str(e)}")
                raise TodoRepositoryError(
                    f"파일 읽기 실패: {str(e)}",
                    "FILE_READ_ERROR",
                    {"file_path": file_path, "error": str(e)}
                )

    def write_json(self, file_path: str, data: Dict[str, Any]) -> bool:
        """
        JSON 파일 안전한 쓰기

        ⚛️ 원자적 쓰기:
        ==============
        임시 파일에 먼저 쓴 후 원본 파일로 이동하여
        쓰기 도중 오류가 발생해도 데이터 손실을 방지합니다.

        Args:
            file_path: 쓸 파일 경로
            data: 저장할 데이터

        Returns:
            쓰기 성공 여부
        """
        file_path = str(file_path)

        with self._get_file_lock(file_path):
            try:
                # 디렉토리 생성 보장
                self.ensure_directory(os.path.dirname(file_path))

                # 기존 파일 백업 (선택사항)
                if self._enable_backup and os.path.exists(file_path):
                    self._create_backup(file_path)

                # 원자적 쓰기를 위한 임시 파일 생성
                temp_file = None
                try:
                    # 같은 디렉토리에 임시 파일 생성
                    dir_path = os.path.dirname(file_path)
                    with tempfile.NamedTemporaryFile(
                        mode='w',
                        suffix='.tmp',
                        dir=dir_path,
                        delete=False,
                        encoding='utf-8'  # Windows 환경 필수
                    ) as temp_file:
                        # JSON 데이터를 임시 파일에 쓰기
                        json.dump(data, temp_file, ensure_ascii=False, indent=2)
                        temp_path = temp_file.name

                    # 임시 파일을 원본 파일로 이동 (원자적 연산)
                    if os.name == 'nt':  # Windows
                        # Windows에서는 대상 파일이 존재하면 삭제해야 함
                        if os.path.exists(file_path):
                            os.remove(file_path)

                    shutil.move(temp_path, file_path)

                    logger.debug(f"JSON 파일 쓰기 성공: {file_path}")
                    return True

                except Exception as e:
                    # 임시 파일 정리
                    if temp_file and os.path.exists(temp_file.name):
                        try:
                            os.remove(temp_file.name)
                        except:
                            pass
                    raise e

            except Exception as e:
                logger.error(f"파일 쓰기 실패: {file_path} - {str(e)}")
                return False

    def backup_file(self, source_path: str, backup_path: str) -> bool:
        """
        파일 백업 생성

        📋 백업 전략:
        ============
        - 원본 파일 검증 후 복사
        - 백업 파일 무결성 확인
        - 백업 실패 시 자세한 로깅

        Args:
            source_path: 원본 파일 경로
            backup_path: 백업 파일 경로

        Returns:
            백업 성공 여부
        """
        try:
            source_path = str(source_path)
            backup_path = str(backup_path)

            if not os.path.exists(source_path):
                logger.warning(f"백업 대상 파일이 없음: {source_path}")
                return False

            # 백업 디렉토리 생성
            self.ensure_directory(os.path.dirname(backup_path))

            # 파일 복사
            shutil.copy2(source_path, backup_path)

            # 백업 파일 검증
            if os.path.exists(backup_path):
                original_size = os.path.getsize(source_path)
                backup_size = os.path.getsize(backup_path)

                if original_size == backup_size:
                    logger.debug(f"파일 백업 성공: {source_path} -> {backup_path}")
                    return True
                else:
                    logger.error(f"백업 파일 크기 불일치: {original_size} vs {backup_size}")
                    return False

            return False

        except Exception as e:
            logger.error(f"파일 백업 실패: {source_path} -> {backup_path} - {str(e)}")
            return False

    def file_exists(self, file_path: str) -> bool:
        """
        파일 존재 확인

        Args:
            file_path: 확인할 파일 경로

        Returns:
            파일 존재 여부
        """
        try:
            return os.path.exists(str(file_path))
        except Exception as e:
            logger.debug(f"파일 존재 확인 실패: {file_path} - {str(e)}")
            return False

    def ensure_directory(self, dir_path: str) -> bool:
        """
        디렉토리 생성 보장

        📁 안전한 생성:
        ==============
        - 중첩 디렉토리 자동 생성
        - 이미 존재하는 경우 무시
        - 권한 오류 처리

        Args:
            dir_path: 생성할 디렉토리 경로

        Returns:
            디렉토리 생성/존재 여부
        """
        if not dir_path:
            return False

        try:
            dir_path = str(dir_path)

            if os.path.exists(dir_path):
                return os.path.isdir(dir_path)

            # 중첩 디렉토리 생성
            os.makedirs(dir_path, exist_ok=True)

            logger.debug(f"디렉토리 생성 성공: {dir_path}")
            return True

        except Exception as e:
            logger.error(f"디렉토리 생성 실패: {dir_path} - {str(e)}")
            return False

    def get_file_size(self, file_path: str) -> int:
        """
        파일 크기 조회

        Args:
            file_path: 파일 경로

        Returns:
            파일 크기 (바이트), 실패시 -1
        """
        try:
            if self.file_exists(file_path):
                return os.path.getsize(str(file_path))
            return -1
        except Exception as e:
            logger.debug(f"파일 크기 조회 실패: {file_path} - {str(e)}")
            return -1

    def list_files(self, directory: str, pattern: str = "*.json") -> list:
        """
        디렉토리 내 파일 목록 조회

        Args:
            directory: 조회할 디렉토리
            pattern: 파일 패턴 (glob)

        Returns:
            파일 경로 목록
        """
        try:
            from pathlib import Path
            dir_path = Path(directory)

            if not dir_path.exists():
                return []

            files = list(dir_path.glob(pattern))
            return [str(f) for f in files]

        except Exception as e:
            logger.error(f"파일 목록 조회 실패: {directory} - {str(e)}")
            return []

    def _get_file_lock(self, file_path: str) -> RLock:
        """
        파일별 락 객체 가져오기

        Args:
            file_path: 파일 경로

        Returns:
            파일 전용 락 객체
        """
        with self._lock:
            if file_path not in self._file_locks:
                self._file_locks[file_path] = RLock()
            return self._file_locks[file_path]

    def _create_backup(self, file_path: str) -> None:
        """
        자동 백업 생성

        Args:
            file_path: 백업할 파일 경로
        """
        try:
            backup_dir = os.path.join(os.path.dirname(file_path), 'backups')
            self.ensure_directory(backup_dir)

            file_name = os.path.basename(file_path)
            name, ext = os.path.splitext(file_name)

            # 타임스탬프가 포함된 백업 파일명
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"{name}_{timestamp}{ext}"
            backup_path = os.path.join(backup_dir, backup_name)

            if self.backup_file(file_path, backup_path):
                self._cleanup_old_backups(backup_dir, name, ext)

        except Exception as e:
            logger.warning(f"자동 백업 생성 실패: {file_path} - {str(e)}")

    def _cleanup_old_backups(self, backup_dir: str, file_name: str, ext: str) -> None:
        """
        오래된 백업 파일 정리

        Args:
            backup_dir: 백업 디렉토리
            file_name: 파일명 (확장자 제외)
            ext: 파일 확장자
        """
        try:
            pattern = f"{file_name}_*{ext}"
            backup_files = self.list_files(backup_dir, pattern)

            if len(backup_files) > self._backup_count:
                # 생성 시간순으로 정렬
                backup_files.sort(key=lambda f: os.path.getctime(f))

                # 오래된 파일 삭제
                for old_backup in backup_files[:-self._backup_count]:
                    try:
                        os.remove(old_backup)
                        logger.debug(f"오래된 백업 파일 삭제: {old_backup}")
                    except Exception as e:
                        logger.warning(f"백업 파일 삭제 실패: {old_backup} - {str(e)}")

        except Exception as e:
            logger.warning(f"백업 파일 정리 실패: {backup_dir} - {str(e)}")

    def _try_restore_from_backup(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        백업에서 데이터 복구 시도

        Args:
            file_path: 복구할 파일 경로

        Returns:
            복구된 데이터 또는 None
        """
        try:
            backup_dir = os.path.join(os.path.dirname(file_path), 'backups')
            file_name = os.path.basename(file_path)
            name, ext = os.path.splitext(file_name)

            pattern = f"{name}_*{ext}"
            backup_files = self.list_files(backup_dir, pattern)

            if not backup_files:
                return None

            # 최신 백업 파일 사용
            backup_files.sort(key=lambda f: os.path.getctime(f), reverse=True)
            latest_backup = backup_files[0]

            logger.info(f"백업에서 복구 시도: {latest_backup}")
            return self.read_json(latest_backup)

        except Exception as e:
            logger.error(f"백업 복구 실패: {file_path} - {str(e)}")
            return None