"""
제어 패널 관리자 모듈

TodoPanelApp에서 제어 패널 관련 메서드들을 분리하여 단일 책임 원칙 적용
DRY+CLEAN+Simple 원칙 준수
"""

import tkinter as tk
import webbrowser
from datetime import datetime
from tkinter import messagebox, ttk
from typing import Any, Callable, Dict, List, Optional, Union

# Phase 4A: 새로운 인터페이스 및 유틸리티 import
from ..interfaces.manager_interfaces import IControlPanelManager, IManagerContainer
from ..utils.constants import DARK_COLORS

# Phase 4B: 에러 처리 및 로깅 유틸리티 import
from ..utils.error_handling import UIManagerError, safe_execute, safe_ui_operation
from ..utils.logging_config import get_logger
from ..utils.ui_helpers import create_styled_button, get_button_style

try:
    from ..sort_dropdown_widget import SortDropdownWidget
except ImportError:
    SortDropdownWidget = None

try:
    from tooltip import ToolTip
except ImportError:
    # ToolTip fallback
    class ToolTip:
        def __init__(self, widget, text):
            pass


class ControlPanelManager(IControlPanelManager):
    """제어 패널 관리자 클래스 - 단일 책임 원칙 적용 (Phase 4A: IControlPanelManager 구현)"""

    def __init__(self, app_instance: IManagerContainer) -> None:
        """ControlPanelManager 초기화

        Args:
            app_instance: TodoPanelApp 인스턴스 참조
        """
        self.app: IManagerContainer = app_instance  # TodoPanelApp 인스턴스 참조
        self.logger = get_logger(__name__)

        # 관리할 위젯들 (app_instance를 통해 접근)
        # entry_var, todo_entry, add_btn, sort_btn, top_btn, clear_btn, info_btn, sort_dropdown, status_label

    @safe_execute("제어 패널 설정 중 오류 발생")
    def setup_control_panel(self, parent: tk.Widget) -> None:
        """상단 통합 제어 패널 설정 (기존 _setup_control_panel 100% 재사용)"""
        control_frame = tk.Frame(parent, bg=DARK_COLORS["bg"])
        control_frame.pack(fill=tk.X, pady=(0, 4))

        # 좌측: TODO 입력 영역
        self.app.entry_var = tk.StringVar()
        self.app.todo_entry = tk.Entry(
            control_frame,
            textvariable=self.app.entry_var,
            font=("Segoe UI", 9),
            bg=DARK_COLORS["entry_bg"],
            fg=DARK_COLORS["text"],
            borderwidth=1,
            relief="solid",
        )
        self.app.todo_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))

        # 추가 버튼
        self.app.add_btn = self._create_control_button(
            control_frame,
            text="추가",
            command=self.app.show_add_todo_dialog,
            tooltip_text="새 할일 추가",
            style_type="primary",
        )
        self.app.add_btn.pack(side=tk.LEFT, padx=(0, 8))

        # 정렬 드롭다운 (기존 토글 버튼 교체)
        if SortDropdownWidget:
            self.app.sort_dropdown = SortDropdownWidget(
                control_frame, self.app.sort_manager, self.app.handle_sort_change
            )
            self.app.sort_dropdown.pack(side=tk.RIGHT, padx=(4, 0))
        else:
            # 폴백: 기본 정렬 버튼
            self.app.sort_btn = self._create_control_button(
                control_frame,
                text="🔄 정렬",
                command=None,  # 기본 정렬 로직은 여기서 구현 필요
                tooltip_text="목록 정렬",
                style_type="secondary",
            )
            self.app.sort_btn.pack(side=tk.RIGHT, padx=(4, 0))

        # 우측 제어 버튼들
        # 항상 위 토글
        self.app.top_btn = self._create_control_button(
            control_frame,
            text="📌",
            width=3,
            command=self.app.toggle_always_on_top,
            tooltip_text="항상 위에 표시",
            style_type="secondary",
        )
        self.app.top_btn.pack(side=tk.RIGHT, padx=(4, 0))

        # 완료된 항목 정리 버튼
        self.app.clear_btn = self._create_control_button(
            control_frame,
            text="🗑️",
            width=3,
            command=self.app.clear_completed_todos,
            tooltip_text="완료된 항목 모두 삭제",
            style_type="secondary",
        )
        self.app.clear_btn.pack(side=tk.RIGHT, padx=(4, 0))

        # 정보 버튼
        self.app.info_btn = self._create_control_button(
            control_frame,
            text="ⓘ",
            width=3,
            command=self.app.show_about_dialog,
            tooltip_text="개발자 정보 및 더 많은 도구들",
            style_type="secondary",
        )
        self.app.info_btn.pack(side=tk.RIGHT, padx=(4, 0))

        # 입력 필드 이벤트 설정
        self.app.todo_entry.bind("<Return>", lambda e: self.app.show_add_todo_dialog())
        self.app.todo_entry.bind("<FocusIn>", lambda e: self.handle_entry_focus("in"))
        self.app.todo_entry.bind("<FocusOut>", lambda e: self.handle_entry_focus("out"))
        self.set_entry_placeholder()

    @safe_execute("상태바 설정 중 오류 발생")
    def setup_status_bar(self, parent: tk.Widget) -> None:
        """하단 상태바 설정 (기존 _setup_status_bar 100% 재사용)"""
        status_frame = tk.Frame(parent, bg=DARK_COLORS["bg"])
        status_frame.pack(fill=tk.X)

        self.app.status_label = tk.Label(
            status_frame,
            text="",
            font=("Segoe UI", 8),
            bg=DARK_COLORS["bg"],
            fg=DARK_COLORS["text_secondary"],
        )
        self.app.status_label.pack(side=tk.LEFT)

        self.update_status()

    @safe_ui_operation()
    def set_entry_placeholder(self) -> None:
        """입력 필드 플레이스홀더 설정 (기존 _set_entry_placeholder 100% 재사용)"""
        if not self.app.entry_var.get():
            self.app.todo_entry.configure(foreground="gray")
            self.app.entry_var.set("새 할 일을 입력하세요...")

    @safe_ui_operation()
    def handle_entry_focus(self, event_type: str) -> None:
        """입력 필드 포커스 처리 (기존 _on_entry_focus_in + _on_entry_focus_out 통합)"""
        if event_type == "in":
            # 입력 필드 포커스 시
            if self.app.entry_var.get() == "새 할 일을 입력하세요...":
                self.app.entry_var.set("")
                self.app.todo_entry.configure(foreground=DARK_COLORS["text"])
        elif event_type == "out":
            # 입력 필드 포커스 해제 시
            if not self.app.entry_var.get():
                self.set_entry_placeholder()

    @safe_ui_operation()
    def update_status(self, message: Optional[str] = None) -> None:
        """상태 메시지 업데이트"""
        if message:
            self.app.status_label.configure(text=message)
        else:
            # 기본 상태 정보 업데이트 (TODO 통계 표시)
            try:
                stats = self.app.todo_manager.get_stats()
                status_text = f"전체: {stats['total']}, 완료: {stats['completed']}, 남은 일: {stats['pending']}"
                self.app.status_label.configure(text=status_text)
            except:
                self.app.status_label.configure(text="상태 정보를 불러올 수 없습니다")

    @safe_execute("컨트롤 버튼 생성 중 오류 발생")
    def _create_control_button(
        self,
        parent: tk.Widget,
        text: str,
        command: Optional[Callable] = None,
        tooltip_text: str = "",
        style_type: str = "secondary",
        width: Optional[int] = None,
        **kwargs: Any,
    ) -> tk.Button:
        """Phase 4A: DRY 원칙 - 공통 유틸리티 사용으로 중복 제거"""
        return create_styled_button(
            parent=parent,
            text=text,
            command=command,
            tooltip_text=tooltip_text,
            style_type=style_type,
            width=width,
            **kwargs,
        )
