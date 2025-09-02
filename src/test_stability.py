"""
TODO Panel 안정성 테스트

프로그램이 멈추는 문제를 재현하고 해결을 검증하는 테스트 스크립트
"""

import sys
import os
import time
import threading
import random
from pathlib import Path

# 프로젝트 경로 추가
sys.path.insert(0, str(Path(__file__).parent))

from async_todo_manager import AsyncTodoManager, AsyncTodoManagerError
from todo_manager import TodoManager, TodoManagerError


def stress_test_todo_manager(manager_class, test_name, num_operations=100):
    """TODO 매니저 스트레스 테스트"""
    print(f"\n{'='*60}")
    print(f"{test_name} 시작")
    print(f"{'='*60}")
    
    manager = manager_class(debug=False)
    errors = []
    success_count = 0
    
    start_time = time.time()
    
    # 1. 대량 TODO 추가 테스트
    print(f"\n1. {num_operations}개의 TODO를 빠르게 추가...")
    created_ids = []
    
    for i in range(num_operations):
        try:
            todo = manager.create_todo(f"테스트 할일 #{i+1}")
            created_ids.append(todo['id'])
            success_count += 1
            
            # 진행상황 표시
            if (i + 1) % 10 == 0:
                print(f"  - {i+1}개 추가 완료", end='\r')
                
        except Exception as e:
            errors.append(f"추가 오류 #{i+1}: {e}")
    
    print(f"\n  [OK] {success_count}/{num_operations}개 추가 성공")
    
    # 2. 동시 읽기/쓰기 테스트
    print(f"\n2. 동시 읽기/쓰기 테스트...")
    concurrent_errors = []
    
    def concurrent_operations():
        """여러 스레드에서 동시에 작업 수행"""
        try:
            # 읽기
            todos = manager.read_todos()
            
            # 무작위 업데이트
            if todos and random.random() > 0.5:
                todo = random.choice(todos)
                manager.update_todo(todo['id'], completed=True)
            
            # 무작위 추가
            if random.random() > 0.5:
                manager.create_todo(f"동시성 테스트 {random.randint(1, 1000)}")
                
        except Exception as e:
            concurrent_errors.append(str(e))
    
    threads = []
    for _ in range(10):
        thread = threading.Thread(target=concurrent_operations)
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()
    
    if concurrent_errors:
        print(f"  ! 동시성 오류 {len(concurrent_errors)}건 발생")
        errors.extend(concurrent_errors)
    else:
        print(f"  [OK] 동시성 테스트 통과")
    
    # 3. 빠른 업데이트 테스트
    print(f"\n3. 빠른 업데이트 테스트...")
    update_errors = 0
    
    for i in range(min(20, len(created_ids))):
        try:
            manager.update_todo(created_ids[i], completed=True)
            manager.update_todo(created_ids[i], text=f"업데이트된 텍스트 {i}")
        except Exception as e:
            update_errors += 1
            errors.append(f"업데이트 오류: {e}")
    
    if update_errors == 0:
        print(f"  [OK] 모든 업데이트 성공")
    else:
        print(f"  ! {update_errors}개 업데이트 실패")
    
    # 4. 삭제 테스트
    print(f"\n4. 삭제 테스트...")
    delete_count = min(10, len(created_ids))
    
    for i in range(delete_count):
        try:
            manager.delete_todo(created_ids[i])
        except Exception as e:
            errors.append(f"삭제 오류: {e}")
    
    print(f"  [OK] {delete_count}개 삭제 완료")
    
    # 5. 통계 확인
    print(f"\n5. 최종 통계...")
    try:
        stats = manager.get_stats()
        print(f"  - 전체: {stats['total']}")
        print(f"  - 완료: {stats['completed']}")
        print(f"  - 대기: {stats['pending']}")
    except Exception as e:
        errors.append(f"통계 오류: {e}")
    
    # AsyncTodoManager의 경우 종료 처리
    if hasattr(manager, 'shutdown'):
        print(f"\n6. 매니저 종료...")
        manager.shutdown()
        print(f"  [OK] 정상 종료")
    
    elapsed_time = time.time() - start_time
    
    # 결과 요약
    print(f"\n{'='*60}")
    print(f"테스트 결과 요약")
    print(f"{'='*60}")
    print(f"소요 시간: {elapsed_time:.2f}초")
    print(f"성공한 작업: {success_count}")
    print(f"발생한 오류: {len(errors)}개")
    
    if errors:
        print(f"\n오류 상세 (최대 5개):")
        for error in errors[:5]:
            print(f"  - {error}")
    
    return len(errors) == 0


def test_deadlock_scenario():
    """데드락 시나리오 테스트"""
    print(f"\n{'='*60}")
    print("데드락 시나리오 테스트")
    print(f"{'='*60}")
    
    # 기본 TodoManager로 테스트
    print("\n기본 TodoManager 테스트...")
    manager = TodoManager(debug=False)
    
    try:
        # 중첩된 lock 호출 시뮬레이션
        todo = manager.create_todo("데드락 테스트")
        
        # 여러 스레드에서 동시에 접근
        def access_manager():
            for _ in range(10):
                manager.create_todo(f"스레드 테스트 {threading.current_thread().name}")
                time.sleep(0.01)
        
        threads = []
        for i in range(5):
            thread = threading.Thread(target=access_manager, name=f"Thread-{i}")
            threads.append(thread)
            thread.start()
        
        # 타임아웃 설정하여 데드락 감지
        for thread in threads:
            thread.join(timeout=5.0)
            if thread.is_alive():
                print(f"  ! 데드락 감지: {thread.name}이 응답하지 않음")
                return False
        
        print("  [OK] 데드락 없음")
        return True
        
    except Exception as e:
        print(f"  ! 오류 발생: {e}")
        return False


def test_ui_responsiveness():
    """UI 응답성 테스트 (시뮬레이션)"""
    print(f"\n{'='*60}")
    print("UI 응답성 테스트")
    print(f"{'='*60}")
    
    # AsyncTodoManager 사용
    manager = AsyncTodoManager(debug=False, batch_save=True)
    
    print("\n연속적인 TODO 추가 중 응답 시간 측정...")
    response_times = []
    
    for i in range(20):
        start = time.time()
        
        # TODO 추가 (UI에서 버튼 클릭 시뮬레이션)
        todo = manager.create_todo(f"UI 테스트 {i+1}")
        
        # 응답 시간 측정
        response_time = (time.time() - start) * 1000  # ms
        response_times.append(response_time)
        
        print(f"  TODO #{i+1}: {response_time:.1f}ms", end='\r')
        
        # 실제 UI처럼 약간의 지연
        time.sleep(0.05)
    
    avg_response = sum(response_times) / len(response_times)
    max_response = max(response_times)
    
    print(f"\n\n결과:")
    print(f"  - 평균 응답 시간: {avg_response:.1f}ms")
    print(f"  - 최대 응답 시간: {max_response:.1f}ms")
    
    if avg_response < 50 and max_response < 200:
        print(f"  [OK] UI 응답성 양호")
        result = True
    else:
        print(f"  ! UI 응답성 개선 필요")
        result = False
    
    manager.shutdown()
    return result


def main():
    """메인 테스트 실행"""
    print("=" * 60)
    print("TODO Panel 안정성 테스트 시작")
    print("=" * 60)
    
    all_passed = True
    
    # 1. 기본 TodoManager 테스트
    if not stress_test_todo_manager(TodoManager, "기본 TodoManager 스트레스 테스트", 50):
        all_passed = False
    
    time.sleep(1)
    
    # 2. AsyncTodoManager 테스트
    if not stress_test_todo_manager(AsyncTodoManager, "AsyncTodoManager 스트레스 테스트", 100):
        all_passed = False
    
    time.sleep(1)
    
    # 3. 데드락 시나리오 테스트
    if not test_deadlock_scenario():
        all_passed = False
    
    time.sleep(1)
    
    # 4. UI 응답성 테스트
    if not test_ui_responsiveness():
        all_passed = False
    
    # 최종 결과
    print(f"\n{'='*60}")
    print("최종 테스트 결과")
    print(f"{'='*60}")
    
    if all_passed:
        print("[PASS] 모든 테스트 통과! 프로그램 안정성이 개선되었습니다.")
    else:
        print("[FAIL] 일부 테스트 실패. 추가 개선이 필요합니다.")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())