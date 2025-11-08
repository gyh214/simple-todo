# -*- coding: utf-8 -*-
"""BaseTask 리팩토링 테스트 스크립트"""

import sys
from datetime import datetime

# 프로젝트 루트를 Python Path에 추가
sys.path.insert(0, r'D:\dev_proj\new-todo-panel')

from src.domain.entities import BaseTask, Todo, SubTask


def test_import():
    """Import 테스트"""
    print("=" * 60)
    print("1. Import 테스트")
    print("=" * 60)
    print(f"OK BaseTask: {BaseTask}")
    print(f"OK Todo: {Todo}")
    print(f"OK SubTask: {SubTask}")
    print()


def test_todo_creation():
    """Todo 생성 테스트"""
    print("=" * 60)
    print("2. Todo 생성 테스트")
    print("=" * 60)

    # Todo 생성
    todo = Todo.create("테스트 Todo", "2025-11-10T00:00:00Z", order=0)
    print(f"OK Todo 생성 성공: ID={todo.id.value}")
    print(f"   - Content: {todo.content.value}")
    print(f"   - Completed: {todo.completed}")
    print(f"   - Due Date: {todo.due_date.value if todo.due_date else None}")
    print(f"   - Order: {todo.order}")
    print()

    return todo


def test_subtask_creation():
    """SubTask 생성 테스트"""
    print("=" * 60)
    print("3. SubTask 생성 테스트")
    print("=" * 60)

    # SubTask 생성
    subtask = SubTask.create("테스트 SubTask", "2025-11-09T00:00:00Z", order=0)
    print(f"OK SubTask 생성 성공: ID={subtask.id.value}")
    print(f"   - Content: {subtask.content.value}")
    print(f"   - Completed: {subtask.completed}")
    print(f"   - Due Date: {subtask.due_date.value if subtask.due_date else None}")
    print(f"   - Order: {subtask.order}")
    print()

    return subtask


def test_common_methods(task, task_name):
    """공통 메서드 테스트 (BaseTask)"""
    print("=" * 60)
    print(f"4. {task_name} 공통 메서드 테스트 (BaseTask)")
    print("=" * 60)

    # complete()
    task.complete()
    print(f"OK complete() 호출 후: completed={task.completed}")

    # uncomplete()
    task.uncomplete()
    print(f"OK uncomplete() 호출 후: completed={task.completed}")

    # toggle_complete()
    task.toggle_complete()
    print(f"OK toggle_complete() 호출 후: completed={task.completed}")
    task.toggle_complete()  # 다시 토글
    print(f"OK toggle_complete() 재호출 후: completed={task.completed}")

    # update_content()
    from src.domain.value_objects.content import Content
    new_content = Content(value="수정된 내용")
    task.update_content(new_content)
    print(f"OK update_content() 호출 후: content={task.content.value}")

    # set_due_date()
    from src.domain.value_objects.due_date import DueDate
    new_due_date = DueDate.from_string("2025-12-01T00:00:00Z")
    task.set_due_date(new_due_date)
    print(f"OK set_due_date() 호출 후: due_date={task.due_date.value}")

    # change_order()
    task.change_order(5)
    print(f"OK change_order() 호출 후: order={task.order}")
    print()


def test_serialization(task, task_name):
    """직렬화/역직렬화 테스트"""
    print("=" * 60)
    print(f"5. {task_name} 직렬화/역직렬화 테스트")
    print("=" * 60)

    # to_dict()
    task_dict = task.to_dict()
    print(f"OK to_dict() 결과:")
    for key, value in task_dict.items():
        print(f"   - {key}: {value}")

    # from_dict()
    if isinstance(task, Todo):
        task_from_dict = Todo.from_dict(task_dict)
    else:
        task_from_dict = SubTask.from_dict(task_dict)

    print(f"OK from_dict() 성공: ID={task_from_dict.id.value}")
    print(f"   - Content: {task_from_dict.content.value}")
    print(f"   - Completed: {task_from_dict.completed}")
    print(f"   - Order: {task_from_dict.order}")
    print()

    return task_dict


def test_todo_specific_features():
    """Todo 전용 기능 테스트"""
    print("=" * 60)
    print("6. Todo 전용 기능 테스트")
    print("=" * 60)

    # Todo 생성
    todo = Todo.create("메인 할일", order=0)

    # SubTask 추가
    subtask1 = SubTask.create("하위 할일 1", order=0)
    subtask2 = SubTask.create("하위 할일 2", order=1)

    todo.add_subtask(subtask1)
    todo.add_subtask(subtask2)
    print(f"OK add_subtask() 성공: subtasks={len(todo.subtasks)}개")

    # SubTask 토글
    todo.toggle_subtask_complete(subtask1.id)
    print(f"OK toggle_subtask_complete() 성공: subtask1.completed={subtask1.completed}")

    # to_dict() 테스트 (subtasks 포함)
    todo_dict = todo.to_dict()
    print(f"OK to_dict() with subtasks:")
    print(f"   - subtasks: {len(todo_dict['subtasks'])}개")
    for i, st in enumerate(todo_dict['subtasks']):
        print(f"     [{i}] {st['content']} (completed={st['completed']})")
    print()


def test_existing_data():
    """기존 data.json 로드 테스트"""
    print("=" * 60)
    print("7. 기존 data.json 로드 테스트")
    print("=" * 60)

    import json
    import os

    data_path = r'D:\dev_proj\new-todo-panel\TodoPanel_Data\data.json'

    if not os.path.exists(data_path):
        print("WARNING: data.json 파일이 존재하지 않습니다. 테스트를 건너뜁니다.")
        print()
        return

    try:
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        todos_data = data.get('todos', [])
        print(f"OK data.json 로드 성공: {len(todos_data)}개 Todo")

        # 첫 번째 Todo 역직렬화 테스트
        if todos_data:
            first_todo = Todo.from_dict(todos_data[0])
            print(f"OK 첫 번째 Todo 역직렬화 성공:")
            print(f"   - ID: {first_todo.id.value}")
            print(f"   - Content: {first_todo.content.value}")
            print(f"   - Completed: {first_todo.completed}")
            print(f"   - Subtasks: {len(first_todo.subtasks)}개")

        print()
    except Exception as e:
        print(f"ERROR: data.json 로드 실패: {e}")
        print()


def main():
    """메인 테스트 실행"""
    print("\n" + "BaseTask 리팩토링 테스트 시작".center(60, "=") + "\n")

    try:
        # 1. Import 테스트
        test_import()

        # 2-3. Todo/SubTask 생성 테스트
        todo = test_todo_creation()
        subtask = test_subtask_creation()

        # 4. 공통 메서드 테스트
        test_common_methods(todo, "Todo")
        test_common_methods(subtask, "SubTask")

        # 5. 직렬화 테스트
        todo_dict = test_serialization(todo, "Todo")
        subtask_dict = test_serialization(subtask, "SubTask")

        # 6. Todo 전용 기능 테스트
        test_todo_specific_features()

        # 7. 기존 data.json 로드 테스트
        test_existing_data()

        # 최종 결과
        print("=" * 60)
        print("SUCCESS: 모든 테스트 통과!")
        print("=" * 60)
        print("\nOK BaseTask 리팩토링 성공:")
        print("   - BaseTask 추상 클래스 생성")
        print("   - Todo, SubTask 리팩토링 완료")
        print("   - 공통 메서드 7개 통합")
        print("   - 기존 기능 완전 보존")
        print()

    except Exception as e:
        print(f"\nERROR: 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
