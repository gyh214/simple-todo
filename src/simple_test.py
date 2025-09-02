#!/usr/bin/env python3
"""
간단한 TodoManager 테스트 (로깅 없이)
"""

import json
import os
import uuid
from datetime import datetime
from pathlib import Path

class SimpleTodoManager:
    def __init__(self):
        # Windows AppData/Local 경로 사용
        appdata_local = os.environ.get('LOCALAPPDATA', os.path.expanduser('~\\AppData\\Local'))
        data_dir = Path(appdata_local) / 'TodoPanel'
        self._data_path = data_dir / 'data.json'
        
        # 디렉토리 생성
        self._data_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 데이터 초기화
        self._todos = []
        self.load_data()
    
    def load_data(self):
        if self._data_path.exists():
            with open(self._data_path, 'r', encoding='utf-8') as f:
                self._todos = json.load(f)
        else:
            self._todos = []
    
    def save_data(self):
        with open(self._data_path, 'w', encoding='utf-8') as f:
            json.dump(self._todos, f, ensure_ascii=False, indent=2)
    
    def create_todo(self, text):
        todo = {
            'id': str(uuid.uuid4()),
            'text': text.strip(),
            'completed': False,
            'created_at': datetime.now().isoformat(),
            'position': len(self._todos)
        }
        self._todos.append(todo)
        self.save_data()
        return todo
    
    def read_todos(self):
        return sorted(self._todos, key=lambda x: x.get('position', 0))
    
    def get_stats(self):
        total = len(self._todos)
        completed = sum(1 for todo in self._todos if todo['completed'])
        return {'total': total, 'completed': completed, 'pending': total - completed}

def main():
    print("Starting simple TodoManager test...")
    
    try:
        manager = SimpleTodoManager()
        print(f"Data path: {manager._data_path}")
        
        # Create test todo
        todo = manager.create_todo("Simple test todo")
        print(f"Created todo: {todo['id'][:8]}...")
        
        # Read todos
        todos = manager.read_todos()
        print(f"Total todos: {len(todos)}")
        
        # Get stats
        stats = manager.get_stats()
        print(f"Stats - Total: {stats['total']}, Completed: {stats['completed']}")
        
        print("Test completed successfully!")
        return True
        
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    main()