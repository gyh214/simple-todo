"""
TODO Panel 메인 애플리케이션 모듈 (섹션 분할 및 새로운 기능 포함)
"""

import tkinter as tk
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

# Phase 4A: 새로운 인터페이스 및 유틸리티 import
from .interfaces.manager_interfaces import IManagerContainer
from .utils.constants import DARK_COLORS, MANAGER_TYPES

# 안전한 import 처리 (Manager들이 의존성 처리)
try:
    from .widgets import StandardTodoDisplay, TodoItemWidget
except ImportError:
    # Manager들에서 처리하므로 최소 fallback만 유지
    TodoItemWidget = StandardTodoDisplay = None

try:
    from .sort_manager import SortManager
except ImportError:
    SortManager = None

# CLEAN 아키텍처 인터페이스 (하위 호환성)
try:
    from interfaces import INotificationService, ITodoService
except ImportError:
    ITodoService = INotificationService = None

from .managers.control_panel_manager import ControlPanelManager
from .managers.event_handler import EventHandler
from .managers.settings_manager import SettingsManager
from .managers.todo_display_manager import TodoDisplayManager

# Manager imports (Phase 2에서 생성된 핵심 컴포넌트들)
from .managers.ui_layout_manager import UILayoutManager


class TodoPanelApp(IManagerContainer):
    """메인 TODO 패널 애플리케이션 (Phase 4A: IManagerContainer 구현)"""

    def __init__(
        self,
        # 기존 CLEAN 아키텍처 서비스들 (하위 호환성 유지)
        root=None,
        todo_service=None,
        notification_service=None,
        # 새로운 Manager 의존성들 (Phase 3 추가)
        ui_layout_manager=None,
        control_panel_manager=None,
        todo_display_manager=None,
        event_handler=None,
        settings_manager=None,
    ):

        # 1. 기본 속성 초기화
        self.root = root or tk.Tk()

        # 2. 기존 서비스 vs 매니저 이중 지원 (CLEAN 아키텍처 유지)
        self._initialize_services(todo_service, notification_service)

        # 3. Manager 의존성 주입 또는 기본 인스턴스 생성
        self._initialize_managers(
            ui_layout_manager,
            control_panel_manager,
            todo_display_manager,
            event_handler,
            settings_manager,
        )

        # 4. Manager들 간 상호 참조 설정
        self._wire_managers()

        # 5. UI 초기화 (Manager들에게 위임)
        self._setup_application()

    def _initialize_services(self, todo_service, notification_service):
        """기존 CLEAN 아키텍처 서비스 초기화 (하위 호환성)"""
        if todo_service is not None:
            # CLEAN 아키텍처 서비스 사용
            self.todo_service = todo_service
            self.notification_service = notification_service
            self.todo_manager = None  # 서비스 패턴 사용시 직접 manager 사용 안함
        else:
            # 기존 TodoManager 초기화 (하위 호환성)
            try:
                from todo_manager import UnifiedTodoManager as TodoManager

                self.todo_manager = TodoManager(debug=True, batch_save=True)
            except (ImportError, TypeError):
                # batch_save 파라미터가 없는 기본 TodoManager의 경우
                self.todo_manager = TodoManager(debug=True)
            self.todo_service = None
            self.notification_service = None

    def _initialize_managers(
        self,
        ui_layout_manager,
        control_panel_manager,
        todo_display_manager,
        event_handler,
        settings_manager,
    ):
        """Manager 인스턴스 초기화 또는 주입받기"""
        # 정렬 관리자 (기존 유지)
        self.sort_manager = SortManager()

        # UI 상태 (기존 유지)
        self.todo_widgets: Dict[str, TodoItemWidget] = {}
        self.always_on_top = False
        self.pending_widgets: Dict[str, TodoItemWidget] = {}
        self.completed_widgets: Dict[str, TodoItemWidget] = {}
        self._save_timer = None  # UILayoutManager에서 사용하는 타이머

        # Manager 의존성 주입 또는 기본 인스턴스 생성
        self.ui_layout_manager = ui_layout_manager or UILayoutManager(self)
        self.control_panel_manager = control_panel_manager or ControlPanelManager(self)
        self.todo_display_manager = todo_display_manager or TodoDisplayManager(self)
        self.event_handler = event_handler or EventHandler(self)
        self.settings_manager = settings_manager or SettingsManager(self)

    def _wire_managers(self):
        """Manager들 간 필요한 참조 설정"""
        # 필요한 경우 Manager들 간 상호 참조 설정
        # 현재는 app_instance를 통해 참조하므로 추가 작업 불필요
        pass

    def get_manager(self, manager_type: str) -> Any:
        """Phase 4A: IManagerContainer 인터페이스 구현 - Manager 컨테이너 패턴

        Args:
            manager_type: Manager 타입 ('ui_layout', 'control_panel', 'todo_display', 'event_handler', 'settings')

        Returns:
            해당 Manager 인스턴스

        Raises:
            ValueError: 알 수 없는 manager_type인 경우
        """
        manager_map = {
            MANAGER_TYPES["ui_layout"]: self.ui_layout_manager,
            MANAGER_TYPES["control_panel"]: self.control_panel_manager,
            MANAGER_TYPES["todo_display"]: self.todo_display_manager,
            MANAGER_TYPES["event_handler"]: self.event_handler,
            MANAGER_TYPES["settings"]: self.settings_manager,
        }

        if manager_type not in manager_map:
            available_types = list(manager_map.keys())
            raise ValueError(
                f"알 수 없는 manager_type '{manager_type}'. 사용 가능한 타입: {available_types}"
            )

        return manager_map[manager_type]

    def _setup_application(self):
        """Manager들에게 설정 작업 위임"""
        # UI 설정을 UILayoutManager로 위임
        self.ui_layout_manager.setup_window(self.root)
        self.ui_layout_manager.setup_main_layout(self.root)

        # 설정 및 데이터 로드
        self.settings_manager.load_sort_settings()
        self.todo_display_manager.load_todos()

        # 이벤트 처리 설정
        self.root.protocol("WM_DELETE_WINDOW", self.event_handler.handle_window_closing)

        # 분할바 초기 비율 설정 (안전한 위치에서 다시 시도)
        self.root.after(200, self._ensure_pane_ratio_applied)

    def show_add_todo_dialog(self) -> None:
        """Manager 위임: 할일 추가 다이얼로그 표시"""
        return self.event_handler.show_add_todo_dialog()

    def create_todo_with_date(self, text: str, due_date: str) -> None:
        """Manager 위임: 날짜가 포함된 TODO 생성"""
        return self.event_handler.create_todo_with_date(text, due_date)

    def handle_sort_change(self, option_key: str) -> None:
        """Manager 위임: 정렬 옵션 변경 처리"""
        return self.event_handler.handle_sort_change(option_key)

    def update_todo(self, todo_id: str, **kwargs) -> None:
        """Manager 위임: TODO 업데이트"""
        return self.event_handler.update_todo(todo_id, **kwargs)

    def delete_todo(self, todo_id: str) -> None:
        """Manager 위임: TODO 삭제"""
        return self.event_handler.delete_todo(todo_id)

    def reorder_todo(self, todo_id: str, move_steps: int) -> None:
        """Manager 위임: TODO 순서 변경"""
        return self.event_handler.reorder_todo(todo_id, move_steps)

    def clear_completed_todos(self) -> None:
        """Manager 위임: 완료된 항목들 정리"""
        return self.event_handler.clear_completed_todos()

    def toggle_always_on_top(self) -> None:
        """Manager 위임: 항상 위 토글"""
        return self.event_handler.toggle_always_on_top()

    def show_about_dialog(self) -> None:
        """Manager 위임: 정보 대화상자 표시"""
        return self.event_handler.show_about_dialog()

    def open_website(self) -> None:
        """Manager 위임: 웹사이트 열기"""
        return self.event_handler.open_website()

    def save_all_ui_settings(self) -> None:
        """Manager 위임: 모든 UI 설정 저장"""
        return self.settings_manager.save_all_ui_settings()

    def save_pane_ratio(self) -> None:
        """Manager 위임: 분할 비율 저장"""
        return self.settings_manager.save_pane_ratio()

    def load_sort_settings(self) -> None:
        """Manager 위임: 정렬 설정 로드"""
        return self.settings_manager.load_sort_settings()

    def get_config_file_path(self) -> str:
        """Manager 위임: 설정 파일 경로 반환"""
        return self.settings_manager.get_config_file_path()

    def load_pane_ratio(self) -> float:
        """Manager 위임: 분할 비율 로드"""
        return self.settings_manager.load_pane_ratio()

    def update_status(self, message: str = None) -> None:
        """Manager 위임: 상태바 업데이트"""
        return self.control_panel_manager.update_status(message)

    def handle_window_closing(self) -> None:
        """Manager 위임: 창 닫기 이벤트 처리"""
        return self.event_handler.handle_window_closing()

    # TodoDisplayManager 위임 메서드들
    def load_todos(self) -> None:
        """Manager 위임: TODO 목록 로드"""
        return self.todo_display_manager.load_todos()

    def create_todo_widget(self, todo_data: dict, section: str = None):
        """Manager 위임: TODO 위젯 생성"""
        return self.todo_display_manager.create_todo_widget(todo_data, section)

    def update_section_titles(self) -> None:
        """Manager 위임: 섹션 제목 업데이트"""
        return self.todo_display_manager.update_section_titles()

    def move_todo_between_sections(self, todo_id: str, completed: bool) -> None:
        """Manager 위임: TODO 섹션 간 이동"""
        return self.todo_display_manager.move_todo_between_sections(todo_id, completed)

    def _ensure_pane_ratio_applied(self) -> None:
        """DRY 원칙: 기존 UILayoutManager 메서드 재사용하여 분할바 비율 적용"""
        try:
            # UILayoutManager 존재 여부 확인
            if not (hasattr(self, 'ui_layout_manager') and self.ui_layout_manager):
                print("[WARNING] UILayoutManager를 찾을 수 없음 - 100ms 후 재시도")
                self.root.after(100, self._ensure_pane_ratio_applied)
                return

            # sections_paned_window 존재 여부 확인 (더 안전한 방식)
            sections_paned_window = getattr(self, 'sections_paned_window', None)
            if not sections_paned_window:
                print("[DEBUG] sections_paned_window 아직 생성되지 않음 - 100ms 후 재시도")
                self.root.after(100, self._ensure_pane_ratio_applied)
                return

            # PanedWindow가 실제로 사용 가능한 상태인지 확인
            try:
                # 윈도우 크기가 유효한지 확인
                total_height = sections_paned_window.winfo_height()
                if total_height < 50:
                    print(f"[DEBUG] PanedWindow 크기가 너무 작음 ({total_height}px) - 100ms 후 재시도")
                    self.root.after(100, self._ensure_pane_ratio_applied)
                    return
            except tk.TclError:
                print("[DEBUG] PanedWindow 아직 렌더링되지 않음 - 100ms 후 재시도")
                self.root.after(100, self._ensure_pane_ratio_applied)
                return

            # 기존 UILayoutManager 메서드 재사용 (DRY 원칙)
            self.ui_layout_manager.set_initial_pane_ratio()
            print("[DEBUG] 분할바 초기 비율 적용 완료")

        except Exception as e:
            print(f"[ERROR] 분할바 비율 적용 실패: {e}")
            # 오류 시에도 재시도 (최대 10번까지)
            retry_count = getattr(self, '_pane_ratio_retry_count', 0)
            if retry_count < 10:
                self._pane_ratio_retry_count = retry_count + 1
                self.root.after(200, self._ensure_pane_ratio_applied)
            else:
                print("[ERROR] 분할바 비율 적용 재시도 한계 도달, 포기")

    def run(self):
        """애플리케이션 실행"""
        # 창을 중앙에 배치
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

        # update_idletasks() 후 분할바 비율이 리셋되므로 다시 설정 (DRY 원칙)
        print("[DEBUG] run() 메서드에서 분할바 비율 재설정")
        self.root.after(100, self._ensure_pane_ratio_applied)

        # 메인 루프 시작
        self.root.mainloop()
