# -*- coding: utf-8 -*-
"""TodoItemWidget - TODO 아이템 위젯

Phase 5-2: TODO 아이템 위젯 구현
docs/todo-app-ui.html의 .todo-item 구조를 정확히 재현합니다.
"""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QCheckBox, QPushButton, QGraphicsOpacityEffect
from PyQt6.QtCore import Qt, pyqtSignal, QEvent
from PyQt6.QtGui import QMouseEvent, QAction, QDragEnterEvent, QDragMoveEvent, QDropEvent
from PyQt6.QtWidgets import QMenu
import json
import re

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
    edit_with_selection_requested = pyqtSignal(object)  # Todo 객체 전달 (하위할일이 있을 때)
    copy_requested = pyqtSignal(str)  # 복사 요청 (todo_id)

    # 하위 할일 시그널
    subtask_toggled = pyqtSignal(object, object)  # parent_id, subtask_id
    subtask_edit_requested = pyqtSignal(object, object)
    subtask_delete_requested = pyqtSignal(object, object)
    subtask_text_expanded_changed = pyqtSignal(object, object, bool)  # parent_id, subtask_id, expanded

    # 펼침 상태 변경 시그널 (Phase 1)
    expanded_changed = pyqtSignal(str, bool)  # (todo_id, is_expanded)

    # 하위 할일 순서 변경 시그널
    subtask_reordered = pyqtSignal(str, list)  # (todo_id, new_subtask_ids)

    # 하위 할일 다른 부모로 이동 시그널
    subtask_moved = pyqtSignal(str, str, str)  # (source_todo_id, target_todo_id, subtask_id)

    # 텍스트 펼침 상태 변경 시그널
    text_expanded_changed = pyqtSignal(str, bool)  # (todo_id, is_expanded)

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

        # 첫 번째 행: TODO 텍스트 + 오른쪽 UI 컨테이너
        first_row_layout = QHBoxLayout()
        first_row_layout.setSpacing(8)
        first_row_layout.setContentsMargins(0, 0, 0, 0)

        # TODO 텍스트 (RichTextWidget 사용 - 링크/경로 인식)
        # 최소 너비만 설정하여 윈도우 크기에 따라 자동 확장되도록 함
        self.todo_text = RichTextWidget(str(self.todo.content))
        self.todo_text.setObjectName("todoText")
        self.todo_text.setMinimumWidth(config.LAYOUT_SIZES['todo_text_base_max_width'])  # 최소 220px
        if self.todo.completed:
            self.todo_text.setProperty("completed", "true")

        # 저장된 텍스트 펼침 상태 적용
        if self.todo.text_expanded:
            self.todo_text.set_expanded(True)

        first_row_layout.addWidget(self.todo_text, 1)  # stretch

        # === 오른쪽 UI 컨테이너 (고정 너비 요소들을 하나로 묶음) ===
        right_widgets_layout = QHBoxLayout()
        right_widgets_layout.setSpacing(8)
        right_widgets_layout.setContentsMargins(0, 0, 0, 0)

        # 텍스트 펼치기/접기 버튼 (개행문자가 있을 때만 표시)
        self.text_expand_btn = QPushButton("▶")
        self.text_expand_btn.setObjectName("textExpandBtn")
        self.text_expand_btn.setFixedSize(16, 16)
        self.text_expand_btn.clicked.connect(self._toggle_text_expand)
        if not self._has_multiline():
            self.text_expand_btn.setVisible(False)
        else:
            # 저장된 펼침 상태에 따라 버튼 아이콘 설정
            if self.todo.text_expanded:
                self.text_expand_btn.setText("▼")
        right_widgets_layout.addWidget(self.text_expand_btn)

        # 하위 할일 펼치기/접기 버튼 (하위 할일이 있을 때만 표시)
        self.expand_btn = QPushButton("▶")
        self.expand_btn.setObjectName("expandBtn")
        self.expand_btn.setFixedSize(config.WIDGET_SIZES['expand_btn_size'],
                                      config.WIDGET_SIZES['expand_btn_size'])
        self.expand_btn.clicked.connect(self._toggle_subtasks)
        if len(self.todo.subtasks) == 0:
            self.expand_btn.setVisible(False)
        right_widgets_layout.addWidget(self.expand_btn)

        # 반복 아이콘 (반복 할일일 때만 표시)
        if self.todo.recurrence:
            self.recurrence_icon = QLabel("🔁")
            self.recurrence_icon.setObjectName("recurrenceIcon")
            self.recurrence_icon.setFixedWidth(20)  # 고정 너비
            self.recurrence_icon.setToolTip(f"반복: {self.todo.recurrence}")
            right_widgets_layout.addWidget(self.recurrence_icon)
        else:
            self.recurrence_icon = None

        # TODO 메타 정보 (납기일 배지)
        if self.todo.due_date:
            self.date_badge = self._create_date_badge()
            # 너비 제약 제거 - QSS padding(2px 6px)과 font-size(11px)로 자연스러운 크기 결정
            right_widgets_layout.addWidget(self.date_badge)
        else:
            self.date_badge = None

        # 오른쪽 UI 컨테이너를 첫 번째 행에 추가 (stretch=0으로 고정)
        first_row_layout.addLayout(right_widgets_layout, 0)

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

        # 드래그 앤 드롭 수락 설정
        self.subtasks_container.setAcceptDrops(True)
        # 이벤트 필터 설치 (드롭 이벤트 처리)
        self.subtasks_container.installEventFilter(self)

        # 메인 위젯에도 드롭 수락 (다른 부모의 하위 할일 이동용)
        self.main_widget = main_widget
        self.main_widget.setAcceptDrops(True)
        self.main_widget.installEventFilter(self)

        # 하위 할일 위젯 생성
        self._populate_subtasks()

        # 초기 상태: 접힌 상태
        self.subtasks_container.setVisible(False)

        # 하위 할일 컨테이너를 전체 레이아웃에 추가
        container_layout.addWidget(self.subtasks_container)

    def _calculate_max_text_width(self) -> int:
        """사용 가능한 TODO 텍스트 최대 너비 동적 계산

        윈도우 기본 너비(420px) 기준:
        - 좌측: 드래그(14) + 체크박스(18) + 여백(10+10) = 52px
        - 우측: 펼치기(16) + 반복(20) + 납기(100) + 삭제(24) + 여백(24) = 184px
        - 사용 가능: 420 - 52 - 184 = 184px
        - 여유 있게 220px로 설정 (긴 텍스트도 일부 표시 가능)

        Returns:
            int: TODO 텍스트 최대 너비 (픽셀)
        """
        return config.LAYOUT_SIZES['todo_text_base_max_width']

    def _create_date_badge(self) -> QLabel:
        """납기일 배지 생성

        Returns:
            QLabel: 날짜 배지 위젯
        """
        badge = QLabel()
        badge.setObjectName("dateBadge")
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
            subtask_widget.text_expanded_changed.connect(self._on_subtask_text_expanded_changed)
            self.subtasks_layout.addWidget(subtask_widget)

    def _has_multiline(self) -> bool:
        """텍스트에 개행문자가 포함되어 있는지 확인

        Returns:
            개행문자(\n, \r) 또는 <br> 태그가 있으면 True
        """
        text = str(self.todo.content)
        # \n, \r, <br>, <br/>, <br /> 체크
        return bool(re.search(r'[\n\r]|<br\s*/?>', text, re.IGNORECASE))

    def _toggle_text_expand(self) -> None:
        """텍스트 펼침/접힘 토글"""
        self.todo.text_expanded = not self.todo.text_expanded

        # 버튼 아이콘 업데이트
        if self.todo.text_expanded:
            self.text_expand_btn.setText("▼")
        else:
            self.text_expand_btn.setText("▶")

        # RichTextWidget 펼침 상태 변경
        self.todo_text.set_expanded(self.todo.text_expanded)

        # 레이아웃 업데이트 (높이 재계산)
        self.todo_text.adjustSize()
        self.adjustSize()
        self.updateGeometry()

        # 부모 위젯 레이아웃 업데이트
        if self.parent():
            self.parent().updateGeometry()

        # 시그널 발생 (상태 저장용)
        self.text_expanded_changed.emit(str(self.todo.id), self.todo.text_expanded)

    def _toggle_subtasks(self) -> None:
        """하위 할일 컨테이너 펼치기/접기"""
        self._subtasks_expanded = not self._subtasks_expanded
        self.subtasks_container.setVisible(self._subtasks_expanded)

        # 버튼 아이콘 변경
        if self._subtasks_expanded:
            self.expand_btn.setText("▼")
        else:
            self.expand_btn.setText("▶")

        # 펼침 상태 변경 시그널 발생 (Phase 1)
        self.expanded_changed.emit(str(self.todo.id), self._subtasks_expanded)

    def _on_subtask_toggled(self, parent_id, subtask_id) -> None:
        """하위 할일 체크박스 토글 시그널 전파"""
        self.subtask_toggled.emit(parent_id, subtask_id)

    def _on_subtask_edit_requested(self, parent_id, subtask_id) -> None:
        """하위 할일 편집 요청 시그널 전파"""
        self.subtask_edit_requested.emit(parent_id, subtask_id)

    def _on_subtask_delete_requested(self, parent_id, subtask_id) -> None:
        """하위 할일 삭제 요청 시그널 전파"""
        self.subtask_delete_requested.emit(parent_id, subtask_id)

    def _on_subtask_text_expanded_changed(self, parent_id, subtask_id, expanded) -> None:
        """하위 할일 텍스트 펼침 상태 변경 시그널 전파"""
        self.subtask_text_expanded_changed.emit(parent_id, subtask_id, expanded)

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

        QPushButton#textExpandBtn {{
            background: transparent;
            border: none;
            color: {config.COLORS['text_disabled']};
            font-size: 10px;
            padding: 0;
        }}

        QPushButton#textExpandBtn:hover {{
            color: {config.COLORS['accent']};
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
            # 하위할일이 있으면 선택 다이얼로그 요청, 없으면 바로 편집
            if self.todo and self.todo.subtasks:
                self.edit_with_selection_requested.emit(self.todo)
            else:
                self.edit_requested.emit(str(self.todo.id))
        # super().mouseDoubleClickEvent(event)를 호출하지 않음
        # 시그널 처리 중 위젯이 삭제될 수 있어 RuntimeError 방지
        event.accept()

    def contextMenuEvent(self, event) -> None:
        """우클릭 컨텍스트 메뉴 이벤트 핸들러

        Args:
            event: 컨텍스트 메뉴 이벤트
        """
        menu = QMenu(self)

        # 복사 액션
        copy_action = QAction("복사", self)
        copy_action.triggered.connect(self._on_copy_clicked)
        menu.addAction(copy_action)

        # 메뉴 표시
        menu.exec(event.globalPos())

    def _on_copy_clicked(self) -> None:
        """복사 메뉴 클릭 이벤트 핸들러"""
        self.copy_requested.emit(str(self.todo.id))

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

    def set_expanded(self, expanded: bool) -> None:
        """외부에서 펼침 상태 설정 (reload 후 복원용)

        Args:
            expanded: 펼침 상태 (True: 펼침, False: 접힘)
        """
        if len(self.todo.subtasks) == 0:
            return

        self._subtasks_expanded = expanded
        self.subtasks_container.setVisible(expanded)
        self.expand_btn.setText("▼" if expanded else "▶")

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

    def eventFilter(self, obj, event):
        """이벤트 필터 (subtasks_container 및 main_widget의 드롭 이벤트 처리)

        Args:
            obj: 이벤트를 받은 객체
            event: 이벤트

        Returns:
            bool: 이벤트 처리 여부
        """
        if obj == self.subtasks_container:
            if event.type() == event.Type.DragEnter:
                return self._handle_drag_enter(event)
            elif event.type() == event.Type.DragMove:
                return self._handle_drag_move(event)
            elif event.type() == event.Type.Drop:
                return self._handle_drop(event)
        elif obj == self.main_widget:
            if event.type() == event.Type.DragEnter:
                return self._handle_main_drag_enter(event)
            elif event.type() == event.Type.DragMove:
                return self._handle_main_drag_move(event)
            elif event.type() == event.Type.Drop:
                return self._handle_main_drop(event)
        return super().eventFilter(obj, event)

    def _handle_drag_enter(self, event: QDragEnterEvent) -> bool:
        """드래그 진입 이벤트 처리 (같은 부모 + 다른 부모 모두 수락)

        Args:
            event: 드래그 이벤트

        Returns:
            bool: 이벤트 처리 여부
        """
        if event.mimeData().hasText():
            try:
                data = json.loads(event.mimeData().text())
                if data.get('type') == 'subtask':
                    event.acceptProposedAction()
                    return True
            except (json.JSONDecodeError, KeyError):
                pass
        event.ignore()
        return True

    def _handle_drag_move(self, event: QDragMoveEvent) -> bool:
        """드래그 이동 이벤트 처리 (같은 부모 + 다른 부모 모두 수락)

        Args:
            event: 드래그 이벤트

        Returns:
            bool: 이벤트 처리 여부
        """
        if event.mimeData().hasText():
            try:
                data = json.loads(event.mimeData().text())
                if data.get('type') == 'subtask':
                    event.acceptProposedAction()
                    return True
            except (json.JSONDecodeError, KeyError):
                pass
        event.ignore()
        return True

    def _handle_drop(self, event: QDropEvent) -> bool:
        """드롭 이벤트 처리 (하위 할일 순서 변경)

        Args:
            event: 드롭 이벤트

        Returns:
            bool: 이벤트 처리 여부
        """
        import logging
        logger = logging.getLogger(__name__)

        if not event.mimeData().hasText():
            event.ignore()
            return True

        try:
            data = json.loads(event.mimeData().text())
            if data.get('type') != 'subtask':
                event.ignore()
                return True

            source_parent_id = data.get('parent_todo_id')
            dragged_subtask_id = data.get('subtask_id')

            # 다른 부모에서 온 하위 할일 → 이동 처리
            if source_parent_id != str(self.todo.id):
                logger.info(f'[SubtaskMove] subtasks_container drop: subtask={dragged_subtask_id[:8]}..., from={source_parent_id[:8]}... to={str(self.todo.id)[:8]}...')
                self.subtask_moved.emit(source_parent_id, str(self.todo.id), dragged_subtask_id)
                event.acceptProposedAction()
                return True

            # 드롭 위치 계산
            drop_pos = event.position().toPoint()
            new_position = self._calculate_subtask_drop_position(drop_pos)

            # 현재 순서 가져오기
            current_ids = [str(st.id) for st in self.todo.subtasks]

            # 드래그된 항목의 현재 위치
            if dragged_subtask_id not in current_ids:
                event.ignore()
                return True

            old_position = current_ids.index(dragged_subtask_id)

            # 새로운 순서 계산
            current_ids.remove(dragged_subtask_id)
            # 새 위치 조정 (항목이 제거되었으므로)
            if new_position > old_position:
                new_position -= 1
            current_ids.insert(new_position, dragged_subtask_id)

            logger.info(f'[SubtaskDrop] todo_id={str(self.todo.id)[:8]}..., subtask_id={dragged_subtask_id[:8]}..., new_order={[sid[:8] for sid in current_ids]}')

            # 순서 변경 시그널 발생
            self.subtask_reordered.emit(str(self.todo.id), current_ids)

            event.acceptProposedAction()
            return True

        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f'[SubtaskDrop] JSON parse error: {e}')
            event.ignore()
            return True

    def _calculate_subtask_drop_position(self, drop_pos) -> int:
        """드롭 위치를 하위 할일 리스트의 인덱스로 변환

        Args:
            drop_pos: 드롭 위치 (QPoint)

        Returns:
            int: 새로운 위치 (0부터 시작하는 인덱스)
        """
        # subtasks_layout에서 각 하위 할일 위젯과 비교
        for i in range(self.subtasks_layout.count()):
            item = self.subtasks_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                widget_rect = widget.geometry()
                widget_center_y = widget_rect.top() + widget_rect.height() / 2

                # 드롭 위치가 위젯의 중앙보다 위에 있으면 해당 인덱스에 삽입
                if drop_pos.y() < widget_center_y:
                    return i

        # 모든 위젯보다 아래면 맨 뒤에 삽입
        return self.subtasks_layout.count()

    def _handle_main_drag_enter(self, event) -> bool:
        """메인 위젯 드래그 진입 이벤트 (다른 부모의 하위 할일 수락)"""
        if event.mimeData().hasText():
            try:
                data = json.loads(event.mimeData().text())
                if data.get('type') == 'subtask' and data.get('parent_todo_id') != str(self.todo.id):
                    event.acceptProposedAction()
                    return True
            except (json.JSONDecodeError, KeyError):
                pass
        event.ignore()
        return True

    def _handle_main_drag_move(self, event) -> bool:
        """메인 위젯 드래그 이동 이벤트 (다른 부모의 하위 할일 수락)"""
        if event.mimeData().hasText():
            try:
                data = json.loads(event.mimeData().text())
                if data.get('type') == 'subtask' and data.get('parent_todo_id') != str(self.todo.id):
                    event.acceptProposedAction()
                    return True
            except (json.JSONDecodeError, KeyError):
                pass
        event.ignore()
        return True

    def _handle_main_drop(self, event) -> bool:
        """메인 위젯 드롭 이벤트 (하위 할일을 이 메인 할일의 마지막 하위로 이동)"""
        import logging
        logger = logging.getLogger(__name__)

        if not event.mimeData().hasText():
            event.ignore()
            return True

        try:
            data = json.loads(event.mimeData().text())
            if data.get('type') != 'subtask':
                event.ignore()
                return True

            source_parent_id = data.get('parent_todo_id')
            subtask_id = data.get('subtask_id')

            # 같은 부모의 하위 할일은 main_widget에서 처리하지 않음
            if source_parent_id == str(self.todo.id):
                event.ignore()
                return True

            logger.info(f'[SubtaskMove] main_widget drop: subtask={subtask_id[:8]}..., from={source_parent_id[:8]}... to={str(self.todo.id)[:8]}...')
            self.subtask_moved.emit(source_parent_id, str(self.todo.id), subtask_id)
            event.acceptProposedAction()
            return True

        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f'[SubtaskMove] main_widget drop error: {e}')
            event.ignore()
            return True

    def update_todo(self, todo: Todo) -> None:
        """TODO 데이터 업데이트

        Args:
            todo: 새로운 Todo Entity
        """
        # 기존 펼침 상태 저장 (P3-3: 하위 할일 펼침 상태 유지)
        was_expanded = self._subtasks_expanded

        self.todo = todo

        # UI 업데이트
        self.todo_text.update_text(str(self.todo.content))
        self.checkbox.setChecked(self.todo.completed)

        # 텍스트 펼침 버튼 가시성 업데이트
        if self._has_multiline():
            self.text_expand_btn.setVisible(True)
        else:
            self.text_expand_btn.setVisible(False)

        # 텍스트 펼침 상태 동기화
        if self.todo.text_expanded:
            self.text_expand_btn.setText("▼")
            self.todo_text.set_expanded(True)
        else:
            self.text_expand_btn.setText("▶")
            self.todo_text.set_expanded(False)

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

        # 펼치기 버튼 표시 여부 및 펼침 상태 복원 (P3-3)
        if len(self.todo.subtasks) > 0:
            self.expand_btn.setVisible(True)

            # 펼침 상태 복원: 이전에 펼쳐져 있었다면 계속 펼친 상태 유지
            if was_expanded:
                self._subtasks_expanded = True
                self.subtasks_container.setVisible(True)
                self.expand_btn.setText("▼")
            # 접혀 있었다면 접힌 상태 유지
            else:
                self._subtasks_expanded = False
                self.subtasks_container.setVisible(False)
                self.expand_btn.setText("▶")
        else:
            # 하위 할일이 모두 삭제된 경우: 펼치기 버튼 숨김 및 컨테이너 숨김
            self.expand_btn.setVisible(False)
            self._subtasks_expanded = False
            self.subtasks_container.setVisible(False)

        self.apply_styles()
