# -*- coding: utf-8 -*-
"""SubTaskWidget - 하위 할일 아이템 위젯

Phase 1.3: SubTask UI 구현
메인 할일의 하위 할일을 표시하는 위젯 (납기일 자동 정렬, 드래그 불필요)
"""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QCheckBox, QPushButton, QGraphicsOpacityEffect
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QMouseEvent

import config
from ...domain.entities.subtask import SubTask
from ...domain.value_objects.todo_id import TodoId
from ...domain.value_objects.due_date import DueDateStatus


class SubTaskWidget(QWidget):
    """하위 할일 아이템 위젯

    UI 구조:
    - 체크박스 (커스텀 스타일)
    - SubTask 내용 영역:
      - SubTask 텍스트
      - 납기일 배지 (선택적)
    - 삭제 버튼 (호버 시 표시)

    Signals:
        subtask_toggled(TodoId, TodoId): 체크박스 토글 (parent_id, subtask_id)
        subtask_edit_requested(TodoId, TodoId): 편집 요청 (parent_id, subtask_id)
        subtask_delete_requested(TodoId, TodoId): 삭제 요청 (parent_id, subtask_id)
    """

    # 시그널 정의
    subtask_toggled = pyqtSignal(object, object)  # parent_id, subtask_id
    subtask_edit_requested = pyqtSignal(object, object)
    subtask_delete_requested = pyqtSignal(object, object)

    def __init__(self, parent_todo_id: TodoId, subtask: SubTask, parent=None):
        """SubTaskWidget 초기화

        Args:
            parent_todo_id: 부모 TODO ID
            subtask: SubTask Entity
            parent: 부모 위젯
        """
        super().__init__(parent)
        self.parent_todo_id = parent_todo_id
        self.subtask = subtask
        self._is_hovered = False

        self._setup_ui()
        self._apply_styles()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """UI 요소 생성 및 배치"""
        # 메인 레이아웃 (수평)
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(
            config.WIDGET_SIZES['subtask_indent'],  # 왼쪽 들여쓰기
            6, 6, 6
        )
        main_layout.setSpacing(10)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # 1. 체크박스
        self.checkbox = QCheckBox()
        self.checkbox.setObjectName("subtaskCheckbox")
        self.checkbox.setChecked(self.subtask.completed)
        self.checkbox.setFixedSize(*config.WIDGET_SIZES['checkbox_size'])
        main_layout.addWidget(self.checkbox)

        # 2. SubTask 콘텐츠 영역 (텍스트 + 메타)
        content_layout = QHBoxLayout()
        content_layout.setSpacing(8)
        content_layout.setContentsMargins(0, 0, 0, 0)

        # SubTask 텍스트
        self.subtask_text = QLabel(str(self.subtask.content))
        self.subtask_text.setObjectName("subtaskText")
        self.subtask_text.setWordWrap(False)
        if self.subtask.completed:
            self.subtask_text.setProperty("completed", "true")
        content_layout.addWidget(self.subtask_text, 1)  # stretch factor = 1

        # SubTask 메타 정보 (납기일 배지)
        if self.subtask.due_date:
            self.date_badge = self._create_date_badge()
            content_layout.addWidget(self.date_badge)
        else:
            self.date_badge = None

        main_layout.addLayout(content_layout, 1)

        # 3. 삭제 버튼
        self.delete_btn = QPushButton("✕")
        self.delete_btn.setObjectName("subtaskDeleteBtn")
        self.delete_btn.setFixedSize(*config.WIDGET_SIZES['delete_btn_size'])

        # Opacity 효과 설정 (초기 숨김)
        self.delete_btn_opacity = QGraphicsOpacityEffect()
        self.delete_btn_opacity.setOpacity(config.OPACITY_VALUES['hidden'])
        self.delete_btn.setGraphicsEffect(self.delete_btn_opacity)

        main_layout.addWidget(self.delete_btn)

        # 위젯 자체 설정
        self.setObjectName("subtaskItem")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground)

    def _create_date_badge(self) -> QLabel:
        """납기일 배지 생성

        Returns:
            QLabel: 날짜 배지 위젯
        """
        badge = QLabel()
        badge.setObjectName("subtaskDateBadge")

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
        if not self.subtask.due_date:
            return ("", "normal")

        # DueDate Value Object 메서드 활용
        status = self.subtask.due_date.calculate_status()
        text = self.subtask.due_date.format_display_text()

        return (text, status)

    def _apply_styles(self) -> None:
        """QSS 스타일 적용"""
        # 완료 상태에 따른 텍스트 스타일
        text_decoration = "line-through" if self.subtask.completed else "none"
        text_color = config.COLORS['text_disabled'] if self.subtask.completed else config.COLORS['text_secondary']

        style_sheet = f"""
        QWidget#subtaskItem {{
            background: transparent;
            border: none;
        }}

        QWidget#subtaskItem:hover {{
            background: rgba(64, 64, 64, 0.1);
            border-radius: {config.UI_METRICS['border_radius']['lg']}px;
        }}

        QCheckBox#subtaskCheckbox {{
            width: {config.WIDGET_SIZES['checkbox_size'][0]}px;
            height: {config.WIDGET_SIZES['checkbox_size'][1]}px;
            border: {config.UI_METRICS['border_width']['medium']}px solid {config.COLORS['border']};
            border-radius: {config.UI_METRICS['border_radius']['sm']}px;
            background: transparent;
        }}

        QCheckBox#subtaskCheckbox:hover {{
            border-color: {config.COLORS['accent']};
        }}

        QCheckBox#subtaskCheckbox:checked {{
            background: {config.COLORS['accent']};
            border-color: {config.COLORS['accent']};
        }}

        QCheckBox#subtaskCheckbox::indicator {{
            width: {config.WIDGET_SIZES['checkbox_size'][0] - 4}px;
            height: {config.WIDGET_SIZES['checkbox_size'][1] - 4}px;
        }}

        QCheckBox#subtaskCheckbox::indicator:checked {{
            image: none;
        }}

        QLabel#subtaskText {{
            color: {text_color};
            font-size: {config.FONT_SIZES['sm']}px;
            line-height: 1.4;
            text-decoration: {text_decoration};
        }}

        QPushButton#subtaskDeleteBtn {{
            background: transparent;
            border: none;
            color: {config.COLORS['text_disabled']};
            font-size: {config.FONT_SIZES['lg']}px;
            padding: {config.UI_METRICS['padding']['sm'][0]}px {config.UI_METRICS['padding']['sm'][1]}px;
            border-radius: {config.UI_METRICS['border_radius']['sm']}px;
        }}

        QPushButton#subtaskDeleteBtn:hover {{
            background: rgba(244, 67, 54, 0.15);
            color: #ef5350;
        }}

        QLabel#subtaskDateBadge {{
            font-size: {config.FONT_SIZES['xs']}px;
            padding: {config.UI_METRICS['padding']['xs'][0]}px {config.UI_METRICS['padding']['xs'][1]}px;
            border-radius: {config.UI_METRICS['border_radius']['sm']}px;
            font-weight: 500;
        }}

        QLabel#subtaskDateBadge[status="overdue_severe"] {{
            background: {config.DUE_DATE_COLORS['overdue_severe']['bg']};
            color: {config.DUE_DATE_COLORS['overdue_severe']['color']};
        }}

        QLabel#subtaskDateBadge[status="overdue_moderate"] {{
            background: {config.DUE_DATE_COLORS['overdue_moderate']['bg']};
            color: {config.DUE_DATE_COLORS['overdue_moderate']['color']};
        }}

        QLabel#subtaskDateBadge[status="overdue_mild"] {{
            background: {config.DUE_DATE_COLORS['overdue_mild']['bg']};
            color: {config.DUE_DATE_COLORS['overdue_mild']['color']};
        }}

        QLabel#subtaskDateBadge[status="today"] {{
            background: {config.DUE_DATE_COLORS['today']['bg']};
            color: {config.DUE_DATE_COLORS['today']['color']};
        }}

        QLabel#subtaskDateBadge[status="upcoming"] {{
            background: {config.DUE_DATE_COLORS['upcoming']['bg']};
            color: {config.DUE_DATE_COLORS['upcoming']['color']};
        }}

        QLabel#subtaskDateBadge[status="normal"] {{
            background: {config.DUE_DATE_COLORS['normal']['bg']};
            color: {config.DUE_DATE_COLORS['normal']['color']};
        }}
        """

        self.setStyleSheet(style_sheet)

        # 완료 상태면 개별 요소에 opacity 효과 적용 (삭제 버튼 제외)
        if self.subtask.completed:
            # 체크박스에 opacity 적용
            checkbox_opacity = QGraphicsOpacityEffect()
            checkbox_opacity.setOpacity(config.OPACITY_VALUES['completed_item'])
            self.checkbox.setGraphicsEffect(checkbox_opacity)

            # SubTask 텍스트에 opacity 적용
            text_opacity = QGraphicsOpacityEffect()
            text_opacity.setOpacity(config.OPACITY_VALUES['completed_item'])
            self.subtask_text.setGraphicsEffect(text_opacity)

            # 날짜 배지에 opacity 적용 (있는 경우)
            if self.date_badge:
                badge_opacity = QGraphicsOpacityEffect()
                badge_opacity.setOpacity(config.OPACITY_VALUES['completed_item'])
                self.date_badge.setGraphicsEffect(badge_opacity)
        else:
            # 완료 해제 시 opacity 효과 제거
            self.checkbox.setGraphicsEffect(None)
            self.subtask_text.setGraphicsEffect(None)
            if self.date_badge:
                self.date_badge.setGraphicsEffect(None)

    def _connect_signals(self) -> None:
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
        self.subtask_toggled.emit(self.parent_todo_id, self.subtask.id)

        # UI 업데이트
        self.subtask.completed = completed
        self._update_completion_style()

    def _on_delete_clicked(self) -> None:
        """삭제 버튼 클릭 이벤트 핸들러"""
        self.subtask_delete_requested.emit(self.parent_todo_id, self.subtask.id)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        """더블클릭 이벤트 핸들러 (편집 요청)

        Args:
            event: 마우스 이벤트
        """
        if event.button() == Qt.MouseButton.LeftButton:
            self.subtask_edit_requested.emit(self.parent_todo_id, self.subtask.id)
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
        if self.subtask.completed:
            self.subtask_text.setProperty("completed", "true")
        else:
            self.subtask_text.setProperty("completed", "false")

        # 스타일 재적용
        self._apply_styles()
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

    def update_subtask(self, subtask: SubTask) -> None:
        """SubTask 데이터 업데이트

        Args:
            subtask: 새로운 SubTask Entity
        """
        self.subtask = subtask

        # UI 업데이트
        self.subtask_text.setText(str(self.subtask.content))
        self.checkbox.setChecked(self.subtask.completed)

        # 날짜 배지 업데이트
        if self.subtask.due_date:
            if self.date_badge:
                text, status = self._format_due_date_text()
                self.date_badge.setText(text)
                self.date_badge.setProperty("status", status)
            else:
                # 날짜 배지가 없었는데 추가된 경우
                self.date_badge = self._create_date_badge()
                # 레이아웃에 추가 (content_layout의 마지막에 삽입)
        else:
            if self.date_badge:
                # 날짜 배지가 있었는데 제거된 경우
                self.date_badge.setVisible(False)

        self._apply_styles()
