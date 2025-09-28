"""
Manager 인터페이스 정의 모듈 (DRY+CLEAN+Simple 원칙 적용)

각 Manager의 인터페이스를 명확히 정의하여 타입 안정성과 확장성을 확보합니다.
"""

import tkinter as tk
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class IManagerContainer(ABC):
    """Manager들이 다른 Manager에 접근하기 위한 컨테이너 인터페이스"""

    @abstractmethod
    def get_manager(self, manager_type: str) -> Any:
        """Manager 타입에 따라 해당 Manager 인스턴스 반환

        Args:
            manager_type: Manager 타입 ('ui_layout', 'control_panel', 'todo_display', 'event_handler', 'settings')

        Returns:
            해당 Manager 인스턴스
        """
        pass


class IUILayoutManager(ABC):
    """UI 레이아웃 관리 인터페이스"""

    @abstractmethod
    def setup_window(self, root: tk.Tk) -> None:
        """메인 윈도우 설정

        Args:
            root: Tkinter 루트 윈도우
        """
        pass

    @abstractmethod
    def setup_main_layout(self, parent: tk.Widget) -> None:
        """메인 레이아웃 설정

        Args:
            parent: 부모 위젯
        """
        pass

    @abstractmethod
    def setup_sections(self, parent: tk.Widget) -> None:
        """섹션 레이아웃 설정

        Args:
            parent: 부모 위젯
        """
        pass


class IControlPanelManager(ABC):
    """제어 패널 관리 인터페이스"""

    @abstractmethod
    def setup_control_panel(self, parent: tk.Widget) -> None:
        """제어 패널 설정

        Args:
            parent: 부모 위젯
        """
        pass

    @abstractmethod
    def setup_status_bar(self, parent: tk.Widget) -> None:
        """상태바 설정

        Args:
            parent: 부모 위젯
        """
        pass

    @abstractmethod
    def update_status(self, message: str = None) -> None:
        """상태 메시지 업데이트

        Args:
            message: 업데이트할 메시지 (None이면 기본 상태 정보)
        """
        pass

    @abstractmethod
    def set_entry_placeholder(self) -> None:
        """입력 필드 플레이스홀더 설정"""
        pass

    @abstractmethod
    def handle_entry_focus(self, event_type: str) -> None:
        """입력 필드 포커스 처리

        Args:
            event_type: 이벤트 타입 ('in' 또는 'out')
        """
        pass


class ITodoDisplayManager(ABC):
    """TODO 표시 관리 인터페이스"""

    @abstractmethod
    def load_todos(self) -> None:
        """TODO 목록 로드 및 표시"""
        pass

    @abstractmethod
    def create_todo_widget(self, todo_data: Dict[str, Any], section: str = None) -> Any:
        """TODO 위젯 생성

        Args:
            todo_data: TODO 데이터 딕셔너리
            section: 섹션 타입 ('pending' 또는 'completed')

        Returns:
            생성된 TodoItemWidget 인스턴스
        """
        pass

    @abstractmethod
    def refresh_display(self) -> None:
        """전체 디스플레이 새로고침"""
        pass

    @abstractmethod
    def update_section_titles(self) -> None:
        """섹션 제목 업데이트"""
        pass

    @abstractmethod
    def move_todo_between_sections(self, todo_id: str, completed: bool) -> None:
        """TODO를 섹션 간에 이동

        Args:
            todo_id: TODO ID
            completed: 완료 여부
        """
        pass


class IEventHandler(ABC):
    """이벤트 처리 인터페이스"""

    @abstractmethod
    def show_add_todo_dialog(self) -> None:
        """할일 추가 다이얼로그 표시"""
        pass

    @abstractmethod
    def create_todo_with_date(self, text: str, due_date: Optional[str]) -> Optional[Dict[str, Any]]:
        """날짜가 포함된 TODO 생성

        Args:
            text: TODO 텍스트
            due_date: 마감일 (선택사항)

        Returns:
            생성된 TODO 데이터 또는 None
        """
        pass

    @abstractmethod
    def handle_sort_change(self, option_key: str) -> None:
        """정렬 옵션 변경 처리

        Args:
            option_key: 정렬 옵션 키
        """
        pass

    @abstractmethod
    def update_todo(self, todo_id: str, **kwargs) -> None:
        """TODO 업데이트

        Args:
            todo_id: TODO ID
            **kwargs: 업데이트할 속성들
        """
        pass

    @abstractmethod
    def delete_todo(self, todo_id: str) -> None:
        """TODO 삭제

        Args:
            todo_id: 삭제할 TODO ID
        """
        pass

    @abstractmethod
    def reorder_todo(self, todo_id: str, move_steps: int) -> None:
        """TODO 순서 변경

        Args:
            todo_id: TODO ID
            move_steps: 이동할 스텝 수
        """
        pass

    @abstractmethod
    def clear_completed_todos(self) -> None:
        """완료된 항목들 정리"""
        pass

    @abstractmethod
    def toggle_always_on_top(self) -> None:
        """항상 위 토글"""
        pass

    @abstractmethod
    def show_about_dialog(self) -> None:
        """정보 대화상자 표시"""
        pass

    @abstractmethod
    def open_website(self) -> None:
        """웹사이트 열기"""
        pass

    @abstractmethod
    def handle_window_closing(self) -> None:
        """창 닫기 이벤트 처리"""
        pass


class ISettingsManager(ABC):
    """설정 관리 인터페이스"""

    @abstractmethod
    def save_setting(self, key: str, value: Any) -> bool:
        """제네릭 설정 저장

        Args:
            key: 설정 키
            value: 설정 값

        Returns:
            저장 성공 여부
        """
        pass

    @abstractmethod
    def load_setting(self, key: str, default: Any = None) -> Any:
        """제네릭 설정 로드

        Args:
            key: 설정 키
            default: 기본값

        Returns:
            설정 값
        """
        pass

    @abstractmethod
    def save_all_ui_settings(self) -> None:
        """모든 UI 설정을 통합 저장"""
        pass

    @abstractmethod
    def save_pane_ratio(self) -> None:
        """현재 분할 비율을 사용자 설정에 저장"""
        pass

    @abstractmethod
    def load_sort_settings(self) -> None:
        """저장된 정렬 설정을 불러와서 SortManager에 적용"""
        pass

    @abstractmethod
    def load_pane_ratio(self) -> float:
        """저장된 분할 비율을 불러오기

        Returns:
            분할 비율 (0.1 ~ 0.9)
        """
        pass

    @abstractmethod
    def get_config_file_path(self) -> str:
        """설정 파일 경로 반환

        Returns:
            설정 파일 절대 경로
        """
        pass
