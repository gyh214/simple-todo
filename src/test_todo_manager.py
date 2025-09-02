#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TodoManager 간단 테스트
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from todo_manager import TodoManager

def main():
    print("Starting TodoManager test...")
    
    try:
        # Initialize TodoManager
        manager = TodoManager()
        print("[OK] TodoManager initialized successfully")
        
        # Test create
        todo1 = manager.create_todo("Test todo item 1")
        print(f"[OK] Created todo: {todo1['id'][:8]}...")
        
        # Test read
        todos = manager.read_todos()
        print(f"[OK] Total todos: {len(todos)}")
        
        # Test update
        success = manager.update_todo(todo1['id'], completed=True)
        print(f"[OK] Update result: {success}")
        
        # Test stats
        stats = manager.get_stats()
        print(f"[OK] Stats - Total: {stats['total']}, Completed: {stats['completed']}")
        
        # Test data persistence
        manager.save_data()
        print("[OK] Data saved successfully")
        
        print("\n[SUCCESS] All tests passed!")
        return True
        
    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)