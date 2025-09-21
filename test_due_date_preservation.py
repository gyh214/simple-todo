#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
납기일 누락 문제 해결 테스트 스크립트

이 스크립트는 TodoManager의 수정된 로직을 테스트하여
편집 시 납기일이 올바르게 보존되는지 검증합니다.
"""

import sys
import os
from datetime import datetime

# src 디렉토리를 path에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from todo_manager import TodoManager
    print("[SUCCESS] TodoManager import success")
except ImportError as e:
    print(f"[ERROR] TodoManager import failed: {e}")
    sys.exit(1)

def test_due_date_preservation():
    """납기일 보존 테스트"""
    print("\n🧪 납기일 보존 테스트 시작")
    print("=" * 50)

    # TodoManager 초기화 (기존 데이터 사용)
    manager = TodoManager(debug=True)

    # 테스트용 TODO ID
    test_id = "test-todo-with-due-date-001"

    print(f"\n📋 테스트 대상 TODO ID: {test_id}")

    # 수정 전 상태 확인
    todos = manager.read_todos()
    test_todo_before = None

    for todo in todos:
        if todo['id'] == test_id:
            test_todo_before = todo
            break

    if not test_todo_before:
        print(f"❌ 테스트 TODO를 찾을 수 없습니다: {test_id}")
        return False

    print(f"\n📊 편집 전 상태:")
    print(f"   텍스트: {test_todo_before.get('text', 'N/A')}")
    print(f"   납기일: {test_todo_before.get('due_date', 'N/A')}")
    print(f"   완료상태: {test_todo_before.get('completed', 'N/A')}")

    original_due_date = test_todo_before.get('due_date')
    if not original_due_date:
        print("❌ 테스트 TODO에 납기일이 없습니다!")
        return False

    print(f"✅ 원본 납기일 확인: {original_due_date}")

    # 🔥 핵심 테스트: 편집 시 납기일 보존되는지 확인
    print(f"\n🔧 텍스트 편집 테스트 (due_date 파라미터 없이 업데이트)")
    new_text = f"🧪 테스트: 편집 완료! (수정시각: {datetime.now().strftime('%H:%M:%S')})"

    # UI에서 호출하는 방식과 동일하게 텍스트만 업데이트
    # (기존 문제: due_date가 명시되지 않아 누락될 가능성)
    success = manager.update_todo(test_id, text=new_text)

    if not success:
        print("❌ TODO 업데이트 실패!")
        return False

    print("✅ TODO 업데이트 성공")

    # 수정 후 상태 확인
    todos_after = manager.read_todos()
    test_todo_after = None

    for todo in todos_after:
        if todo['id'] == test_id:
            test_todo_after = todo
            break

    if not test_todo_after:
        print("❌ 수정 후 TODO를 찾을 수 없습니다!")
        return False

    print(f"\n📊 편집 후 상태:")
    print(f"   텍스트: {test_todo_after.get('text', 'N/A')}")
    print(f"   납기일: {test_todo_after.get('due_date', 'N/A')}")
    print(f"   완료상태: {test_todo_after.get('completed', 'N/A')}")

    # 🎯 핵심 검증: 납기일이 보존되었는가?
    after_due_date = test_todo_after.get('due_date')

    print(f"\n🔍 납기일 보존 검증:")
    print(f"   수정 전: {original_due_date}")
    print(f"   수정 후: {after_due_date}")

    if original_due_date == after_due_date:
        print("🎉 성공! 편집 시 납기일이 완벽하게 보존되었습니다!")
        return True
    else:
        print("❌ 실패! 편집 시 납기일이 누락되었습니다!")
        return False

def test_multiple_edits():
    """여러 번 편집 테스트"""
    print("\n🔄 연속 편집 테스트")
    print("=" * 30)

    manager = TodoManager(debug=True)
    test_id = "test-todo-with-due-date-001"

    # 원본 납기일 확인
    todos = manager.read_todos()
    original_due_date = None
    for todo in todos:
        if todo['id'] == test_id:
            original_due_date = todo.get('due_date')
            break

    if not original_due_date:
        print("❌ 원본 납기일을 찾을 수 없습니다!")
        return False

    print(f"📅 원본 납기일: {original_due_date}")

    # 3번 연속 편집
    for i in range(1, 4):
        new_text = f"🧪 연속편집 {i}차: 납기일 보존 테스트 ({datetime.now().strftime('%H:%M:%S')})"
        success = manager.update_todo(test_id, text=new_text)

        if not success:
            print(f"❌ {i}차 편집 실패!")
            return False

        # 편집 후 납기일 확인
        todos = manager.read_todos()
        current_due_date = None
        for todo in todos:
            if todo['id'] == test_id:
                current_due_date = todo.get('due_date')
                break

        if current_due_date == original_due_date:
            print(f"✅ {i}차 편집 성공 - 납기일 보존됨")
        else:
            print(f"❌ {i}차 편집 실패 - 납기일 누락! (원본: {original_due_date}, 현재: {current_due_date})")
            return False

    print("🎉 연속 편집 테스트 모두 성공!")
    return True

if __name__ == "__main__":
    print("🚀 납기일 누락 문제 해결 검증 테스트")
    print("=" * 60)

    try:
        # 기본 편집 테스트
        result1 = test_due_date_preservation()

        # 연속 편집 테스트
        result2 = test_multiple_edits()

        print("\n" + "=" * 60)
        print("📊 최종 결과:")
        print(f"   기본 편집 테스트: {'✅ 성공' if result1 else '❌ 실패'}")
        print(f"   연속 편집 테스트: {'✅ 성공' if result2 else '❌ 실패'}")

        if result1 and result2:
            print("\n🎉 모든 테스트 성공! 납기일 누락 문제가 완전히 해결되었습니다!")
            print("💡 이제 사용자가 TODO를 편집해도 납기일이 안전하게 보존됩니다.")
        else:
            print("\n❌ 일부 테스트 실패! 추가 수정이 필요합니다.")

    except Exception as e:
        print(f"\n💥 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()