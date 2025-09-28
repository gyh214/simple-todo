"""
EventHandler - 사용자 이벤트 처리 전담 매니저

모든 액션 및 이벤트 처리 로직을 담당하며, DRY+CLEAN+Simple 원칙을 적용하여
main_app.py에서 분리된 이벤트 처리 메서드들을 관리합니다.
"""

import tkinter as tk
import webbrowser
from datetime import datetime
from tkinter import messagebox
from typing import Any, Dict, Optional, Union

# 다이얼로그 import
from ..dialogs.date_picker_dialog import DatePickerDialog

# Phase 4A: 새로운 인터페이스 및 유틸리티 import
from ..interfaces.manager_interfaces import IEventHandler, IManagerContainer
from ..utils.constants import DARK_COLORS

# Phase 4B: 에러 처리 및 로깅 유틸리티 import
from ..utils.error_handling import EventHandlerError, safe_execute, safe_ui_operation
from ..utils.logging_config import get_logger
from ..utils.ui_helpers import get_button_style


class EventHandler(IEventHandler):
    """사용자 이벤트 처리 전담 클래스 (Phase 4A: IEventHandler 구현)"""

    def __init__(self, app_instance: IManagerContainer) -> None:
        """
        EventHandler 초기화

        Args:
            app_instance: TodoPanelApp 인스턴스 참조
        """
        self.app: IManagerContainer = app_instance
        self.logger = get_logger(__name__)

    @safe_execute("할일 추가 다이얼로그 표시 중 오류 발생")
    def show_add_todo_dialog(self) -> None:
        """할일 추가 다이얼로그 표시 (기존 _show_add_todo_dialog 100% 재사용)"""
        text = self.app.entry_var.get().strip()
        if not text or text == "새 할 일을 입력하세요...":
            return

        # 날짜 선택 다이얼로그 표시
        dialog = DatePickerDialog(self.app.root, text)
        result, selected_date = dialog.show()

        if result == "cancelled":
            return

        try:
            # TODO 생성 (due_date 포함)
            due_date = selected_date if result == "with_date" else None
            todo = self.create_todo_with_date(text, due_date)

            if todo:
                self.app.todo_display_manager.create_todo_widget(todo)

                # 입력 필드 초기화
                self.app.entry_var.set("")
                self.app.control_panel_manager.set_entry_placeholder()

                self.app.update_status()
                self.app.todo_display_manager.update_section_titles()

        except Exception as e:
            messagebox.showerror("오류", f"TODO 추가에 실패했습니다: {e}")

    @safe_execute("날짜가 포함된 TODO 생성 중 오류 발생")
    def create_todo_with_date(
        self, text: str, due_date: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """날짜가 포함된 TODO 생성 (기존 _create_todo_with_date 100% 재사용)"""
        # 기존 create_todo 메소드가 due_date 파라미터를 지원하는지 확인
        try:
            # 새로운 방식으로 시도 (due_date 파라미터 포함)
            todo = self.app.todo_manager.create_todo(text, due_date=due_date)
            return todo
        except TypeError:
            # 기존 방식으로 TODO 생성 후 수동으로 due_date 추가
            todo = self.app.todo_manager.create_todo(text)
            if due_date:
                # 🔒 안전한 업데이트로 due_date 추가 (데이터 보존 보장)
                update_method = getattr(
                    self.app.todo_manager, "update_todo_safe", self.app.todo_manager.update_todo
                )
                update_method(todo["id"], due_date=due_date)
                todo["due_date"] = due_date
            return todo

    @safe_execute("정렬 옵션 변경 처리 중 오류 발생")
    def handle_sort_change(self, option_key: str) -> None:
        """정렬 옵션 변경 시 처리 - position 자동 동기화 포함 (기존 _on_sort_changed 100% 재사용)"""
        try:
            # 먼저 현재 TODO 목록을 새로운 정렬 기준으로 가져오기
            todos = self.app.todo_manager.get_todos()
            pending_todos, completed_todos = self.app.sort_manager.separate_by_completion(todos)

            # 🚀 NEW: 정렬 변경 후 position 자동 동기화
            print(f"[DEBUG] 정렬 변경됨: {option_key} - position 동기화 시작")

            # 미완료 항목들 position 동기화
            if pending_todos:
                sync_success = self.app.sort_manager.sync_positions_with_current_sort(
                    pending_todos, self.app.todo_manager
                )
                print(f"[DEBUG] 미완료 항목 position 동기화: {'성공' if sync_success else '실패'}")

            # 완료된 항목들 position 동기화
            if completed_todos:
                sync_success = self.app.sort_manager.sync_positions_with_current_sort(
                    completed_todos, self.app.todo_manager
                )
                print(f"[DEBUG] 완료 항목 position 동기화: {'성공' if sync_success else '실패'}")

            # 정렬 적용을 위해 TODO 목록 다시 로드
            self.app.todo_display_manager.load_todos()

            # 드롭다운 디스플레이 업데이트
            if hasattr(self.app, "sort_dropdown") and self.app.sort_dropdown:
                self.app.sort_dropdown.update_display()

            # 🆕 정렬 변경 시 즉시 설정 저장
            self.app.save_all_ui_settings()
            print(f"[DEBUG] 정렬 변경 후 즉시 저장 완료: {option_key}")

        except Exception as e:
            print(f"[ERROR] 정렬 변경 처리 실패: {e}")
            # 폴백: 기본 로드만 수행
            self.app.todo_display_manager.load_todos()

    @safe_execute("TODO 업데이트 중 오류 발생")
    def update_todo(self, todo_id: str, **kwargs: Any) -> None:
        """TODO 업데이트 (섹션 이동 처리) - 완전한 데이터 보존 (기존 _update_todo 100% 재사용)"""
        try:
            # 🔒 중앙집중식 데이터 보존을 위해 update_todo_safe 사용
            # 납기일, 우선순위 등 모든 메타데이터가 자동으로 보존
            success = getattr(
                self.app.todo_manager, "update_todo_safe", self.app.todo_manager.update_todo
            )(todo_id, **kwargs)
            if success:
                # 완료 상태 변경 시 섹션 이동
                if "completed" in kwargs:
                    self.app.todo_display_manager.move_todo_between_sections(
                        todo_id, kwargs["completed"]
                    )

                # 위젯 데이터 업데이트
                if todo_id in self.app.todo_widgets:
                    updated_todo = self.app.todo_manager.get_todo_by_id(todo_id)
                    if updated_todo:
                        self.app.todo_widgets[todo_id].update_data(updated_todo)

                self.app.update_status()
                self.app.todo_display_manager.update_section_titles()
            else:
                messagebox.showerror("오류", "TODO 업데이트에 실패했습니다.")

        except Exception as e:
            messagebox.showerror("오류", f"TODO 업데이트에 실패했습니다: {e}")

    @safe_execute("TODO 삭제 중 오류 발생")
    def delete_todo(self, todo_id: str) -> None:
        """TODO 삭제 (기존 _delete_todo 100% 재사용)"""
        try:
            success = self.app.todo_manager.delete_todo(todo_id)
            if success:
                # UI에서 위젯 제거
                if todo_id in self.app.todo_widgets:
                    self.app.todo_widgets[todo_id].destroy()
                    del self.app.todo_widgets[todo_id]

                # 섹션별 위젯 관리에서도 제거
                if todo_id in self.app.pending_widgets:
                    del self.app.pending_widgets[todo_id]
                if todo_id in self.app.completed_widgets:
                    del self.app.completed_widgets[todo_id]

                self.app.update_status()
                self.app.todo_display_manager.update_section_titles()
            else:
                messagebox.showerror("오류", "TODO 삭제에 실패했습니다.")

        except Exception as e:
            messagebox.showerror("오류", f"TODO 삭제 중 오류가 발생했습니다: {e}")

    @safe_execute("TODO 순서 변경 중 오류 발생")
    def reorder_todo(self, todo_id: str, move_steps: int) -> None:
        """TODO 순서 변경 (수동 모드 자동 전환) - 정리된 로직 (기존 _reorder_todo 100% 재사용)"""
        try:
            # 현재 TODO 찾기
            widget = self.app.todo_widgets.get(todo_id)
            if not widget:
                print(f"[WARNING] TODO 위젯을 찾을 수 없음: {todo_id}")
                return

            is_completed = widget.todo_data.get("completed", False)
            print(
                f"[DEBUG] TODO 이동 시작: {todo_id[:8]} ({'완료' if is_completed else '미완료'} 섹션)"
            )

            # 🔄 올바른 화면 순서 가져오기 (정렬된 순서)
            todos = self.app.todo_manager.get_todos()
            pending_todos, completed_todos = self.app.sort_manager.separate_by_completion(todos)
            current_section_todos = completed_todos if is_completed else pending_todos

            # 현재 위치 찾기
            current_pos = None
            for i, todo in enumerate(current_section_todos):
                if todo["id"] == todo_id:
                    current_pos = i
                    break

            if current_pos is None:
                print(f"[WARNING] TODO 위치를 찾을 수 없음: {todo_id}")
                return

            # 새 위치 계산
            new_pos = max(0, min(len(current_section_todos) - 1, current_pos + move_steps))
            print(f"[DEBUG] 위치 변경: {current_pos} -> {new_pos}")

            if new_pos != current_pos:
                # 🚀 수동 이동 전 position 동기화 (MANUAL 모드가 아닌 경우에만)
                if not self.app.sort_manager.is_manual_mode():
                    print("[DEBUG] 수동 모드 전환 전 position 동기화 수행")
                    sync_success = self.app.sort_manager.sync_positions_with_current_sort(
                        current_section_todos, self.app.todo_manager
                    )
                    if not sync_success:
                        print("[WARNING] Position 동기화 실패, 계속 진행합니다.")

                # MANUAL 모드로 전환
                self.app.sort_manager.set_manual_mode()

                # 순서 변경
                success = self.app.todo_manager.reorder_todos(todo_id, new_pos)
                if success:
                    print(f"[DEBUG] TODO 순서 변경 성공: {todo_id[:8]}")
                    # UI 업데이트
                    if hasattr(self.app, "sort_dropdown") and self.app.sort_dropdown:
                        self.app.sort_dropdown.update_display()
                    self.app.todo_display_manager.load_todos()

                    # 🆕 수동 모드 전환 및 순서 변경 후 즉시 설정 저장
                    self.app.save_all_ui_settings()
                    print("[DEBUG] 수동 모드 전환 후 즉시 저장 완료")
                else:
                    print(f"[ERROR] TODO 순서 변경 실패: {todo_id[:8]}")

        except Exception as e:
            print(f"[ERROR] reorder_todo 실패: {e}")
            messagebox.showerror("오류", f"TODO 순서 변경에 실패했습니다: {e}")

    @safe_execute("완료된 항목 정리 중 오류 발생")
    def clear_completed_todos(self) -> None:
        """완료된 항목들 정리 (기존 _clear_completed 100% 재사용)"""
        try:
            completed_count = len(self.app.completed_widgets)

            if completed_count == 0:
                messagebox.showinfo("정보", "삭제할 완료된 항목이 없습니다.")
                return

            # 확인창 표시
            confirm = messagebox.askyesno(
                "완료된 항목 일괄 삭제",
                f"완료된 {completed_count}개의 항목을 모두 삭제하시겠습니까?\n\n삭제 후 복구할 수 없습니다.",
                parent=self.app.root,
                icon="warning",
            )

            if confirm:
                count = self.app.todo_manager.clear_completed_todos()
                if count > 0:
                    self.app.todo_display_manager.load_todos()
                    messagebox.showinfo("완료", f"{count}개의 완료된 항목을 삭제했습니다.")

        except Exception as e:
            messagebox.showerror("오류", f"완료된 항목 정리에 실패했습니다: {e}")

    @safe_ui_operation()
    def toggle_always_on_top(self) -> None:
        """항상 위 토글 (기존 _toggle_always_on_top 100% 재사용)"""
        self.app.always_on_top = not self.app.always_on_top
        self.app.root.wm_attributes("-topmost", self.app.always_on_top)

        # 버튼 스타일 변경
        if self.app.always_on_top:
            self.app.top_btn.configure(bg=DARK_COLORS["accent"], fg="white")
        else:
            self.app.top_btn.configure(bg=DARK_COLORS["button_bg"], fg=DARK_COLORS["text"])

    @safe_ui_operation()
    def show_about_dialog(self) -> None:
        """정보 대화상자 표시 (기존 _show_about_dialog 100% 재사용)"""
        try:
            about_window = tk.Toplevel(self.app.root)
            about_window.title("TODO Panel 정보")
            about_window.geometry("400x300")
            about_window.resizable(False, False)
            about_window.transient(self.app.root)
            about_window.grab_set()

            # 색상 테마 설정
            colors = DARK_COLORS
            about_window.configure(bg=colors["bg"])

            # 중앙 정렬
            x = (about_window.winfo_screenwidth() // 2) - 200
            y = (about_window.winfo_screenheight() // 2) - 150
            about_window.geometry(f"400x300+{x}+{y}")

            # 메인 프레임
            main_frame = tk.Frame(about_window, bg=colors["bg"])
            main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

            # 제목
            title_label = tk.Label(
                main_frame,
                text="📝 TODO Panel",
                font=("Segoe UI", 16, "bold"),
                bg=colors["bg"],
                fg=colors["text"],
            )
            title_label.pack(pady=(0, 10))

            # 버전 정보
            version_label = tk.Label(
                main_frame,
                text="Windows 데스크탑 TODO 관리 도구",
                font=("Segoe UI", 10),
                bg=colors["bg"],
                fg=colors["text_secondary"],
            )
            version_label.pack(pady=(0, 20))

            # 개발자 정보
            dev_frame = tk.Frame(main_frame, bg=colors["bg"])
            dev_frame.pack(fill=tk.X, pady=(0, 20))

            dev_label = tk.Label(
                dev_frame,
                text="개발자: kochim.com 팀",
                font=("Segoe UI", 10),
                bg=colors["bg"],
                fg=colors["text"],
            )
            dev_label.pack()

            # kochim.com 버튼
            website_style = get_button_style("primary")
            website_btn = tk.Button(
                main_frame,
                text="🌐 kochim.com 방문하기",
                command=self.open_website,
                **website_style,
            )
            website_btn.pack(pady=15)

            # 닫기 버튼
            close_style = get_button_style("secondary")
            close_btn = tk.Button(
                main_frame, text="닫기", command=about_window.destroy, **close_style
            )
            close_btn.pack()

        except Exception as e:
            messagebox.showerror("오류", f"정보 창을 열 수 없습니다: {e}")

    @safe_ui_operation()
    def open_website(self, url: Optional[str] = None) -> None:
        """웹사이트 열기 (기존 _open_kochim_website를 일반화하여 100% 재사용)"""
        try:
            target_url = url or "https://kochim.com"
            webbrowser.open(target_url)
            if hasattr(self.app, "status_label"):
                original_text = self.app.status_label.cget("text")
                website_name = target_url.replace("https://", "").replace("http://", "")
                self.app.status_label.configure(text=f"{website_name}이 브라우저에서 열렸습니다")
                self.app.root.after(
                    3000, lambda: self.app.status_label.configure(text=original_text)
                )
        except Exception as e:
            messagebox.showerror(
                "웹사이트 열기 오류", f"브라우저에서 웹사이트를 열 수 없습니다.\n\n오류: {e}"
            )

    @safe_execute("애플리케이션 종료 처리 중 오류 발생")
    def handle_window_closing(self) -> None:
        """앱 종료 시 처리 (기존 _on_closing 100% 재사용)"""
        try:
            # 1. 모든 UI 설정 저장 (분할 비율 + 정렬 설정)
            print("[DEBUG] 애플리케이션 종료: UI 설정 저장 중...")
            self.app.save_all_ui_settings()

            # 2. TODO 데이터 저장
            # AsyncTodoManager의 경우 shutdown 메소드 호출
            if hasattr(self.app.todo_manager, "shutdown"):
                print("[DEBUG] AsyncTodoManager shutdown 호출")
                self.app.todo_manager.shutdown()
            # 기본 TodoManager의 경우 save_data 호출
            elif hasattr(self.app.todo_manager, "save_data"):
                print("[DEBUG] TodoManager save_data 호출")
                self.app.todo_manager.save_data()

            print("[DEBUG] 애플리케이션 정상 종료")

        except Exception as e:
            print(f"[ERROR] 종료 중 오류: {e}")
        finally:
            self.app.root.destroy()
