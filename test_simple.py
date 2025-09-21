#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple test script to verify due_date preservation during TODO editing
"""

import sys
import os
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from todo_manager import TodoManager
    print("[SUCCESS] TodoManager imported successfully")
except ImportError as e:
    print(f"[ERROR] TodoManager import failed: {e}")
    sys.exit(1)

def main():
    print("\n=== Due Date Preservation Test ===")

    # Initialize TodoManager with existing data
    manager = TodoManager(debug=True)

    # Test TODO ID
    test_id = "test-todo-with-due-date-001"

    print(f"Testing TODO ID: {test_id}")

    # Get current state
    todos = manager.read_todos()
    test_todo = None

    for todo in todos:
        if todo['id'] == test_id:
            test_todo = todo
            break

    if not test_todo:
        print(f"[ERROR] Test TODO not found: {test_id}")
        return False

    print(f"BEFORE - Text: {test_todo.get('text', 'N/A')}")
    print(f"BEFORE - Due Date: {test_todo.get('due_date', 'N/A')}")

    original_due_date = test_todo.get('due_date')
    if not original_due_date:
        print("[ERROR] No due_date in test TODO!")
        return False

    print(f"Original due_date confirmed: {original_due_date}")

    # CRITICAL TEST: Edit text without specifying due_date
    print("\n--- Testing text edit (without due_date parameter) ---")
    new_text = f"EDITED: Due date preservation test - {datetime.now().strftime('%H:%M:%S')}"

    success = manager.update_todo(test_id, text=new_text)

    if not success:
        print("[ERROR] TODO update failed!")
        return False

    print("[SUCCESS] TODO updated")

    # Check result
    todos_after = manager.read_todos()
    test_todo_after = None

    for todo in todos_after:
        if todo['id'] == test_id:
            test_todo_after = todo
            break

    if not test_todo_after:
        print("[ERROR] Cannot find TODO after update!")
        return False

    print(f"AFTER - Text: {test_todo_after.get('text', 'N/A')}")
    print(f"AFTER - Due Date: {test_todo_after.get('due_date', 'N/A')}")

    # VERIFY: Due date preservation
    after_due_date = test_todo_after.get('due_date')

    print(f"\nDue Date Verification:")
    print(f"  Original: {original_due_date}")
    print(f"  After:    {after_due_date}")

    if original_due_date == after_due_date:
        print("\n[SUCCESS] Due date preserved during editing!")
        print("The fix is working correctly!")
        return True
    else:
        print("\n[FAILURE] Due date was lost during editing!")
        print("The fix needs more work!")
        return False

if __name__ == "__main__":
    try:
        result = main()
        if result:
            print("\n=== TEST PASSED ===")
            print("Due date preservation is working correctly!")
        else:
            print("\n=== TEST FAILED ===")
            print("Due date preservation needs fixing!")
    except Exception as e:
        print(f"\n[ERROR] Test failed with exception: {e}")
        import traceback
        traceback.print_exc()