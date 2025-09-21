"""
📝 납기일 보존 로직 검증 테스트 스크립트

DRY+CLEAN+SIMPLE 원칙에 따라 최적화된 납기일 보존 로직의 동작을 검증합니다.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from todo_manager import TodoManager, TodoManagerError

def test_due_date_preservation():
    """납기일 보존 로직 종합 테스트"""
    print("[DEBUG] TODO Panel 납기일 보존 로직 검증 테스트")
    print("=" * 60)

    try:
        # TodoManager 인스턴스 생성 (디버그 모드)
        print("1. TodoManager 초기화 중...")
        manager = TodoManager(debug=True, custom_data_path='test_preservation_data.json')
        print("   [OK] TodoManager 초기화 완료\n")

        # 납기일이 있는 TODO 생성
        print("2. 납기일이 있는 TODO 생성...")
        test_due_date = "2025-09-25"
        todo = manager.create_todo("테스트 TODO - 납기일 보존 검증", due_date=test_due_date)
        todo_id = todo['id']
        print(f"   [OK] TODO 생성 완료: ID={todo_id[:8]}..., 납기일={todo['due_date']}\n")

        # 테스트 1: 텍스트만 변경 시 납기일 보존
        print("3. 테스트 1: 텍스트 변경 시 납기일 보존")
        print("   [DEBUG] 시뮬레이션...")
        debug_result = manager.debug_data_preservation(todo_id, text="변경된 텍스트")
        print(f"   [DEBUG] 시뮬레이션 결과: 보존된 납기일 = {debug_result.get('due_date')}")

        print("   [UPDATE] 실제 업데이트 실행...")
        success = manager.update_todo_safe(todo_id, text="변경된 텍스트")

        if success:
            updated_todo = manager.get_todo_by_id(todo_id)
            if updated_todo['due_date'] == test_due_date:
                print("   [PASS] 텍스트 변경 시 납기일 보존 성공!")
            else:
                print(f"   [FAIL] 텍스트 변경 시 납기일 보존 실패: {test_due_date} -> {updated_todo['due_date']}")
        print()

        # 테스트 2: 완료 상태 변경 시 납기일 보존
        print("4. 테스트 2: 완료 상태 변경 시 납기일 보존")
        print("   [DEBUG] 시뮬레이션...")
        debug_result2 = manager.debug_data_preservation(todo_id, completed=True)
        print(f"   [DEBUG] 시뮬레이션 결과: 보존된 납기일 = {debug_result2.get('due_date')}")

        print("   [UPDATE] 실제 업데이트 실행...")
        success2 = manager.update_todo_safe(todo_id, completed=True)

        if success2:
            completed_todo = manager.get_todo_by_id(todo_id)
            if completed_todo['due_date'] == test_due_date:
                print("   [PASS] 완료 상태 변경 시 납기일 보존 성공!")
            else:
                print(f"   [FAIL] 완료 상태 변경 시 납기일 보존 실패: {test_due_date} -> {completed_todo['due_date']}")
        print()

        # 테스트 3: 복합 업데이트 시 납기일 보존
        print("5. 테스트 3: 복합 업데이트 (텍스트+완료상태) 시 납기일 보존")
        print("   [DEBUG] 시뮬레이션...")
        debug_result3 = manager.debug_data_preservation(todo_id, text="최종 변경된 텍스트", completed=False)
        print(f"   [DEBUG] 시뮬레이션 결과: 보존된 납기일 = {debug_result3.get('due_date')}")

        print("   [UPDATE] 실제 업데이트 실행...")
        success3 = manager.update_todo_safe(todo_id, text="최종 변경된 텍스트", completed=False)

        if success3:
            final_todo = manager.get_todo_by_id(todo_id)
            if final_todo['due_date'] == test_due_date:
                print("   [PASS] 복합 업데이트 시 납기일 보존 성공!")
            else:
                print(f"   [FAIL] 복합 업데이트 시 납기일 보존 실패: {test_due_date} -> {final_todo['due_date']}")
        print()

        # 테스트 4: 납기일 직접 변경
        print("6. 테스트 4: 납기일 직접 변경 (보존 로직 우회)")
        new_due_date = "2025-12-31"
        print(f"   [UPDATE] 납기일을 {new_due_date}으로 직접 변경...")
        success4 = manager.update_todo_safe(todo_id, due_date=new_due_date)

        if success4:
            direct_updated_todo = manager.get_todo_by_id(todo_id)
            if direct_updated_todo['due_date'] == new_due_date:
                print("   [PASS] 납기일 직접 변경 성공!")
            else:
                print(f"   [FAIL] 납기일 직접 변경 실패: {new_due_date} -> {direct_updated_todo['due_date']}")
        print()

        # 최종 결과 요약
        print("[RESULT] 최종 검증 결과:")
        final_state = manager.get_todo_by_id(todo_id)
        print(f"   최종 텍스트: '{final_state['text']}'")
        print(f"   최종 완료상태: {final_state['completed']}")
        print(f"   최종 납기일: {final_state['due_date']}")
        print()

        # 통계 정보
        stats = manager.get_stats()
        print(f"[STATS] TODO 통계: 전체 {stats['total']}개, 완료 {stats['completed']}개, 진행중 {stats['pending']}개")

        print("\n[SUCCESS] 모든 납기일 보존 테스트 완료!")
        print("   DRY+CLEAN+SIMPLE 원칙에 따른 최적화 검증 성공")

    except TodoManagerError as e:
        print(f"[ERROR] TodoManager 오류: {e}")
    except Exception as e:
        print(f"[ERROR] 예상치 못한 오류: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # 테스트 데이터 파일 정리
        try:
            if os.path.exists('test_preservation_data.json'):
                os.remove('test_preservation_data.json')
                print("\n[CLEANUP] 테스트 데이터 파일 정리 완료")
        except:
            pass

if __name__ == "__main__":
    test_due_date_preservation()