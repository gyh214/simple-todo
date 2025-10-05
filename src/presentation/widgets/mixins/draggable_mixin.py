# -*- coding: utf-8 -*-
"""DraggableMixin - 드래그앤드롭 기능 제공 Mixin

재사용 가능한 드래그앤드롭 기능을 제공하는 Mixin 클래스입니다.
"""

from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QMouseEvent, QDrag
from PyQt6.QtCore import QMimeData
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class DraggableMixin:
    """드래그앤드롭 기능을 제공하는 Mixin 클래스

    이 Mixin을 사용하려면:
    1. 클래스에 상속 추가: class MyWidget(QWidget, DraggableMixin)
    2. __init__에서 setup_draggable() 호출
    3. drag_handle 속성 설정 (QLabel 등)
    4. get_drag_data() 메서드 구현 (드래그할 데이터 반환)
    5. get_widget_styles() 메서드 구현 (스타일 복원용)

    사용 예시:
        class TodoItemWidget(QWidget, DraggableMixin):
            def __init__(self, todo: Todo, parent=None):
                super().__init__(parent)
                self.todo = todo

                # DraggableMixin 초기화
                self.setup_draggable()

                # UI 구성 (drag_handle 생성 포함)
                self.setup_ui()

            def get_drag_data(self) -> str:
                return str(self.todo.id)

            def get_widget_styles(self) -> str:
                return self.styleSheet()
    """

    def setup_draggable(self) -> None:
        """드래그 기능 초기화

        __init__에서 호출해야 합니다.
        """
        self._drag_start_position: Optional[QPoint] = None

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """마우스 프레스 이벤트 핸들러

        드래그 핸들을 클릭하면 드래그 시작 위치를 저장합니다.

        Args:
            event: 마우스 이벤트
        """
        if event.button() == Qt.MouseButton.LeftButton:
            if hasattr(self, 'drag_handle') and self._is_drag_handle_clicked(event.pos()):
                self._drag_start_position = event.pos()

        # Cooperative Multiple Inheritance: super()에 메서드가 있는지 확인 후 호출
        if hasattr(super(), 'mousePressEvent'):
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """마우스 이동 이벤트 핸들러

        드래그 핸들을 클릭한 상태로 이동하면 드래그를 시작합니다.

        Args:
            event: 마우스 이벤트
        """
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            # Cooperative Multiple Inheritance: super()에 메서드가 있는지 확인 후 호출
            if hasattr(super(), 'mouseMoveEvent'):
                super().mouseMoveEvent(event)
            return
        if self._drag_start_position is None:
            # Cooperative Multiple Inheritance: super()에 메서드가 있는지 확인 후 호출
            if hasattr(super(), 'mouseMoveEvent'):
                super().mouseMoveEvent(event)
            return

        # 최소 드래그 거리 확인 (의도하지 않은 드래그 방지)
        distance = (event.pos() - self._drag_start_position).manhattanLength()
        if distance < 5:
            # Cooperative Multiple Inheritance: super()에 메서드가 있는지 확인 후 호출
            if hasattr(super(), 'mouseMoveEvent'):
                super().mouseMoveEvent(event)
            return

        # 드래그 시작
        self._start_drag()

    def _is_drag_handle_clicked(self, pos: QPoint) -> bool:
        """드래그 핸들 영역이 클릭되었는지 확인

        Args:
            pos: 클릭 위치

        Returns:
            bool: 드래그 핸들 클릭 여부
        """
        if not hasattr(self, 'drag_handle'):
            logger.warning("drag_handle attribute not found")
            return False

        handle_rect = self.drag_handle.geometry()
        return handle_rect.contains(pos)

    def _start_drag(self) -> None:
        """드래그 시작

        QDrag 객체를 생성하고 드래그를 시작합니다.
        """
        # Mime Data 생성 (get_drag_data() 메서드 호출)
        drag_data = self.get_drag_data()
        if not drag_data:
            logger.warning("No drag data provided, canceling drag")
            return

        mime_data = QMimeData()
        mime_data.setText(drag_data)

        # QDrag 객체 생성
        drag = QDrag(self)
        drag.setMimeData(mime_data)

        # 드래그 시각적 피드백 (투명도 조정)
        current_style = self.get_widget_styles()
        self.setStyleSheet(current_style + """
            QWidget#todoItem {
                opacity: 0.5;
            }
        """)

        # 드래그 실행 (Move 모드)
        drop_action = drag.exec(Qt.DropAction.MoveAction)

        # 드래그 종료 후 원래 스타일로 복원
        self._drag_start_position = None
        self.apply_styles()

    def get_drag_data(self) -> str:
        """드래그할 데이터 반환

        서브클래스에서 반드시 구현해야 합니다.

        Returns:
            str: 드래그할 데이터 (예: TODO ID)

        Raises:
            NotImplementedError: 서브클래스에서 구현하지 않은 경우
        """
        raise NotImplementedError("Subclass must implement get_drag_data()")

    def get_widget_styles(self) -> str:
        """현재 위젯 스타일 반환

        서브클래스에서 반드시 구현해야 합니다.

        Returns:
            str: 현재 위젯 스타일 시트

        Raises:
            NotImplementedError: 서브클래스에서 구현하지 않은 경우
        """
        raise NotImplementedError("Subclass must implement get_widget_styles()")
