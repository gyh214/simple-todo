"""
Windows TODO 패널 앱의 데이터 관리 모듈

완전한 CRUD 작업과 Windows AppData 저장소를 지원하는 TODO 데이터 관리자.
드래그 앤 드롭을 위한 position 기능과 완전한 에러 처리를 포함합니다.
"""

import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
from threading import Lock


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
        self._lock = Lock()
        self._data_path = self._get_data_path(custom_data_path)
        self._todos: List[Dict[str, Any]] = []
        
        # 데이터 디렉토리 생성 및 초기 데이터 로드
        self._ensure_data_directory()
        self.load_data()
        
        if self._debug:
            print(f"TodoManager 초기화 완료. 데이터 경로: {self._data_path}")
    
    def _log(self, message: str) -> None:
        """디버그 모드에서만 로그 출력"""
        if self._debug:
            print(f"[TodoManager] {message}")
    
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
        
        # Windows AppData/Local 경로 사용
        appdata_local = os.environ.get('LOCALAPPDATA')
        if not appdata_local:
            # LOCALAPPDATA 환경변수가 없는 경우 대체 경로 사용
            appdata_local = os.path.expanduser('~\\AppData\\Local')
        
        data_dir = Path(appdata_local) / 'TodoPanel'
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
    
    def _validate_todo_data(self, text: str) -> None:
        """TODO 데이터 유효성 검증"""
        if not isinstance(text, str):
            raise TodoManagerError("TODO 텍스트는 문자열이어야 합니다.")
        
        if not text.strip():
            raise TodoManagerError("TODO 텍스트는 비어있을 수 없습니다.")
        
        if len(text.strip()) > 500:
            raise TodoManagerError("TODO 텍스트는 500자를 초과할 수 없습니다.")
    
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
                        # 기존 데이터에 position 필드가 없는 경우 추가
                        for i, todo in enumerate(self._todos):
                            if 'position' not in todo:
                                todo['position'] = i
                        
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
    
    def create_todo(self, text: str) -> Dict[str, Any]:
        """
        새로운 TODO 항목을 생성
        
        Args:
            text: TODO 항목의 텍스트
            
        Returns:
            생성된 TODO 항목 딕셔너리
            
        Raises:
            TodoManagerError: 유효하지 않은 입력이나 저장 실패시
        """
        self._validate_todo_data(text)
        
        todo = {
            'id': self._generate_id(),
            'text': text.strip(),
            'completed': False,
            'created_at': datetime.now().isoformat(),
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
        TODO 항목을 업데이트
        
        Args:
            todo_id: 업데이트할 TODO의 ID
            **kwargs: 업데이트할 필드들 (text, completed)
            
        Returns:
            성공 여부
            
        Raises:
            TodoManagerError: 유효하지 않은 입력이나 저장 실패시
        """
        with self._lock:
            for todo in self._todos:
                if todo['id'] == todo_id:
                    # 허용된 필드만 업데이트
                    if 'text' in kwargs:
                        self._validate_todo_data(kwargs['text'])
                        todo['text'] = kwargs['text'].strip()
                    
                    if 'completed' in kwargs:
                        if not isinstance(kwargs['completed'], bool):
                            raise TodoManagerError("completed는 boolean 값이어야 합니다.")
                        todo['completed'] = kwargs['completed']
                    
                    self.save_data()
                    self._log(f"TODO 항목 업데이트: {todo_id}")
                    return True
        
        return False
    
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
    
    def _reindex_positions(self) -> None:
        """모든 TODO 항목의 position을 순서대로 재인덱싱"""
        for i, todo in enumerate(self._todos):
            todo['position'] = i
    
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