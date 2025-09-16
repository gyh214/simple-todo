#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DatePickerDialog 위치 및 크기 테스트 스크립트
"""

import sys
import os
import tkinter as tk
from pathlib import Path

# 프로젝트 root 경로를 Python path에 추가
project_root = Path(__file__).parent
src_path = project_root / 'src'
sys.path.insert(0, str(src_path))

try:
    from ui.main_app import DatePickerDialog, DARK_COLORS
    print("[SUCCESS] 모듈 임포트 성공")
except ImportError as e:
    print(f"[ERROR] 모듈 임포트 실패: {e}")
    sys.exit(1)


class DialogTestApp:
    """DatePickerDialog 테스트용 앱"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("DatePickerDialog 테스트")
        self.root.geometry("400x600")
        self.root.configure(bg=DARK_COLORS['bg'])

        self.setup_ui()

    def setup_ui(self):
        """테스트 UI 구성"""
        colors = DARK_COLORS

        # 제목
        title_label = tk.Label(self.root,
                              text="DatePickerDialog 위치 테스트",
                              font=('Segoe UI', 14, 'bold'),
                              bg=colors['bg'],
                              fg=colors['text'])
        title_label.pack(pady=20)

        # 설명
        desc_label = tk.Label(self.root,
                             text="다양한 위치에서 다이얼로그를 테스트하세요.",
                             font=('Segoe UI', 10),
                             bg=colors['bg'],
                             fg=colors['text_secondary'])
        desc_label.pack(pady=(0, 20))

        # 테스트 버튼들
        test_scenarios = [
            ("짧은 텍스트 테스트", "할일"),
            ("중간 길이 텍스트 테스트", "오늘 해야 할 중요한 업무를 처리하기"),
            ("긴 텍스트 테스트", "매우 긴 텍스트를 가진 할일 항목으로 다이얼로그의 크기 조정과 위치 계산이 제대로 작동하는지 확인하는 테스트입니다. 이 텍스트는 일부러 길게 만들어졌습니다."),
            ("빈 텍스트 테스트", ""),
        ]

        for title, text in test_scenarios:
            btn = tk.Button(self.root,
                           text=title,
                           font=('Segoe UI', 10),
                           bg=colors['button_bg'],
                           fg=colors['text'],
                           command=lambda t=text: self.test_dialog(t),
                           padx=20, pady=8)
            btn.pack(pady=5)

        # 위치 이동 버튼들
        position_frame = tk.Frame(self.root, bg=colors['bg'])
        position_frame.pack(pady=20)

        tk.Label(position_frame,
                text="창 위치 이동 테스트:",
                font=('Segoe UI', 11, 'bold'),
                bg=colors['bg'],
                fg=colors['text']).pack(pady=(0, 10))

        positions = [
            ("왼쪽 위", lambda: self.move_window(50, 50)),
            ("오른쪽 위", lambda: self.move_window_to_top_right()),
            ("왼쪽 아래", lambda: self.move_window_to_bottom_left()),
            ("오른쪽 아래", lambda: self.move_window_to_bottom_right()),
            ("화면 중앙", lambda: self.center_window()),
        ]

        for text, command in positions:
            btn = tk.Button(position_frame,
                           text=text,
                           font=('Segoe UI', 9),
                           bg=colors['accent'],
                           fg='white',
                           command=command,
                           padx=15, pady=5)
            btn.pack(side=tk.LEFT, padx=2)

    def test_dialog(self, todo_text):
        """DatePickerDialog 테스트 실행"""
        try:
            dialog = DatePickerDialog(self.root, todo_text)
            self.root.wait_window(dialog.dialog)
            print(f"[SUCCESS] 다이얼로그 테스트 완료: '{todo_text[:30]}...' | 결과: {dialog.result}")
        except Exception as e:
            print(f"[ERROR] 다이얼로그 테스트 실패: {e}")

    def move_window(self, x, y):
        """창을 지정된 위치로 이동"""
        self.root.geometry(f"400x600+{x}+{y}")
        self.root.update()

    def move_window_to_top_right(self):
        """창을 오른쪽 위로 이동"""
        screen_width = self.root.winfo_screenwidth()
        self.move_window(screen_width - 450, 50)

    def move_window_to_bottom_left(self):
        """창을 왼쪽 아래로 이동"""
        screen_height = self.root.winfo_screenheight()
        self.move_window(50, screen_height - 650)

    def move_window_to_bottom_right(self):
        """창을 오른쪽 아래로 이동"""
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        self.move_window(screen_width - 450, screen_height - 650)

    def center_window(self):
        """창을 화면 중앙으로 이동"""
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - 400) // 2
        y = (screen_height - 600) // 2
        self.move_window(x, y)

    def run(self):
        """테스트 앱 실행"""
        print("DatePickerDialog 위치 테스트 시작")
        print("1. 다양한 텍스트 길이로 다이얼로그 테스트")
        print("2. 창 위치를 이동한 후 다이얼로그 테스트")
        print("3. 다이얼로그가 화면을 벗어나지 않는지 확인")
        print("-" * 50)

        self.center_window()
        self.root.mainloop()


if __name__ == "__main__":
    try:
        app = DialogTestApp()
        app.run()
    except Exception as e:
        print(f"[ERROR] 테스트 앱 실행 실패: {e}")
        import traceback
        traceback.print_exc()