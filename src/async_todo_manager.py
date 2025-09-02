"""
비동기 TODO 매니저 - 안정성과 성능 개선

파일 I/O를 비동기로 처리하여 UI 응답성을 보장하고,
에러 처리 및 재시도 로직을 강화한 TodoManager입니다.
"""

import json
import os
import sys
import uuid
import time
import queue
import threading
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any, Callable
from threading import RLock, Thread, Event
import shutil
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AsyncTodoManagerError(Exception):
    """AsyncTodoManager 전용 예외 클래스"""
    pass


class AsyncTodoManager:
    """
    비동기 파일 I/O와 강화된 에러 처리를 제공하는 TODO 관리자
    
    Features:
    - 비동기 파일 저장으로 UI 블로킹 방지
    - 재시도 로직과 백업 시스템
    - 배치 저장으로 성능 최적화
    - 메모리 캐싱으로 읽기 성능 향상
    """
    
    def __init__(self, custom_data_path: Optional[str] = None, debug: bool = False,
                 batch_save: bool = True, batch_interval: float = 1.0):
        """
        AsyncTodoManager 초기화
        
        Args:
            custom_data_path: 커스텀 데이터 저장 경로
            debug: 디버그 모드
            batch_save: 배치 저장 활성화 여부
            batch_interval: 배치 저장 간격 (초)
        """
        self._debug = debug
        self._lock = RLock()
        self._data_path = self._get_data_path(custom_data_path)
        self._todos: List[Dict[str, Any]] = []
        
        # 비동기 처리를 위한 큐와 이벤트
        self._save_queue = queue.Queue()
        self._stop_event = Event()
        
        # 배치 저장 설정
        self._batch_save = batch_save
        self._batch_interval = batch_interval
        self._pending_save = False
        self._last_save_time = time.time()
        
        # 에러 처리
        self._max_retries = 3
        self._retry_delay = 0.5
        
        # 콜백 함수들
        self._save_callbacks = []
        self._error_callbacks = []
        
        # 초기화
        self._ensure_data_directory()
        self.load_data()
        
        # 백그라운드 저장 스레드 시작
        self._start_save_thread()
        
        if self._debug:
            logger.info(f"AsyncTodoManager 초기화 완료. 데이터 경로: {self._data_path}")
    
    def _get_data_path(self, custom_path: Optional[str] = None) -> Path:
        """데이터 저장 경로 결정"""
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
        """데이터 디렉토리 생성"""
        try:
            self._data_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 백업 디렉토리도 생성
            backup_dir = self._data_path.parent / 'backups'
            backup_dir.mkdir(exist_ok=True)
            
        except OSError as e:
            raise AsyncTodoManagerError(f"데이터 디렉토리 생성 실패: {e}")
    
    def _start_save_thread(self):
        """백그라운드 저장 스레드 시작"""
        self._save_thread = Thread(target=self._save_worker, daemon=True)
        self._save_thread.start()
    
    def _save_worker(self):
        """백그라운드에서 파일 저장을 처리하는 워커"""
        while not self._stop_event.is_set():
            try:
                # 큐에서 저장 요청 대기 (타임아웃 설정)
                try:
                    save_request = self._save_queue.get(timeout=0.1)
                    
                    if save_request is None:  # 종료 신호
                        break
                    
                    # 배치 저장이 활성화된 경우 잠시 대기
                    if self._batch_save:
                        time.sleep(self._batch_interval)
                        # 큐에 있는 추가 요청들 무시 (최신 상태만 저장)
                        while not self._save_queue.empty():
                            try:
                                self._save_queue.get_nowait()
                            except queue.Empty:
                                break
                    
                    # 실제 저장 수행
                    self._perform_save()
                    
                except queue.Empty:
                    continue
                    
            except Exception as e:
                logger.error(f"저장 워커 오류: {e}")
                self._notify_error(e)
    
    def _perform_save(self):
        """실제 파일 저장 수행 (재시도 로직 포함)"""
        with self._lock:
            data_to_save = [todo.copy() for todo in self._todos]
        
        # position 기준으로 정렬
        data_to_save.sort(key=lambda x: x.get('position', 0))
        
        for attempt in range(self._max_retries):
            try:
                # 임시 파일에 먼저 저장
                temp_path = self._data_path.with_suffix('.tmp')
                
                with open(temp_path, 'w', encoding='utf-8') as f:
                    json.dump(data_to_save, f, ensure_ascii=False, indent=2)
                
                # 백업 생성
                if self._data_path.exists():
                    backup_path = self._create_backup()
                    if self._debug:
                        logger.info(f"백업 생성: {backup_path}")
                
                # 임시 파일을 실제 파일로 교체 (원자적 연산)
                temp_path.replace(self._data_path)
                
                # 저장 성공 알림
                self._notify_save_success()
                
                if self._debug:
                    logger.info(f"{len(data_to_save)}개 항목 저장 완료")
                
                return  # 성공
                
            except Exception as e:
                if attempt < self._max_retries - 1:
                    time.sleep(self._retry_delay * (attempt + 1))
                    logger.warning(f"저장 시도 {attempt + 1} 실패, 재시도...")
                else:
                    logger.error(f"저장 실패 (모든 재시도 소진): {e}")
                    self._notify_error(e)
                    raise AsyncTodoManagerError(f"데이터 저장 실패: {e}")
    
    def _create_backup(self) -> Path:
        """백업 파일 생성"""
        backup_dir = self._data_path.parent / 'backups'
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = backup_dir / f'data_{timestamp}.json'
        
        try:
            shutil.copy2(self._data_path, backup_path)
            
            # 오래된 백업 파일 정리 (최근 10개만 유지)
            self._cleanup_old_backups(backup_dir, keep=10)
            
            return backup_path
        except Exception as e:
            logger.warning(f"백업 생성 실패: {e}")
            return None
    
    def _cleanup_old_backups(self, backup_dir: Path, keep: int = 10):
        """오래된 백업 파일 정리"""
        try:
            backups = sorted(backup_dir.glob('data_*.json'), 
                           key=lambda p: p.stat().st_mtime, 
                           reverse=True)
            
            for old_backup in backups[keep:]:
                old_backup.unlink()
                
        except Exception as e:
            logger.warning(f"백업 정리 실패: {e}")
    
    def load_data(self) -> None:
        """JSON 파일에서 TODO 데이터를 로드"""
        with self._lock:
            try:
                if self._data_path.exists():
                    with open(self._data_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    if isinstance(data, list):
                        self._todos = data
                        # position 필드 확인 및 추가
                        for i, todo in enumerate(self._todos):
                            if 'position' not in todo:
                                todo['position'] = i
                        
                        # position 기준 정렬
                        self._todos.sort(key=lambda x: x.get('position', 0))
                        
                        if self._debug:
                            logger.info(f"{len(self._todos)}개 항목 로드 완료")
                    else:
                        self._todos = []
                        logger.warning("잘못된 데이터 형식, 초기화")
                else:
                    self._todos = []
                    if self._debug:
                        logger.info("새 데이터 파일 생성")
                        
            except Exception as e:
                # 백업에서 복구 시도
                if self._try_restore_from_backup():
                    logger.info("백업에서 데이터 복구 성공")
                else:
                    self._todos = []
                    raise AsyncTodoManagerError(f"데이터 로드 실패: {e}")
    
    def _try_restore_from_backup(self) -> bool:
        """백업 파일에서 데이터 복구 시도"""
        backup_dir = self._data_path.parent / 'backups'
        
        if not backup_dir.exists():
            return False
        
        try:
            # 가장 최근 백업 파일 찾기
            backups = sorted(backup_dir.glob('data_*.json'),
                           key=lambda p: p.stat().st_mtime,
                           reverse=True)
            
            for backup_path in backups[:3]:  # 최근 3개 백업 시도
                try:
                    with open(backup_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    if isinstance(data, list):
                        self._todos = data
                        logger.info(f"백업 복구 성공: {backup_path}")
                        return True
                        
                except Exception:
                    continue
                    
        except Exception as e:
            logger.error(f"백업 복구 실패: {e}")
        
        return False
    
    def request_save(self):
        """비동기 저장 요청"""
        self._save_queue.put(True)
    
    def create_todo(self, text: str) -> Dict[str, Any]:
        """새로운 TODO 항목을 생성"""
        if not isinstance(text, str) or not text.strip():
            raise AsyncTodoManagerError("유효하지 않은 TODO 텍스트")
        
        if len(text.strip()) > 500:
            raise AsyncTodoManagerError("TODO 텍스트는 500자를 초과할 수 없습니다")
        
        todo = {
            'id': str(uuid.uuid4()),
            'text': text.strip(),
            'completed': False,
            'created_at': datetime.now().isoformat(),
            'position': self._get_next_position()
        }
        
        with self._lock:
            self._todos.append(todo)
        
        # 비동기 저장 요청
        self.request_save()
        
        if self._debug:
            logger.info(f"TODO 생성: {todo['id']}")
        
        return todo.copy()
    
    def _get_next_position(self) -> int:
        """새로운 TODO 항목의 position 값 계산"""
        with self._lock:
            if not self._todos:
                return 0
            return max(todo['position'] for todo in self._todos) + 1
    
    def read_todos(self) -> List[Dict[str, Any]]:
        """모든 TODO 항목을 position 순서로 조회"""
        with self._lock:
            sorted_todos = sorted(self._todos, key=lambda x: x.get('position', 0))
            return [todo.copy() for todo in sorted_todos]
    
    def get_todo_by_id(self, todo_id: str) -> Optional[Dict[str, Any]]:
        """ID로 특정 TODO 항목 조회"""
        with self._lock:
            for todo in self._todos:
                if todo['id'] == todo_id:
                    return todo.copy()
        return None
    
    def update_todo(self, todo_id: str, **kwargs) -> bool:
        """TODO 항목 업데이트"""
        with self._lock:
            for todo in self._todos:
                if todo['id'] == todo_id:
                    # 텍스트 업데이트
                    if 'text' in kwargs:
                        text = kwargs['text']
                        if not isinstance(text, str) or not text.strip():
                            raise AsyncTodoManagerError("유효하지 않은 텍스트")
                        todo['text'] = text.strip()
                    
                    # 완료 상태 업데이트
                    if 'completed' in kwargs:
                        if not isinstance(kwargs['completed'], bool):
                            raise AsyncTodoManagerError("completed는 boolean이어야 합니다")
                        todo['completed'] = kwargs['completed']
                    
                    # 비동기 저장 요청
                    self.request_save()
                    
                    if self._debug:
                        logger.info(f"TODO 업데이트: {todo_id}")
                    
                    return True
        
        return False
    
    def delete_todo(self, todo_id: str) -> bool:
        """TODO 항목 삭제"""
        with self._lock:
            for i, todo in enumerate(self._todos):
                if todo['id'] == todo_id:
                    del self._todos[i]
                    
                    # position 재조정
                    self._reindex_positions()
                    
                    # 비동기 저장 요청
                    self.request_save()
                    
                    if self._debug:
                        logger.info(f"TODO 삭제: {todo_id}")
                    
                    return True
        
        return False
    
    def reorder_todos(self, todo_id: str, new_position: int) -> bool:
        """TODO 항목의 위치를 변경"""
        with self._lock:
            # 현재 TODO 찾기
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
            
            # 비동기 저장 요청
            self.request_save()
            
            if self._debug:
                logger.info(f"TODO 순서 변경: {todo_id} -> {new_position}")
            
            return True
    
    def _reindex_positions(self):
        """모든 TODO 항목의 position을 순서대로 재인덱싱"""
        for i, todo in enumerate(self._todos):
            todo['position'] = i
    
    def clear_completed(self) -> int:
        """완료된 TODO 항목들을 삭제"""
        with self._lock:
            original_count = len(self._todos)
            self._todos = [todo for todo in self._todos if not todo['completed']]
            deleted_count = original_count - len(self._todos)
            
            if deleted_count > 0:
                self._reindex_positions()
                self.request_save()
                
                if self._debug:
                    logger.info(f"{deleted_count}개 완료 항목 삭제")
            
            return deleted_count
    
    def get_stats(self) -> Dict[str, int]:
        """TODO 항목 통계 조회"""
        with self._lock:
            total = len(self._todos)
            completed = sum(1 for todo in self._todos if todo['completed'])
            pending = total - completed
            
            return {
                'total': total,
                'completed': completed,
                'pending': pending
            }
    
    def add_save_callback(self, callback: Callable):
        """저장 성공 콜백 추가"""
        self._save_callbacks.append(callback)
    
    def add_error_callback(self, callback: Callable):
        """에러 발생 콜백 추가"""
        self._error_callbacks.append(callback)
    
    def _notify_save_success(self):
        """저장 성공 알림"""
        for callback in self._save_callbacks:
            try:
                callback()
            except Exception as e:
                logger.error(f"저장 콜백 오류: {e}")
    
    def _notify_error(self, error: Exception):
        """에러 발생 알림"""
        for callback in self._error_callbacks:
            try:
                callback(error)
            except Exception as e:
                logger.error(f"에러 콜백 오류: {e}")
    
    def shutdown(self):
        """AsyncTodoManager 종료"""
        if self._debug:
            logger.info("AsyncTodoManager 종료 중...")
        
        # 남은 저장 작업 처리
        while not self._save_queue.empty():
            time.sleep(0.1)
        
        # 마지막 저장 수행
        self._perform_save()
        
        # 스레드 종료
        self._stop_event.set()
        self._save_queue.put(None)  # 종료 신호
        
        if self._save_thread.is_alive():
            self._save_thread.join(timeout=5)
        
        if self._debug:
            logger.info("AsyncTodoManager 종료 완료")