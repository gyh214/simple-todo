# -*- coding: utf-8 -*-
"""TodoItemWidget - TODO 아이템 위젯

Phase 5-2: TODO 아이템 위젯 구현
docs/todo-app-ui.html의 .todo-item 구조를 정확히 재현합니다.
"""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QCheckBox, QPushButton, QGraphicsOpacityEffect
from PyQt6.QtCore import Qt, pyqtSignal, QEvent
from PyQt6.QtGui import QMouseEvent

import config
from ...domain.entities.todo import Todo
from ...domain.value_objects.due_date import DueDateStatus
from .rich_text_widget import RichTextWidget
from .mixins.draggable_mixin import DraggableMixin


class TodoItemWidget(QWidget, DraggableMixin):
    """TODO 아이템 위젯

    UI 구조:
    - 드래그 핸들 (☰)
    - 체크박스 (커스텀 스타일)
    - TODO 내용 영역:
      - TODO 텍스트
      - 납기일 배지 (선택적)
    - 삭제 버튼 (호버 시 표시)

    Signals:
        delete_requested(str): 삭제 요청 (todo_id)
        check_toggled(str, bool): 체크박스 토글 (todo_id, completed)
        edit_requested(str): 편집 요청 (todo_id)
    """

    # 시그널 정의
    delete_requested = pyqtSignal(str)
    check_toggled = pyqtSignal(str, bool)
    edit_requested = pyqtSignal(str)

    def __init__(self, todo: Todo, parent=None):
        """TodoItemWidget 초기화

        Args:
            todo: Todo Entity
            parent: 부모 위젯
        """
        super().__init__(parent)
        self.todo = todo
        self._is_hovered = False

        # DraggableMixin 초기화
        self.setup_draggable()

        self.setup_ui()
        self.apply_styles()
        self.connect_signals()

    def setup_ui(self) -> None:
        """UI 요소 생성 및 배치"""
        # 메인 레이아웃 (수평)
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(*config.LAYOUT_MARGINS['todo_item'])
        main_layout.setSpacing(config.LAYOUT_SPACING['todo_item_main'])
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)  # HTML align-items: flex-start

        # 1. 드래그 핸들
        self.drag_handle = QLabel("☰")
        self.drag_handle.setObjectName("dragHandle")
        self.drag_handle.setFixedWidth(config.WIDGET_SIZES['drag_handle_width'])
        self.drag_handle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.drag_handle)

        # 2. 체크박스
        self.checkbox = QCheckBox()
        self.checkbox.setObjectName("todoCheckbox")
        self.checkbox.setChecked(self.todo.completed)
        self.checkbox.setFixedSize(*config.WIDGET_SIZES['checkbox_size'])
        main_layout.addWidget(self.checkbox)

        # 3. TODO 콘텐츠 영역 (텍스트 + 메타)
        content_layout = QVBoxLayout()
        content_layout.setSpacing(config.LAYOUT_SPACING['todo_item_content'])
        content_layout.setContentsMargins(0, 0, 0, 0)

        # TODO 텍스트 (RichTextWidget 사용 - 링크/경로 인식)
        self.todo_text = RichTextWidget(str(self.todo.content))
        self.todo_text.setObjectName("todoText")
        if self.todo.completed:
            self.todo_text.setProperty("completed", "true")
        content_layout.addWidget(self.todo_text)

        # TODO 메타 정보 (납기일 배지)
        if self.todo.due_date:
            self.date_badge = self._create_date_badge()
            content_layout.addWidget(self.date_badge)
        else:
            self.date_badge = None

        main_layout.addLayout(content_layout, 1)  # stretch factor = 1

        # 4. 삭제 버튼 (레이아웃에 포함)
        self.delete_btn = QPushButton("✕")
        self.delete_btn.setObjectName("deleteBtn")
        self.delete_btn.setFixedSize(*config.WIDGET_SIZES['delete_btn_size'])

        # Opacity 효과 설정 (초기 숨김)
        self.delete_btn_opacity = QGraphicsOpacityEffect()
        self.delete_btn_opacity.setOpacity(config.OPACITY_VALUES['hidden'])
        self.delete_btn.setGraphicsEffect(self.delete_btn_opacity)

        # 레이아웃에 추가
        main_layout.addWidget(self.delete_btn)

        # 위젯 자체 설정
        self.setObjectName("todoItem")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        # QSS 배경 렌더링 강제 (setAutoFillBackground 대신 사용)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground)

    def _create_date_badge(self) -> QLabel:
        """납기일 배지 생성

        Returns:
            QLabel: 날짜 배지 위젯
        """
        badge = QLabel()
        badge.setObjectName("dateBadge")

        # 날짜 텍스트 및 상태 설정
        text, status = self._format_due_date_text()
        badge.setText(text)
        badge.setProperty("status", status)

        return badge

    def _format_due_date_text(self) -> tuple[str, str]:
        """납기일 텍스트와 상태 반환

        Returns:
            tuple: (표시 텍스트, 상태)
            예: ("2일 남음", "upcoming"), ("오늘", "today")
        """
        if not self.todo.due_date:
            return ("", "normal")

        # DueDate Value Object 메서드 활용
        status = self.todo.due_date.calculate_status()
        text = self.todo.due_date.format_display_text()

        return (text, status)


    def apply_styles(self) -> None:
        """QSS 스타일 적용 (프로토타입 정확히 재현)"""

        # 기본 스타일 - config에서 가져오기 (DRY 원칙)
        bg_color = config.COLORS['card']
        border_color = config.COLORS['border_strong']
        drag_handle_color = config.COLORS['text_disabled']

        # 완료 상태에 따른 텍스트 스타일
        text_decoration = "line-through" if self.todo.completed else "none"
        text_color = config.COLORS['text_disabled'] if self.todo.completed else config.COLORS['text_primary']

        style_sheet = f"""
        QWidget#todoItem {{
            background: {bg_color};
            border: {config.UI_METRICS['border_width']['thin']}px solid {border_color};
            border-radius: {config.UI_METRICS['border_radius']['lg']}px;
        }}

        QWidget#todoItem:hover {{
            background: {config.COLORS['card_hover']};
            border-color: {config.COLORS['accent']};
        }}

        QLabel#dragHandle {{
            color: {drag_handle_color};
            font-size: {config.FONT_SIZES['lg']}px;
        }}

        QCheckBox#todoCheckbox {{
            width: {config.WIDGET_SIZES['checkbox_size'][0]}px;
            height: {config.WIDGET_SIZES['checkbox_size'][1]}px;
            border: {config.UI_METRICS['border_width']['medium']}px solid {config.COLORS['border']};
            border-radius: {config.UI_METRICS['border_radius']['sm']}px;
            background: transparent;
        }}

        QCheckBox#todoCheckbox:hover {{
            border-color: {config.COLORS['accent']};
        }}

        QCheckBox#todoCheckbox:checked {{
            background: {config.COLORS['accent']};
            border-color: {config.COLORS['accent']};
        }}

        QCheckBox#todoCheckbox::indicator {{
            width: {config.WIDGET_SIZES['checkbox_size'][0] - 4}px;
            height: {config.WIDGET_SIZES['checkbox_size'][1] - 4}px;
        }}

        QCheckBox#todoCheckbox::indicator:checked {{
            image: none;
        }}

        QLabel#todoText {{
            color: {text_color};
            font-size: {config.FONT_SIZES['base']}px;
            line-height: 1.4;
            text-decoration: {text_decoration};
        }}

        QPushButton#deleteBtn {{
            background: transparent;
            border: none;
            color: {config.COLORS['text_disabled']};
            font-size: {config.FONT_SIZES['lg']}px;
            padding: {config.UI_METRICS['padding']['sm'][0]}px {config.UI_METRICS['padding']['sm'][1]}px;
            border-radius: {config.UI_METRICS['border_radius']['sm']}px;
        }}

        QPushButton#deleteBtn:hover {{
            background: rgba(244, 67, 54, 0.15);
            color: #ef5350;
        }}

        QLabel#dateBadge {{
            font-size: {config.FONT_SIZES['sm']}px;
            padding: {config.UI_METRICS['padding']['sm'][0]}px {config.UI_METRICS['padding']['sm'][1]}px;
            border-radius: {config.UI_METRICS['border_radius']['sm']}px;
            font-weight: 500;
        }}

        QLabel#dateBadge[status="overdue_severe"] {{
            background: {config.DUE_DATE_COLORS['overdue_severe']['bg']};
            color: {config.DUE_DATE_COLORS['overdue_severe']['color']};
        }}

        QLabel#dateBadge[status="overdue_moderate"] {{
            background: {config.DUE_DATE_COLORS['overdue_moderate']['bg']};
            color: {config.DUE_DATE_COLORS['overdue_moderate']['color']};
        }}

        QLabel#dateBadge[status="overdue_mild"] {{
            background: {config.DUE_DATE_COLORS['overdue_mild']['bg']};
            color: {config.DUE_DATE_COLORS['overdue_mild']['color']};
        }}

        QLabel#dateBadge[status="today"] {{
            background: {config.DUE_DATE_COLORS['today']['bg']};
            color: {config.DUE_DATE_COLORS['today']['color']};
        }}

        QLabel#dateBadge[status="upcoming"] {{
            background: {config.DUE_DATE_COLORS['upcoming']['bg']};
            color: {config.DUE_DATE_COLORS['upcoming']['color']};
        }}

        QLabel#dateBadge[status="normal"] {{
            background: {config.DUE_DATE_COLORS['normal']['bg']};
            color: {config.DUE_DATE_COLORS['normal']['color']};
        }}
        """

        self.setStyleSheet(style_sheet)

        # 완료 상태면 개별 요소에만 opacity 효과 적용 (X버튼 제외)
        if self.todo.completed:
            # 드래그 핸들에 opacity 적용
            handle_opacity = QGraphicsOpacityEffect()
            handle_opacity.setOpacity(config.OPACITY_VALUES['completed_item'])
            self.drag_handle.setGraphicsEffect(handle_opacity)

            # 체크박스에 opacity 적용
            checkbox_opacity = QGraphicsOpacityEffect()
            checkbox_opacity.setOpacity(config.OPACITY_VALUES['completed_item'])
            self.checkbox.setGraphicsEffect(checkbox_opacity)

            # TODO 텍스트에 opacity 적용
            text_opacity = QGraphicsOpacityEffect()
            text_opacity.setOpacity(config.OPACITY_VALUES['completed_item'])
            self.todo_text.setGraphicsEffect(text_opacity)

            # 날짜 배지에 opacity 적용 (있는 경우)
            if self.date_badge:
                badge_opacity = QGraphicsOpacityEffect()
                badge_opacity.setOpacity(config.OPACITY_VALUES['completed_item'])
                self.date_badge.setGraphicsEffect(badge_opacity)
        else:
            # 완료 해제 시 opacity 효과 제거
            self.drag_handle.setGraphicsEffect(None)
            self.checkbox.setGraphicsEffect(None)
            self.todo_text.setGraphicsEffect(None)
            if self.date_badge:
                self.date_badge.setGraphicsEffect(None)

    def connect_signals(self) -> None:
        """이벤트 시그널 연결"""
        # 체크박스 클릭
        self.checkbox.checkStateChanged.connect(self._on_checkbox_toggled)

        # 삭제 버튼 클릭
        self.delete_btn.clicked.connect(self._on_delete_clicked)

    def _on_checkbox_toggled(self, state: Qt.CheckState) -> None:
        """체크박스 토글 이벤트 핸들러

        Args:
            state: 체크박스 상태
        """
        completed = (state == Qt.CheckState.Checked)
        self.check_toggled.emit(str(self.todo.id), completed)

        # UI 업데이트
        self.todo.completed = completed
        self._update_completion_style()

    def _on_delete_clicked(self) -> None:
        """삭제 버튼 클릭 이벤트 핸들러"""
        self.delete_requested.emit(str(self.todo.id))

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        """더블클릭 이벤트 핸들러 (편집 요청)

        Args:
            event: 마우스 이벤트
        """
        if event.button() == Qt.MouseButton.LeftButton:
            self.edit_requested.emit(str(self.todo.id))
        super().mouseDoubleClickEvent(event)

    def enterEvent(self, event) -> None:
        """마우스 진입 이벤트 (호버 효과)

        Args:
            event: 이벤트 객체
        """
        self._is_hovered = True
        # Opacity로 부드럽게 표시
        self.delete_btn_opacity.setOpacity(config.OPACITY_VALUES['visible'])
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        """마우스 이탈 이벤트 (호버 효과 해제)

        Args:
            event: 이벤트 객체
        """
        self._is_hovered = False
        # Opacity로 부드럽게 숨김
        self.delete_btn_opacity.setOpacity(config.OPACITY_VALUES['hidden'])
        super().leaveEvent(event)

    def _update_completion_style(self) -> None:
        """완료 상태에 따른 스타일 업데이트"""
        if self.todo.completed:
            self.todo_text.setProperty("completed", "true")
        else:
            self.todo_text.setProperty("completed", "false")

        # 스타일 재적용
        self.apply_styles()
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

    def get_drag_data(self) -> str:
        """드래그할 데이터 반환 (DraggableMixin 요구 메서드)

        Returns:
            str: TODO ID
        """
        return str(self.todo.id)

    def get_widget_styles(self) -> str:
        """현재 위젯 스타일 반환 (DraggableMixin 요구 메서드)

        Returns:
            str: 현재 위젯 스타일 시트
        """
        return self.styleSheet()

    def update_todo(self, todo: Todo) -> None:
        """TODO 데이터 업데이트

        Args:
            todo: 새로운 Todo Entity
        """
        self.todo = todo

        # UI 업데이트
        self.todo_text.update_text(str(self.todo.content))
        self.checkbox.setChecked(self.todo.completed)

        # 날짜 배지 업데이트
        if self.todo.due_date:
            if self.date_badge:
                text, status = self._format_due_date_text()
                self.date_badge.setText(text)
                self.date_badge.setProperty("status", status)
            else:
                # 날짜 배지가 없었는데 추가된 경우
                self.date_badge = self._create_date_badge()
                # TODO: 레이아웃에 추가 필요
        else:
            if self.date_badge:
                # 날짜 배지가 있었는데 제거된 경우
                self.date_badge.setVisible(False)

        self.apply_styles()
