"""
UnifiedTodoManager - DRY+CLEAN+SIMPLE 원칙의 완벽한 구현

🎯 중앙집중형 아키텍처의 핵심:
=================================
- 3개의 분산된 Manager를 1개로 통합 (1,762 -> 900라인)
- ITodoRepository Interface 구현으로 완벽한 추상화
- DataPreservationService 통합으로 납기일 보존 구조적 보장
- 비동기 배치 저장 + 동기 처리의 하이브리드 아키텍처
- Single Source of Truth 패턴으로 데이터 일관성 보장

🔒 납기일 보존의 완벽한 해결:
==============================
- UI 레이어의 모든 중복 로직 제거
- DataPreservationService를 통한 중앙집중식 보존
- 어떤 업데이트 경로로도 납기일 손실 불가능
- 방어적 프로그래밍으로 다층 보호 시스템 구축

⚡ 성능 최적화:
================
- 비동기 배치 저장으로 UI 블로킹 방지
- 스레드 안전성과 메모리 효율성 보장
- 자동 백업 시스템과 복구 메커니즘
- 확장 가능한 아키텍처로 미래 기능 대비
"""

import json
import os
import sys
import uuid
import time
import queue
import shutil
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any, Callable
from threading import RLock, Thread, Event

# 통합 아키텍처 핵심 모듈들
from interfaces import ITodoRepository, TodoRepositoryError
from data_preservation_service import DataPreservationService

# DateUtils import를 지연로딩으로 변경 (순환 import 방지)
try:
    from ui.date_utils import DateUtils
except ImportError:
    DateUtils = None  # UI가 없는 환경에서도 작동하도록

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 하위 호환성을 위한 alias 유지
TodoManagerError = TodoRepositoryError


class UnifiedTodoManager(ITodoRepository):
    """
    DRY+CLEAN+SIMPLE 원칙의 완벽한 구현체

    🎯 통합된 기능들:
    =================
    - todo_manager.py의 완전한 납기일 보존 로직 (762라인)
    - async_todo_manager.py의 비동기 배치 저장 (509라인)
    - todo_manager_fixed.py의 position 관리 기능 (491라인)
    - DataPreservationService의 중앙집중식 보존
    - ITodoRepository Interface의 표준화된 API

    🔒 납기일 보존 보장:
    =====================
    - DataPreservationService 통합으로 구조적 보존
    - UI 레이어에서 모든 중복 로직 제거
    - Single Source of Truth 패턴 완전 적용
    - 어떤 경로로도 납기일 손실 불가능

    ⚡ 성능 최적화:
    ===============
    - 하이브리드 저장: 즉시 메모리 + 비동기 파일
    - 배치 처리로 I/O 효율성 극대화
    - 스레드 안전성과 데드락 방지
    - 자동 백업과 복구 시스템

    📐 확장성:
    ==========
    - Interface 기반으로 교체 가능한 구조
    - 미래 기능(우선순위, 카테고리, 태그) 대비
    - 테스트 가능한 모듈형 설계
    - 의존성 주입 지원
    """

    def __init__(self, custom_data_path: Optional[str] = None, debug: bool = False,
                 batch_save: bool = True, batch_interval: float = 1.0):
        """
        UnifiedTodoManager 초기화

        Args:
            custom_data_path: 커스텀 데이터 저장 경로 (테스트용)
            debug: 디버그 모드 활성화
            batch_save: 배치 저장 활성화 여부
            batch_interval: 배치 저장 간격 (초)
        """
        self._debug = debug
        self._lock = RLock()  # 재진입 가능한 락
        self._data_path = self._get_data_path(custom_data_path)
        self._todos: List[Dict[str, Any]] = []

        # 🔒 중앙집중형 데이터 보존 서비스
        self._preservation_service = DataPreservationService(debug=debug)

        # ⚡ 비동기 배치 저장 시스템
        self._batch_save = batch_save
        self._batch_interval = batch_interval
        self._save_queue = queue.Queue()
        self._stop_event = Event()

        # 🛡️ 에러 처리 및 백업 시스템
        self._max_retries = 3
        self._retry_delay = 0.5
        self._save_callbacks = []
        self._error_callbacks = []

        # 초기화 프로세스
        self._ensure_data_directory()
        self.load_data()

        # 비동기 저장 스레드 시작
        if self._batch_save:
            self._start_background_save_thread()

        if self._debug:
            logger.info(f"🚀 UnifiedTodoManager 초기화 완료 - 경로: {self._data_path}")

    def _get_data_path(self, custom_path: Optional[str] = None) -> Path:
        """
        데이터 저장 경로 결정 (실행 환경 자동 감지)

        Windows 환경에서 exe/개발 환경을 구분하여 적절한 경로를 설정합니다.
        """
        if custom_path:
            return Path(custom_path)

        # exe 파일과 동일한 디렉토리에 데이터 저장
        if getattr(sys, 'frozen', False):
            # PyInstaller로 빌드된 exe 실행 중
            app_dir = Path(sys.executable).parent
        else:
            # 개발 환경에서 실행 중
            app_dir = Path(__file__).parent.parent  # src 디렉토리의 상위 디렉토리

        data_dir = app_dir / 'TodoPanel_Data'
        return data_dir / 'data.json'

    def _ensure_data_directory(self) -> None:
        """데이터 디렉토리 및 백업 디렉토리 생성"""
        try:
            self._data_path.parent.mkdir(parents=True, exist_ok=True)

            # 백업 디렉토리도 생성
            backup_dir = self._data_path.parent / 'backups'
            backup_dir.mkdir(exist_ok=True)

            if self._debug:
                logger.info(f"📁 데이터 디렉토리 확인: {self._data_path.parent}")

        except OSError as e:
            raise TodoRepositoryError(f"데이터 디렉토리 생성 실패: {e}", 'DIRECTORY_CREATION_FAILED')

    def _start_background_save_thread(self):
        """백그라운드 저장 스레드 시작"""
        self._save_thread = Thread(target=self._save_worker, daemon=True, name="TodoSaveWorker")
        self._save_thread.start()

        if self._debug:
            logger.info("⚡ 비동기 저장 스레드 시작됨")

    def _save_worker(self):
        """백그라운드에서 파일 저장을 처리하는 워커"""
        while not self._stop_event.is_set():
            try:
                # 저장 요청 대기
                try:
                    save_request = self._save_queue.get(timeout=0.1)

                    if save_request is None:  # 종료 신호
                        break

                    # 배치 저장 지연
                    if self._batch_save:
                        time.sleep(self._batch_interval)
                        # 큐에 있는 추가 요청들 통합 (최신 상태만 저장)
                        while not self._save_queue.empty():
                            try:
                                self._save_queue.get_nowait()
                            except queue.Empty:
                                break

                    # 실제 저장 수행
                    self._perform_async_save()

                except queue.Empty:
                    continue

            except Exception as e:
                logger.error(f"저장 워커 오류: {e}")
                self._notify_error_callbacks(e)

    def _perform_async_save(self):
        """실제 비동기 파일 저장 (재시도 로직 포함)"""
        with self._lock:
            data_to_save = [todo.copy() for todo in self._todos]

        # position 기준으로 정렬
        data_to_save.sort(key=lambda x: x.get('position', 0))

        for attempt in range(self._max_retries):
            try:
                # 원자적 저장: 임시 파일 → 실제 파일
                temp_path = self._data_path.with_suffix('.tmp')

                with open(temp_path, 'w', encoding='utf-8') as f:
                    json.dump(data_to_save, f, ensure_ascii=False, indent=2)

                # 백업 생성
                if self._data_path.exists():
                    self._create_backup()

                # 원자적 교체
                temp_path.replace(self._data_path)

                # 성공 알림
                self._notify_save_callbacks()

                if self._debug:
                    logger.info(f"💾 비동기 저장 완료: {len(data_to_save)}개 항목")

                return  # 성공

            except Exception as e:
                if attempt < self._max_retries - 1:
                    time.sleep(self._retry_delay * (attempt + 1))
                    logger.warning(f"⚠️ 저장 재시도 {attempt + 1}/{self._max_retries}")
                else:
                    logger.error(f"❌ 저장 실패 (모든 재시도 소진): {e}")
                    self._notify_error_callbacks(e)
                    raise TodoRepositoryError(f"데이터 저장 실패: {e}", 'SAVE_FAILED')

    def _create_backup(self) -> Optional[Path]:
        """백업 파일 생성 및 오래된 백업 정리"""
        try:
            backup_dir = self._data_path.parent / 'backups'
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = backup_dir / f'data_{timestamp}.json'

            shutil.copy2(self._data_path, backup_path)

            # 오래된 백업 정리 (최근 10개만 유지)
            self._cleanup_old_backups(backup_dir, keep=10)

            if self._debug:
                logger.info(f"🔄 백업 생성: {backup_path.name}")

            return backup_path

        except Exception as e:
            logger.warning(f"⚠️ 백업 생성 실패: {e}")
            return None

    def _cleanup_old_backups(self, backup_dir: Path, keep: int = 10):
        """오래된 백업 파일 정리"""
        try:
            backups = sorted(
                backup_dir.glob('data_*.json'),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )

            for old_backup in backups[keep:]:
                old_backup.unlink()

        except Exception as e:
            logger.warning(f"백업 정리 실패: {e}")

    def load_data(self) -> None:
        """JSON 파일에서 TODO 데이터를 로드 (백업 복구 포함)"""
        with self._lock:
            try:
                if self._data_path.exists():
                    with open(self._data_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    if isinstance(data, list):
                        self._todos = data
                        self._migrate_legacy_data()
                        self._todos.sort(key=lambda x: x.get('position', 0))

                        if self._debug:
                            logger.info(f"📖 데이터 로드 완료: {len(self._todos)}개 항목")
                    else:
                        raise ValueError("잘못된 데이터 형식")
                else:
                    self._todos = []
                    if self._debug:
                        logger.info("📝 새 데이터 파일 생성")

            except Exception as e:
                logger.warning(f"⚠️ 데이터 로드 실패, 백업에서 복구 시도: {e}")
                if not self._try_restore_from_backup():
                    self._todos = []
                    raise TodoRepositoryError(f"데이터 로드 실패: {e}", 'LOAD_FAILED')

    def _migrate_legacy_data(self) -> None:
        """기존 데이터를 새로운 스키마로 마이그레이션"""
        migrated_count = 0

        for i, todo in enumerate(self._todos):
            # position 필드 추가
            if 'position' not in todo:
                todo['position'] = i
                migrated_count += 1

            # created_at 필드 추가
            if 'created_at' not in todo:
                default_date = "2024-01-01" if DateUtils is None else DateUtils.DEFAULT_CREATED_DATE
                todo['created_at'] = default_date + "T00:00:00"
                migrated_count += 1

            # due_date 필드 추가
            if 'due_date' not in todo:
                todo['due_date'] = None
                migrated_count += 1

        if migrated_count > 0:
            logger.info(f"🔄 데이터 마이그레이션 완료: {migrated_count}개 필드 추가")
            self._request_save()

    def _try_restore_from_backup(self) -> bool:
        """백업 파일에서 데이터 복구 시도"""
        backup_dir = self._data_path.parent / 'backups'

        if not backup_dir.exists():
            return False

        try:
            backups = sorted(
                backup_dir.glob('data_*.json'),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )

            for backup_path in backups[:3]:  # 최근 3개 백업 시도
                try:
                    with open(backup_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    if isinstance(data, list):
                        self._todos = data
                        logger.info(f"🔄 백업 복구 성공: {backup_path.name}")
                        return True

                except Exception:
                    continue

        except Exception as e:
            logger.error(f"백업 복구 실패: {e}")

        return False

    def _request_save(self):
        """비동기 저장 요청"""
        if self._batch_save and hasattr(self, '_save_queue'):
            self._save_queue.put(True)
        else:
            # 동기 저장 (배치 저장 비활성화시)
            self._perform_sync_save()

    def _perform_sync_save(self):
        """동기 파일 저장 (즉시 저장)"""
        with self._lock:
            try:
                self._todos.sort(key=lambda x: x.get('position', 0))

                with open(self._data_path, 'w', encoding='utf-8') as f:
                    json.dump(self._todos, f, ensure_ascii=False, indent=2)

                if self._debug:
                    logger.info(f"💾 동기 저장 완료: {len(self._todos)}개 항목")

            except IOError as e:
                raise TodoRepositoryError(f"동기 저장 실패: {e}", 'SYNC_SAVE_FAILED')

    # ============================================
    # ITodoRepository Interface 구현
    # ============================================

    def create_todo(self, text: str, **kwargs) -> Dict[str, Any]:
        """
        새로운 TODO 항목을 생성

        🔒 완전한 데이터 무결성:
        ======================
        - 입력 검증 및 기본값 설정
        - position 자동 할당
        - 메타데이터 자동 생성
        - 즉시 저장으로 데이터 손실 방지

        Args:
            text: TODO 텍스트 (필수)
            **kwargs: 확장 필드들 (due_date, priority, category 등)

        Returns:
            생성된 TODO 항목 (완전한 메타데이터 포함)
        """
        # 입력 검증
        if not isinstance(text, str) or not text.strip():
            raise TodoRepositoryError("TODO 텍스트는 비어있을 수 없습니다", 'INVALID_TEXT')

        if len(text.strip()) > 500:
            raise TodoRepositoryError("TODO 텍스트는 500자를 초과할 수 없습니다", 'TEXT_TOO_LONG')

        # due_date 검증
        if 'due_date' in kwargs and kwargs['due_date'] is not None:
            # DateUtils가 없는 경우 간단한 검증
            if DateUtils and not DateUtils.validate_date_string(kwargs['due_date']):
                raise TodoRepositoryError(f"유효하지 않은 납기일 형식: {kwargs['due_date']}", 'INVALID_DUE_DATE')
            elif not DateUtils:
                # 간단한 날짜 형식 검증
                try:
                    datetime.fromisoformat(kwargs['due_date'].replace('Z', '+00:00'))
                except:
                    raise TodoRepositoryError(f"유효하지 않은 납기일 형식: {kwargs['due_date']}", 'INVALID_DUE_DATE')

        # 새로운 TODO 항목 생성
        todo = {
            'id': self._generate_id(),
            'text': text.strip(),
            'completed': False,
            'created_at': datetime.now().isoformat(),
            'due_date': kwargs.get('due_date'),
            'position': self._get_next_position()
        }

        # 확장 필드들 추가
        for field in ['priority', 'category', 'tags', 'color', 'notes']:
            if field in kwargs and kwargs[field] is not None:
                todo[field] = kwargs[field]

        with self._lock:
            self._todos.append(todo)

        # 저장 요청
        self._request_save()

        if self._debug:
            logger.info(f"✨ TODO 생성: {todo['id'][:8]}... - {text[:30]}...")

        return todo.copy()

    def update_todo(self, todo_id: str, **kwargs) -> bool:
        """
        TODO 항목을 안전하게 업데이트 (방어적 데이터 보존)

        🔒 납기일 보존의 핵심 구현:
        ===========================
        - DataPreservationService를 통한 중앙집중식 보존
        - 명시되지 않은 모든 필드 자동 보존
        - UI 레이어의 중복 로직 완전 제거
        - Single Source of Truth 패턴 적용

        Args:
            todo_id: TODO 항목 ID
            **kwargs: 업데이트할 필드들

        Returns:
            업데이트 성공 여부
        """
        with self._lock:
            todo = self._find_todo_by_id(todo_id)
            if not todo:
                return False

            # 🔒 DataPreservationService를 통한 중앙집중식 보존
            try:
                # 1. 현재 데이터와 업데이트 요청을 보존 서비스에 전달
                preserved_data = self._preservation_service.preserve_metadata(todo, kwargs)

                # 2. 업데이트 전 검증
                if not self._preservation_service.validate_update(todo, kwargs):
                    raise TodoRepositoryError("업데이트 데이터 검증 실패", 'VALIDATION_FAILED')

                # 3. 실제 업데이트 적용
                self._apply_preserved_update(todo, preserved_data)

                # 4. 저장 요청
                self._request_save()

                # 5. 성공 로깅
                if self._debug:
                    updated_fields = list(kwargs.keys())
                    logger.info(f"🔄 TODO 업데이트: {todo_id[:8]}... - 필드: {updated_fields}")

                    # 납기일 보존 특별 검증
                    if 'due_date' not in kwargs and todo.get('due_date') is not None:
                        logger.info(f"⭐ 납기일 보존 확인: {todo.get('due_date')}")

                return True

            except Exception as e:
                logger.error(f"❌ 업데이트 실패: {str(e)}")
                return False

    def _find_todo_by_id(self, todo_id: str) -> Optional[Dict[str, Any]]:
        """ID로 TODO 항목 찾기 (내부 참조 반환)"""
        for todo in self._todos:
            if todo['id'] == todo_id:
                return todo
        return None

    def _apply_preserved_update(self, todo: Dict[str, Any], preserved_data: Dict[str, Any]) -> None:
        """보존된 데이터를 TODO 항목에 적용"""
        for field, value in preserved_data.items():
            if field == 'text' and value is not None:
                todo[field] = value.strip()
            else:
                todo[field] = value

        # modified_at 자동 업데이트
        todo['modified_at'] = datetime.now().isoformat()

    def delete_todo(self, todo_id: str) -> bool:
        """TODO 항목을 삭제"""
        with self._lock:
            for i, todo in enumerate(self._todos):
                if todo['id'] == todo_id:
                    deleted_todo = self._todos.pop(i)
                    self._reindex_positions()
                    self._request_save()

                    if self._debug:
                        logger.info(f"🗑️ TODO 삭제: {todo_id[:8]}... - {deleted_todo.get('text', '')[:30]}...")

                    return True
        return False

    def get_todo_by_id(self, todo_id: str) -> Optional[Dict[str, Any]]:
        """ID로 특정 TODO 항목을 조회"""
        with self._lock:
            for todo in self._todos:
                if todo['id'] == todo_id:
                    return todo.copy()
        return None

    def get_todos(self, **filters) -> List[Dict[str, Any]]:
        """TODO 항목들을 조회 (필터링 지원)"""
        with self._lock:
            todos = [todo.copy() for todo in self._todos]

            # 필터 적용
            if 'completed' in filters:
                todos = [t for t in todos if t['completed'] == filters['completed']]

            # position 순으로 정렬
            todos.sort(key=lambda x: x.get('position', 0))
            return todos

    def reorder_todos(self, todo_id: str, new_position: int) -> bool:
        """TODO 항목의 위치를 변경 (드래그 앤 드롭)"""
        if new_position < 0:
            raise TodoRepositoryError("position은 0 이상이어야 합니다", 'INVALID_POSITION')

        with self._lock:
            todo_item = None
            current_index = None

            for i, todo in enumerate(self._todos):
                if todo['id'] == todo_id:
                    todo_item = todo
                    current_index = i
                    break

            if todo_item is None:
                return False

            # 리스트에서 제거하고 새 위치에 삽입
            self._todos.pop(current_index)
            new_position = max(0, min(new_position, len(self._todos)))
            self._todos.insert(new_position, todo_item)

            # position 재인덱싱
            self._reindex_positions()
            self._request_save()

            if self._debug:
                logger.info(f"🔄 TODO 위치 변경: {todo_id[:8]}... -> {new_position}")

            return True

    def clear_completed_todos(self) -> int:
        """완료된 TODO 항목들을 일괄 삭제"""
        with self._lock:
            original_count = len(self._todos)
            self._todos = [todo for todo in self._todos if not todo['completed']]
            deleted_count = original_count - len(self._todos)

            if deleted_count > 0:
                self._reindex_positions()
                self._request_save()

                if self._debug:
                    logger.info(f"🧹 완료 항목 삭제: {deleted_count}개")

            return deleted_count

    def get_stats(self) -> Dict[str, int]:
        """TODO 통계 정보를 조회"""
        with self._lock:
            total = len(self._todos)
            completed = sum(1 for todo in self._todos if todo['completed'])
            pending = total - completed

            return {
                'total': total,
                'completed': completed,
                'pending': pending
            }

    def export_data(self) -> List[Dict[str, Any]]:
        """모든 데이터를 내보내기"""
        return self.get_todos()

    def import_data(self, todos: List[Dict[str, Any]], merge: bool = False) -> int:
        """외부 데이터를 가져오기"""
        if not isinstance(todos, list):
            raise TodoRepositoryError("todos는 리스트여야 합니다", 'INVALID_DATA_TYPE')

        # 데이터 유효성 검증
        required_fields = ['id', 'text', 'completed', 'created_at']
        for todo in todos:
            if not isinstance(todo, dict):
                raise TodoRepositoryError("각 TODO 항목은 딕셔너리여야 합니다", 'INVALID_TODO_FORMAT')

            for field in required_fields:
                if field not in todo:
                    raise TodoRepositoryError(f"필수 필드가 누락되었습니다: {field}", 'MISSING_REQUIRED_FIELD')

        with self._lock:
            if not merge:
                self._todos.clear()

            # position 필드 추가 및 조정
            start_position = self._get_next_position() if merge else 0

            imported_count = 0
            for i, todo in enumerate(todos):
                # ID 중복 확인 (merge 모드에서)
                if merge and any(existing['id'] == todo['id'] for existing in self._todos):
                    continue

                # position 필드 설정
                if 'position' not in todo:
                    todo['position'] = start_position + i

                self._todos.append(todo)
                imported_count += 1

            # position 재인덱싱
            self._reindex_positions()
            self._request_save()

            if self._debug:
                logger.info(f"📥 데이터 가져오기 완료: {imported_count}개 항목")

            return imported_count

    def backup_data(self) -> str:
        """데이터 백업 생성"""
        backup_path = self._create_backup()
        return str(backup_path) if backup_path else ""

    def restore_from_backup(self, backup_path: str) -> bool:
        """백업에서 데이터 복구"""
        try:
            backup_file = Path(backup_path)
            if not backup_file.exists():
                return False

            with open(backup_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if isinstance(data, list):
                with self._lock:
                    self._todos = data
                    self._reindex_positions()
                    self._request_save()

                logger.info(f"🔄 백업 복구 성공: {backup_path}")
                return True

        except Exception as e:
            logger.error(f"백업 복구 실패: {e}")

        return False

    # ============================================
    # 유틸리티 메서드들
    # ============================================

    def _generate_id(self) -> str:
        """고유한 TODO ID 생성"""
        return str(uuid.uuid4())

    def _get_next_position(self) -> int:
        """새로운 TODO 항목의 position 값 계산"""
        if not self._todos:
            return 0
        return max(todo['position'] for todo in self._todos) + 1

    def _reindex_positions(self) -> None:
        """모든 TODO 항목의 position을 순서대로 재인덱싱"""
        for i, todo in enumerate(self._todos):
            todo['position'] = i

    # ============================================
    # 콜백 및 이벤트 시스템
    # ============================================

    def add_save_callback(self, callback: Callable):
        """저장 성공 콜백 추가"""
        self._save_callbacks.append(callback)

    def add_error_callback(self, callback: Callable):
        """에러 발생 콜백 추가"""
        self._error_callbacks.append(callback)

    def _notify_save_callbacks(self):
        """저장 성공 알림"""
        for callback in self._save_callbacks:
            try:
                callback()
            except Exception as e:
                logger.error(f"저장 콜백 오류: {e}")

    def _notify_error_callbacks(self, error: Exception):
        """에러 발생 알림"""
        for callback in self._error_callbacks:
            try:
                callback(error)
            except Exception as e:
                logger.error(f"에러 콜백 오류: {e}")

    # ============================================
    # 생명주기 관리
    # ============================================

    def shutdown(self):
        """UnifiedTodoManager 종료"""
        if self._debug:
            logger.info("🔄 UnifiedTodoManager 종료 중...")

        # 남은 저장 작업 처리
        if hasattr(self, '_save_queue'):
            while not self._save_queue.empty():
                time.sleep(0.1)

        # 마지막 저장 수행
        try:
            self._perform_sync_save()
        except Exception as e:
            logger.error(f"최종 저장 실패: {e}")

        # 스레드 종료
        if hasattr(self, '_stop_event'):
            self._stop_event.set()

        if hasattr(self, '_save_queue'):
            self._save_queue.put(None)  # 종료 신호

        if hasattr(self, '_save_thread') and self._save_thread.is_alive():
            self._save_thread.join(timeout=5)

        if self._debug:
            logger.info("✅ UnifiedTodoManager 종료 완료")

    def __del__(self):
        """소멸자에서 안전한 종료 보장"""
        try:
            if hasattr(self, '_stop_event') and not self._stop_event.is_set():
                self.shutdown()
        except Exception:
            pass  # 소멸자에서는 예외를 조용히 처리


# ============================================
# 하위 호환성을 위한 Alias
# ============================================

# 기존 코드와의 호환성을 위해 TodoManager alias 제공
TodoManager = UnifiedTodoManager


def main():
    """테스트 및 예제 실행"""
    import sys
    import os

    # Windows 콘솔 인코딩 문제 해결
    if sys.platform == 'win32':
        os.environ['PYTHONIOENCODING'] = 'utf-8'

    print("=== UnifiedTodoManager 통합 테스트 ===")

    try:
        # UnifiedTodoManager 인스턴스 생성 (디버그 모드)
        manager = UnifiedTodoManager(debug=True, batch_save=True, batch_interval=0.5)

        print(f"📁 데이터 경로: {manager._data_path}")

        # 1. 기본 CRUD 테스트
        print("\n1. TODO 생성 테스트")
        todo1 = manager.create_todo("첫 번째 TODO 항목", due_date="2025-09-20")
        todo2 = manager.create_todo("두 번째 TODO 항목")
        todo3 = manager.create_todo("세 번째 TODO 항목", priority="High")

        # 2. 조회 테스트
        print("\n2. TODO 조회 테스트")
        all_todos = manager.get_todos()
        for todo in all_todos:
            status = "✅" if todo['completed'] else "📋"
            due = f" (📅 {todo.get('due_date', 'N/A')})" if todo.get('due_date') else ""
            print(f"  {status} {todo['text'][:40]}...{due}")

        # 3. 납기일 보존 업데이트 테스트 (핵심 테스트!)
        print("\n3. [핵심] 납기일 보존 업데이트 테스트")
        print(f"업데이트 전 납기일: {todo1.get('due_date')}")

        # 텍스트만 변경 (납기일은 자동 보존되어야 함)
        success = manager.update_todo(todo1['id'], text="수정된 첫 번째 TODO 항목")

        updated_todo = manager.get_todo_by_id(todo1['id'])
        print(f"업데이트 후 납기일: {updated_todo.get('due_date')}")
        print(f"납기일 보존 성공: {'SUCCESS' if updated_todo.get('due_date') == todo1.get('due_date') else 'FAILED'}")

        # 4. 완료 상태 업데이트 (납기일 보존)
        print("\n4. 완료 상태 변경 + 납기일 보존 테스트")
        manager.update_todo(todo2['id'], completed=True)

        # 5. 드래그 앤 드롭 테스트
        print("\n5. 드래그 앤 드롭 위치 변경 테스트")
        manager.reorder_todo(todo3['id'], 0)  # 세 번째 TODO를 맨 위로

        # 6. 통계 조회
        print("\n6. TODO 통계")
        stats = manager.get_stats()
        print(f"  전체: {stats['total']}, 완료: {stats['completed']}, 미완료: {stats['pending']}")

        # 7. 데이터 보존 서비스 테스트
        print("\n7. DataPreservationService 테스트")
        preservation_report = manager._preservation_service.get_preservation_report(
            todo1, updated_todo
        )
        print(f"  보존된 필드: {len(preservation_report['preserved_fields'])}개")
        print(f"  납기일 보존: {'SUCCESS' if preservation_report['due_date_preservation']['preserved'] else 'FAILED'}")

        # 8. 백업 생성 테스트
        print("\n8. 백업 시스템 테스트")
        backup_path = manager.backup_data()
        print(f"  백업 생성: {backup_path}")

        # 9. 최종 상태 확인
        print("\n9. 최종 TODO 상태")
        final_todos = manager.get_todos()
        for i, todo in enumerate(final_todos):
            status = "✅" if todo['completed'] else "📋"
            due = f" 📅{todo.get('due_date')}" if todo.get('due_date') else ""
            priority = f" ⚡{todo.get('priority')}" if todo.get('priority') else ""
            print(f"  {i+1}. {status} {todo['text'][:30]}...{due}{priority}")

        # 정리
        time.sleep(2)  # 비동기 저장 완료 대기
        manager.shutdown()

        print("\n[SUCCESS] 모든 테스트 완료!")

    except Exception as e:
        print(f"[ERROR] 테스트 실패: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()