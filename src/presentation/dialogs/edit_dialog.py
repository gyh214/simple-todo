# -*- coding: utf-8 -*-
"""
TODO 편집 다이얼로그 구현
내용 편집, 날짜 선택, 하위 할일 관리 기능 제공
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QTextEdit, QPushButton,
                            QHBoxLayout, QLabel, QCalendarWidget, QWidget,
                            QScrollArea, QCheckBox, QListWidget, QListWidgetItem,
                            QComboBox, QMessageBox, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from typing import Optional, List
from datetime import datetime
import config
from ...domain.entities.subtask import SubTask
from ...domain.value_objects.todo_id import TodoId
from ...domain.value_objects.recurrence_rule import RecurrenceRule
from .date_picker_dialog import DatePickerDialog


class CollapsibleSection(QWidget):
    """접을 수 있는 섹션 위젯"""

    def __init__(self, title: str, count_text: str = "", parent=None):
        super().__init__(parent)
        self._is_expanded = False
        self.title = title
        self.count_text = count_text

        self._setup_ui()
        self._apply_styles()

    def _setup_ui(self):
        """UI 구성"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 헤더 (클릭 가능)
        self.header_btn = QPushButton()
        self.header_btn.setObjectName("collapsibleHeader")
        self.header_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.header_btn.clicked.connect(self._toggle)
        self._update_header_text()
        layout.addWidget(self.header_btn)

        # 콘텐츠 컨테이너
        self.content_widget = QWidget()
        self.content_widget.setObjectName("collapsibleContent")
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 10, 0, 0)
        self.content_layout.setSpacing(8)
        self.content_widget.setVisible(False)

        layout.addWidget(self.content_widget)

    def _update_header_text(self):
        """헤더 텍스트 업데이트"""
        arrow = "▼" if self._is_expanded else "▶"
        if self.count_text:
            self.header_btn.setText(f"{arrow} {self.title} ({self.count_text})")
        else:
            self.header_btn.setText(f"{arrow} {self.title}")

    def _toggle(self):
        """섹션 펼치기/접기"""
        self._is_expanded = not self._is_expanded
        self.content_widget.setVisible(self._is_expanded)
        self._update_header_text()

    def set_count_text(self, text: str):
        """카운트 텍스트 설정"""
        self.count_text = text
        self._update_header_text()

    def add_content(self, widget: QWidget):
        """콘텐츠 추가"""
        self.content_layout.addWidget(widget)

    def _apply_styles(self):
        """스타일 적용"""
        self.setStyleSheet(f"""
            QPushButton#collapsibleHeader {{
                background: transparent;
                border: none;
                color: {config.COLORS['text_secondary']};
                font-size: {config.FONT_SIZES['md']}px;
                font-weight: 500;
                text-align: left;
                padding: {config.UI_METRICS['padding']['md'][0]}px 0px;
            }}

            QPushButton#collapsibleHeader:hover {{
                color: {config.COLORS['text_primary']};
            }}

            QWidget#collapsibleContent {{
                background: transparent;
            }}
        """)


class EditDialog(QDialog):
    """TODO 편집/추가 다이얼로그"""

    # 시그널: todo_id가 None이면 신규 TODO, 아니면 수정
    save_requested = pyqtSignal(str, str, str)  # todo_id (or None), content, due_date

    def __init__(self, parent=None):
        super().__init__(parent)
        self.todo_id: Optional[str] = None
        self.subtasks: List[SubTask] = []  # 하위 할일 리스트
        self.setup_ui()
        self.apply_styles()

        # 모달 설정
        self.setModal(True)
        self.setWindowTitle("TODO 편집")
        self.setFixedSize(*config.WIDGET_SIZES['edit_dialog_size'])

    def setup_ui(self):
        """UI 구성"""
        # 메인 레이아웃
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # === 스크롤 영역 ===
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # 콘텐츠 컨테이너
        content_widget = QWidget()
        content_widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground)
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(24, 24, 24, 24)
        content_layout.setSpacing(16)

        # 제목
        self.title_label = QLabel("TODO 편집")
        self.title_label.setObjectName("titleLabel")
        content_layout.addWidget(self.title_label)

        # 내용 입력 섹션
        content_label = QLabel("내용")
        content_label.setObjectName("sectionLabel")
        content_layout.addWidget(content_label)

        self.content_edit = QTextEdit()
        self.content_edit.setObjectName("contentEdit")
        self.content_edit.setPlaceholderText("할일 내용을 입력하세요...")
        self.content_edit.setMinimumHeight(config.WIDGET_SIZES['content_edit_height_min'])
        self.content_edit.setMaximumHeight(config.WIDGET_SIZES['content_edit_height_max'])
        content_layout.addWidget(self.content_edit)

        # 날짜 선택 섹션
        date_label = QLabel("납기일")
        date_label.setObjectName("sectionLabel")
        content_layout.addWidget(date_label)

        # 캘린더 위젯 (PyQt6 기본 제공)
        self.calendar = QCalendarWidget(self)
        self.calendar.setGridVisible(True)
        self.calendar.clicked.connect(self._on_date_clicked)
        content_layout.addWidget(self.calendar)

        # 날짜 클리어 버튼
        self.clear_date_btn = QPushButton("날짜 제거")
        self.clear_date_btn.setObjectName("clearBtn")
        self.clear_date_btn.clicked.connect(self._on_clear_date)
        content_layout.addWidget(self.clear_date_btn)

        # 선택된 날짜 표시
        self.selected_date_label = QLabel("선택된 날짜: 없음")
        self.selected_date_label.setObjectName("selectedDateLabel")
        content_layout.addWidget(self.selected_date_label)

        # 하위 할일 섹션 (접을 수 있는 섹션)
        self.subtasks_section = CollapsibleSection("하위 할일", "0/0 완료")
        content_layout.addWidget(self.subtasks_section)

        # 하위 할일 추가 버튼
        add_subtask_btn = QPushButton("+ 하위 할일 추가")
        add_subtask_btn.setObjectName("addSubtaskBtn")
        add_subtask_btn.clicked.connect(self._on_add_subtask)
        self.subtasks_section.add_content(add_subtask_btn)

        # 하위 할일 리스트
        self.subtasks_list = QListWidget()
        self.subtasks_list.setObjectName("subtasksList")
        self.subtasks_list.setMinimumHeight(100)
        self.subtasks_list.setMaximumHeight(300)  # 200 → 300으로 증가하여 더 많은 하위 할일 표시
        self.subtasks_section.add_content(self.subtasks_list)

        # 반복 설정 섹션 (접을 수 있는 구조)
        self.recurrence_section = CollapsibleSection("반복 설정")
        content_layout.addWidget(self.recurrence_section)

        # 반복 설정 컨테이너
        recurrence_container = QWidget()
        recurrence_container_layout = QVBoxLayout(recurrence_container)
        recurrence_container_layout.setContentsMargins(0, 0, 0, 0)
        recurrence_container_layout.setSpacing(10)

        # 반복 설정 UI
        recurrence_control_layout = QHBoxLayout()
        recurrence_control_layout.setSpacing(10)

        # 반복 활성화 체크박스
        self.recurrence_enabled_checkbox = QCheckBox("반복")
        self.recurrence_enabled_checkbox.setObjectName("recurrenceCheckbox")
        self.recurrence_enabled_checkbox.stateChanged.connect(self._on_recurrence_enabled_changed)
        recurrence_control_layout.addWidget(self.recurrence_enabled_checkbox)

        # 반복 빈도 선택 (ComboBox)
        self.recurrence_frequency_combo = QComboBox()
        self.recurrence_frequency_combo.setObjectName("recurrenceCombo")
        self.recurrence_frequency_combo.addItem("매일", "daily")
        self.recurrence_frequency_combo.addItem("매주", "weekly")
        self.recurrence_frequency_combo.addItem("매달", "monthly")
        self.recurrence_frequency_combo.setEnabled(False)  # 초기 비활성화
        self.recurrence_frequency_combo.currentIndexChanged.connect(self._on_recurrence_frequency_changed)
        recurrence_control_layout.addWidget(self.recurrence_frequency_combo)

        recurrence_control_layout.addStretch()
        recurrence_container_layout.addLayout(recurrence_control_layout)

        # --- 신규 UI: 종료일 설정 ---
        recurrence_end_layout = QHBoxLayout()
        recurrence_end_layout.setSpacing(10)

        self.recurrence_end_checkbox = QCheckBox("종료일")
        self.recurrence_end_checkbox.setObjectName("recurrenceCheckbox")
        self.recurrence_end_checkbox.setEnabled(False)  # 초기 비활성화
        self.recurrence_end_checkbox.stateChanged.connect(self._on_recurrence_end_changed)
        recurrence_end_layout.addWidget(self.recurrence_end_checkbox)

        self.recurrence_end_btn = QPushButton("날짜 선택")
        self.recurrence_end_btn.setObjectName("recurrenceEndBtn")
        self.recurrence_end_btn.clicked.connect(self._on_recurrence_end_select)
        self.recurrence_end_btn.setEnabled(False)
        recurrence_end_layout.addWidget(self.recurrence_end_btn)

        recurrence_end_layout.addStretch()
        recurrence_container_layout.addLayout(recurrence_end_layout)

        # 종료일 저장용 변수
        self.recurrence_end_date = None

        # --- 신규 UI: 주간 반복 요일 선택 ---
        self.weekdays_container = QWidget()
        weekdays_layout = QVBoxLayout()
        weekdays_layout.setContentsMargins(0, 0, 0, 0)
        weekdays_layout.setSpacing(8)
        self.weekdays_container.setLayout(weekdays_layout)
        self.weekdays_container.setVisible(False)  # 초기 숨김

        weekdays_label = QLabel("반복 요일:")
        weekdays_label.setObjectName("sectionLabel")
        weekdays_layout.addWidget(weekdays_label)

        weekdays_checkboxes_layout = QHBoxLayout()
        weekdays_checkboxes_layout.setSpacing(5)
        self.weekday_checkboxes = []
        weekday_names = ["월", "화", "수", "목", "금", "토", "일"]

        for i, name in enumerate(weekday_names):
            checkbox = QCheckBox(name)
            checkbox.setObjectName("weekdayCheckbox")
            checkbox.setProperty("weekday", i)  # 0=월, 6=일
            self.weekday_checkboxes.append(checkbox)
            weekdays_checkboxes_layout.addWidget(checkbox)

        weekdays_layout.addLayout(weekdays_checkboxes_layout)
        recurrence_container_layout.addWidget(self.weekdays_container)

        # --- 신규 UI: 하위 할일 복사 옵션 ---
        self.copy_subtasks_checkbox = QCheckBox("반복 시 하위 할일도 함께 복사")
        self.copy_subtasks_checkbox.setObjectName("recurrenceCheckbox")
        self.copy_subtasks_checkbox.setToolTip("활성화하면 반복 할일 완료 시 하위 할일도 복사됩니다.")
        self.copy_subtasks_checkbox.setEnabled(False)  # 초기 비활성화
        recurrence_container_layout.addWidget(self.copy_subtasks_checkbox)

        # 반복 설명 라벨
        self.recurrence_description = QLabel("")
        self.recurrence_description.setObjectName("recurrenceDescription")
        self.recurrence_description.setWordWrap(True)
        recurrence_container_layout.addWidget(self.recurrence_description)

        self.recurrence_section.add_content(recurrence_container)

        # 스크롤 영역 설정
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)

        # === 버튼 영역 (하단 고정) ===
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(24, 16, 24, 24)
        button_layout.setSpacing(config.LAYOUT_SPACING['edit_dialog_buttons'])

        self.cancel_btn = QPushButton("취소")
        self.cancel_btn.setObjectName("cancelBtn")
        self.cancel_btn.clicked.connect(self.reject)

        self.save_btn = QPushButton("저장")
        self.save_btn.setObjectName("saveBtn")
        self.save_btn.clicked.connect(self._on_save_clicked)

        button_layout.addStretch()
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.save_btn)

        main_layout.addLayout(button_layout)

        # 내용 입력창에 포커스
        self.content_edit.setFocus()

    def _on_recurrence_enabled_changed(self, state: int) -> None:
        """반복 활성화/비활성화 시 호출"""
        is_enabled = state == Qt.CheckState.Checked.value
        self.recurrence_frequency_combo.setEnabled(is_enabled)
        self.recurrence_end_checkbox.setEnabled(is_enabled)
        self.copy_subtasks_checkbox.setEnabled(is_enabled)

        # 주간 반복일 때만 요일 선택 표시
        if is_enabled and self.recurrence_frequency_combo.currentData() == "weekly":
            self.weekdays_container.setVisible(True)
        else:
            self.weekdays_container.setVisible(False)

        # 설명 업데이트
        self._update_recurrence_description()

    def _on_recurrence_frequency_changed(self, index: int) -> None:
        """빈도 변경 시 요일 선택 표시/숨김"""
        frequency = self.recurrence_frequency_combo.currentData()
        is_weekly = frequency == "weekly"

        # 주간 반복일 때만 요일 선택 표시
        self.weekdays_container.setVisible(
            is_weekly and self.recurrence_enabled_checkbox.isChecked()
        )

        self._update_recurrence_description()

    def _on_recurrence_end_changed(self, state: int) -> None:
        """종료일 체크박스 토글"""
        is_checked = state == Qt.CheckState.Checked.value
        self.recurrence_end_btn.setEnabled(is_checked)

        if not is_checked:
            self.recurrence_end_date = None
            self.recurrence_end_btn.setText("날짜 선택")

    def _on_recurrence_end_select(self) -> None:
        """종료일 선택 다이얼로그"""
        # 기존 종료일을 datetime 객체로 변환
        initial_date = None
        if self.recurrence_end_date:
            try:
                if isinstance(self.recurrence_end_date, datetime):
                    initial_date = self.recurrence_end_date
                else:
                    # date 객체인 경우 datetime으로 변환
                    initial_date = datetime.combine(
                        self.recurrence_end_date,
                        datetime.min.time()
                    )
            except:
                pass

        # DatePickerDialog 사용
        dialog = DatePickerDialog(
            parent=self,
            title="종료일 선택",
            initial_date=initial_date,
            min_date=QDate.currentDate(),
            show_clear_button=False
        )

        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected = dialog.get_selected_date()
            if selected:
                self.recurrence_end_date = selected.date()
                self.recurrence_end_btn.setText(selected.strftime("%Y-%m-%d"))

    def _update_recurrence_description(self) -> None:
        """반복 설명 업데이트"""
        if self.recurrence_enabled_checkbox.isChecked():
            frequency_text = self.recurrence_frequency_combo.currentText()
            self.recurrence_description.setText(
                f"완료 체크 시 {frequency_text} 반복되는 새로운 할일이 자동으로 생성됩니다."
            )
        else:
            self.recurrence_description.setText("")

    def set_todo(self, todo_id: Optional[str], content: str = "", due_date: Optional[str] = None, subtasks: List[SubTask] = None, recurrence: Optional[RecurrenceRule] = None):
        """TODO 정보 설정

        Args:
            todo_id: TODO ID (None이면 신규 추가 모드)
            content: TODO 내용 (빈 문자열 가능)
            due_date: 납기일 (ISO 문자열, None 가능)
            subtasks: 하위 할일 리스트 (None 가능)
            recurrence: 반복 규칙 (RecurrenceRule 또는 None)
        """
        self.todo_id = todo_id
        self.subtasks = subtasks if subtasks else []

        # 타이틀 설정 (신규/수정 구분)
        if todo_id is None:
            self.setWindowTitle("TODO 추가")
            self.title_label.setText("TODO 추가")
        else:
            self.setWindowTitle("TODO 편집")
            self.title_label.setText("TODO 편집")

        # 내용 설정
        self.content_edit.setPlainText(content)

        # 날짜 설정
        if due_date:
            try:
                if 'T' in due_date:
                    dt = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
                    qdate = QDate(dt.year, dt.month, dt.day)
                else:
                    dt = datetime.fromisoformat(due_date)
                    qdate = QDate(dt.year, dt.month, dt.day)
                self.calendar.setSelectedDate(qdate)
                self._update_date_label(due_date)
            except (ValueError, AttributeError):
                pass
        else:
            # 신규 추가 모드일 때 오늘 날짜 자동 선택
            if todo_id is None:
                # 신규 추가 모드: 오늘 날짜 자동 선택 및 표시
                today = QDate.currentDate()
                self.calendar.setSelectedDate(today)
                today_str = today.toString(Qt.DateFormat.ISODate)
                self._update_date_label(today_str)
            else:
                # 편집 모드에서 날짜 없음: 오늘 날짜 선택하되 "없음" 표시
                self.calendar.setSelectedDate(QDate.currentDate())
                self._update_date_label(None)

        # 하위 할일 UI 업데이트
        self._update_subtasks_ui()

        # 반복 설정
        if recurrence:
            # 시그널 일시 차단 (UI 업데이트 중 핸들러 호출 방지)
            self.recurrence_enabled_checkbox.blockSignals(True)
            self.recurrence_frequency_combo.blockSignals(True)

            try:
                # 빈도 선택 (반복 체크박스보다 먼저 설정)
                frequency = recurrence.frequency
                index = self.recurrence_frequency_combo.findData(frequency)
                if index >= 0:
                    self.recurrence_frequency_combo.setCurrentIndex(index)

                # 반복 활성화 (빈도 설정 후에 활성화)
                self.recurrence_enabled_checkbox.setChecked(True)

                # 신규: end_date 설정
                if recurrence.end_date:
                    self.recurrence_end_checkbox.setChecked(True)
                    if isinstance(recurrence.end_date, datetime):
                        self.recurrence_end_date = recurrence.end_date.date()
                        self.recurrence_end_btn.setText(recurrence.end_date.strftime("%Y-%m-%d"))
                    else:
                        self.recurrence_end_date = recurrence.end_date
                        self.recurrence_end_btn.setText(recurrence.end_date.strftime("%Y-%m-%d"))

                # 신규: weekdays 설정
                if recurrence.weekdays and frequency == "weekly":
                    for checkbox in self.weekday_checkboxes:
                        weekday = checkbox.property("weekday")
                        if weekday in recurrence.weekdays:
                            checkbox.setChecked(True)

                # 신규: copy_subtasks 설정
                self.copy_subtasks_checkbox.setChecked(recurrence.copy_subtasks)
            finally:
                # 시그널 차단 해제
                self.recurrence_enabled_checkbox.blockSignals(False)
                self.recurrence_frequency_combo.blockSignals(False)

            # UI 활성화 상태 수동 업데이트
            self.recurrence_frequency_combo.setEnabled(True)
            self.recurrence_end_checkbox.setEnabled(True)
            self.copy_subtasks_checkbox.setEnabled(True)

            # 주간 반복이고 요일이 있으면 컨테이너 표시
            if recurrence.weekdays and frequency == "weekly":
                self.weekdays_container.setVisible(True)
            else:
                self.weekdays_container.setVisible(False)

            # 설명 업데이트
            self._update_recurrence_description()
        else:
            # 반복 설정 없음: 초기화
            self.recurrence_enabled_checkbox.setChecked(False)
            self.recurrence_end_checkbox.setChecked(False)
            self.recurrence_end_date = None
            self.recurrence_end_btn.setText("날짜 선택")
            for checkbox in self.weekday_checkboxes:
                checkbox.setChecked(False)
            self.weekdays_container.setVisible(False)

            # P2-4 수정: 신규 추가 모드일 때 하위 할일 복사 기본값 체크
            if todo_id is None:
                # 신규 추가 모드: 하위 할일 복사 옵션 기본 체크
                self.copy_subtasks_checkbox.setChecked(True)
            else:
                # 편집 모드: 체크 해제
                self.copy_subtasks_checkbox.setChecked(False)

    def _on_date_clicked(self, qdate: QDate):
        """캘린더 날짜 클릭 시"""
        date_str = qdate.toString(Qt.DateFormat.ISODate)
        self._update_date_label(date_str)

    def _on_clear_date(self):
        """날짜 클리어"""
        self.calendar.setSelectedDate(QDate.currentDate())
        self._update_date_label(None)

    def _update_date_label(self, date_str: Optional[str]):
        """선택된 날짜 레이블 업데이트"""
        if date_str:
            # ISO 형식을 사용자 친화적 형식으로 변환
            try:
                if 'T' in date_str:
                    dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    formatted = dt.strftime("%Y년 %m월 %d일")
                else:
                    dt = datetime.fromisoformat(date_str)
                    formatted = dt.strftime("%Y년 %m월 %d일")
                self.selected_date_label.setText(f"선택된 날짜: {formatted}")
            except ValueError:
                self.selected_date_label.setText(f"선택된 날짜: {date_str}")
        else:
            self.selected_date_label.setText("선택된 날짜: 없음")

    def _on_save_clicked(self):
        """저장 버튼 클릭"""
        content = self.content_edit.toPlainText().strip()
        if not content:
            # 내용이 비어있으면 저장하지 않음
            return

        # 선택된 날짜 가져오기
        qdate = self.calendar.selectedDate()
        current_qdate = QDate.currentDate()
        if qdate != current_qdate or self.selected_date_label.text() != "선택된 날짜: 없음":
            due_date = qdate.toString(Qt.DateFormat.ISODate)
        else:
            due_date = ""

        # 반복 설정이 있는데 납기일이 없는 경우 경고
        if self.recurrence_enabled_checkbox.isChecked() and not due_date:
            QMessageBox.warning(
                self,
                "경고",
                "반복 할일은 반드시 납기일이 있어야 합니다."
            )
            return

        # 시그널 발생 (todo_id가 None이면 신규, 아니면 수정)
        # 시그널 타입이 str이므로 None을 빈 문자열로 변환
        todo_id_str = self.todo_id if self.todo_id is not None else ""
        self.save_requested.emit(todo_id_str, content, due_date)

        # 다이얼로그 닫기
        self.accept()

    def _update_subtasks_ui(self):
        """하위 할일 UI 업데이트"""
        # 리스트 클리어
        self.subtasks_list.clear()

        # 하위 할일 추가
        for subtask in self.subtasks:
            self._add_subtask_item(subtask)

        # 완료 카운트 업데이트
        self._update_subtasks_count()

    def _add_subtask_item(self, subtask: SubTask):
        """하위 할일 아이템을 리스트에 추가"""
        # 아이템 위젯 생성
        item_widget = QWidget()
        item_layout = QHBoxLayout(item_widget)
        item_layout.setContentsMargins(5, 5, 5, 5)
        item_layout.setSpacing(8)

        # 체크박스
        checkbox = QCheckBox()
        checkbox.setChecked(subtask.completed)
        checkbox.setObjectName("subtaskCheckbox")
        checkbox.stateChanged.connect(lambda state, st=subtask: self._on_subtask_toggled(st, state))
        item_layout.addWidget(checkbox)

        # 내용 라벨
        content_label = QLabel(str(subtask.content))
        content_label.setObjectName("subtaskContentLabel")
        if subtask.completed:
            content_label.setStyleSheet(f"text-decoration: line-through; color: {config.COLORS['text_disabled']};")
        else:
            content_label.setStyleSheet(f"color: {config.COLORS['text_primary']};")
        item_layout.addWidget(content_label, 1)

        # 납기일 표시 (있는 경우)
        if subtask.due_date:
            due_label = QLabel(subtask.due_date.format_display_text())
            due_label.setObjectName("subtaskDueLabel")
            due_label.setStyleSheet(f"color: {config.COLORS['text_secondary']}; font-size: {config.FONT_SIZES['xs']}px;")
            item_layout.addWidget(due_label)

        # 편집 버튼
        edit_btn = QPushButton("편집")
        edit_btn.setObjectName("subtaskEditBtn")
        edit_btn.clicked.connect(lambda checked, st=subtask: self._on_edit_subtask(st))
        item_layout.addWidget(edit_btn)

        # 삭제 버튼
        delete_btn = QPushButton("삭제")
        delete_btn.setObjectName("subtaskDeleteBtn")
        delete_btn.clicked.connect(lambda checked, st=subtask: self._on_delete_subtask(st))
        item_layout.addWidget(delete_btn)

        # QListWidget에 추가
        list_item = QListWidgetItem()
        list_item.setSizeHint(item_widget.sizeHint())
        self.subtasks_list.addItem(list_item)
        self.subtasks_list.setItemWidget(list_item, item_widget)

    def _on_add_subtask(self):
        """하위 할일 추가"""
        # 간단한 다이얼로그 생성
        dialog = SubTaskEditDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            content, due_date = dialog.get_data()
            # 새로운 SubTask 생성
            new_subtask = SubTask.create(content=content, due_date=due_date)
            self.subtasks.append(new_subtask)
            self._update_subtasks_ui()

    def _on_edit_subtask(self, subtask: SubTask):
        """하위 할일 편집"""
        dialog = SubTaskEditDialog(self)
        dialog.set_data(str(subtask.content), str(subtask.due_date) if subtask.due_date else None)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            content, due_date = dialog.get_data()
            # SubTask 업데이트
            from ...domain.value_objects.content import Content
            from ...domain.value_objects.due_date import DueDate
            subtask.update_content(Content(value=content))
            subtask.set_due_date(DueDate.from_string(due_date) if due_date else None)
            self._update_subtasks_ui()

    def _on_delete_subtask(self, subtask: SubTask):
        """하위 할일 삭제"""
        # 리스트에서 제거
        self.subtasks = [st for st in self.subtasks if st.id != subtask.id]
        self._update_subtasks_ui()

    def _on_subtask_toggled(self, subtask: SubTask, state: Qt.CheckState):
        """하위 할일 체크박스 토글"""
        subtask.completed = (state == Qt.CheckState.Checked)
        self._update_subtasks_ui()

    def _update_subtasks_count(self):
        """하위 할일 완료 카운트 업데이트"""
        completed_count = sum(1 for st in self.subtasks if st.completed)
        total_count = len(self.subtasks)
        self.subtasks_section.set_count_text(f"{completed_count}/{total_count} 완료")

    def get_subtasks(self) -> List[SubTask]:
        """하위 할일 리스트 반환"""
        return self.subtasks

    def get_recurrence(self) -> Optional[RecurrenceRule]:
        """반복 규칙 반환

        Returns:
            RecurrenceRule 또는 None
        """
        if not self.recurrence_enabled_checkbox.isChecked():
            return None

        from datetime import time

        frequency = self.recurrence_frequency_combo.currentData()

        # end_date 가져오기
        end_date = None
        if self.recurrence_end_checkbox.isChecked() and self.recurrence_end_date:
            # date → datetime 변환 (시간은 23:59:59로 설정)
            end_date = datetime.combine(self.recurrence_end_date, time(23, 59, 59))

        # weekdays 가져오기 (주간 반복일 때만)
        weekdays = None
        if frequency == "weekly":
            selected_weekdays = [
                checkbox.property("weekday")
                for checkbox in self.weekday_checkboxes
                if checkbox.isChecked()
            ]
            if selected_weekdays:
                weekdays = selected_weekdays

        # copy_subtasks 가져오기
        copy_subtasks = self.copy_subtasks_checkbox.isChecked()

        return RecurrenceRule.create(
            frequency=frequency,
            end_date=end_date,
            weekdays=weekdays,
            copy_subtasks=copy_subtasks
        )

    def keyPressEvent(self, event):
        """키보드 이벤트: ESC로 닫기"""
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)

    def apply_styles(self):
        """스타일 시트 적용"""
        self.setStyleSheet(f"""
            QDialog {{
                background: {config.COLORS['secondary_bg']};
                border-radius: {config.UI_METRICS['border_radius']['xl']}px;
            }}

            /* Scroll Area */
            QScrollArea {{
                background: transparent;
                border: none;
            }}

            QScrollBar:vertical {{
                background: {config.COLORS['secondary_bg']};
                width: 10px;
                border-radius: 5px;
                margin: 0px;
            }}

            QScrollBar::handle:vertical {{
                background: {config.COLORS['border_strong']};
                min-height: 20px;
                border-radius: 5px;
            }}

            QScrollBar::handle:vertical:hover {{
                background: {config.COLORS['accent']};
            }}

            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}

            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}

            QLabel#titleLabel {{
                color: {config.COLORS['text_primary']};
                font-size: {config.FONT_SIZES['xxl']}px;
                font-weight: 600;
            }}

            QLabel#sectionLabel {{
                color: {config.COLORS['text_secondary']};
                font-size: {config.FONT_SIZES['base']}px;
                font-weight: 500;
                margin-top: 5px;
            }}

            QLabel#selectedDateLabel {{
                color: {config.COLORS['text_secondary']};
                font-size: {config.FONT_SIZES['md']}px;
                font-style: italic;
            }}

            QTextEdit#contentEdit {{
                background: {config.COLORS['card']};
                border: {config.UI_METRICS['border_width']['thin']}px solid {config.COLORS['border']};
                border-radius: {config.UI_METRICS['border_radius']['lg']}px;
                padding: {config.UI_METRICS['padding']['md'][0]}px;
                color: {config.COLORS['text_primary']};
                font-size: {config.FONT_SIZES['lg']}px;
                font-family: "Segoe UI", "Malgun Gothic", sans-serif;
            }}

            QTextEdit#contentEdit:focus {{
                border-color: {config.COLORS['accent']};
            }}

            QPushButton#saveBtn {{
                background: {config.COLORS['accent']};
                color: white;
                border: none;
                border-radius: {config.UI_METRICS['border_radius']['lg']}px;
                padding: {config.UI_METRICS['padding']['lg'][0]}px {config.UI_METRICS['padding']['lg'][1]}px;
                font-weight: 500;
                font-size: {config.FONT_SIZES['lg']}px;
                min-width: 80px;
            }}

            QPushButton#saveBtn:hover {{
                background: {config.COLORS['accent_hover']};
            }}

            QPushButton#saveBtn:pressed {{
                background: #B56B4A;
            }}

            QPushButton#cancelBtn {{
                background: transparent;
                border: {config.UI_METRICS['border_width']['thin']}px solid {config.COLORS['border']};
                border-radius: {config.UI_METRICS['border_radius']['lg']}px;
                padding: {config.UI_METRICS['padding']['lg'][0]}px {config.UI_METRICS['padding']['lg'][1]}px;
                color: {config.COLORS['text_secondary']};
                font-size: {config.FONT_SIZES['lg']}px;
                min-width: 80px;
            }}

            QPushButton#cancelBtn:hover {{
                border-color: {config.COLORS['accent']};
                color: {config.COLORS['text_primary']};
            }}

            QPushButton#cancelBtn:pressed {{
                background: rgba(64, 64, 64, 0.1);
            }}

            QPushButton#clearBtn {{
                background: transparent;
                border: {config.UI_METRICS['border_width']['thin']}px solid {config.COLORS['border']};
                border-radius: {config.UI_METRICS['border_radius']['lg']}px;
                padding: {config.UI_METRICS['padding']['lg'][0]}px {config.UI_METRICS['padding']['lg'][1]}px;
                color: {config.COLORS['text_secondary']};
                font-size: {config.FONT_SIZES['lg']}px;
            }}

            QPushButton#clearBtn:hover {{
                border-color: {config.COLORS['accent']};
                color: {config.COLORS['text_primary']};
            }}

            QPushButton#clearBtn:pressed {{
                background: rgba(64, 64, 64, 0.1);
            }}

            /* Calendar Widget */
            QCalendarWidget QWidget {{
                background-color: {config.COLORS['card']};
                color: {config.COLORS['text_primary']};
            }}

            QCalendarWidget QAbstractItemView:enabled {{
                background-color: {config.COLORS['secondary_bg']};
                selection-background-color: {config.COLORS['accent']};
                selection-color: white;
                border-radius: {config.UI_METRICS['border_radius']['sm']}px;
            }}

            QCalendarWidget QWidget#qt_calendar_navigationbar {{
                background-color: {config.COLORS['card']};
            }}

            QCalendarWidget QToolButton {{
                color: {config.COLORS['text_primary']};
                background-color: transparent;
                border-radius: {config.UI_METRICS['border_radius']['sm']}px;
                padding: {config.UI_METRICS['padding']['sm'][0]}px;
            }}

            QCalendarWidget QToolButton:hover {{
                background-color: {config.COLORS['card_hover']};
            }}

            QCalendarWidget QMenu {{
                background-color: {config.COLORS['secondary_bg']};
                color: {config.COLORS['text_primary']};
                border: {config.UI_METRICS['border_width']['thin']}px solid {config.COLORS['border']};
            }}

            QCalendarWidget QSpinBox {{
                background-color: {config.COLORS['card']};
                color: {config.COLORS['text_primary']};
                selection-background-color: {config.COLORS['accent']};
                border: {config.UI_METRICS['border_width']['thin']}px solid {config.COLORS['border']};
                border-radius: {config.UI_METRICS['border_radius']['sm']}px;
                padding: {config.UI_METRICS['padding']['sm'][0]}px;
            }}

            /* SubTasks Section */
            QPushButton#addSubtaskBtn {{
                background: transparent;
                border: {config.UI_METRICS['border_width']['thin']}px dashed {config.COLORS['border']};
                border-radius: {config.UI_METRICS['border_radius']['lg']}px;
                padding: {config.UI_METRICS['padding']['md'][0]}px {config.UI_METRICS['padding']['md'][1]}px;
                color: {config.COLORS['text_secondary']};
                font-size: {config.FONT_SIZES['base']}px;
            }}

            QPushButton#addSubtaskBtn:hover {{
                border-color: {config.COLORS['accent']};
                color: {config.COLORS['text_primary']};
            }}

            QListWidget#subtasksList {{
                background: {config.COLORS['card']};
                border: {config.UI_METRICS['border_width']['thin']}px solid {config.COLORS['border']};
                border-radius: {config.UI_METRICS['border_radius']['lg']}px;
                padding: 5px;
            }}

            QPushButton#subtaskEditBtn, QPushButton#subtaskDeleteBtn {{
                background: transparent;
                border: {config.UI_METRICS['border_width']['thin']}px solid {config.COLORS['border']};
                border-radius: {config.UI_METRICS['border_radius']['sm']}px;
                padding: 4px 12px;
                color: {config.COLORS['text_secondary']};
                font-size: {config.FONT_SIZES['sm']}px;
                min-width: 50px;
            }}

            QPushButton#subtaskEditBtn:hover {{
                border-color: {config.COLORS['accent']};
                color: {config.COLORS['text_primary']};
            }}

            QPushButton#subtaskDeleteBtn:hover {{
                border-color: #ef5350;
                color: #ef5350;
            }}

            /* Recurrence Section */
            QCheckBox#recurrenceCheckbox {{
                color: {config.COLORS['text_primary']};
                font-size: {config.FONT_SIZES['base']}px;
                spacing: 8px;
            }}

            QCheckBox#recurrenceCheckbox:hover {{
                color: {config.COLORS['accent']};
            }}

            QComboBox#recurrenceCombo {{
                background: {config.COLORS['card']};
                border: {config.UI_METRICS['border_width']['thin']}px solid {config.COLORS['border']};
                border-radius: {config.UI_METRICS['border_radius']['lg']}px;
                padding: {config.UI_METRICS['padding']['md'][0]}px {config.UI_METRICS['padding']['md'][1]}px;
                color: {config.COLORS['text_primary']};
                font-size: {config.FONT_SIZES['base']}px;
                min-width: 100px;
            }}

            QComboBox#recurrenceCombo:hover {{
                border-color: {config.COLORS['accent']};
            }}

            QComboBox#recurrenceCombo:disabled {{
                color: {config.COLORS['text_disabled']};
                border-color: {config.COLORS['border']};
            }}

            QComboBox#recurrenceCombo::drop-down {{
                border: none;
                padding-right: 10px;
            }}

            QComboBox#recurrenceCombo::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 6px solid {config.COLORS['text_secondary']};
                margin-right: 5px;
            }}

            QComboBox#recurrenceCombo QAbstractItemView {{
                background: {config.COLORS['secondary_bg']};
                border: {config.UI_METRICS['border_width']['thin']}px solid {config.COLORS['border']};
                selection-background-color: {config.COLORS['accent']};
                selection-color: white;
                color: {config.COLORS['text_primary']};
                padding: 4px;
            }}

            QLabel#recurrenceDescription {{
                color: {config.COLORS['text_secondary']};
                font-size: {config.FONT_SIZES['sm']}px;
                font-style: italic;
            }}

            /* 종료일 버튼 */
            QPushButton#recurrenceEndBtn {{
                background: transparent;
                border: {config.UI_METRICS['border_width']['thin']}px solid {config.COLORS['border']};
                border-radius: {config.UI_METRICS['border_radius']['lg']}px;
                padding: {config.UI_METRICS['padding']['md'][0]}px {config.UI_METRICS['padding']['md'][1]}px;
                color: {config.COLORS['text_secondary']};
                font-size: {config.FONT_SIZES['base']}px;
                min-width: 100px;
            }}

            QPushButton#recurrenceEndBtn:hover {{
                border-color: {config.COLORS['accent']};
                color: {config.COLORS['text_primary']};
            }}

            QPushButton#recurrenceEndBtn:disabled {{
                color: {config.COLORS['text_disabled']};
                border-color: {config.COLORS['border']};
            }}

            /* 요일 체크박스 */
            QCheckBox#weekdayCheckbox {{
                color: {config.COLORS['text_primary']};
                font-size: {config.FONT_SIZES['base']}px;
                spacing: 5px;
            }}

            QCheckBox#weekdayCheckbox::indicator {{
                width: 16px;
                height: 16px;
                border: {config.UI_METRICS['border_width']['thin']}px solid {config.COLORS['border']};
                background: {config.COLORS['secondary_bg']};
                border-radius: {config.UI_METRICS['border_radius']['sm']}px;
            }}

            QCheckBox#weekdayCheckbox::indicator:hover {{
                border-color: {config.COLORS['accent']};
            }}

            QCheckBox#weekdayCheckbox::indicator:checked {{
                background: {config.COLORS['accent']};
                border-color: {config.COLORS['accent']};
            }}

            QCheckBox#weekdayCheckbox:hover {{
                color: {config.COLORS['accent']};
            }}
        """)


class SubTaskEditDialog(QDialog):
    """하위 할일 편집 다이얼로그 (간단 버전)"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setModal(True)
        self.setWindowTitle("하위 할일 편집")
        self.setFixedSize(380, 300)
        self._setup_ui()
        self._apply_styles()

    def _setup_ui(self):
        """UI 구성"""
        # 다이얼로그 배경 렌더링을 위한 속성 설정
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 제목
        title_label = QLabel("하위 할일")
        title_label.setObjectName("titleLabel")
        layout.addWidget(title_label)

        # 내용 입력
        content_label = QLabel("내용")
        content_label.setObjectName("sectionLabel")
        layout.addWidget(content_label)

        self.content_edit = QTextEdit()
        self.content_edit.setObjectName("contentEdit")
        self.content_edit.setPlaceholderText("하위 할일 내용을 입력하세요...")
        self.content_edit.setMinimumHeight(80)
        self.content_edit.setMaximumHeight(100)
        layout.addWidget(self.content_edit)

        # 날짜 입력 (간단 버전)
        date_label = QLabel("납기일 (선택)")
        date_label.setObjectName("sectionLabel")
        layout.addWidget(date_label)

        date_row = QHBoxLayout()
        date_row.setSpacing(10)

        # 날짜 선택 버튼
        self.date_btn = QPushButton("날짜 선택")
        self.date_btn.setObjectName("dateBtn")
        self.date_btn.clicked.connect(self._on_select_date)
        date_row.addWidget(self.date_btn)

        # 선택된 날짜 표시
        self.selected_date_label = QLabel("없음")
        self.selected_date_label.setObjectName("selectedDateLabel")
        date_row.addWidget(self.selected_date_label, 1)

        layout.addLayout(date_row)

        # 버튼 영역
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        self.cancel_btn = QPushButton("취소")
        self.cancel_btn.setObjectName("cancelBtn")
        self.cancel_btn.clicked.connect(self.reject)

        self.save_btn = QPushButton("저장")
        self.save_btn.setObjectName("saveBtn")
        self.save_btn.clicked.connect(self._on_save)

        button_layout.addStretch()
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.save_btn)

        layout.addLayout(button_layout)

        # 내용 입력창에 포커스
        self.content_edit.setFocus()

        # 선택된 날짜 저장용 변수
        self.selected_date: Optional[str] = None

    def _on_select_date(self):
        """날짜 선택 다이얼로그 표시"""
        # 기존 선택된 날짜를 datetime 객체로 변환
        initial_date = None
        if self.selected_date:
            try:
                initial_date = datetime.fromisoformat(self.selected_date)
            except:
                pass

        # DatePickerDialog 사용
        dialog = DatePickerDialog(
            parent=self,
            title="날짜 선택",
            initial_date=initial_date,
            show_clear_button=True
        )

        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected = dialog.get_selected_date()
            if selected:
                # 날짜 선택됨
                self.selected_date = selected.strftime("%Y-%m-%d")
                self.selected_date_label.setText(selected.strftime("%Y년 %m월 %d일"))
            else:
                # 날짜 제거됨
                self.selected_date = None
                self.selected_date_label.setText("없음")

    def _on_save(self):
        """저장 버튼 클릭"""
        content = self.content_edit.toPlainText().strip()
        if not content:
            return
        self.accept()

    def set_data(self, content: str, due_date: Optional[str] = None):
        """데이터 설정"""
        self.content_edit.setPlainText(content)
        if due_date:
            self.selected_date = due_date
            try:
                dt = datetime.fromisoformat(due_date)
                self.selected_date_label.setText(dt.strftime("%Y년 %m월 %d일"))
            except:
                self.selected_date_label.setText(due_date)
        else:
            self.selected_date = None
            self.selected_date_label.setText("없음")

    def get_data(self) -> tuple[str, Optional[str]]:
        """데이터 반환 (content, due_date)"""
        content = self.content_edit.toPlainText().strip()
        return (content, self.selected_date)

    def _apply_styles(self):
        """스타일 적용"""
        self.setStyleSheet(f"""
            QDialog {{
                background: {config.COLORS['secondary_bg']};
            }}

            QLabel#titleLabel {{
                color: {config.COLORS['text_primary']};
                font-size: {config.FONT_SIZES['xl']}px;
                font-weight: 600;
            }}

            QLabel#sectionLabel {{
                color: {config.COLORS['text_secondary']};
                font-size: {config.FONT_SIZES['base']}px;
                font-weight: 500;
            }}

            QLabel#selectedDateLabel {{
                color: {config.COLORS['text_secondary']};
                font-size: {config.FONT_SIZES['md']}px;
            }}

            QTextEdit#contentEdit {{
                background: {config.COLORS['card']};
                border: {config.UI_METRICS['border_width']['thin']}px solid {config.COLORS['border']};
                border-radius: {config.UI_METRICS['border_radius']['lg']}px;
                padding: {config.UI_METRICS['padding']['md'][0]}px;
                color: {config.COLORS['text_primary']};
                font-size: {config.FONT_SIZES['base']}px;
            }}

            QTextEdit#contentEdit:focus {{
                border-color: {config.COLORS['accent']};
            }}

            QPushButton#dateBtn {{
                background: transparent;
                border: {config.UI_METRICS['border_width']['thin']}px solid {config.COLORS['border']};
                border-radius: {config.UI_METRICS['border_radius']['lg']}px;
                padding: {config.UI_METRICS['padding']['md'][0]}px {config.UI_METRICS['padding']['md'][1]}px;
                color: {config.COLORS['text_secondary']};
                font-size: {config.FONT_SIZES['base']}px;
            }}

            QPushButton#dateBtn:hover {{
                border-color: {config.COLORS['accent']};
                color: {config.COLORS['text_primary']};
            }}

            QPushButton#saveBtn {{
                background: {config.COLORS['accent']};
                color: white;
                border: none;
                border-radius: {config.UI_METRICS['border_radius']['lg']}px;
                padding: {config.UI_METRICS['padding']['lg'][0]}px {config.UI_METRICS['padding']['lg'][1]}px;
                font-weight: 500;
                font-size: {config.FONT_SIZES['base']}px;
                min-width: 60px;
            }}

            QPushButton#saveBtn:hover {{
                background: {config.COLORS['accent_hover']};
            }}

            QPushButton#cancelBtn {{
                background: transparent;
                border: {config.UI_METRICS['border_width']['thin']}px solid {config.COLORS['border']};
                border-radius: {config.UI_METRICS['border_radius']['lg']}px;
                padding: {config.UI_METRICS['padding']['lg'][0]}px {config.UI_METRICS['padding']['lg'][1]}px;
                color: {config.COLORS['text_secondary']};
                font-size: {config.FONT_SIZES['base']}px;
                min-width: 60px;
            }}

            QPushButton#cancelBtn:hover {{
                border-color: {config.COLORS['accent']};
                color: {config.COLORS['text_primary']};
            }}
        """)
