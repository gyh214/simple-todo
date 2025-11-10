# -*- coding: utf-8 -*-
"""Update Settings Repository - data.json에서 업데이트 설정 관리"""

import json
import logging
import tempfile
import shutil
from pathlib import Path
from typing import Optional
from datetime import datetime
from threading import RLock

from ...domain.value_objects.app_version import AppVersion


logger = logging.getLogger(__name__)


class UpdateSettingsRepository:
    """data.json에서 업데이트 관련 설정을 관리하는 Repository

    updateSettings 필드를 통해 다음 정보를 관리합니다:
    - lastUpdateCheck: 마지막 업데이트 체크 시간
    - skippedVersion: 사용자가 건너뛴 버전
    - autoCheckEnabled: 자동 체크 활성화 여부

    Thread-safe하며, 원자적 쓰기를 보장합니다.

    Attributes:
        data_file_path: data.json 파일 경로

    Examples:
        >>> repo = UpdateSettingsRepository(Path("data.json"))
        >>> repo.save_last_check_time(datetime.now())
        >>> last_check = repo.get_last_check_time()
    """

    def __init__(self, data_file_path: Path):
        """UpdateSettingsRepository 초기화

        Args:
            data_file_path: data.json 파일의 경로

        Raises:
            ValueError: data_file_path가 None이거나 비어있는 경우
        """
        if not data_file_path:
            raise ValueError("data_file_path는 비어있을 수 없습니다")

        self.data_file_path = Path(data_file_path)
        self._lock = RLock()  # 스레드 안전성

        logger.info(f"UpdateSettingsRepository 초기화: {self.data_file_path}")

    def get_last_check_time(self) -> Optional[datetime]:
        """마지막 업데이트 체크 시간을 조회합니다.

        Returns:
            Optional[datetime]: 마지막 체크 시간 (없으면 None)
        """
        with self._lock:
            data = self._load_data()
            update_settings = data.get('updateSettings', {})
            last_check_str = update_settings.get('lastUpdateCheck')

            if not last_check_str:
                return None

            try:
                # ISO 8601 형식 파싱
                return datetime.fromisoformat(last_check_str.replace('Z', '+00:00'))
            except (ValueError, AttributeError) as e:
                logger.warning(f"유효하지 않은 lastUpdateCheck 형식: {last_check_str} - {e}")
                return None

    def save_last_check_time(self, check_time: datetime) -> bool:
        """마지막 업데이트 체크 시간을 저장합니다.

        Args:
            check_time: 체크 시간

        Returns:
            bool: 성공 여부

        Raises:
            TypeError: check_time이 datetime이 아닌 경우
        """
        if not isinstance(check_time, datetime):
            raise TypeError(
                f"check_time은 datetime이어야 합니다. "
                f"받은 타입: {type(check_time)}"
            )

        with self._lock:
            data = self._load_data()
            data = self._ensure_update_settings(data)

            # ISO 8601 형식으로 저장
            data['updateSettings']['lastUpdateCheck'] = check_time.isoformat()

            success = self._save_data(data)
            if success:
                logger.info(f"마지막 체크 시간 저장: {check_time.isoformat()}")
            return success

    def get_skipped_version(self) -> Optional[AppVersion]:
        """사용자가 건너뛴 버전을 조회합니다.

        Returns:
            Optional[AppVersion]: 건너뛴 버전 (없으면 None)
        """
        with self._lock:
            data = self._load_data()
            update_settings = data.get('updateSettings', {})
            skipped_version_str = update_settings.get('skippedVersion')

            if not skipped_version_str:
                return None

            try:
                return AppVersion.from_string(skipped_version_str)
            except ValueError as e:
                logger.warning(f"유효하지 않은 skippedVersion 형식: {skipped_version_str} - {e}")
                return None

    def set_skipped_version(self, version: Optional[AppVersion]) -> bool:
        """건너뛴 버전을 설정합니다.

        Args:
            version: 건너뛴 버전 (None: 초기화)

        Returns:
            bool: 성공 여부

        Raises:
            TypeError: version이 AppVersion이 아닌 경우 (None은 제외)
        """
        if version is not None and not isinstance(version, AppVersion):
            raise TypeError(
                f"version은 AppVersion이어야 합니다. "
                f"받은 타입: {type(version)}"
            )

        with self._lock:
            data = self._load_data()
            data = self._ensure_update_settings(data)

            # 버전 저장 또는 초기화
            if version is None:
                data['updateSettings']['skippedVersion'] = None
                logger.info("건너뛴 버전 초기화")
            else:
                data['updateSettings']['skippedVersion'] = str(version)
                logger.info(f"건너뛴 버전 설정: {version}")

            return self._save_data(data)

    def is_auto_check_enabled(self) -> bool:
        """자동 업데이트 체크가 활성화되어 있는지 확인합니다.

        Returns:
            bool: 자동 체크 활성화 여부 (기본값: True)
        """
        with self._lock:
            data = self._load_data()
            update_settings = data.get('updateSettings', {})

            # 기본값: True (자동 체크 활성화)
            return update_settings.get('autoCheckEnabled', True)

    def set_auto_check_enabled(self, enabled: bool) -> bool:
        """자동 업데이트 체크 활성화 여부를 설정합니다.

        Args:
            enabled: 활성화 여부

        Returns:
            bool: 성공 여부

        Raises:
            TypeError: enabled가 bool이 아닌 경우
        """
        if not isinstance(enabled, bool):
            raise TypeError(
                f"enabled는 bool이어야 합니다. "
                f"받은 타입: {type(enabled)}"
            )

        with self._lock:
            data = self._load_data()
            data = self._ensure_update_settings(data)

            data['updateSettings']['autoCheckEnabled'] = enabled

            success = self._save_data(data)
            if success:
                logger.info(f"자동 체크 {'활성화' if enabled else '비활성화'}")
            return success

    def _load_data(self) -> dict:
        """data.json을 로드합니다.

        Returns:
            dict: 로드된 데이터 (실패 시 빈 딕셔너리)

        Note:
            파일이 없거나 파싱 오류 시 기본 구조를 반환합니다.
        """
        if not self.data_file_path.exists():
            logger.warning(f"데이터 파일이 없습니다: {self.data_file_path}")
            return {
                'version': '1.0',
                'settings': {},
                'updateSettings': {},
                'todos': []
            }

        try:
            with open(self.data_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 기본 구조 보장
            if not isinstance(data, dict):
                logger.error(f"데이터가 딕셔너리가 아닙니다: {type(data)}")
                return {
                    'version': '1.0',
                    'settings': {},
                    'updateSettings': {},
                    'todos': []
                }

            return data

        except json.JSONDecodeError as e:
            logger.error(f"JSON 파싱 오류: {e}")
            return {
                'version': '1.0',
                'settings': {},
                'updateSettings': {},
                'todos': []
            }

        except Exception as e:
            logger.error(f"데이터 로드 중 오류: {e}", exc_info=True)
            return {
                'version': '1.0',
                'settings': {},
                'updateSettings': {},
                'todos': []
            }

    def _save_data(self, data: dict) -> bool:
        """data.json을 원자적으로 저장합니다.

        임시 파일에 쓴 후 원본 파일로 이동하여 원자성을 보장합니다.

        Args:
            data: 저장할 데이터

        Returns:
            bool: 성공 여부
        """
        try:
            # 부모 디렉토리 생성
            self.data_file_path.parent.mkdir(parents=True, exist_ok=True)

            # 임시 파일에 쓰기
            with tempfile.NamedTemporaryFile(
                mode='w',
                encoding='utf-8',
                delete=False,
                dir=self.data_file_path.parent,
                suffix='.tmp'
            ) as temp_file:
                json.dump(data, temp_file, indent=2, ensure_ascii=False)
                temp_path = Path(temp_file.name)

            # 원자적 교체
            shutil.move(str(temp_path), str(self.data_file_path))

            return True

        except Exception as e:
            logger.error(f"데이터 저장 중 오류: {e}", exc_info=True)
            return False

    def _ensure_update_settings(self, data: dict) -> dict:
        """updateSettings 필드가 존재하는지 확인하고 초기화합니다.

        Args:
            data: 데이터 딕셔너리

        Returns:
            dict: updateSettings가 보장된 데이터
        """
        if 'updateSettings' not in data:
            data['updateSettings'] = {}

        # 기본값 설정
        update_settings = data['updateSettings']

        if 'autoCheckEnabled' not in update_settings:
            update_settings['autoCheckEnabled'] = True

        if 'lastUpdateCheck' not in update_settings:
            update_settings['lastUpdateCheck'] = None

        if 'skippedVersion' not in update_settings:
            update_settings['skippedVersion'] = None

        return data

    def __repr__(self) -> str:
        """개발자용 문자열 표현을 반환합니다."""
        return f"UpdateSettingsRepository(data_file='{self.data_file_path}')"
