# -*- coding: utf-8 -*-
"""BackupService - 데이터 자동 백업 및 복구 시스템"""

import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging

# 로깅 설정
logger = logging.getLogger(__name__)


class BackupService:
    """데이터 백업 및 복구를 담당하는 서비스

    저장 시마다 자동 백업을 생성하고, 최근 10개의 백업만 유지합니다.
    데이터 손상 시 가장 최근 백업으로 자동 복구합니다.
    """

    def __init__(self, data_file: Path, backup_dir: Path, max_backups: Optional[int] = None):
        """BackupService 초기화

        Args:
            data_file: 원본 데이터 파일 경로
            backup_dir: 백업 디렉토리 경로
            max_backups: 유지할 최대 백업 개수 (None: 무제한)
        """
        self.data_file = data_file
        self.backup_dir = backup_dir
        self.max_backups = max_backups

        # 백업 디렉토리 생성
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(self) -> Optional[Path]:
        """현재 데이터 파일의 백업을 생성합니다.

        Returns:
            Path: 생성된 백업 파일 경로 (실패 시 None)
        """
        if not self.data_file.exists():
            logger.warning(f"Data file not found for backup: {self.data_file}")
            return None

        try:
            # 백업 파일명 생성: data_YYYYMMDD_HHMMSS.json
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"data_{timestamp}.json"
            backup_path = self.backup_dir / backup_filename

            # 파일 복사
            shutil.copy2(self.data_file, backup_path)
            logger.info(f"Backup created: {backup_path}")

            # 오래된 백업 정리
            self._cleanup_old_backups()

            return backup_path

        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return None

    def create_legacy_backup(self) -> Optional[Path]:
        """레거시 데이터 마이그레이션 전 백업을 생성합니다.

        Returns:
            Path: 생성된 백업 파일 경로 (실패 시 None)
        """
        if not self.data_file.exists():
            logger.warning(f"Data file not found for legacy backup: {self.data_file}")
            return None

        try:
            # 레거시 백업 파일명: data_legacy_backup_YYYYMMDD_HHMMSS.json
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"data_legacy_backup_{timestamp}.json"
            backup_path = self.backup_dir / backup_filename

            # 파일 복사
            shutil.copy2(self.data_file, backup_path)
            logger.info(f"Legacy backup created: {backup_path}")

            return backup_path

        except Exception as e:
            logger.error(f"Failed to create legacy backup: {e}")
            return None

    def get_latest_backup(self) -> Optional[Path]:
        """가장 최근 백업 파일을 반환합니다.

        Returns:
            Path: 최신 백업 파일 경로 (백업 없음 시 None)
        """
        backups = self._get_backup_files()
        if not backups:
            return None

        # 파일명으로 정렬 (최신순)
        backups.sort(reverse=True)
        return self.backup_dir / backups[0]

    def restore_from_backup(self, backup_path: Optional[Path] = None) -> bool:
        """백업 파일로부터 데이터를 복구합니다.

        Args:
            backup_path: 복구할 백업 파일 경로 (None일 경우 최신 백업 사용)

        Returns:
            bool: 복구 성공 여부
        """
        if backup_path is None:
            backup_path = self.get_latest_backup()

        if backup_path is None or not backup_path.exists():
            logger.error("No backup file available for restore")
            return False

        try:
            # 백업 파일 유효성 검증
            with open(backup_path, 'r', encoding='utf-8') as f:
                json.load(f)  # JSON 파싱 테스트

            # 원본 파일에 복사
            shutil.copy2(backup_path, self.data_file)
            logger.info(f"Data restored from backup: {backup_path}")
            return True

        except json.JSONDecodeError as e:
            logger.error(f"Backup file is corrupted: {backup_path}, {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to restore from backup: {e}")
            return False

    def _get_backup_files(self) -> List[str]:
        """백업 파일 목록을 가져옵니다 (레거시 백업 제외).

        Returns:
            List[str]: 백업 파일명 리스트 (정렬되지 않음)
        """
        if not self.backup_dir.exists():
            return []

        # data_YYYYMMDD_HHMMSS.json 패턴만 매칭 (레거시 백업 제외)
        backups = [
            f.name for f in self.backup_dir.iterdir()
            if f.is_file() and f.name.startswith("data_") and f.name.endswith(".json")
            and "legacy" not in f.name
        ]
        return backups

    def _cleanup_old_backups(self) -> None:
        """오래된 백업 파일을 삭제하여 최대 개수를 유지합니다."""
        # 무제한 보관 모드
        if self.max_backups is None:
            return

        backups = self._get_backup_files()
        if len(backups) <= self.max_backups:
            return

        # 파일명으로 정렬 (최신순)
        backups.sort(reverse=True)

        # 최대 개수 초과분 삭제
        for old_backup in backups[self.max_backups:]:
            old_path = self.backup_dir / old_backup
            try:
                old_path.unlink()
                logger.info(f"Old backup deleted: {old_path}")
            except Exception as e:
                logger.error(f"Failed to delete old backup {old_path}: {e}")

    def get_backup_count(self) -> int:
        """현재 백업 파일 개수를 반환합니다.

        Returns:
            int: 백업 파일 개수
        """
        return len(self._get_backup_files())

    def _load_backup_json(self, backup_path: Path) -> Any:
        """백업 파일에서 JSON 데이터를 로드합니다 (공통 메서드).

        Args:
            backup_path: 백업 파일 경로

        Returns:
            Any: 로드된 JSON 데이터 (dict 또는 list)

        Raises:
            json.JSONDecodeError: JSON 파싱 에러
        """
        with open(backup_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _extract_todos_data(self, data: Any) -> list:
        """신규/레거시 포맷에서 TODO 데이터를 추출합니다 (공통 메서드).

        Args:
            data: 로드된 JSON 데이터

        Returns:
            list: TODO 딕셔너리 리스트

        Raises:
            ValueError: 잘못된 포맷
        """
        if isinstance(data, dict):
            # 신규 포맷: {version, settings, todos}
            return data.get('todos', [])
        elif isinstance(data, list):
            # 레거시 포맷: 배열
            return data
        else:
            raise ValueError("Invalid backup format: expected dict or list")

    def verify_backup(self, backup_path: Path) -> bool:
        """백업 파일의 유효성을 검증합니다.

        Args:
            backup_path: 검증할 백업 파일 경로

        Returns:
            bool: 유효한 백업 파일 여부
        """
        if not backup_path.exists():
            return False

        try:
            # 공통 메서드 재사용
            data = self._load_backup_json(backup_path)

            # 기본 구조 검증
            if isinstance(data, dict):
                # 신규 포맷
                return "version" in data and "todos" in data
            elif isinstance(data, list):
                # 레거시 포맷
                return True
            else:
                return False

        except Exception as e:
            logger.error(f"Backup verification failed for {backup_path}: {e}")
            return False

    def get_backup_list(self, days: Optional[int] = None) -> List[Dict[str, Any]]:
        """백업 파일 목록 + 메타정보 반환

        Args:
            days: 최근 N일 백업만 반환 (None이면 전체)

        Returns:
            List[Dict]: 백업 정보 리스트 (최신순 정렬)
                - filename: 파일명
                - path: Path 객체
                - size: 파일 크기 (bytes)
                - created: 생성 시각 (timestamp)
                - is_valid: 유효성 여부
        """
        backups = self._get_backup_files()  # 기존 private 메서드 재사용
        backups.sort(reverse=True)  # 최신순

        result = []
        cutoff_date = None

        # 일수 필터링 준비
        if days is not None:
            cutoff_date = datetime.now() - timedelta(days=days)

        for filename in backups:
            path = self.backup_dir / filename

            # 일수 필터링
            if cutoff_date is not None:
                try:
                    # 파일명에서 날짜 추출: data_20251005_102213.json -> 20251005
                    date_str = filename.split('_')[1]
                    backup_date = datetime.strptime(date_str, '%Y%m%d')

                    # cutoff_date보다 오래된 백업은 스킵
                    if backup_date.date() < cutoff_date.date():
                        continue
                except (IndexError, ValueError):
                    # 파일명 형식이 다르면 포함 (레거시 백업 등)
                    pass

            result.append({
                'filename': filename,
                'path': path,
                'size': path.stat().st_size,
                'created': path.stat().st_mtime,
                'is_valid': self.verify_backup(path)  # 기존 메서드 재사용
            })

        return result

    def get_backup_todos(self, backup_path: Path) -> List['Todo']:
        """백업 파일에서 TODO 목록을 반환합니다.

        Args:
            backup_path: 백업 파일 경로

        Returns:
            List[Todo]: TODO 엔티티 리스트

        Raises:
            FileNotFoundError: 백업 파일이 없는 경우
            ValueError: JSON 파싱 에러 또는 잘못된 포맷
        """
        # 도메인 엔티티 import (메서드 내부에서)
        from ...domain.entities.todo import Todo

        # 1. 파일 존재 확인
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_path}")

        # 2. JSON 로드 (공통 메서드 재사용)
        try:
            data = self._load_backup_json(backup_path)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in backup file: {e}")

        # 3. TODO 목록 추출 (공통 메서드 재사용)
        todos_data = self._extract_todos_data(data)

        # 4. Todo 엔티티 리스트 생성
        todos = []
        for todo_dict in todos_data:
            try:
                # Todo.from_dict() 재사용
                todo = Todo.from_dict(todo_dict)
                todos.append(todo)
            except Exception as e:
                logger.error(f"Failed to parse TODO: {todo_dict}, error: {e}")
                # 에러 발생 시 해당 항목만 건너뛰기
                continue

        logger.info(f"Loaded {len(todos)} TODOs from backup: {backup_path}")
        return todos
