"""
TODO 표시 관리자 모듈

TodoPanelApp에서 TODO 표시 관련 메서드들을 분리하여 단일 책임 원칙 적용
DRY+CLEAN+Simple 원칙 준수
"""

import tkinter as tk
from tkinter import messagebox
from typing import Any, Callable, Dict, List, Optional, Union

# Phase 4A: 새로운 인터페이스 import
from ..interfaces.manager_interfaces import IManagerContainer, ITodoDisplayManager

# Phase 4B: 에러 처리 및 로깅 유틸리티 import
from ..utils.error_handling import DisplayManagerError, safe_execute, safe_ui_operation
from ..utils.logging_config import get_logger

# 안전한 import 처리
try:
    from ..widgets import TodoItemWidget
except ImportError as e:
    print(f"Warning: Failed to import TodoItemWidget from widgets module: {e}")
    TodoItemWidget = None


class TodoDisplayManager(ITodoDisplayManager):
    """TODO 표시 관리자 클래스 - 단일 책임 원칙 적용 (Phase 4A: ITodoDisplayManager 구현)"""

    def __init__(self, app_instance: IManagerContainer) -> None:
        """TodoDisplayManager 초기화

        Args:
            app_instance: TodoPanelApp 인스턴스 참조
        """
        self.app: IManagerContainer = app_instance  # TodoPanelApp 인스턴스 참조
        self.logger = get_logger(__name__)

        # 관리할 위젯들은 app_instance를 통해 접근
        # todo_widgets, pending_widgets, completed_widgets
        # pending_scrollable_frame, completed_scrollable_frame
        # pending_canvas, completed_canvas
        # pending_section, completed_section

    @safe_execute("TODO 목록 로드 중 오류 발생")
    def load_todos(self) -> None:
        """TODO 목록 로드 및 표시 (기존 _load_todos 100% 재사용)"""
        try:
            todos = self.app.todo_manager.get_todos()

            # 기존 위젯들 정리
            for widget in list(self.app.pending_widgets.values()) + list(
                self.app.completed_widgets.values()
            ):
                widget.destroy()
            self.app.pending_widgets.clear()
            self.app.completed_widgets.clear()
            self.app.todo_widgets.clear()

            # 완료/미완료로 분리 후 정렬
            pending_todos, completed_todos = self.app.sort_manager.separate_by_completion(todos)

            # 위젯 생성
            for todo in pending_todos:
                self.create_todo_widget(todo, section="pending")

            for todo in completed_todos:
                self.create_todo_widget(todo, section="completed")

            self.app.update_status()
            self.update_section_titles()

        except Exception as e:
            messagebox.showerror("오류", f"TODO 목록을 불러오는데 실패했습니다: {e}")

    @safe_execute("TODO 위젯 생성 중 오류 발생")
    def create_todo_widget(
        self, todo_data: Dict[str, Any], section: Optional[str] = None
    ) -> Optional["TodoItemWidget"]:
        """TODO 위젯 생성 (기존 _create_todo_widget 100% 재사용)"""
        # 섹션 자동 결정
        if section is None:
            section = "completed" if todo_data.get("completed", False) else "pending"

        # 적절한 부모 프레임 선택
        parent_frame = (
            self.app.pending_scrollable_frame
            if section == "pending"
            else self.app.completed_scrollable_frame
        )

        widget = TodoItemWidget(
            parent_frame,
            todo_data,
            self.app.update_todo,
            self.app.delete_todo,
            self.app.reorder_todo,
            debug=getattr(self.app.todo_manager, "_debug", False),
        )
        widget.pack(fill=tk.X, pady=1)

        # ✅ 마우스 휠 스크롤 바인딩 - 모든 자식 위젯에 Canvas 스크롤 적용
        target_canvas = (
            self.app.pending_canvas if section == "pending" else self.app.completed_canvas
        )
        if target_canvas:
            widget.bind_mousewheel_to_canvas(target_canvas)

        # 섹션별 관리
        if section == "pending":
            self.app.pending_widgets[todo_data["id"]] = widget
        else:
            self.app.completed_widgets[todo_data["id"]] = widget

        # 전체 관리용
        self.app.todo_widgets[todo_data["id"]] = widget

        return widget

    @safe_ui_operation()
    def update_section_titles(self) -> None:
        """섹션 제목 업데이트 (기존 _update_section_titles 100% 재사용)"""
        pending_count = len(self.app.pending_widgets)
        completed_count = len(self.app.completed_widgets)

        self.app.pending_section.update_title(f"📋 진행중인 할일 ({pending_count}개)")
        self.app.completed_section.update_title(f"✅ 완료된 할일 ({completed_count}개)")

    @safe_execute("TODO 섹션 이동 중 오류 발생")
    def move_todo_between_sections(self, todo_id: str, completed: bool) -> None:
        """TODO를 섹션 간에 이동 (기존 _move_todo_between_sections 100% 재사용)"""
        if todo_id not in self.app.todo_widgets:
            return

        widget = self.app.todo_widgets[todo_id]
        todo_data = widget.todo_data

        # 기존 섹션에서 제거
        if todo_id in self.app.pending_widgets:
            del self.app.pending_widgets[todo_id]
        if todo_id in self.app.completed_widgets:
            del self.app.completed_widgets[todo_id]

        # 위젯 제거
        widget.destroy()

        # 새로운 섹션에서 다시 생성
        section = "completed" if completed else "pending"
        self.create_todo_widget(todo_data, section)

    @safe_ui_operation()
    def refresh_display(self) -> None:
        """전체 디스플레이 새로고침"""
        self.load_todos()

    def get_todo_widget(self, todo_id: str) -> Optional["TodoItemWidget"]:
        """특정 TODO 위젯 반환

        Args:
            todo_id: TODO ID

        Returns:
            TodoItemWidget 또는 None
        """
        return self.app.todo_widgets.get(todo_id)

    @safe_execute("TODO 위젯 제거 중 오류 발생")
    def remove_todo_widget(self, todo_id: str) -> None:
        """TODO 위젯 제거 및 정리

        Args:
            todo_id: 제거할 TODO ID
        """
        if todo_id in self.app.todo_widgets:
            # 위젯 제거
            self.app.todo_widgets[todo_id].destroy()
            del self.app.todo_widgets[todo_id]

            # 섹션별 위젯 관리에서도 제거
            if todo_id in self.app.pending_widgets:
                del self.app.pending_widgets[todo_id]
            if todo_id in self.app.completed_widgets:
                del self.app.completed_widgets[todo_id]

            # 섹션 제목 업데이트
            self.update_section_titles()
