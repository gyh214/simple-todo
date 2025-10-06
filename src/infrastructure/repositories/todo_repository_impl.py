# -*- coding: utf-8 -*-
"""TodoRepositoryImpl - JSON 파일 기반 Todo 저장소 구현"""

import json
import tempfile
import shutil
from pathlib import Path
from typing import List, Optional, Dict, Any
import logging
from threading import RLock

from ...domain.interfaces.repository_interface import ITodoRepository
from ...domain.entities.todo import Todo
from ...domain.value_objects.todo_id import TodoId
from ..file_system.backup_service import BackupService
from ..file_system.migration_service import DataMigrationService
from ..utils.debounce_manager import DebounceManager

# 로깅 설정
logger = logging.getLogger(__name__)


class TodoRepositoryImpl(ITodoRepository):
    """JSON 파일 기반 Todo 저장소 구현

    데이터 영속성을 담당하며, 자동 백업 및 레거시 마이그레이션을 지원합니다.
    """

    def __init__(self, data_file: Path, backup_dir: Path, max_backups: Optional[int] = None):
        """TodoRepositoryImpl 초기화

        Args:
            data_file: 데이터 파일 경로
            backup_dir: 백업 디렉토리 경로
            max_backups: 최대 백업 개수 (None: 무제한)
        """
        self.data_file = data_file
        self.backup_service = BackupService(data_file, backup_dir, max_backups)
        self.migration_service = DataMigrationService()
        self._lock = RLock()  # 재진입 가능한 Lock (스레드 안전성 + 중첩 호출 지원)
        self._data_cache: Optional[Dict[str, Any]] = None

        # 비동기 배치 저장을 위한 debounce 관련 변수
        self._pending_data: Optional[Dict[str, Any]] = None
        self._pending_create_backup: bool = True
        self._pending_max_retries: int = 3

        # DebounceManager 초기화 (300ms 지연)
        self._save_debouncer = DebounceManager(
            delay_ms=300,
            callback=self._execute_save
        )

        # 데이터 파일 초기화
        self._ensure_data_file_exists()
        # 초기 로드 및 마이그레이션
        self._load_data()

    def find_all(self) -> List[Todo]:
        """모든 TODO를 조회합니다.

        Returns:
            List[Todo]: 모든 TODO 리스트
        """
        with self._lock:
            data = self._load_data()
            todos_data = data.get("todos", [])

            todos = []
            for todo_dict in todos_data:
                try:
                    todo = Todo.from_dict(todo_dict)
                    todos.append(todo)
                except Exception as e:
                    logger.error(f"Failed to deserialize todo: {todo_dict}, {e}")

            return todos

    def find_by_id(self, todo_id: TodoId) -> Optional[Todo]:
        """ID로 TODO를 조회합니다.

        Args:
            todo_id: TODO ID

        Returns:
            Optional[Todo]: TODO 엔티티 (없으면 None)
        """
        todos = self.find_all()
        for todo in todos:
            if str(todo.id) == str(todo_id):
                return todo
        return None

    def save(self, todo: Todo) -> None:
        """TODO를 저장합니다 (생성 또는 업데이트).

        Args:
            todo: TODO 엔티티
        """
        with self._lock:
            data = self._load_data()
            todos_data = data.get("todos", [])

            # 기존 TODO 찾기
            existing_index = None
            for i, todo_dict in enumerate(todos_data):
                if todo_dict.get("id") == str(todo.id):
                    existing_index = i
                    break

            # 업데이트 또는 추가
            todo_dict = todo.to_dict()
            if existing_index is not None:
                todos_data[existing_index] = todo_dict
            else:
                todos_data.append(todo_dict)

            data["todos"] = todos_data
            self._save_data(data)

    def save_all(self, todos: List[Todo]) -> None:
        """여러 TODO를 일괄 저장합니다.

        Args:
            todos: TODO 리스트
        """
        with self._lock:
            data = self._load_data()

            # 모든 TODO를 딕셔너리로 변환
            todos_data = [todo.to_dict() for todo in todos]
            data["todos"] = todos_data

            # 즉시 저장 (드래그 앤 드롭 등에서 사용되므로 debounce 우회)
            self._save_data(data, immediate=True)

    def delete(self, todo_id: TodoId) -> None:
        """TODO를 삭제합니다.

        Args:
            todo_id: TODO ID
        """
        with self._lock:
            data = self._load_data()
            todos_data = data.get("todos", [])

            # TODO 삭제
            todos_data = [
                todo_dict for todo_dict in todos_data
                if todo_dict.get("id") != str(todo_id)
            ]

            data["todos"] = todos_data
            self._save_data(data)

    def get_settings(self) -> Dict[str, Any]:
        """애플리케이션 설정을 조회합니다.

        Returns:
            Dict: 설정 딕셔너리
        """
        with self._lock:
            data = self._load_data()
            return data.get("settings", {})

    def update_settings(self, settings: Dict[str, Any]) -> None:
        """애플리케이션 설정을 업데이트합니다.

        Args:
            settings: 설정 딕셔너리
        """
        with self._lock:
            data = self._load_data()
            data["settings"].update(settings)
            self._save_data(data)

    def _ensure_data_file_exists(self) -> None:
        """데이터 파일이 존재하지 않으면 기본값으로 생성합니다."""
        if not self.data_file.exists():
            # 부모 디렉토리 생성
            self.data_file.parent.mkdir(parents=True, exist_ok=True)

            # 기본 데이터 생성
            default_data = {
                "version": "1.0",
                "settings": {
                    "sortOrder": "dueDate_asc",
                    "splitRatio": [9, 1],  # 진행중 섹션 최대화
                    "alwaysOnTop": False
                },
                "todos": []
            }

            try:
                with open(self.data_file, 'w', encoding='utf-8') as f:
                    json.dump(default_data, f, ensure_ascii=False, indent=2)
                logger.info(f"Created default data file: {self.data_file}")
            except Exception as e:
                logger.error(f"Failed to create data file: {e}")
                raise

    def _load_data(self) -> Dict[str, Any]:
        """데이터 파일을 로드하고 필요 시 마이그레이션을 수행합니다.

        Returns:
            Dict: 로드된 데이터

        Raises:
            Exception: 로드 실패 시
        """
        # 캐시가 있으면 캐시 반환 (반복 migration 방지)
        if self._data_cache is not None:
            return self._data_cache

        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 레거시 포맷 감지 및 마이그레이션
            if self.migration_service.detect_legacy_format(data):
                logger.info("Legacy format detected, starting migration...")

                # 레거시 백업 생성
                self.backup_service.create_legacy_backup()

                # 마이그레이션 수행
                migrated_data = self.migration_service.migrate_legacy_data(data)

                # 마이그레이션 결과 검증
                if not self.migration_service.validate_migrated_data(migrated_data):
                    raise ValueError("Migrated data validation failed")

                # 마이그레이션된 데이터 저장
                self._save_data(migrated_data, create_backup=False)
                data = migrated_data

                logger.info("Migration completed successfully")

            # manualOrder 필드 추가 마이그레이션 (신규 포맷인데 manualOrder 없는 경우)
            elif self.migration_service.needs_manual_order_migration(data):
                logger.info("manualOrder field missing, adding it...")

                # 백업 생성
                self.backup_service.create_backup()

                # manualOrder 필드 추가
                migrated_data = self.migration_service.add_manual_order_field(data)

                # 저장
                self._save_data(migrated_data, create_backup=False)
                data = migrated_data

                logger.info("manualOrder field added successfully")

            # manualOrder 필드 제거 마이그레이션 (기존 데이터에 manualOrder 있는 경우)
            elif self.migration_service.needs_manual_order_removal_migration(data):
                logger.info("manualOrder field found, removing it...")

                # 백업 생성
                self.backup_service.create_backup()

                # manualOrder 필드 제거
                migrated_data = self.migration_service.remove_manual_order_field(data)

                # 저장
                self._save_data(migrated_data, create_backup=False)
                data = migrated_data

                logger.info("manualOrder field removed successfully")

            self._data_cache = data
            return data

        except FileNotFoundError:
            logger.warning(f"Data file not found: {self.data_file}")
            self._ensure_data_file_exists()
            return self._load_data()

        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            # 백업으로부터 복구 시도
            if self.backup_service.restore_from_backup():
                logger.info("Restored from backup successfully")
                return self._load_data()
            else:
                raise Exception("Failed to load data and no valid backup found") from e

        except Exception as e:
            logger.error(f"Failed to load data: {e}")
            raise

    def _save_data(self, data: Dict[str, Any], create_backup: bool = True, max_retries: int = 3, immediate: bool = False) -> None:
        """데이터를 파일에 저장합니다.

        immediate=False (기본값): 비동기 배치 저장 (Debounce 패턴)
        - 연속적인 저장 요청을 300ms 동안 대기하여 마지막 요청만 실행
        - UI 블로킹을 최소화하고 성능을 향상

        immediate=True: 즉시 동기 저장
        - debounce 없이 즉시 저장 실행
        - 드래그 앤 드롭 등 즉시 저장이 필요한 경우 사용

        Args:
            data: 저장할 데이터
            create_backup: 백업 생성 여부
            max_retries: 최대 재시도 횟수
            immediate: 즉시 저장 여부 (기본값: False)
        """
        with self._lock:
            # 캐시 즉시 업데이트 (반복 migration 방지)
            self._data_cache = data

            # pending 데이터 업데이트
            self._pending_data = data
            self._pending_create_backup = create_backup
            self._pending_max_retries = max_retries

            if immediate:
                # 즉시 저장: debounce 없이 바로 실행
                logger.debug("Immediate save requested")
                self._execute_save()
            else:
                # 비동기 저장: DebounceManager를 통한 debounce 적용 (300ms)
                self._save_debouncer.schedule()

    def _execute_save(self, data: Any = None) -> None:
        """실제 저장을 실행합니다 (Debounce 타이머 완료 시 호출).

        DebounceManager의 타이머가 만료되면 호출되어 실제 파일 저장을 수행합니다.
        원자적 저장, 백업 생성, 재시도 로직을 포함합니다.

        Args:
            data: DebounceManager에서 전달되는 데이터 (사용하지 않음)
        """
        with self._lock:
            # pending 데이터가 없으면 무시
            if not self._pending_data:
                logger.debug("No pending data to save")
                return

            # pending 데이터 복사 및 초기화
            save_data = self._pending_data
            create_backup = self._pending_create_backup
            max_retries = self._pending_max_retries
            self._pending_data = None

            # 재시도 로직
            for attempt in range(max_retries):
                try:
                    # 원자적 저장: 임시 파일에 먼저 쓰고 원본 교체
                    self._atomic_save(save_data)

                    # 백업 생성
                    if create_backup:
                        self.backup_service.create_backup()

                    self._data_cache = save_data
                    logger.info(f"Async batch save completed (attempt {attempt + 1})")
                    return

                except Exception as e:
                    logger.error(f"Async save attempt {attempt + 1} failed: {e}")
                    if attempt == max_retries - 1:
                        logger.error(f"Failed to save data after {max_retries} attempts")
                        raise Exception(f"Failed to save data after {max_retries} attempts") from e

    def _atomic_save(self, data: Dict[str, Any]) -> None:
        """원자적으로 데이터를 저장합니다 (임시 파일 → 원본 교체).

        Args:
            data: 저장할 데이터
        """
        # 임시 파일에 저장
        with tempfile.NamedTemporaryFile(
            mode='w',
            encoding='utf-8',
            delete=False,
            dir=self.data_file.parent,
            prefix='.tmp_',
            suffix='.json'
        ) as tmp_file:
            json.dump(data, tmp_file, ensure_ascii=False, indent=2)
            tmp_path = Path(tmp_file.name)

        try:
            # 임시 파일을 원본으로 교체 (원자적 연산)
            shutil.move(str(tmp_path), str(self.data_file))
        except Exception as e:
            # 실패 시 임시 파일 삭제
            if tmp_path.exists():
                tmp_path.unlink()
            raise e
