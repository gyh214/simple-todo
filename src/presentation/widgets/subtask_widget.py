# -*- coding: utf-8 -*-
"""SubTaskWidget - 하위 할일 아이템 위젯

Phase 1.3: SubTask UI 구현
메인 할일의 하위 할일을 표시하는 위젯 (납기일 자동 정렬, 드래그 불필요)
"""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QCheckBox, QPushButton, QGraphicsOpacityEffect
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QMouseEvent
import json
import re

import config
from ...domain.entities.subtask import SubTask
from ...domain.value_objects.todo_id import TodoId
from ...domain.value_objects.due_date import DueDateStatus
from .rich_text_widget import RichTextWidget
from .mixins.draggable_mixin import DraggableMixin


class SubTaskWidget(DraggableMixin, QWidget):
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
    text_expanded_changed = pyqtSignal(object, object, bool)  # parent_id, subtask_id, expanded

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

        # DraggableMixin 초기화
        self.setup_draggable()

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

        # 0. 드래그 핸들 (DraggableMixin 필수)
        self.drag_handle = QLabel("☰")
        self.drag_handle.setObjectName("subtaskDragHandle")
        self.drag_handle.setFixedWidth(14)
        self.drag_handle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drag_handle.setCursor(Qt.CursorShape.OpenHandCursor)
        main_layout.addWidget(self.drag_handle)

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

        # SubTask 텍스트 (RichTextWidget 사용 - 링크/경로 인식)
        # 메인 TODO 텍스트 최소 너비(220px) - 들여쓰기(24px) = 196px
        self.subtask_text = RichTextWidget(str(self.subtask.content))
        self.subtask_text.setObjectName("subtaskText")
        self.subtask_text.setMinimumWidth(
            config.LAYOUT_SIZES['todo_text_base_max_width'] - config.WIDGET_SIZES['subtask_indent'] - 14
        )
        if self.subtask.completed:
            self.subtask_text.setProperty("completed", "true")
        content_layout.addWidget(self.subtask_text, 1)  # stretch factor = 1

        # 펼침 버튼 (납기배지 앞에 배치)
        self.expand_btn = QPushButton("▶")
        self.expand_btn.setObjectName("subtaskExpandBtn")
        self.expand_btn.setFixedSize(16, 16)
        self.expand_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        # 개행문자가 있을 때만 표시
        if not self._has_multiline():
            self.expand_btn.setVisible(False)

        content_layout.addWidget(self.expand_btn)

        # 저장된 펼침 상태 적용
        if self.subtask.text_expanded:
            self.expand_btn.setText("▼")
            self.subtask_text.set_expanded(True)

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

        # 펼침 시 높이 자동 확장을 위한 SizePolicy 설정
        from PyQt6.QtWidgets import QSizePolicy
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)

    def _create_date_badge(self) -> QLabel:
        """납기일 배지 생성

        Returns:
            QLabel: 날짜 배지 위젯
        """
        badge = QLabel()
        badge.setObjectName("subtaskDateBadge")
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)  # 텍스트 중앙 정렬

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

        QLabel#subtaskDragHandle {{
            color: {config.COLORS['text_disabled']};
            font-size: {config.FONT_SIZES['base']}px;
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

        QPushButton#subtaskExpandBtn {{
            background: transparent;
            border: none;
            color: {config.COLORS['text_disabled']};
            font-size: 10px;
            padding: 0;
        }}

        QPushButton#subtaskExpandBtn:hover {{
            color: {config.COLORS['accent']};
        }}
        """

        self.setStyleSheet(style_sheet)

        # 완료 상태면 개별 요소에 opacity 효과 적용 (삭제 버튼 제외)
        if self.subtask.completed:
            # 드래그 핸들에 opacity 적용
            handle_opacity = QGraphicsOpacityEffect()
            handle_opacity.setOpacity(config.OPACITY_VALUES['completed_item'])
            self.drag_handle.setGraphicsEffect(handle_opacity)

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

            # 펼침 버튼에 opacity 적용
            expand_opacity = QGraphicsOpacityEffect()
            expand_opacity.setOpacity(config.OPACITY_VALUES['completed_item'])
            self.expand_btn.setGraphicsEffect(expand_opacity)
        else:
            # 완료 해제 시 opacity 효과 제거
            self.drag_handle.setGraphicsEffect(None)
            self.checkbox.setGraphicsEffect(None)
            self.subtask_text.setGraphicsEffect(None)
            if self.date_badge:
                self.date_badge.setGraphicsEffect(None)
            self.expand_btn.setGraphicsEffect(None)

    def _connect_signals(self) -> None:
        """이벤트 시그널 연결"""
        # 체크박스 클릭
        self.checkbox.checkStateChanged.connect(self._on_checkbox_toggled)

        # 삭제 버튼 클릭
        self.delete_btn.clicked.connect(self._on_delete_clicked)

        # 펼침 버튼 클릭
        self.expand_btn.clicked.connect(self._toggle_text_expand)

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

    def _toggle_text_expand(self) -> None:
        """텍스트 펼침/접힘 토글"""
        self.subtask.text_expanded = not self.subtask.text_expanded

        # 버튼 아이콘 업데이트
        if self.subtask.text_expanded:
            self.expand_btn.setText("▼")
        else:
            self.expand_btn.setText("▶")

        # RichTextWidget 펼침 상태 변경
        self.subtask_text.set_expanded(self.subtask.text_expanded)

        # 레이아웃 업데이트 (높이 재계산)
        self.subtask_text.adjustSize()
        self.adjustSize()
        self.updateGeometry()

        # 부모 위젯 레이아웃 업데이트
        if self.parent():
            self.parent().updateGeometry()

        # 시그널 발생 (상태 저장용)
        self.text_expanded_changed.emit(
            self.parent_todo_id,
            self.subtask.id,
            self.subtask.text_expanded
        )

    def _has_multiline(self) -> bool:
        """텍스트에 개행문자가 포함되어 있는지 확인

        Returns:
            개행문자(\n, \r) 또는 <br> 태그가 있으면 True
        """
        text = str(self.subtask.content)
        # \n, \r, <br>, <br/>, <br /> 체크
        return bool(re.search(r'[\n\r]|<br\s*/?>', text, re.IGNORECASE))

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        """더블클릭 이벤트 핸들러 (편집 요청)

        Args:
            event: 마우스 이벤트
        """
        if event.button() == Qt.MouseButton.LeftButton:
            self.subtask_edit_requested.emit(self.parent_todo_id, self.subtask.id)
        # super().mouseDoubleClickEvent(event)를 호출하지 않음
        # 이벤트가 부모 위젯(TodoItemWidget)으로 전파되는 것을 방지
        event.accept()

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

    def get_drag_data(self) -> str:
        """드래그할 데이터 반환 (DraggableMixin 요구 메서드)

        Returns:
            str: JSON 형식의 subtask_id와 parent_todo_id
        """
        data = {
            "type": "subtask",
            "subtask_id": str(self.subtask.id),
            "parent_todo_id": str(self.parent_todo_id)
        }
        return json.dumps(data)

    def get_widget_styles(self) -> str:
        """현재 위젯 스타일 반환 (DraggableMixin 요구 메서드)

        Returns:
            str: 현재 위젯 스타일 시트
        """
        return self.styleSheet()

    def apply_styles(self) -> None:
        """스타일 재적용 (DraggableMixin 요구 메서드)

        DraggableMixin._start_drag()에서 드래그 종료 후 호출됩니다.
        """
        self._apply_styles()

    def update_subtask(self, subtask: SubTask) -> None:
        """SubTask 데이터 업데이트

        Args:
            subtask: 새로운 SubTask Entity
        """
        self.subtask = subtask

        # UI 업데이트
        self.subtask_text.update_text(str(self.subtask.content))
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

        # 펼침 버튼 가시성 업데이트
        if self._has_multiline():
            self.expand_btn.setVisible(True)
        else:
            self.expand_btn.setVisible(False)

        # 펼침 상태 동기화
        if self.subtask.text_expanded:
            self.expand_btn.setText("▼")
            self.subtask_text.set_expanded(True)
        else:
            self.expand_btn.setText("▶")
            self.subtask_text.set_expanded(False)

        self._apply_styles()
