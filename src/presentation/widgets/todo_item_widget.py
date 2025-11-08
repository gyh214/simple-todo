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
from .subtask_widget import SubTaskWidget


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

    # 하위 할일 시그널
    subtask_toggled = pyqtSignal(object, object)  # parent_id, subtask_id
    subtask_edit_requested = pyqtSignal(object, object)
    subtask_delete_requested = pyqtSignal(object, object)

    def __init__(self, todo: Todo, parent=None):
        """TodoItemWidget 초기화

        Args:
            todo: Todo Entity
            parent: 부모 위젯
        """
        super().__init__(parent)
        self.todo = todo
        self._is_hovered = False
        self._subtasks_expanded = False  # 하위 할일 펼침 상태

        # DraggableMixin 초기화
        self.setup_draggable()

        self.setup_ui()
        self.apply_styles()
        self.connect_signals()

    def setup_ui(self) -> None:
        """UI 요소 생성 및 배치"""
        # 전체 레이아웃 (수직) - 메인 콘텐츠 + 하위 할일 컨테이너
        container_layout = QVBoxLayout(self)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # === 메인 TODO 위젯 ===
        main_widget = QWidget()
        main_widget.setObjectName("todoItemMain")
        main_widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground)

        # 메인 레이아웃 (수평)
        main_layout = QHBoxLayout(main_widget)
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

        # 첫 번째 행: TODO 텍스트 + 펼치기 버튼 + 날짜 배지
        first_row_layout = QHBoxLayout()
        first_row_layout.setSpacing(8)
        first_row_layout.setContentsMargins(0, 0, 0, 0)

        # TODO 텍스트 (RichTextWidget 사용 - 링크/경로 인식)
        self.todo_text = RichTextWidget(str(self.todo.content))
        self.todo_text.setObjectName("todoText")
        if self.todo.completed:
            self.todo_text.setProperty("completed", "true")
        first_row_layout.addWidget(self.todo_text, 1)  # stretch

        # 펼치기/접기 버튼 (하위 할일이 있을 때만 표시)
        self.expand_btn = QPushButton("▶")
        self.expand_btn.setObjectName("expandBtn")
        self.expand_btn.setFixedSize(config.WIDGET_SIZES['expand_btn_size'],
                                      config.WIDGET_SIZES['expand_btn_size'])
        self.expand_btn.clicked.connect(self._toggle_subtasks)
        if len(self.todo.subtasks) == 0:
            self.expand_btn.setVisible(False)
        first_row_layout.addWidget(self.expand_btn)

        # 반복 아이콘 (반복 할일일 때만 표시)
        if self.todo.recurrence:
            self.recurrence_icon = QLabel("🔁")
            self.recurrence_icon.setObjectName("recurrenceIcon")
            self.recurrence_icon.setToolTip(f"반복: {self.todo.recurrence}")
            first_row_layout.addWidget(self.recurrence_icon)
        else:
            self.recurrence_icon = None

        # TODO 메타 정보 (납기일 배지)
        if self.todo.due_date:
            self.date_badge = self._create_date_badge()
            first_row_layout.addWidget(self.date_badge)
        else:
            self.date_badge = None

        content_layout.addLayout(first_row_layout)
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

        # 메인 위젯을 컨테이너에 추가
        container_layout.addWidget(main_widget)

        # === 하위 할일 컨테이너 ===
        self.subtasks_container = QWidget()
        self.subtasks_container.setObjectName("subtasksContainer")
        self.subtasks_layout = QVBoxLayout(self.subtasks_container)
        self.subtasks_layout.setContentsMargins(0, 0, 0, 0)
        self.subtasks_layout.setSpacing(2)

        # 하위 할일 위젯 생성
        self._populate_subtasks()

        # 초기 상태: 접힌 상태
        self.subtasks_container.setVisible(False)

        # 하위 할일 컨테이너를 전체 레이아웃에 추가
        container_layout.addWidget(self.subtasks_container)

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


    def _populate_subtasks(self) -> None:
        """하위 할일 위젯들을 생성하여 컨테이너에 추가"""
        # 기존 위젯들 모두 제거
        while self.subtasks_layout.count():
            item = self.subtasks_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 새로운 하위 할일 위젯 생성
        for subtask in self.todo.subtasks:
            subtask_widget = SubTaskWidget(self.todo.id, subtask)
            # 시그널 연결
            subtask_widget.subtask_toggled.connect(self._on_subtask_toggled)
            subtask_widget.subtask_edit_requested.connect(self._on_subtask_edit_requested)
            subtask_widget.subtask_delete_requested.connect(self._on_subtask_delete_requested)
            self.subtasks_layout.addWidget(subtask_widget)

    def _toggle_subtasks(self) -> None:
        """하위 할일 컨테이너 펼치기/접기"""
        self._subtasks_expanded = not self._subtasks_expanded
        self.subtasks_container.setVisible(self._subtasks_expanded)

        # 버튼 아이콘 변경
        if self._subtasks_expanded:
            self.expand_btn.setText("▼")
        else:
            self.expand_btn.setText("▶")

    def _on_subtask_toggled(self, parent_id, subtask_id) -> None:
        """하위 할일 체크박스 토글 시그널 전파"""
        self.subtask_toggled.emit(parent_id, subtask_id)

    def _on_subtask_edit_requested(self, parent_id, subtask_id) -> None:
        """하위 할일 편집 요청 시그널 전파"""
        self.subtask_edit_requested.emit(parent_id, subtask_id)

    def _on_subtask_delete_requested(self, parent_id, subtask_id) -> None:
        """하위 할일 삭제 요청 시그널 전파"""
        self.subtask_delete_requested.emit(parent_id, subtask_id)

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
            background: transparent;
            border: none;
        }}

        QWidget#todoItemMain {{
            background: {bg_color};
            border: {config.UI_METRICS['border_width']['thin']}px solid {border_color};
            border-radius: {config.UI_METRICS['border_radius']['lg']}px;
        }}

        QWidget#todoItemMain:hover {{
            background: {config.COLORS['card_hover']};
            border-color: {config.COLORS['accent']};
        }}

        QWidget#subtasksContainer {{
            background: transparent;
            border: none;
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

        QPushButton#expandBtn {{
            background: transparent;
            border: none;
            color: {config.COLORS['text_secondary']};
            font-size: {config.FONT_SIZES['sm']}px;
            padding: 0px;
        }}

        QPushButton#expandBtn:hover {{
            color: {config.COLORS['accent']};
        }}

        QLabel#recurrenceIcon {{
            color: {config.COLORS['accent']};
            font-size: {config.FONT_SIZES['base']}px;
            padding: 0px 2px;
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

        # 반복 아이콘 업데이트
        if self.todo.recurrence:
            if not self.recurrence_icon:
                # 반복 아이콘이 없었는데 추가된 경우
                self.recurrence_icon = QLabel("🔁")
                self.recurrence_icon.setObjectName("recurrenceIcon")
                # 첫 번째 행 레이아웃에서 펼치기 버튼 앞에 추가
                # (레이아웃 재구성이 복잡하므로 툴팁만 업데이트)
            self.recurrence_icon.setToolTip(f"반복: {self.todo.recurrence}")
            self.recurrence_icon.setVisible(True)
        else:
            if self.recurrence_icon:
                # 반복 아이콘이 있었는데 제거된 경우
                self.recurrence_icon.setVisible(False)

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

        # 하위 할일 업데이트
        self._populate_subtasks()

        # 펼치기 버튼 표시 여부 업데이트
        if len(self.todo.subtasks) > 0:
            self.expand_btn.setVisible(True)
        else:
            self.expand_btn.setVisible(False)
            self._subtasks_expanded = False
            self.subtasks_container.setVisible(False)

        self.apply_styles()
