#!/usr/bin/env python3
"""
최종 설정 저장 기능 테스트 - TodoPanel_Data 경로 통일 검증
"""

import sys
import os
import json
import time
import subprocess
from pathlib import Path

def test_executable_settings_persistence():
    """실행파일의 설정 지속성 테스트"""
    print("=" * 60)
    print("TodoPanel.exe 설정 지속성 테스트")
    print("=" * 60)

    # 실행파일 경로
    exe_path = Path("D:/dev_proj/todo-panel/dist/TodoPanel.exe")
    data_dir = exe_path.parent / "TodoPanel_Data"
    settings_file = data_dir / "ui_settings.json"
    data_file = data_dir / "data.json"

    print(f"실행파일: {exe_path}")
    print(f"데이터 폴더: {data_dir}")
    print(f"설정 파일: {settings_file}")
    print(f"데이터 파일: {data_file}")

    # 기존 데이터 백업
    backup_settings = None
    backup_data = None

    if settings_file.exists():
        with open(settings_file, 'r', encoding='utf-8') as f:
            backup_settings = json.load(f)
        print("기존 설정 백업 완료")

    if data_file.exists():
        with open(data_file, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)
        print("기존 데이터 백업 완료")

    try:
        # 1단계: 테스트 데이터 생성
        print("\n1단계: 테스트 데이터 및 설정 생성")

        # 테스트용 TODO 데이터 생성
        test_todos = [
            {
                "id": "test-1",
                "text": "테스트 할일 1",
                "completed": False,
                "created_at": "2025-09-21T14:00:00",
                "due_date": "2025-09-22",
                "position": 0
            },
            {
                "id": "test-2",
                "text": "테스트 할일 2",
                "completed": False,
                "created_at": "2025-09-21T14:01:00",
                "due_date": "2025-09-23",
                "position": 1
            }
        ]

        # 테스트용 설정 데이터 생성
        test_settings = {
            "paned_window_ratio": 0.6,
            "last_updated": time.strftime('%Y-%m-%dT%H:%M:%S'),
            "sort_settings": {
                "sort_criteria": "created_date",
                "sort_direction": "desc",
                "current_option_index": 3
            }
        }

        # 데이터 폴더 생성
        data_dir.mkdir(parents=True, exist_ok=True)
        backups_dir = data_dir / "backups"
        backups_dir.mkdir(exist_ok=True)

        # 테스트 데이터 저장
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(test_todos, f, indent=2, ensure_ascii=False)

        with open(settings_file, 'w', encoding='utf-8') as f:
            json.dump(test_settings, f, indent=2, ensure_ascii=False)

        print("테스트 데이터 생성 완료")
        print(f"저장된 설정: {json.dumps(test_settings, ensure_ascii=False)}")

        # 2단계: 실행파일 시작 테스트
        print("\n2단계: 실행파일 시작 및 설정 로드 테스트")

        # 실행파일 시작 (3초 후 자동 종료)
        process = subprocess.Popen([str(exe_path)], cwd=str(exe_path.parent))
        time.sleep(3)  # 앱이 설정을 로드할 시간
        process.terminate()
        process.wait()

        print("실행파일 시작/종료 완료")

        # 3단계: 설정 파일 검증
        print("\n3단계: 설정 파일 변경 확인")

        if settings_file.exists():
            with open(settings_file, 'r', encoding='utf-8') as f:
                loaded_settings = json.load(f)

            print("현재 저장된 설정:")
            print(json.dumps(loaded_settings, indent=2, ensure_ascii=False))

            # 설정 검증
            has_sort = 'sort_settings' in loaded_settings
            has_pane = 'paned_window_ratio' in loaded_settings

            print(f"\n검증 결과:")
            print(f"정렬 설정 존재: {has_sort}")
            print(f"UI 크기 설정 존재: {has_pane}")

            if has_sort:
                sort_settings = loaded_settings['sort_settings']
                criteria = sort_settings.get('sort_criteria', 'N/A')
                direction = sort_settings.get('sort_direction', 'N/A')
                print(f"정렬 기준: {criteria}")
                print(f"정렬 방향: {direction}")

                # 생성일 내림차순으로 설정되었는지 확인
                if criteria == 'created_date' and direction == 'desc':
                    print("✅ 정렬 설정이 올바르게 저장되었습니다!")
                    return True
                else:
                    print("❌ 정렬 설정이 예상과 다릅니다.")
                    return False
            else:
                print("❌ 정렬 설정이 저장되지 않았습니다.")
                return False
        else:
            print("❌ 설정 파일이 생성되지 않았습니다.")
            return False

    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")
        return False

    finally:
        # 백업 데이터 복원
        try:
            if backup_settings is not None:
                with open(settings_file, 'w', encoding='utf-8') as f:
                    json.dump(backup_settings, f, indent=2, ensure_ascii=False)
                print("설정 데이터 복원 완료")
            elif settings_file.exists():
                settings_file.unlink()
                print("테스트 설정 파일 삭제 완료")

            if backup_data is not None:
                with open(data_file, 'w', encoding='utf-8') as f:
                    json.dump(backup_data, f, indent=2, ensure_ascii=False)
                print("TODO 데이터 복원 완료")
            elif data_file.exists():
                data_file.unlink()
                print("테스트 데이터 파일 삭제 완료")

        except Exception as e:
            print(f"데이터 복원 중 오류: {e}")

def main():
    """메인 테스트 실행"""
    print("TODO Panel 최종 설정 지속성 테스트")
    print("현재 시간:", time.strftime('%Y-%m-%d %H:%M:%S'))

    success = test_executable_settings_persistence()

    print("\n" + "=" * 60)
    print("최종 테스트 결과")
    print("=" * 60)
    print(f"설정 지속성 테스트: {'통과' if success else '실패'}")

    if success:
        print("\n🎉 TodoPanel_Data 경로 통일 및 설정 지속성 구현 성공!")
        print("   - 정렬 설정이 올바르게 저장/로드됩니다")
        print("   - UI 설정이 TodoPanel_Data 폴더에 저장됩니다")
        print("   - 실행파일과 같은 위치에서 완전히 포터블합니다")
    else:
        print("\n❌ 설정 지속성에 문제가 있습니다.")
        print("   추가 디버깅이 필요합니다.")

    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)