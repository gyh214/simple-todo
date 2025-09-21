"""
TODO 정렬 드롭다운 위젯 (Magic UI 스타일)
DRY+CLEAN+Simple 원칙 적용
"""

import tkinter as tk
from typing import Dict, Any, List, Callable, Optional
from .widgets import DARK_COLORS, get_button_style


class SortDropdownWidget:
    """Magic UI 스타일 정렬 드롭다운 위젯"""

    def __init__(self, parent, sort_manager, callback: Callable[[str], None]):
        self.parent = parent
        self.sort_manager = sort_manager
        self.callback = callback

        # 상태 관리
        self.dropdown_window = None
        self.is_open = False

        # UI 생성
        self._setup_ui()
        self._update_main_button()

        # 외부 클릭 감지를 위한 이벤트 바인딩
        self._bind_global_events()

    def _setup_ui(self):
        """메인 드롭다운 버튼 UI 구성"""
        colors = DARK_COLORS

        # 메인 버튼 스타일
        self.main_button = tk.Button(
            self.parent,
            font=('Segoe UI', 9),
            bg=colors['button_bg'],
            fg=colors['text'],
            relief='flat',
            borderwidth=1,
            padx=8,
            pady=5,
            cursor='hand2',
            command=self._toggle_dropdown
        )

        # 호버 효과
        self.main_button.bind('<Enter>', self._on_button_enter)
        self.main_button.bind('<Leave>', self._on_button_leave)

    def _update_main_button(self):
        """현재 정렬 상태에 따라 메인 버튼 텍스트 업데이트"""
        sort_info = self.sort_manager.get_current_sort_info()
        button_text = f"{sort_info['icon']} {sort_info['description']} ▼"
        self.main_button.configure(text=button_text)

    def _on_button_enter(self, event):
        """버튼 호버 시 스타일 변경"""
        colors = DARK_COLORS
        self.main_button.configure(bg=colors['bg_hover'])

    def _on_button_leave(self, event):
        """버튼 호버 해제 시 스타일 복원"""
        colors = DARK_COLORS
        self.main_button.configure(bg=colors['button_bg'])

    def _toggle_dropdown(self):
        """드롭다운 메뉴 토글"""
        if self.is_open:
            self._close_dropdown()
        else:
            self._open_dropdown()

    def _open_dropdown(self):
        """드롭다운 메뉴 열기"""
        if self.is_open:
            return

        self.is_open = True
        colors = DARK_COLORS

        # 드롭다운 윈도우 생성
        self.dropdown_window = tk.Toplevel(self.parent)
        self.dropdown_window.wm_overrideredirect(True)  # 타이틀바 제거
        self.dropdown_window.configure(bg=colors['bg_secondary'])
        self.dropdown_window.wm_attributes('-topmost', True)

        # 위치 계산
        self._position_dropdown()

        # 메뉴 옵션들 생성
        self._create_menu_options()

        # 외부 클릭 감지
        self.dropdown_window.bind('<FocusOut>', self._on_focus_out)
        self.dropdown_window.focus_set()

    def _position_dropdown(self):
        """드롭다운 위치 계산 및 설정"""
        # 메인 버튼의 위치와 크기 가져오기
        button_x = self.main_button.winfo_rootx()
        button_y = self.main_button.winfo_rooty()
        button_height = self.main_button.winfo_height()

        # 드롭다운을 버튼 바로 아래에 위치
        dropdown_x = button_x
        dropdown_y = button_y + button_height + 2

        # 화면 경계 확인 및 조정
        screen_width = self.parent.winfo_screenwidth()
        screen_height = self.parent.winfo_screenheight()

        # 예상 드롭다운 크기 (4개 옵션 * 30px + 여백)
        estimated_width = 200
        estimated_height = 4 * 30 + 10

        # 화면 경계를 벗어나지 않도록 조정
        if dropdown_x + estimated_width > screen_width:
            dropdown_x = screen_width - estimated_width - 10
        if dropdown_y + estimated_height > screen_height:
            dropdown_y = button_y - estimated_height - 2

        self.dropdown_window.geometry(f"+{dropdown_x}+{dropdown_y}")

    def _create_menu_options(self):
        """드롭다운 메뉴 옵션들 생성"""
        colors = DARK_COLORS
        current_sort_info = self.sort_manager.get_current_sort_info()

        # 메뉴 프레임
        menu_frame = tk.Frame(
            self.dropdown_window,
            bg=colors['bg_secondary'],
            relief='solid',
            borderwidth=1
        )
        menu_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # 정렬 옵션들 생성
        options = self.sort_manager.get_sort_options()

        for i, option in enumerate(options):
            is_current = (
                option['criteria'] == current_sort_info['criteria'] and
                option['direction'] == current_sort_info['direction']
            )

            self._create_option_button(menu_frame, option, is_current, i)

        # 수동 순서 옵션 추가 (현재 MANUAL 모드인 경우에만 표시)
        if self.sort_manager.is_manual_mode():
            self._create_manual_option(menu_frame, len(options))

    def _create_option_button(self, parent, option: Dict[str, Any], is_current: bool, index: int):
        """개별 옵션 버튼 생성"""
        colors = DARK_COLORS

        # 현재 선택된 옵션 표시
        prefix = "✓ " if is_current else "   "
        button_text = f"{prefix}{option['icon']} {option['display_name']}"

        # 버튼 색상 설정
        if is_current:
            bg_color = colors['accent']
            fg_color = 'white'
        else:
            bg_color = colors['bg_secondary']
            fg_color = colors['text']

        option_button = tk.Button(
            parent,
            text=button_text,
            font=('Segoe UI', 9),
            bg=bg_color,
            fg=fg_color,
            relief='flat',
            borderwidth=0,
            padx=12,
            pady=6,
            anchor='w',
            cursor='hand2',
            command=lambda key=option['key']: self._on_option_selected(key)
        )
        option_button.pack(fill=tk.X, pady=1)

        # 호버 효과 (현재 선택되지 않은 항목만)
        if not is_current:
            option_button.bind('<Enter>', lambda e, btn=option_button: btn.configure(bg=colors['bg_hover']))
            option_button.bind('<Leave>', lambda e, btn=option_button: btn.configure(bg=bg_color))

    def _create_manual_option(self, parent, index: int):
        """수동 순서 옵션 생성"""
        colors = DARK_COLORS

        button_text = "✓ 🔧 수동 순서"

        manual_button = tk.Button(
            parent,
            text=button_text,
            font=('Segoe UI', 9),
            bg=colors['accent'],
            fg='white',
            relief='flat',
            borderwidth=0,
            padx=12,
            pady=6,
            anchor='w',
            cursor='hand2',
            state='disabled'  # 현재 상태이므로 비활성화
        )
        manual_button.pack(fill=tk.X, pady=1)

    def _on_option_selected(self, option_key: str):
        """옵션 선택 시 처리"""
        # 정렬 설정 변경
        if self.sort_manager.set_sort_option(option_key):
            # 메인 버튼 업데이트
            self._update_main_button()

            # 콜백 호출
            if self.callback:
                self.callback(option_key)

        # 드롭다운 닫기
        self._close_dropdown()

    def _close_dropdown(self):
        """드롭다운 메뉴 닫기"""
        if not self.is_open:
            return

        self.is_open = False

        if self.dropdown_window:
            self.dropdown_window.destroy()
            self.dropdown_window = None

    def _on_focus_out(self, event):
        """포커스 해제 시 드롭다운 닫기"""
        # 약간의 지연을 두어 클릭 이벤트가 처리되도록 함
        self.parent.after(100, self._close_dropdown)

    def _bind_global_events(self):
        """전역 이벤트 바인딩 (외부 클릭 감지)"""
        def on_global_click(event):
            if self.is_open and self.dropdown_window:
                # 클릭한 위젯이 드롭다운 내부가 아닌 경우 닫기
                clicked_widget = event.widget
                if not self._is_child_of(clicked_widget, self.dropdown_window):
                    self._close_dropdown()

        # 루트 윈도우에 글로벌 클릭 이벤트 바인딩
        root = self.parent
        while root.master:
            root = root.master

        root.bind('<Button-1>', on_global_click, add='+')

    def _is_child_of(self, widget, parent):
        """위젯이 부모의 자식인지 확인"""
        try:
            current = widget
            while current:
                if current == parent:
                    return True
                current = current.master
            return False
        except:
            return False

    def pack(self, **kwargs):
        """메인 버튼 패킹"""
        self.main_button.pack(**kwargs)

    def configure(self, **kwargs):
        """메인 버튼 설정"""
        self.main_button.configure(**kwargs)

    def destroy(self):
        """위젯 정리"""
        self._close_dropdown()
        if hasattr(self, 'main_button'):
            self.main_button.destroy()

    def update_display(self):
        """정렬 상태 변경 시 디스플레이 업데이트"""
        self._update_main_button()
        if self.is_open:
            self._close_dropdown()