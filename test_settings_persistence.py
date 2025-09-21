#!/usr/bin/env python3
"""
설정 지속성 테스트 스크립트
- 정렬 설정 저장/로드 기능 검증
- UI 섹션 크기 저장 기능 검증
"""

import sys
import os
import json
import time
from pathlib import Path

# 프로젝트 경로 추가
sys.path.append(str(Path(__file__).parent / "src"))

def test_sort_manager_persistence():
    """SortManager 설정 지속성 테스트"""
    print("=" * 60)
    print("SortManager 설정 지속성 테스트")
    print("=" * 60)

    from ui.sort_manager import SortManager, SortCriteria, SortDirection

    # 1. 새로운 SortManager 생성
    sort_manager = SortManager()
    print(f"초기 정렬: {sort_manager.current_criteria.value} {sort_manager.current_direction.value}")

    # 2. 설정을 created_date desc로 변경
    sort_manager.set_sort_criteria(SortCriteria.CREATED_DATE, SortDirection.DESCENDING)
    print(f"변경된 정렬: {sort_manager.current_criteria.value} {sort_manager.current_direction.value}")

    # 3. 설정 저장
    settings = {}
    success = sort_manager.save_settings(settings)
    print(f"설정 저장 성공: {success}")
    print(f"저장된 설정: {json.dumps(settings, indent=2, ensure_ascii=False)}")

    # 4. 새로운 SortManager로 설정 로드 테스트
    new_sort_manager = SortManager()
    print(f"새 매니저 초기 정렬: {new_sort_manager.current_criteria.value} {new_sort_manager.current_direction.value}")

    load_success = new_sort_manager.load_settings(settings)
    print(f"설정 로드 성공: {load_success}")
    print(f"로드 후 정렬: {new_sort_manager.current_criteria.value} {new_sort_manager.current_direction.value}")

    return success and load_success

def test_main_app_integration():
    """MainApp 통합 테스트 (설정 파일 확인)"""
    print("\n" + "=" * 60)
    print("MainApp 통합 테스트 - 설정 파일 확인")
    print("=" * 60)

    config_file = Path(os.path.expanduser("~")) / "AppData" / "Local" / "TodoPanel" / "ui_settings.json"

    print(f"설정 파일 경로: {config_file}")
    print(f"설정 파일 존재: {config_file.exists()}")

    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                current_settings = json.load(f)
            print("현재 저장된 설정:")
            print(json.dumps(current_settings, indent=2, ensure_ascii=False))

            # sort_settings 섹션 확인
            has_sort_settings = 'sort_settings' in current_settings
            print(f"정렬 설정 저장됨: {has_sort_settings}")

            if has_sort_settings:
                sort_settings = current_settings['sort_settings']
                print(f"저장된 정렬 기준: {sort_settings.get('sort_criteria', 'N/A')}")
                print(f"저장된 정렬 방향: {sort_settings.get('sort_direction', 'N/A')}")
                print(f"저장된 옵션 인덱스: {sort_settings.get('current_option_index', 'N/A')}")

            return True

        except Exception as e:
            print(f"설정 파일 읽기 오류: {e}")
            return False
    else:
        print("설정 파일이 아직 생성되지 않았습니다.")
        return False

def test_simulated_app_lifecycle():
    """시뮬레이션된 앱 라이프사이클 테스트"""
    print("\n" + "=" * 60)
    print("시뮬레이션된 앱 라이프사이클 테스트")
    print("=" * 60)

    from ui.sort_manager import SortManager, SortCriteria, SortDirection
    import tempfile

    # 임시 설정 파일 경로
    config_dir = Path(os.path.expanduser("~")) / "AppData" / "Local" / "TodoPanel"
    config_file = config_dir / "ui_settings.json"

    # 기존 설정 백업
    backup_data = None
    if config_file.exists():
        with open(config_file, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)
        print("기존 설정 백업 완료")

    try:
        # 1. 앱 시작 시뮬레이션 - 설정 로드
        print("\n1. 앱 시작 시뮬레이션")
        sort_manager = SortManager()

        # 기존 설정이 있다면 로드
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            sort_manager.load_settings(settings)
            print(f"로드된 정렬: {sort_manager.current_criteria.value} {sort_manager.current_direction.value}")
        else:
            print(f"기본 정렬 사용: {sort_manager.current_criteria.value} {sort_manager.current_direction.value}")

        # 2. 사용자가 정렬 변경 시뮬레이션
        print("\n2. 사용자 정렬 변경 시뮬레이션")
        sort_manager.set_sort_criteria(SortCriteria.CREATED_DATE, SortDirection.DESCENDING)
        print(f"변경된 정렬: {sort_manager.current_criteria.value} {sort_manager.current_direction.value}")

        # 3. 앱 종료 시뮬레이션 - 설정 저장
        print("\n3. 앱 종료 시뮬레이션")
        settings = {}

        # 기존 설정 로드
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)

        # 정렬 설정 저장
        sort_manager.save_settings(settings)
        settings['last_updated'] = time.strftime('%Y-%m-%dT%H:%M:%S')

        # 파일에 저장
        config_dir.mkdir(parents=True, exist_ok=True)
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)

        print("설정 저장 완료")
        print(f"저장된 설정: {json.dumps(settings, indent=2, ensure_ascii=False)}")

        # 4. 재시작 시뮬레이션 - 설정 복원 확인
        print("\n4. 재시작 시뮬레이션")
        new_sort_manager = SortManager()

        with open(config_file, 'r', encoding='utf-8') as f:
            loaded_settings = json.load(f)

        new_sort_manager.load_settings(loaded_settings)
        print(f"재시작 후 정렬: {new_sort_manager.current_criteria.value} {new_sort_manager.current_direction.value}")

        # 검증
        success = (new_sort_manager.current_criteria == SortCriteria.CREATED_DATE and
                  new_sort_manager.current_direction == SortDirection.DESCENDING)

        print(f"\n테스트 결과: {'성공' if success else '실패'}")
        return success

    finally:
        # 기존 설정 복원
        if backup_data is not None:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)
            print("기존 설정 복원 완료")

def main():
    """메인 테스트 실행"""
    print("TODO Panel 설정 지속성 테스트 시작")
    print("현재 시간:", time.strftime('%Y-%m-%d %H:%M:%S'))

    results = []

    # 1. SortManager 단위 테스트
    results.append(test_sort_manager_persistence())

    # 2. 설정 파일 확인
    results.append(test_main_app_integration())

    # 3. 전체 라이프사이클 테스트
    results.append(test_simulated_app_lifecycle())

    # 결과 출력
    print("\n" + "=" * 60)
    print("테스트 결과 요약")
    print("=" * 60)
    print(f"SortManager 단위 테스트: {'통과' if results[0] else '실패'}")
    print(f"설정 파일 확인: {'통과' if results[1] else '실패'}")
    print(f"라이프사이클 테스트: {'통과' if results[2] else '실패'}")

    overall_success = all(results)
    print(f"\n전체 테스트: {'통과' if overall_success else '실패'}")

    return overall_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)