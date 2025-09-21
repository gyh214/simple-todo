#!/usr/bin/env python3
"""
즉시 저장 기능 테스트 스크립트
"""

import sys
import os
import json
import time
from pathlib import Path

def test_current_settings():
    """현재 저장된 설정 확인"""
    print("=" * 60)
    print("현재 저장된 설정 확인")
    print("=" * 60)

    config_file = Path(os.path.expanduser("~")) / "AppData" / "Local" / "TodoPanel" / "ui_settings.json"

    if not config_file.exists():
        print("❌ 설정 파일이 존재하지 않습니다.")
        return False

    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            settings = json.load(f)

        print(f"📁 설정 파일: {config_file}")
        print(f"📊 파일 크기: {config_file.stat().st_size} bytes")
        print("\n📋 현재 설정:")
        print(json.dumps(settings, indent=2, ensure_ascii=False))

        # 중요 설정 확인
        has_sort_settings = 'sort_settings' in settings
        has_pane_ratio = 'paned_window_ratio' in settings

        print(f"\n✅ 검증 결과:")
        print(f"   정렬 설정: {'저장됨' if has_sort_settings else '누락'}")
        print(f"   UI 크기:   {'저장됨' if has_pane_ratio else '누락'}")

        if has_sort_settings:
            sort_settings = settings['sort_settings']
            criteria = sort_settings.get('sort_criteria', 'N/A')
            direction = sort_settings.get('sort_direction', 'N/A')
            print(f"   정렬 모드: {criteria} {direction}")

            # 수동 모드 테스트
            if criteria == 'manual':
                print("🎯 수동 모드 저장 확인됨!")
            elif criteria == 'due_date':
                print("📅 납기일 정렬 모드")
            elif criteria == 'created_date':
                print("📝 생성일 정렬 모드")

        return has_sort_settings and has_pane_ratio

    except Exception as e:
        print(f"❌ 설정 파일 읽기 오류: {e}")
        return False

def test_sort_manager_functions():
    """SortManager 기능 테스트"""
    print("\n" + "=" * 60)
    print("SortManager 기능 테스트")
    print("=" * 60)

    try:
        # 프로젝트 경로 추가
        sys.path.append(str(Path(__file__).parent / "src"))

        from ui.sort_manager import SortManager, SortCriteria, SortDirection

        # 새로운 SortManager 생성
        sort_manager = SortManager()
        print(f"✅ SortManager 생성 성공")
        print(f"   기본 정렬: {sort_manager.current_criteria.value} {sort_manager.current_direction.value}")

        # 설정 저장 테스트
        settings = {}
        success = sort_manager.save_settings(settings)
        print(f"✅ 설정 저장 테스트: {'성공' if success else '실패'}")

        if success:
            sort_settings = settings.get('sort_settings', {})
            print(f"   저장된 설정: {json.dumps(sort_settings, ensure_ascii=False)}")

        # 수동 모드 전환 테스트
        sort_manager.set_manual_mode()
        print(f"✅ 수동 모드 전환: {sort_manager.current_criteria.value}")

        # 수동 모드 설정 저장 테스트
        manual_settings = {}
        success = sort_manager.save_settings(manual_settings)
        print(f"✅ 수동 모드 저장 테스트: {'성공' if success else '실패'}")

        if success:
            manual_sort_settings = manual_settings.get('sort_settings', {})
            print(f"   수동 모드 설정: {json.dumps(manual_sort_settings, ensure_ascii=False)}")

            if manual_sort_settings.get('sort_criteria') == 'manual':
                print("🎯 수동 모드 저장 확인!")
                return True

        return False

    except Exception as e:
        print(f"❌ SortManager 테스트 실패: {e}")
        import traceback
        print(f"   스택 트레이스: {traceback.format_exc()}")
        return False

def main():
    """메인 테스트 실행"""
    print("TODO Panel 즉시 저장 기능 테스트")
    print("현재 시간:", time.strftime('%Y-%m-%d %H:%M:%S'))

    results = []

    # 1. 현재 설정 확인
    results.append(test_current_settings())

    # 2. SortManager 기능 테스트
    results.append(test_sort_manager_functions())

    # 결과 출력
    print("\n" + "=" * 60)
    print("테스트 결과 요약")
    print("=" * 60)
    print(f"현재 설정 확인: {'통과' if results[0] else '실패'}")
    print(f"SortManager 테스트: {'통과' if results[1] else '실패'}")

    overall_success = all(results)
    print(f"\n전체 테스트: {'통과' if overall_success else '실패'}")

    if overall_success:
        print("\n🎉 모든 테스트가 통과했습니다!")
        print("   - 정렬 설정 저장/로드 기능 정상 작동")
        print("   - 수동 모드 저장 기능 정상 작동")
        print("   - UI 섹션 크기 저장 기능 정상 작동")
    else:
        print("\n❌ 일부 테스트가 실패했습니다.")

    return overall_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)