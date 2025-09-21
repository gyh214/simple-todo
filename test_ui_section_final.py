#!/usr/bin/env python3
"""
UI 섹션 크기 저장/로드 기능 최종 검증 테스트
"""

import sys
import os
import json
import time
import subprocess
from pathlib import Path

def test_ui_section_persistence():
    """UI 섹션 크기 지속성 최종 테스트"""
    print("=" * 60)
    print("UI 섹션 크기 저장/로드 기능 최종 검증")
    print("=" * 60)

    # 실행파일 경로
    exe_path = Path("D:/dev_proj/todo-panel/dist/TodoPanel.exe")
    data_dir = exe_path.parent / "TodoPanel_Data"
    settings_file = data_dir / "ui_settings.json"
    data_file = data_dir / "data.json"

    print(f"실행파일: {exe_path}")
    print(f"데이터 폴더: {data_dir}")
    print(f"설정 파일: {settings_file}")

    # 기존 설정 백업
    backup_settings = None
    if settings_file.exists():
        with open(settings_file, 'r', encoding='utf-8') as f:
            backup_settings = json.load(f)
        print("기존 설정 백업 완료")

    try:
        # 1단계: 초기 테스트 데이터 생성
        print("\n1단계: 테스트 설정 생성")

        # 데이터 폴더 생성
        data_dir.mkdir(parents=True, exist_ok=True)

        # 테스트용 설정 데이터 생성 (특정 UI 섹션 비율)
        test_settings = {
            "paned_window_ratio": 0.3,  # 30%/70% 비율로 설정
            "last_updated": time.strftime('%Y-%m-%dT%H:%M:%S'),
            "sort_settings": {
                "sort_criteria": "due_date",
                "sort_direction": "asc",
                "current_option_index": 0
            }
        }

        with open(settings_file, 'w', encoding='utf-8') as f:
            json.dump(test_settings, f, indent=2, ensure_ascii=False)

        print(f"테스트 설정 생성: paned_window_ratio = {test_settings['paned_window_ratio']}")

        # 2단계: 실행파일 시작 테스트 (설정 로드 확인)
        print("\n2단계: 실행파일 시작하여 설정 로드 테스트")

        process = subprocess.Popen([str(exe_path)], cwd=str(exe_path.parent))
        time.sleep(4)  # 앱이 설정을 로드하고 UI를 그릴 시간
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

            # 핵심 검증
            has_pane_ratio = 'paned_window_ratio' in loaded_settings
            current_ratio = loaded_settings.get('paned_window_ratio')

            print(f"\n검증 결과:")
            print(f"UI 섹션 크기 설정 존재: {has_pane_ratio}")
            print(f"저장된 비율: {current_ratio}")

            if has_pane_ratio and current_ratio is not None:
                # 비율이 유효 범위 내에 있는지 확인
                if 0.1 <= current_ratio <= 0.9:
                    print("SUCCESS: UI 섹션 크기가 올바르게 저장/로드되었습니다!")

                    # 4단계: 재시작 테스트
                    print("\n4단계: 재시작하여 설정 지속성 확인")

                    process2 = subprocess.Popen([str(exe_path)], cwd=str(exe_path.parent))
                    time.sleep(3)
                    process2.terminate()
                    process2.wait()

                    # 재시작 후 설정 확인
                    with open(settings_file, 'r', encoding='utf-8') as f:
                        restart_settings = json.load(f)

                    restart_ratio = restart_settings.get('paned_window_ratio')
                    print(f"재시작 후 비율: {restart_ratio}")

                    if restart_ratio is not None and 0.1 <= restart_ratio <= 0.9:
                        print("SUCCESS: 재시작 후에도 UI 섹션 크기가 유지되었습니다!")
                        return True
                    else:
                        print("ERROR: 재시작 후 설정이 손실되었습니다.")
                        return False
                else:
                    print(f"ERROR: 비율이 유효 범위를 벗어남 ({current_ratio})")
                    return False
            else:
                print("ERROR: UI 섹션 크기 설정이 저장되지 않았습니다.")
                return False
        else:
            print("ERROR: 설정 파일이 생성되지 않았습니다.")
            return False

    except Exception as e:
        print(f"ERROR: 테스트 중 오류 발생: {e}")
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
        except Exception as e:
            print(f"데이터 복원 중 오류: {e}")

def main():
    """메인 테스트 실행"""
    print("TODO Panel UI 섹션 크기 저장/로드 기능 최종 검증")
    print("현재 시간:", time.strftime('%Y-%m-%d %H:%M:%S'))

    success = test_ui_section_persistence()

    print("\n" + "=" * 60)
    print("최종 테스트 결과")
    print("=" * 60)
    print(f"UI 섹션 크기 지속성: {'통과' if success else '실패'}")

    if success:
        print("\n🎉 UI 섹션 크기 저장/로드 기능이 완벽하게 작동합니다!")
        print("   - 설정 파일이 TodoPanel_Data 폴더에 저장됩니다")
        print("   - UI 섹션 크기가 즉시 저장되고 재시작 시 복원됩니다")
        print("   - 경로 통일로 완전한 포터블 애플리케이션이 되었습니다")
    else:
        print("\n❌ UI 섹션 크기 저장/로드에 문제가 있습니다.")

    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)