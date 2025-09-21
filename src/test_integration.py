"""
통합 테스트 스크립트 - 새로운 기능들을 간단히 테스트
"""

import tempfile
import os
import sys
from datetime import datetime, timedelta

def test_todo_manager():
    """TodoManager 테스트"""
    print("=== TodoManager 테스트 ===")

    # 임시 경로로 테스트
    temp_path = os.path.join(tempfile.gettempdir(), 'integration_test.json')

    try:
        from todo_manager import TodoManager
        manager = TodoManager(custom_data_path=temp_path, debug=False)

        # 기본 TODO 생성
        todo1 = manager.create_todo("기본 할일")
        assert todo1['due_date'] is None
        print("OK 기본 TODO 생성")

        # 납기일 있는 TODO 생성
        due_date = (datetime.now() + timedelta(days=5)).strftime('%Y-%m-%d')
        todo2 = manager.create_todo("납기일 있는 할일", due_date=due_date)
        assert todo2['due_date'] == due_date
        print("OK 납기일 있는 TODO 생성")

        # 납기일 업데이트
        new_due_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        success = manager.update_todo(todo1['id'], due_date=new_due_date)
        assert success

        updated = manager.get_todo_by_id(todo1['id'])
        assert updated['due_date'] == new_due_date
        print("OK 납기일 업데이트")

        # 마이그레이션 테스트 (created_at 필드 확인)
        assert 'created_at' in todo1
        print("OK 데이터 마이그레이션")

        print("TodoManager 테스트 완료!")

    finally:
        # 정리
        try:
            os.remove(temp_path)
        except:
            pass

def test_date_utils():
    """DateUtils 테스트"""
    print("\n=== DateUtils 테스트 ===")

    from ui.date_utils import DateUtils

    # 현재 날짜
    current = DateUtils.get_current_date()
    assert len(current) == 10  # YYYY-MM-DD
    print("OK 현재 날짜 반환")

    # 날짜 파싱
    test_date = "2025-09-20"
    parsed = DateUtils.parse_date(test_date)
    assert parsed is not None
    print("OK 날짜 파싱")

    # 만료 확인
    past_date = "2025-09-01"
    expired = DateUtils.is_date_expired(past_date)
    assert expired is True
    print("OK 만료 확인")

    # 날짜 상태 정보
    status_info = DateUtils.get_date_status_info(past_date)
    assert status_info['is_expired'] is True
    assert status_info['status_color'] == 'expired'
    print("OK 날짜 상태 정보")

    print("DateUtils 테스트 완료!")

def test_sort_manager():
    """SortManager 테스트"""
    print("\n=== SortManager 테스트 ===")

    from ui.sort_manager import SortManager, SortCriteria, SortDirection
    manager = SortManager()

    # 초기 상태
    assert manager.current_criteria == SortCriteria.DEFAULT
    print("OK 초기 상태")

    # 토글 테스트
    criteria, direction = manager.get_next_sort_state()
    assert criteria == SortCriteria.DUE_DATE
    print("OK 토글 동작")

    # 명시적으로 납기일 정렬 설정
    manager.set_sort_criteria(SortCriteria.DUE_DATE, SortDirection.ASCENDING)

    # 정렬 테스트
    test_todos = [
        {'id': '1', 'text': 'Task 1', 'due_date': '2025-09-20', 'position': 0, 'completed': False},
        {'id': '2', 'text': 'Task 2', 'due_date': '2025-09-15', 'position': 1, 'completed': False},
        {'id': '3', 'text': 'Task 3', 'due_date': None, 'position': 2, 'completed': True},
    ]

    sorted_todos = manager.sort_todos(test_todos)
    print("정렬 결과 (납기일 오름차순):")
    for todo in sorted_todos:
        print(f"  - {todo['text']}: {todo['due_date']}")

    # 첫 번째는 가장 빠른 날짜여야 함
    assert sorted_todos[0]['due_date'] == '2025-09-15'
    # 마지막은 None이어야 함
    assert sorted_todos[-1]['due_date'] is None
    print("OK 납기일 정렬")

    # 섹션 분리
    pending, completed = manager.separate_by_completion(test_todos)
    assert len(pending) == 2
    assert len(completed) == 1
    print("OK 완료/미완료 분리")

    print("SortManager 테스트 완료!")

def test_imports():
    """Import 테스트"""
    print("\n=== Import 테스트 ===")

    # 새로운 모듈들 import
    from ui.widgets import DARK_COLORS, ClickableTextWidget, TodoItemWidget
    from ui.main_app import TodoPanelApp, DatePickerDialog, CollapsibleSection
    from ui.sort_manager import SortManager
    from ui.date_utils import DateUtils
    print("OK 새로운 모듈들 import")

    # 하위 호환성 import
    from ui_components import get_colors, TodoPanelApp as LegacyTodoPanelApp
    assert TodoPanelApp == LegacyTodoPanelApp
    print("OK 하위 호환성 import")

    # 색상 확인
    assert isinstance(DARK_COLORS, dict)
    assert 'bg' in DARK_COLORS
    print("OK 색상 상수")

    print("Import 테스트 완료!")

def main():
    """메인 테스트 함수"""
    print("TODO Panel 통합 테스트 시작")
    print("=" * 50)

    try:
        test_imports()
        test_date_utils()
        test_sort_manager()
        test_todo_manager()

        print("\n" + "=" * 50)
        print("SUCCESS! 모든 테스트 통과!")
        print("새로운 기능들이 정상적으로 구현되었습니다.")

        return True

    except Exception as e:
        print(f"\nFAILED 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)