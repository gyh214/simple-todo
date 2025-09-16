#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DatePickerDialog 함수 단위 테스트
"""

import sys
import os
from pathlib import Path

# 프로젝트 root 경로를 Python path에 추가
project_root = Path(__file__).parent
src_path = project_root / 'src'
sys.path.insert(0, str(src_path))

try:
    import tkinter as tk
    from ui.main_app import DatePickerDialog
    print("[SUCCESS] 모듈 임포트 성공")
except ImportError as e:
    print(f"[ERROR] 모듈 임포트 실패: {e}")
    sys.exit(1)


def test_dialog_sizing():
    """DatePickerDialog 크기 계산 테스트"""
    print("\n=== 크기 계산 테스트 ===")

    # 가상의 부모 창 생성
    root = tk.Tk()
    root.withdraw()  # 창 숨기기

    try:
        # 다양한 텍스트 길이로 테스트
        test_cases = [
            ("", "빈 텍스트"),
            ("짧은 텍스트", "짧은 텍스트"),
            ("중간 길이의 텍스트로 다이얼로그 크기 테스트", "중간 길이 텍스트"),
            ("매우 긴 텍스트를 가진 할일 항목으로 다이얼로그의 크기 조정과 위치 계산이 제대로 작동하는지 확인하는 매우 긴 테스트 텍스트입니다", "매우 긴 텍스트")
        ]

        for text, description in test_cases:
            # DatePickerDialog 인스턴스 생성 (실제 표시는 안함)
            dialog = DatePickerDialog.__new__(DatePickerDialog)
            dialog.parent = root
            dialog.todo_text = text

            # 크기 계산 함수 테스트
            width, height = dialog._get_optimal_size()
            print(f"[INFO] {description}: {width}x{height}")

            # 기본 검증
            assert 320 <= width <= 800, f"너비가 범위를 벗어남: {width}"
            assert 350 <= height <= 600, f"높이가 범위를 벗어남: {height}"

        print("[SUCCESS] 크기 계산 테스트 통과")

    except Exception as e:
        print(f"[ERROR] 크기 계산 테스트 실패: {e}")
        raise
    finally:
        root.destroy()


def test_position_calculation():
    """DatePickerDialog 위치 계산 테스트"""
    print("\n=== 위치 계산 테스트 ===")

    root = tk.Tk()
    root.withdraw()

    try:
        # 화면 크기 확인
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        print(f"[INFO] 화면 크기: {screen_width}x{screen_height}")

        # DatePickerDialog 인스턴스 생성
        dialog = DatePickerDialog.__new__(DatePickerDialog)
        dialog.parent = root
        dialog.todo_text = "테스트"

        # 다양한 다이얼로그 크기로 위치 테스트
        test_sizes = [
            (350, 400),  # 기본 크기
            (450, 500),  # 큰 크기
            (320, 350),  # 최소 크기
        ]

        for width, height in test_sizes:
            x, y = dialog._calculate_safe_position(width, height)
            print(f"[INFO] 크기 {width}x{height} -> 위치 ({x}, {y})")

            # 위치가 화면 범위 내에 있는지 검증
            assert 0 <= x <= screen_width - width, f"X 위치가 화면을 벗어남: {x}"
            assert 0 <= y <= screen_height - height, f"Y 위치가 화면을 벗어남: {y}"

            # 마진이 제대로 적용되었는지 검증
            margin = 20
            assert x >= margin or x == 0, f"왼쪽 마진 부족: {x}"
            assert y >= margin or y == 0, f"위쪽 마진 부족: {y}"

        print("[SUCCESS] 위치 계산 테스트 통과")

    except Exception as e:
        print(f"[ERROR] 위치 계산 테스트 실패: {e}")
        raise
    finally:
        root.destroy()


def test_edge_cases():
    """극단적인 경우 테스트"""
    print("\n=== 극단 케이스 테스트 ===")

    root = tk.Tk()
    root.withdraw()

    try:
        dialog = DatePickerDialog.__new__(DatePickerDialog)
        dialog.parent = root

        # 매우 긴 텍스트
        very_long_text = "A" * 500
        dialog.todo_text = very_long_text

        width, height = dialog._get_optimal_size()
        print(f"[INFO] 매우 긴 텍스트 크기: {width}x{height}")

        # 화면 크기의 80%를 넘지 않아야 함
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        max_width = int(screen_width * 0.8)
        max_height = int(screen_height * 0.8)

        assert width <= max_width, f"최대 너비 초과: {width} > {max_width}"
        assert height <= max_height, f"최대 높이 초과: {height} > {max_height}"

        # 위치 계산도 테스트
        x, y = dialog._calculate_safe_position(width, height)
        assert 0 <= x < screen_width, f"X 위치 범위 초과: {x}"
        assert 0 <= y < screen_height, f"Y 위치 범위 초과: {y}"

        print("[SUCCESS] 극단 케이스 테스트 통과")

    except Exception as e:
        print(f"[ERROR] 극단 케이스 테스트 실패: {e}")
        raise
    finally:
        root.destroy()


def main():
    """메인 테스트 실행"""
    print("DatePickerDialog 함수 단위 테스트 시작")
    print("=" * 50)

    try:
        test_dialog_sizing()
        test_position_calculation()
        test_edge_cases()

        print("\n" + "=" * 50)
        print("[SUCCESS] 모든 테스트 통과!")
        print("DatePickerDialog 개선이 성공적으로 완료되었습니다.")

    except Exception as e:
        print(f"\n[ERROR] 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())