#!/usr/bin/env python3
"""
분할바 비율 로드 테스트 스크립트
기존 코드 재사용으로 문제점 파악
"""

import sys
import os
import json
from pathlib import Path

# 프로젝트 경로 추가
sys.path.append(str(Path(__file__).parent / "src"))

def test_config_file_path():
    """설정 파일 경로 계산 테스트 (기존 로직 재사용)"""
    # TodoManager와 동일한 로직 사용
    import platform

    if platform.system() == "Windows":
        base_path = Path(os.path.expanduser("~")) / "AppData" / "Local" / "TodoPanel"
    else:
        base_path = Path(os.path.expanduser("~")) / ".config" / "TodoPanel"

    # 현재 실행 경로 기준 (빌드된 exe의 경우)
    current_dir = Path(__file__).parent
    if (current_dir / "TodoPanel_Data").exists():
        base_path = current_dir / "TodoPanel_Data"

    config_file = base_path / "ui_settings.json"
    print(f"[DEBUG] 계산된 설정 파일 경로: {config_file}")
    print(f"[DEBUG] 설정 파일 존재 여부: {config_file.exists()}")

    return config_file

def test_load_pane_ratio():
    """분할 비율 로드 테스트 (기존 함수 로직 재사용)"""
    try:
        config_file = test_config_file_path()

        if not config_file.exists():
            print(f"[DEBUG] 설정 파일 없음, 기본값 0.8 사용")
            return 0.8

        with open(config_file, 'r', encoding='utf-8') as f:
            settings = json.load(f)

        print(f"[DEBUG] 로드된 설정: {settings}")
        ratio = settings.get('paned_window_ratio', 0.8)
        print(f"[DEBUG] 원본 비율값: {ratio}")

        # 유효한 범위인지 검증 (0.1 ~ 0.9)
        ratio = max(0.1, min(0.9, ratio))
        print(f"[DEBUG] 검증된 비율값: {ratio}")

        return ratio

    except Exception as e:
        print(f"[DEBUG] 분할 비율 로드 실패, 기본값 사용: {e}")
        return 0.8

if __name__ == "__main__":
    print("분할 비율 로드 테스트 시작")
    print("=" * 50)

    ratio = test_load_pane_ratio()

    print("=" * 50)
    print(f"최종 결과: {ratio}")

    # 추가 디버그: 다른 경로들도 확인
    print("\n추가 경로 확인:")
    src_data = Path(__file__).parent / "src" / "TodoPanel_Data" / "ui_settings.json"
    print(f"src 폴더 경로: {src_data} (존재: {src_data.exists()})")

    dist_data = Path(__file__).parent / "dist" / "TodoPanel_Data" / "ui_settings.json"
    print(f"dist 폴더 경로: {dist_data} (존재: {dist_data.exists()})")

    root_data = Path(__file__).parent / "TodoPanel_Data" / "ui_settings.json"
    print(f"root 폴더 경로: {root_data} (존재: {root_data.exists()})")