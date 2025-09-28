"""
UI 레이아웃 관리자 모듈

TodoPanelApp에서 UI 레이아웃 관련 메서드들을 분리하여 단일 책임 원칙 적용
"""

import sys
import tkinter as tk
from datetime import datetime
from tkinter import ttk
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

# Phase 4B: 타입 힌트 및 에러 처리 표준화
from ..interfaces.manager_interfaces import IManagerContainer, IUILayoutManager
from ..utils.constants import DARK_COLORS
from ..utils.error_handling import UIManagerError, log_method_call, safe_execute, safe_ui_operation
from ..utils.logging_config import get_logger

try:
    from ..components.collapsible_section import CollapsibleSection
except ImportError:
    # CollapsibleSection fallback
    class CollapsibleSection:
        def __init__(self, parent, title, initial_collapsed=False):
            self.frame = tk.Frame(parent)

        def pack(self, **kwargs):
            self.frame.pack(**kwargs)

        def get_content_frame(self):
            return self.frame

        def update_title(self, title):
            pass


class UILayoutManager(IUILayoutManager):
    """UI 레이아웃 관리자 클래스 - 단일 책임 원칙 적용 (Phase 4B: 완전한 타입 힌트 및 에러 처리)"""

    def __init__(self, app_instance: IManagerContainer) -> None:
        """UILayoutManager 초기화

        Args:
            app_instance: TodoPanelApp 인스턴스 참조
        """
        self.app: IManagerContainer = app_instance  # TodoPanelApp 인스턴스 참조
        self.logger = get_logger(__name__)

        # 관리할 UI 속성들 (app_instance를 통해 접근)
        # sections_paned_window, pending_section, completed_section,
        # pending_canvas, completed_canvas, pending_scrollable_frame, completed_scrollable_frame

    @safe_execute("윈도우 설정 중 오류 발생")
    @log_method_call()
    def setup_window(self, root: tk.Tk) -> None:
        """메인 윈도우 설정 (기존 _setup_window 100% 재사용)"""
        root.title("TODO Panel")
        root.geometry("400x600")
        root.minsize(300, 400)

        # 다크테마 배경
        colors = DARK_COLORS
        root.configure(bg=colors["bg"])

        # 아이콘 설정
        try:
            root.iconbitmap(default="")
        except Exception as e:
            self.logger.debug(f"아이콘 설정 실패 (무시): {e}")

        root.resizable(True, True)

    @safe_execute("메인 레이아웃 설정 중 오류 발생")
    @log_method_call()
    def setup_main_layout(self, parent: tk.Widget) -> None:
        """UI 구성 요소 설정 (기존 _setup_ui 100% 재사용)"""
        colors = DARK_COLORS

        # 메인 컨테이너
        main_frame = tk.Frame(parent, bg=colors["bg"])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=6, pady=4)

        # 상단 통합 제어 패널 (ControlPanelManager로 위임)
        control_panel_manager = self.app.get_manager("control_panel")
        if control_panel_manager:
            control_panel_manager.setup_control_panel(main_frame)

        # TODO 리스트 섹션 (분할된 섹션들)
        self.setup_sections(main_frame)

        # 하단 상태바 (ControlPanelManager로 위임)
        if control_panel_manager:
            control_panel_manager.setup_status_bar(main_frame)

    @safe_execute("섹션 설정 중 오류 발생")
    @log_method_call()
    def setup_sections(self, parent: tk.Widget) -> None:
        """섹션 분할된 TODO 리스트 설정 (기존 _setup_sections 100% 재사용)"""
        colors = DARK_COLORS

        # PanedWindow로 동적 크기조절 구현
        self.app.sections_paned_window = tk.PanedWindow(
            parent,
            orient=tk.VERTICAL,  # 세로 방향 분할
            bg=colors["bg"],
            bd=0,
            sashwidth=6,  # 분할바 두께
            sashrelief=tk.FLAT,
            sashpad=2,
            handlesize=8,
            handlepad=10,
            showhandle=True,
        )
        self.app.sections_paned_window.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        # 분할바 스타일링 (Magic UI 다크 테마)
        self.style_paned_window_sash()

        # 진행중인 할일 섹션 프레임
        pending_frame = tk.Frame(self.app.sections_paned_window, bg=colors["bg"])
        self.app.pending_section = CollapsibleSection(
            pending_frame, "📋 진행중인 할일 (0개)", initial_collapsed=False
        )
        self.app.pending_section.pack(fill=tk.BOTH, expand=True)

        # 진행중 할일을 위한 스크롤 가능한 영역
        self.setup_scrollable_area(self.app.pending_section.get_content_frame(), "pending")

        # 완료된 할일 섹션 프레임
        completed_frame = tk.Frame(self.app.sections_paned_window, bg=colors["bg"])
        self.app.completed_section = CollapsibleSection(
            completed_frame,
            "✅ 완료된 할일 (0개)",
            initial_collapsed=False,  # PanedWindow에서는 기본으로 펼쳐둠
        )
        self.app.completed_section.pack(fill=tk.BOTH, expand=True)

        # 완료된 할일을 위한 스크롤 가능한 영역
        self.setup_scrollable_area(self.app.completed_section.get_content_frame(), "completed")

        # PanedWindow에 프레임들 추가
        self.app.sections_paned_window.add(pending_frame, minsize=100, sticky="nsew")
        self.app.sections_paned_window.add(completed_frame, minsize=40, sticky="nsew")

        # 분할바 초기 비율은 main_app.py의 _ensure_pane_ratio_applied에서 처리 (DRY 원칙)
        print("[DEBUG] 분할바 초기화는 main_app.py에서 처리됨 - 중복 호출 방지")

    @safe_execute("스크롤 영역 설정 중 오류 발생")
    @log_method_call(include_args=True)
    def setup_scrollable_area(
        self, parent: tk.Widget, section_type: str
    ) -> Tuple[tk.Canvas, tk.Frame]:
        """스크롤 가능한 영역 설정 (기존 _setup_scrollable_area 100% 재사용)

        Args:
            parent: 부모 위젯
            section_type: 섹션 타입 ('pending' 또는 'completed')

        Returns:
            Tuple[tk.Canvas, tk.Frame]: 생성된 캔버스와 스크롤 가능한 프레임
        """
        colors = DARK_COLORS

        # 스크롤 컨테이너
        scroll_container = tk.Frame(parent, bg=colors["bg"])
        scroll_container.pack(fill=tk.BOTH, expand=True)

        # 캔버스와 스크롤바 (동적 크기 조정)
        # 최소 높이와 최대 높이 설정
        min_height = 100
        max_height = 400 if section_type == "pending" else 300
        default_height = 200 if section_type == "pending" else 150

        canvas = tk.Canvas(
            scroll_container,
            highlightthickness=0,
            bg=colors["bg"],
            height=default_height,
            takefocus=True,
        )  # 포커스 설정 추가
        scrollbar = tk.Scrollbar(
            scroll_container,
            orient=tk.VERTICAL,
            command=canvas.yview,
            bg=colors["bg_secondary"],
            troughcolor=colors["bg"],
            activebackground=colors["accent"],
            highlightthickness=0,
            borderwidth=1,
            elementborderwidth=1,
        )

        canvas.configure(yscrollcommand=scrollbar.set)

        # 스크롤 가능한 프레임
        scrollable_frame = tk.Frame(canvas, bg=colors["bg"])
        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        # 패킹
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 이벤트 바인딩
        def configure_scroll_region(event: tk.Event) -> None:
            # 레이아웃 계산 완료 후 스크롤 영역 업데이트
            canvas.after_idle(lambda: _update_scroll_region(canvas))

        def _update_scroll_region(canvas_widget: tk.Canvas) -> None:
            """스크롤 영역을 안전하게 업데이트"""
            try:
                # 업데이트 전 잠시 대기 (레이아웃 완료 확보)
                canvas_widget.update_idletasks()

                # bbox("all")이 None을 반환할 수 있으므로 안전하게 처리
                bbox = canvas_widget.bbox("all")
                if bbox:
                    # 스크롤 영역 정확한 설정
                    canvas_widget.configure(scrollregion=bbox)
                    # 스크롤바 가시성 업데이트
                    _update_scrollbar_visibility(canvas_widget, scrollbar)
                else:
                    # 내용이 없으면 스크롤 영역 초기화
                    canvas_widget.configure(scrollregion=(0, 0, 0, 0))
                    scrollbar.pack_forget()  # 스크롤바 숨김
            except Exception as e:
                # 예외 발생 시 로그 출력 (디버깅용)
                self.logger.debug(f"스크롤 영역 업데이트 실패: {e}")

        def _update_scrollbar_visibility(
            canvas_widget: tk.Canvas, scrollbar_widget: tk.Scrollbar
        ) -> None:
            """스크롤바 가시성을 동적으로 조정"""
            try:
                # 캔버스 크기와 내용 크기 비교
                canvas_height = canvas_widget.winfo_height()
                scroll_region = canvas_widget.cget("scrollregion")

                if scroll_region:
                    # scrollregion은 "x1 y1 x2 y2" 형식의 문자열
                    coords = scroll_region.split()
                    if len(coords) >= 4:
                        content_height = int(float(coords[3])) - int(float(coords[1]))

                        # 내용이 캔버스보다 클 때만 스크롤바 표시
                        if content_height > canvas_height:
                            scrollbar_widget.pack(side=tk.RIGHT, fill=tk.Y)
                        else:
                            scrollbar_widget.pack_forget()
            except Exception as e:
                # 에러 발생 시 기본적으로 스크롤바 표시
                self.logger.debug(f"스크롤바 가시성 조정 실패: {e}")
                scrollbar_widget.pack(side=tk.RIGHT, fill=tk.Y)

        def configure_canvas_width(event: tk.Event) -> None:
            canvas.itemconfig(canvas_window, width=event.width)

        def adjust_canvas_height() -> None:
            """내용에 따라 Canvas 높이를 동적으로 조정"""
            try:
                # 스크롤 가능한 프레임의 실제 높이 계산
                scrollable_frame.update_idletasks()
                content_height = scrollable_frame.winfo_reqheight()

                # 최소/최대 높이 제한 적용
                new_height = max(min_height, min(content_height + 20, max_height))

                # 현재 높이와 다르면 업데이트
                current_height = canvas.winfo_reqheight()
                if abs(new_height - current_height) > 5:  # 5px 이상 차이날 때만 업데이트
                    canvas.configure(height=new_height)

                    # Canvas 크기 변경 후 스크롤 영역도 업데이트
                    canvas.after_idle(lambda: _update_scroll_region(canvas))

            except Exception as e:
                self.logger.debug(f"Canvas 높이 조정 실패: {e}")

        def on_content_change() -> None:
            """내용 변경 시 Canvas 높이 조정"""
            canvas.after_idle(adjust_canvas_height)

        # 공통 마우스 휠 핸들러 (Canvas 참조를 클로저로 캡처)
        def create_mousewheel_handler(
            target_canvas: tk.Canvas,
        ) -> Callable[[tk.Event], Optional[str]]:
            """마우스 휠 핸들러 팩토리 함수 - Canvas 참조를 캡처"""

            def on_mousewheel(event: tk.Event) -> str:
                """마우스 휠 스크롤 처리 (멀티 플랫폼 지원)"""
                try:
                    # Windows/macOS에서 event.delta 사용
                    if sys.platform.startswith("win") or sys.platform == "darwin":
                        delta = event.delta
                        if delta > 0:
                            target_canvas.yview_scroll(-1, "units")  # 위로 스크롤
                        elif delta < 0:
                            target_canvas.yview_scroll(1, "units")  # 아래로 스크롤
                    else:
                        # Linux: Button-4 (위) / Button-5 (아래)
                        if event.num == 4:
                            target_canvas.yview_scroll(-1, "units")  # 위로 스크롤
                        elif event.num == 5:
                            target_canvas.yview_scroll(1, "units")  # 아래로 스크롤

                    # 스크롤 후 포커스 유지
                    target_canvas.focus_set()
                    return "break"  # 이벤트 전파 중단
                except Exception as e:
                    self.logger.debug(f"마우스 휠 스크롤 처리 실패: {e}")
                    return "break"

            return on_mousewheel

        def create_linux_mousewheel_handlers(
            target_canvas: tk.Canvas,
        ) -> Tuple[Callable[[tk.Event], str], Callable[[tk.Event], str]]:
            """Linux용 마우스 휠 핸들러 팩토리 함수"""

            def on_linux_mousewheel_up(event: tk.Event) -> str:
                """Linux 마우스 휠 위로 스크롤"""
                target_canvas.yview_scroll(-1, "units")
                target_canvas.focus_set()
                return "break"

            def on_linux_mousewheel_down(event: tk.Event) -> str:
                """Linux 마우스 휠 아래로 스크롤"""
                target_canvas.yview_scroll(1, "units")
                target_canvas.focus_set()
                return "break"

            return on_linux_mousewheel_up, on_linux_mousewheel_down

        # 핸들러 인스턴스 생성
        mousewheel_handler = create_mousewheel_handler(canvas)
        linux_up_handler, linux_down_handler = create_linux_mousewheel_handlers(canvas)

        # 포커스 및 마우스 이벤트 관리
        def on_canvas_click(event: tk.Event) -> None:
            """캔버스 클릭 시 포커스 설정"""
            canvas.focus_set()

        def on_canvas_focus(event: tk.Event) -> None:
            """마우스가 캔버스 영역에 들어올 때 포커스 설정"""
            canvas.focus_set()

        # 기본 이벤트 바인딩
        scrollable_frame.bind("<Configure>", configure_scroll_region)
        canvas.bind("<Configure>", configure_canvas_width)

        # 동적 크기 조정 이벤트 바인딩
        scrollable_frame.bind("<Map>", lambda e: on_content_change())
        scrollable_frame.bind("<Unmap>", lambda e: on_content_change())

        # 정적 마우스 휠 이벤트 바인딩 (항상 활성화)
        if sys.platform.startswith("win") or sys.platform == "darwin":
            canvas.bind("<MouseWheel>", mousewheel_handler)
        else:  # Linux
            canvas.bind("<Button-4>", linux_up_handler)
            canvas.bind("<Button-5>", linux_down_handler)

        # 포커스 이벤트 바인딩
        canvas.bind("<Enter>", on_canvas_focus)
        canvas.bind("<Button-1>", on_canvas_click)  # 클릭 시 포커스 설정

        # 외부에서 접근 가능한 마우스 휠 핸들러 저장 (TodoItemWidget에서 사용)
        canvas._mousewheel_handler = mousewheel_handler
        canvas._linux_up_handler = linux_up_handler
        canvas._linux_down_handler = linux_down_handler

        # 초기 Canvas 높이 조정
        canvas.after_idle(adjust_canvas_height)

        # 섹션별로 참조 저장
        if section_type == "pending":
            self.app.pending_canvas = canvas
            self.app.pending_scrollable_frame = scrollable_frame
        else:
            self.app.completed_canvas = canvas
            self.app.completed_scrollable_frame = scrollable_frame

        return canvas, scrollable_frame

    @safe_ui_operation()
    @log_method_call()
    def style_paned_window_sash(self) -> None:
        """PanedWindow 분할바 스타일링 (기존 _style_paned_window_sash 100% 재사용)"""
        colors = DARK_COLORS

        # 분할바 색상 설정
        self.app.sections_paned_window.configure(
            sashcursor="sb_v_double_arrow",  # 세로 리사이즈 커서
            bg=colors["border"],  # 분할바 기본 색상
            relief=tk.FLAT,
        )

        # 분할바 호버 효과를 위한 바인딩 (기존 Configure 이벤트)
        self.app.sections_paned_window.bind("<Configure>", self.handle_paned_window_configure)

        # 분할바 드래그 실시간 감지를 위한 마우스 이벤트 바인딩 (DRY 원칙: widgets.py 패턴 재사용)
        self.app.sections_paned_window.bind("<Button-1>", self.handle_sash_drag_start)
        self.app.sections_paned_window.bind("<B1-Motion>", self.handle_sash_drag_motion)
        self.app.sections_paned_window.bind("<ButtonRelease-1>", self.handle_sash_drag_end)

    @safe_ui_operation()
    @log_method_call()
    def set_initial_pane_ratio(self) -> None:
        """초기 분할 비율 설정 (기존 _set_initial_pane_ratio 100% 재사용)"""
        self.logger.debug("초기 분할 비율 설정 시작")
        print(f"[DEBUG] set_initial_pane_ratio 호출됨")

        # 창 높이 계산
        total_height = self.app.sections_paned_window.winfo_height()
        if total_height < 50:  # 아직 레이아웃이 완료되지 않았으면 처리 안함
            print(f"[DEBUG] PanedWindow 크기가 너무 작음 ({total_height}px) - 처리 건너뛰기")
            return

        # 저장된 분할 비율 불러오기 (기본값: 0.7)
        settings_manager = self.app.get_manager("settings")
        if not settings_manager:
            self.logger.warning("SettingsManager를 찾을 수 없음")
            return

        saved_ratio = settings_manager.load_pane_ratio()

        # sash Y 위치 계산 (DRY 원칙: 명확한 변수명 사용)
        sash_y_position = int(total_height * saved_ratio)

        # 상세 디버깅 정보 출력
        self.logger.debug(f"분할바 위치 계산: total_height={total_height}, saved_ratio={saved_ratio:.4f}, sash_y={sash_y_position}")
        print(f"[DEBUG] 분할바 위치 적용: 전체높이={total_height}px, 비율={saved_ratio:.1%}, Y위치={sash_y_position}px")

        # sash 위치 설정 (올바른 파라미터 순서: index, x, y)
        self.app.sections_paned_window.sash_place(0, 0, sash_y_position)

        # 적용 결과 검증
        try:
            actual_sash_coord = self.app.sections_paned_window.sash_coord(0)
            print(f"[DEBUG] 적용 후 실제 sash 좌표: {actual_sash_coord}")
            if actual_sash_coord and abs(actual_sash_coord[1] - sash_y_position) > 10:
                print(f"[WARNING] sash 위치 불일치: 요청={sash_y_position}, 실제={actual_sash_coord[1]}")
            else:
                print(f"[SUCCESS] 분할바 위치 정상 적용됨")
        except Exception as verify_error:
            print(f"[WARNING] sash 위치 검증 실패: {verify_error}")

    @safe_ui_operation()
    def handle_paned_window_configure(self, event: tk.Event) -> None:
        """PanedWindow 구조 변경 시 처리 (기존 _on_paned_window_configure 100% 재사용)

        Args:
            event: Tkinter 이벤트 객체
        """
        # 기존 타이머가 있으면 안전하게 취소 (DRY 원칙: 안전한 after_cancel)
        if hasattr(self.app, "_save_timer") and self.app._save_timer is not None:
            try:
                self.app.root.after_cancel(self.app._save_timer)
            except (tk.TclError, ValueError):
                # 이미 취소되었거나 유효하지 않은 타이머 ID인 경우 무시
                pass

        # 1초 후 설정 저장 (디바운싱)
        self.app._save_timer = self.app.root.after(1000, self.save_ui_settings_debounced)

    @safe_ui_operation()
    def save_ui_settings_debounced(self) -> None:
        """디바운싱된 UI 설정 저장 (기존 _save_ui_settings_debounced 100% 재사용)"""
        settings_manager = self.app.get_manager("settings")
        if settings_manager:
            settings_manager.save_all_ui_settings()
            self.logger.debug("분할바 조절 후 설정 저장 완료")
        else:
            self.logger.warning("SettingsManager를 찾을 수 없어 설정 저장 실패")

    # 새로운 분할바 드래그 실시간 감지 메서드들 (DRY 원칙: widgets.py 패턴 재사용)
    @safe_ui_operation()
    def handle_sash_drag_start(self, event: tk.Event) -> None:
        """분할바 드래그 시작 처리 (DRY 원칙: widgets.py의 _start_drag 패턴 재사용)

        Args:
            event: 마우스 클릭 이벤트 (Button-1)
        """
        try:
            # 분할바 영역에서 클릭이 발생했는지 확인
            widget_under_cursor = event.widget.winfo_containing(event.x_root, event.y_root)
            if widget_under_cursor == self.app.sections_paned_window:
                # 드래그 시작 상태 저장
                self.app._sash_dragging = True
                self.app._drag_start_time = tk._default_root.tk.call('clock', 'milliseconds')
                print(f"[DEBUG] 분할바 드래그 시작: 마우스 좌표=({event.x}, {event.y})")
        except Exception as e:
            self.logger.debug(f"분할바 드래그 시작 처리 실패: {e}")

    @safe_ui_operation()
    def handle_sash_drag_motion(self, event: tk.Event) -> None:
        """분할바 드래그 중 처리 (DRY 원칙: widgets.py의 _drag_motion 패턴 재사용)

        Args:
            event: 마우스 이동 이벤트 (B1-Motion)
        """
        try:
            # 드래그 상태 확인
            if hasattr(self.app, '_sash_dragging') and self.app._sash_dragging:
                # 실시간 위치 업데이트 (너무 빈번하지 않게 throttling)
                current_time = tk._default_root.tk.call('clock', 'milliseconds')
                last_update = getattr(self.app, '_last_sash_update', 0)

                if current_time - last_update > 100:  # 100ms 간격으로 업데이트
                    self.app._last_sash_update = current_time
                    # 현재 분할바 위치 확인
                    try:
                        total_height = self.app.sections_paned_window.winfo_height()
                        sash_coord = self.app.sections_paned_window.sash_coord(0)
                        if sash_coord and total_height > 50:
                            current_ratio = sash_coord[1] / total_height
                            print(f"[DEBUG] 분할바 드래그 중: 비율={current_ratio:.3f}")
                    except Exception:
                        pass  # 드래그 중 에러는 무시
        except Exception as e:
            self.logger.debug(f"분할바 드래그 중 처리 실패: {e}")

    @safe_ui_operation()
    def handle_sash_drag_end(self, event: tk.Event) -> None:
        """분할바 드래그 종료 처리 (DRY 원칙: widgets.py의 _end_drag 패턴 재사용)

        Args:
            event: 마우스 릴리즈 이벤트 (ButtonRelease-1)
        """
        try:
            # 드래그 상태 확인
            if hasattr(self.app, '_sash_dragging') and self.app._sash_dragging:
                self.app._sash_dragging = False

                # 드래그 완료 후 즉시 설정 저장 (실시간 저장)
                print(f"[DEBUG] 분할바 드래그 완료 - 즉시 설정 저장")
                settings_manager = self.app.get_manager("settings")
                if settings_manager:
                    # 기존 타이머 취소
                    if hasattr(self.app, "_save_timer") and self.app._save_timer is not None:
                        try:
                            self.app.root.after_cancel(self.app._save_timer)
                        except (tk.TclError, ValueError):
                            pass

                    # 즉시 저장 (디바운싱 없이)
                    settings_manager.save_all_ui_settings()
                    print(f"[DEBUG] 분할바 드래그 종료 후 설정 즉시 저장 완료")
                else:
                    self.logger.warning("SettingsManager를 찾을 수 없어 설정 저장 실패")

        except Exception as e:
            self.logger.debug(f"분할바 드래그 종료 처리 실패: {e}")
            # 에러 시에도 드래그 상태는 해제
            if hasattr(self.app, '_sash_dragging'):
                self.app._sash_dragging = False
