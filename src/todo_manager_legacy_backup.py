"""
Windows TODO 패널 앱의 데이터 관리 모듈

완전한 CRUD 작업과 Windows AppData 저장소를 지원하는 TODO 데이터 관리자.
드래그 앤 드롭을 위한 position 기능과 완전한 에러 처리를 포함합니다.
"""

import json
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
from threading import RLock
from ui.date_utils import DateUtils


class TodoManagerError(Exception):
    """TodoManager 전용 예외 클래스"""
    pass


class TodoManager:
    """
    TODO 항목의 완전한 CRUD 작업을 처리하는 데이터 관리자
    
    Features:
    - JSON 기반 영구 저장소 (Windows AppData/Local)
    - 완전한 CRUD 작업 지원
    - 드래그 앤 드롭을 위한 position 관리
    - 스레드 안전성
    - 완전한 에러 처리 및 로깅
    """
    
    def __init__(self, custom_data_path: Optional[str] = None, debug: bool = False):
        """
        TodoManager 초기화
        
        Args:
            custom_data_path: 커스텀 데이터 저장 경로 (테스트용, 선택사항)
            debug: 디버그 모드 (True시 상세 출력)
        """
        self._debug = debug
        self._lock = RLock()  # RLock으로 변경 - 재진입 가능한 락
        self._data_path = self._get_data_path(custom_data_path)
        self._todos: List[Dict[str, Any]] = []
        
        # 데이터 디렉토리 생성 및 초기 데이터 로드
        self._ensure_data_directory()
        self.load_data()
        
        if self._debug:
            print(f"TodoManager 초기화 완료. 데이터 경로: {self._data_path}")
    
    def _log(self, message: str) -> None:
        """디버그 모드에서만 로그 출력 (Windows 인코딩 안전처리)"""
        if self._debug:
            try:
                print(f"[TodoManager] {message}")
            except UnicodeEncodeError:
                # Windows 콘솔 인코딩 문제에 대한 안전처리
                safe_message = message.encode('cp949', errors='ignore').decode('cp949')
                print(f"[TodoManager] {safe_message}")
    
    def _get_data_path(self, custom_path: Optional[str] = None) -> Path:
        """
        데이터 저장 경로 결정
        
        Args:
            custom_path: 커스텀 경로 (주로 테스트용)
            
        Returns:
            데이터 파일의 전체 경로
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
        """데이터 디렉토리가 존재하는지 확인하고 없으면 생성"""
        try:
            self._data_path.parent.mkdir(parents=True, exist_ok=True)
            self._log(f"데이터 디렉토리 확인/생성: {self._data_path.parent}")
        except OSError as e:
            raise TodoManagerError(f"데이터 디렉토리 생성 실패: {e}")
    
    def _generate_id(self) -> str:
        """고유한 TODO ID 생성"""
        return str(uuid.uuid4())
    
    def _get_next_position(self) -> int:
        """새로운 TODO 항목의 position 값 계산"""
        if not self._todos:
            return 0
        return max(todo['position'] for todo in self._todos) + 1
    
    def _validate_todo_data(self, text: str, due_date: Optional[str] = None) -> None:
        """TODO 데이터 유효성 검증"""
        if not isinstance(text, str):
            raise TodoManagerError("TODO 텍스트는 문자열이어야 합니다.")

        if not text.strip():
            raise TodoManagerError("TODO 텍스트는 비어있을 수 없습니다.")

        if len(text.strip()) > 500:
            raise TodoManagerError("TODO 텍스트는 500자를 초과할 수 없습니다.")

        # 납기일 유효성 검증
        if due_date is not None and not DateUtils.validate_date_string(due_date):
            raise TodoManagerError(f"유효하지 않은 납기일 형식입니다: {due_date}")
    
    def load_data(self) -> None:
        """JSON 파일에서 TODO 데이터를 로드"""
        with self._lock:
            try:
                if self._data_path.exists():
                    with open(self._data_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # 데이터 구조 검증
                    if isinstance(data, list):
                        self._todos = data
                        # 기존 데이터 마이그레이션
                        self._migrate_data()

                        self._log(f"{len(self._todos)}개의 TODO 항목을 로드했습니다.")
                    else:
                        self._log("잘못된 데이터 형식. 새로운 데이터로 초기화합니다.")
                        self._todos = []
                else:
                    self._todos = []
                    self._log("새로운 데이터 파일을 생성합니다.")
                
                # 로드 후 position 기준으로 정렬
                self._todos.sort(key=lambda x: x.get('position', 0))
                
            except (json.JSONDecodeError, IOError) as e:
                self._log(f"데이터 로드 실패: {e}")
                self._todos = []
                raise TodoManagerError(f"데이터 로드 중 오류가 발생했습니다: {e}")
    
    def save_data(self) -> None:
        """TODO 데이터를 JSON 파일에 저장"""
        with self._lock:
            try:
                # position 기준으로 정렬 후 저장
                self._todos.sort(key=lambda x: x.get('position', 0))
                
                with open(self._data_path, 'w', encoding='utf-8') as f:
                    json.dump(self._todos, f, ensure_ascii=False, indent=2)
                
                self._log(f"{len(self._todos)}개의 TODO 항목을 저장했습니다.")
                
            except IOError as e:
                self._log(f"데이터 저장 실패: {e}")
                raise TodoManagerError(f"데이터 저장 중 오류가 발생했습니다: {e}")
    
    def create_todo(self, text: str, due_date: Optional[str] = None) -> Dict[str, Any]:
        """
        새로운 TODO 항목을 생성

        Args:
            text: TODO 항목의 텍스트
            due_date: 납기일 (선택사항, ISO 날짜 형식: YYYY-MM-DD)

        Returns:
            생성된 TODO 항목 딕셔너리

        Raises:
            TodoManagerError: 유효하지 않은 입력이나 저장 실패시
        """
        self._validate_todo_data(text, due_date)
        
        todo = {
            'id': self._generate_id(),
            'text': text.strip(),
            'completed': False,
            'created_at': datetime.now().isoformat(),
            'due_date': due_date,
            'position': self._get_next_position()
        }
        
        with self._lock:
            self._todos.append(todo)
            self.save_data()
        
        self._log(f"새로운 TODO 항목 생성: {todo['id']}")
        return todo.copy()
    
    def read_todos(self) -> List[Dict[str, Any]]:
        """
        모든 TODO 항목을 position 순서로 조회
        
        Returns:
            TODO 항목 리스트 (position 기준 정렬)
        """
        with self._lock:
            # position 기준으로 정렬하여 반환
            sorted_todos = sorted(self._todos, key=lambda x: x.get('position', 0))
            return [todo.copy() for todo in sorted_todos]
    
    def get_todo_by_id(self, todo_id: str) -> Optional[Dict[str, Any]]:
        """
        ID로 특정 TODO 항목을 조회
        
        Args:
            todo_id: 조회할 TODO의 ID
            
        Returns:
            TODO 항목 딕셔너리 또는 None
        """
        with self._lock:
            for todo in self._todos:
                if todo['id'] == todo_id:
                    return todo.copy()
        return None
    
    def update_todo(self, todo_id: str, **kwargs) -> bool:
        """
        TODO 항목을 업데이트 (방어적 필드 보존 적용)

        Args:
            todo_id: 업데이트할 TODO의 ID
            **kwargs: 업데이트할 필드들 (text, completed, due_date)

        Returns:
            성공 여부

        Raises:
            TodoManagerError: 유효하지 않은 입력이나 저장 실패시

        Note:
            명시적으로 전달되지 않은 필드는 자동으로 기존 값이 보존됩니다.
            특히 due_date(납기일) 필드는 UI에서 텍스트 편집 시에도 자동으로 보존됩니다.
        """
        with self._lock:
            todo = self._find_todo_by_id(todo_id)
            if not todo:
                return False

            # 방어적 필드 보존: 전달되지 않은 필드는 기존 값 유지
            update_data = self._prepare_update_data(todo, **kwargs)

            # 업데이트 전 유효성 검증
            self._validate_update_data(update_data)

            # 실제 업데이트 적용
            self._apply_todo_update(todo, update_data)

            self.save_data()

            # 업데이트 완료 로그 및 검증
            self._log(f"TODO 항목 업데이트 완료: {todo_id} (요청 필드: {list(kwargs.keys())})")
            if 'due_date' in update_data and self._debug:
                self._log(f"⭐ 최종 납기일 값: {update_data['due_date']}")

            # 납기일 보존 성공 검증
            if self._debug and 'due_date' not in kwargs:
                final_todo = self._find_todo_by_id(todo_id)
                if final_todo and final_todo.get('due_date') == update_data.get('due_date'):
                    self._log(f"[SUCCESS] 납기일 보존 최종 확인 성공")

            return True
    
    def delete_todo(self, todo_id: str) -> bool:
        """
        TODO 항목을 삭제
        
        Args:
            todo_id: 삭제할 TODO의 ID
            
        Returns:
            성공 여부
        """
        with self._lock:
            for i, todo in enumerate(self._todos):
                if todo['id'] == todo_id:
                    deleted_todo = self._todos.pop(i)
                    
                    # position 재조정
                    self._reindex_positions()
                    
                    self.save_data()
                    self._log(f"TODO 항목 삭제: {todo_id}")
                    return True
        
        return False
    
    def reorder_todos(self, todo_id: str, new_position: int) -> bool:
        """
        TODO 항목의 위치를 변경 (드래그 앤 드롭용)
        
        Args:
            todo_id: 이동할 TODO의 ID
            new_position: 새로운 위치 (0부터 시작)
            
        Returns:
            성공 여부
            
        Raises:
            TodoManagerError: 유효하지 않은 position이나 저장 실패시
        """
        if new_position < 0:
            raise TodoManagerError("position은 0 이상이어야 합니다.")
        
        with self._lock:
            # 해당 TODO 찾기
            target_todo = None
            old_index = None
            
            for i, todo in enumerate(self._todos):
                if todo['id'] == todo_id:
                    target_todo = todo
                    old_index = i
                    break
            
            if target_todo is None:
                return False
            
            # 리스트에서 제거
            self._todos.pop(old_index)
            
            # 새로운 위치 조정 (리스트 범위 내로)
            new_position = min(new_position, len(self._todos))
            
            # 새로운 위치에 삽입
            self._todos.insert(new_position, target_todo)
            
            # 전체 position 재인덱싱
            self._reindex_positions()
            
            self.save_data()
            self._log(f"TODO 항목 위치 변경: {todo_id} -> position {new_position}")
            return True
    
    def _find_todo_by_id(self, todo_id: str) -> Optional[Dict[str, Any]]:
        """ID로 TODO 항목을 찾아서 반환 (내부 참조)"""
        for todo in self._todos:
            if todo['id'] == todo_id:
                return todo
        return None

    def _prepare_update_data(self, current_todo: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        업데이트용 데이터 준비 (완전한 방어적 필드 보존)

        📋 중앙집중형 데이터 보존 로직:
        ===============================
        모든 업데이트 작업에서 중요한 메타데이터가 누락되지 않도록 보장합니다.
        UI 레이어에서는 이 메서드를 통해 안전하게 데이터를 업데이트할 수 있습니다.

        🔒 보존되는 필드들:
        - text: TODO 텍스트 내용
        - completed: 완료 상태
        - due_date: 납기일 정보 (⭐ 핵심 보존 대상)
        - priority: 우선순위 (미래 확장용)
        - category: 카테고리 (미래 확장용)
        - tags: 태그 목록 (미래 확장용)
        - created_at: 생성 시간
        - modified_at: 수정 시간
        - color: 색상 코드 (미래 확장용)
        - notes: 추가 메모 (미래 확장용)

        Args:
            current_todo: 현재 TODO 항목
            **kwargs: 업데이트하려는 필드들

        Returns:
            기존 값이 보존된 완전한 업데이트 데이터

        Note:
            이 메서드는 UI 레이어의 중복 로직을 대체하여 DRY 원칙을 준수합니다.
        """
        # 업데이트 가능한 모든 필드 정의 (UI 레이어와 통합)
        updatable_fields = {
            # 핵심 필드들
            'text': str,
            'completed': bool,
            'due_date': (str, type(None)),  # ⭐ 납기일 보존 핵심 필드

            # 확장 필드들 (미래 기능용)
            'priority': str,         # High/Medium/Low
            'category': str,         # Work/Personal/Study 등
            'tags': list,            # 태그 목록
            'created_at': str,       # 생성 시간
            'modified_at': str,      # 수정 시간
            'color': str,            # 색상 코드
            'notes': str,            # 추가 메모
        }

        # 기존 값으로 초기화 (완전한 방어적 보존)
        update_data = {}
        for field in updatable_fields:
            current_value = current_todo.get(field)
            # None이 아닌 의미있는 값만 보존
            if current_value is not None:
                update_data[field] = current_value

        # 명시적으로 전달된 필드만 업데이트
        for field, value in kwargs.items():
            if field in updatable_fields:
                update_data[field] = value
            else:
                self._log(f"경고: 알 수 없는 필드 무시됨: {field}")

        # 디버그 정보 출력
        preserved_count = len([f for f in updatable_fields if f in current_todo and f not in kwargs])
        updated_count = len([f for f in kwargs if f in updatable_fields])

        self._log(f"업데이트 데이터 준비 완룼: {preserved_count}개 필드 보존, {updated_count}개 필드 업데이트")
        if 'due_date' in update_data:
            self._log(f"⭐ 납기일 보존 확인: {update_data['due_date']}")
        if self._debug and 'due_date' in kwargs:
            self._log(f"납기일 업데이트 요청: {kwargs['due_date']}")

        # 납기일 보존 로직 검증 로그 추가
        if self._debug and 'due_date' not in kwargs and 'due_date' in update_data:
            self._log(f"[PRESERVE] 납기일 자동 보존 작동: {update_data['due_date']}")

        return update_data

    def _validate_update_data(self, update_data: Dict[str, Any]) -> None:
        """
        업데이트 데이터 유효성 검증

        Args:
            update_data: 검증할 업데이트 데이터

        Raises:
            TodoManagerError: 유효하지 않은 데이터
        """
        # text 필드 검증
        if 'text' in update_data:
            text = update_data['text']
            due_date = update_data.get('due_date')
            self._validate_todo_data(text, due_date)

        # completed 필드 검증
        if 'completed' in update_data:
            if not isinstance(update_data['completed'], bool):
                raise TodoManagerError("completed는 boolean 값이어야 합니다.")

        # due_date 필드 검증
        if 'due_date' in update_data:
            due_date = update_data['due_date']
            if due_date is not None and not DateUtils.validate_date_string(due_date):
                raise TodoManagerError(f"유효하지 않은 납기일 형식입니다: {due_date}")

    def _apply_todo_update(self, todo: Dict[str, Any], update_data: Dict[str, Any]) -> None:
        """
        TODO 항목에 업데이트 데이터 적용

        Args:
            todo: 업데이트할 TODO 항목 (참조)
            update_data: 적용할 업데이트 데이터
        """
        # text 필드 적용 (strip 처리)
        if 'text' in update_data and update_data['text'] is not None:
            todo['text'] = update_data['text'].strip()

        # completed 필드 적용
        if 'completed' in update_data:
            todo['completed'] = update_data['completed']

        # due_date 필드 적용
        if 'due_date' in update_data:
            todo['due_date'] = update_data['due_date']

    def _reindex_positions(self) -> None:
        """모든 TODO 항목의 position을 순서대로 재인덱싱"""
        for i, todo in enumerate(self._todos):
            todo['position'] = i

    def _migrate_data(self) -> None:
        """기존 데이터를 새로운 스키마로 마이그레이션"""
        migrated_count = 0

        for i, todo in enumerate(self._todos):
            # position 필드 추가 (기존 기능)
            if 'position' not in todo:
                todo['position'] = i
                migrated_count += 1

            # created_at 필드 추가 (기본값: 2025-09-01)
            if 'created_at' not in todo:
                todo['created_at'] = DateUtils.DEFAULT_CREATED_DATE + "T00:00:00"
                migrated_count += 1

            # due_date 필드 추가 (기본값: None)
            if 'due_date' not in todo:
                todo['due_date'] = None
                migrated_count += 1

        if migrated_count > 0:
            self._log(f"데이터 마이그레이션 완료: {migrated_count}개 필드 추가")
            # 마이그레이션 후 저장
            self.save_data()
    
    def get_completed_todos(self) -> List[Dict[str, Any]]:
        """완료된 TODO 항목들만 조회"""
        with self._lock:
            completed = [todo.copy() for todo in self._todos if todo['completed']]
            return sorted(completed, key=lambda x: x.get('position', 0))
    
    def get_pending_todos(self) -> List[Dict[str, Any]]:
        """미완료된 TODO 항목들만 조회"""
        with self._lock:
            pending = [todo.copy() for todo in self._todos if not todo['completed']]
            return sorted(pending, key=lambda x: x.get('position', 0))
    
    def clear_completed_todos(self) -> int:
        """
        완료된 모든 TODO 항목을 삭제
        
        Returns:
            삭제된 항목의 수
        """
        with self._lock:
            original_count = len(self._todos)
            self._todos = [todo for todo in self._todos if not todo['completed']]
            
            # position 재인덱싱
            self._reindex_positions()
            
            deleted_count = original_count - len(self._todos)
            
            if deleted_count > 0:
                self.save_data()
                self._log(f"{deleted_count}개의 완료된 TODO 항목을 삭제했습니다.")
            
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
    
    def export_data(self) -> List[Dict[str, Any]]:
        """전체 데이터를 내보내기용으로 반환"""
        return self.read_todos()
    
    def import_data(self, todos: List[Dict[str, Any]], merge: bool = False) -> int:
        """
        외부 데이터를 가져오기
        
        Args:
            todos: 가져올 TODO 항목들
            merge: True면 기존 데이터와 합치기, False면 덮어쓰기
            
        Returns:
            가져온 항목의 수
            
        Raises:
            TodoManagerError: 잘못된 데이터 형식
        """
        if not isinstance(todos, list):
            raise TodoManagerError("todos는 리스트여야 합니다.")
        
        # 데이터 유효성 검증
        required_fields = ['id', 'text', 'completed', 'created_at']
        for todo in todos:
            if not isinstance(todo, dict):
                raise TodoManagerError("각 TODO 항목은 딕셔너리여야 합니다.")
            
            for field in required_fields:
                if field not in todo:
                    raise TodoManagerError(f"필수 필드가 누락되었습니다: {field}")
        
        with self._lock:
            if not merge:
                self._todos.clear()
            
            # position 필드 추가 및 조정
            start_position = self._get_next_position() if merge else 0
            
            for i, todo in enumerate(todos):
                # ID 중복 확인 (merge 모드에서)
                if merge and any(existing['id'] == todo['id'] for existing in self._todos):
                    continue
                
                # position 필드 설정
                if 'position' not in todo:
                    todo['position'] = start_position + i
                
                self._todos.append(todo)
            
            # position 재인덱싱
            self._reindex_positions()
            
            self.save_data()
            imported_count = len(todos)
            self._log(f"{imported_count}개의 TODO 항목을 가져왔습니다.")
            
            return imported_count

    def update_todo_safe(self, todo_id: str, **kwargs) -> bool:
        """
        안전한 TODO 업데이트 (완전한 데이터 컨텍스트 보존)

        🚪 UI 레이어 전용 인터페이스:
        ===========================
        UI 레이어에서 중복 로직 없이 안전하게 데이터를 업데이트할 수 있습니다.
        납기일, 우선순위 등 모든 메타데이터가 자동으로 보존됩니다.

        🔄 기존 update_todo 와의 차이점:
        - update_todo: 내부 로직을 직접 사용 (기본용)
        - update_todo_safe: UI 레이어를 위한 안전한 래퍼 (추천)

        Args:
            todo_id: 업데이트할 TODO의 ID
            **kwargs: 업데이트할 필드들 (text, completed, due_date 등)

        Returns:
            성공 여부

        Example:
            # 텍스트만 변경 (납기일 자동 보존)
            manager.update_todo_safe(todo_id, text="New text")

            # 완료 상태 변경 (납기일 자동 보존)
            manager.update_todo_safe(todo_id, completed=True)

            # 납기일 변경
            manager.update_todo_safe(todo_id, due_date="2025-09-20")

            # 여러 필드 동시 변경
            manager.update_todo_safe(todo_id, text="New", completed=True, due_date="2025-09-20")
        """
        # 이 메서드는 기존 update_todo와 동일하지만 더 명시적인 이름
        return self.update_todo(todo_id, **kwargs)

    def debug_data_preservation(self, todo_id: str, **update_fields) -> Dict[str, Any]:
        """
        데이터 보존 로직 디버깅용 메서드

        🔍 납기일 보존 로직 검증:
        =============================
        이 메서드는 업데이트 전후의 데이터 변화를 디버깅할 때 사용합니다.
        실제 업데이트를 수행하지는 않고 데이터 보존 과정을 시뮤레이션합니다.

        Args:
            todo_id: TODO 항목 ID
            **update_fields: 업데이트하려는 필드들

        Returns:
            보존 로직이 적용된 업데이트 데이터 (실제 적용 전)

        Example:
            # 텍스트 변경 시 납기일 보존 확인
            result = manager.debug_data_preservation(todo_id, text="New text")
            print("Due date preserved:", result.get('due_date'))

            # 완료 상태 변경 시 납기일 보존 확인
            result = manager.debug_data_preservation(todo_id, completed=True)
            print("Due date preserved:", result.get('due_date'))
        """
        with self._lock:
            todo = self._find_todo_by_id(todo_id)
            if not todo:
                return {}

            # 기존 납기일 정보 기록
            original_due_date = todo.get('due_date')
            self._log(f"[DEBUG] 기존 납기일 = {original_due_date}")
            self._log(f"[DEBUG] 업데이트 요청 필드 = {list(update_fields.keys())}")

            # 방어적 필드 보존 로직 실행
            preserved_data = self._prepare_update_data(todo, **update_fields)

            self._log(f"[DEBUG] 보존 로직 후 납기일 = {preserved_data.get('due_date')}")
            self._log(f"[DEBUG] 보존된 전체 필드 = {list(preserved_data.keys())}")

            # 납기일 보존 상태 검증
            if 'due_date' not in update_fields:  # 납기일을 명시적으로 변경하지 않은 경우
                if original_due_date == preserved_data.get('due_date'):
                    self._log(f"[PASS] 납기일 보존 성공: {original_due_date}")
                else:
                    self._log(f"[FAIL] 납기일 보존 실패: {original_due_date} -> {preserved_data.get('due_date')}")

            return preserved_data


def main():
    """테스트 및 예제 실행"""
    print("=== Windows TODO Panel Data Manager Test ===")
    
    try:
        # TodoManager 인스턴스 생성 (디버그 모드)
        manager = TodoManager(debug=True)
        
        print(f"Data Path: {manager._data_path}")
        
        # 기본 CRUD 테스트
        print("\n1. Create TODO items test")
        todo1 = manager.create_todo("First todo item")
        todo2 = manager.create_todo("Second todo item")
        todo3 = manager.create_todo("Third todo item")
        print(f"Created {len([todo1, todo2, todo3])} todos")
        
        print("\n2. Read all todos")
        all_todos = manager.read_todos()
        for todo in all_todos:
            print(f"  - {todo['text']} (ID: {todo['id'][:8]}..., Position: {todo['position']})")
        
        print("\n3. Update todo test")
        manager.update_todo(todo2['id'], completed=True)
        manager.update_todo(todo1['id'], text="Updated first todo item")
        
        print("\n4. Reorder test (drag & drop)")
        manager.reorder_todos(todo3['id'], 0)  # Move third todo to top
        
        print("\n5. Read todos after update")
        all_todos = manager.read_todos()
        for todo in all_todos:
            status = "[DONE]" if todo['completed'] else "[TODO]"
            print(f"  {status} {todo['text']} (Position: {todo['position']})")
        
        print("\n6. Statistics")
        stats = manager.get_stats()
        print(f"  Total: {stats['total']}, Completed: {stats['completed']}, Pending: {stats['pending']}")
        
        print("\n7. Delete todo test")
        deleted = manager.delete_todo(todo2['id'])
        print(f"Delete result: {deleted}")
        
        print("\n8. Final state")
        final_todos = manager.read_todos()
        for todo in final_todos:
            status = "[DONE]" if todo['completed'] else "[TODO]"
            print(f"  {status} {todo['text']} (Position: {todo['position']})")
        
        print("\n[SUCCESS] All tests completed successfully!")
        
    except TodoManagerError as e:
        print(f"[ERROR] TodoManager error: {e}")
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()