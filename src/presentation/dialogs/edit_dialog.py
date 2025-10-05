# -*- coding: utf-8 -*-
"""
TODO 편집 다이얼로그 구현
내용 편집, 날짜 선택 기능 제공
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QTextEdit, QPushButton,
                            QHBoxLayout, QLabel, QCalendarWidget)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from typing import Optional
from datetime import datetime
import config


class EditDialog(QDialog):
    """TODO 편집/추가 다이얼로그"""

    # 시그널: todo_id가 None이면 신규 TODO, 아니면 수정
    save_requested = pyqtSignal(str, str, str)  # todo_id (or None), content, due_date

    def __init__(self, parent=None):
        super().__init__(parent)
        self.todo_id: Optional[str] = None
        self.setup_ui()
        self.apply_styles()

        # 모달 설정
        self.setModal(True)
        self.setWindowTitle("TODO 편집")
        self.setFixedSize(*config.WIDGET_SIZES['edit_dialog_size'])

    def setup_ui(self):
        """UI 구성"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(*config.LAYOUT_MARGINS['edit_dialog'])
        layout.setSpacing(config.LAYOUT_SPACING['edit_dialog_main'])

        # 제목
        self.title_label = QLabel("TODO 편집")
        self.title_label.setObjectName("titleLabel")
        layout.addWidget(self.title_label)

        # 내용 입력 섹션
        content_label = QLabel("내용")
        content_label.setObjectName("sectionLabel")
        layout.addWidget(content_label)

        self.content_edit = QTextEdit()
        self.content_edit.setObjectName("contentEdit")
        self.content_edit.setPlaceholderText("할일 내용을 입력하세요...")
        self.content_edit.setMinimumHeight(config.WIDGET_SIZES['content_edit_height_min'])
        self.content_edit.setMaximumHeight(config.WIDGET_SIZES['content_edit_height_max'])
        layout.addWidget(self.content_edit)

        # 날짜 선택 섹션
        date_label = QLabel("납기일")
        date_label.setObjectName("sectionLabel")
        layout.addWidget(date_label)

        # 캘린더 위젯 (PyQt6 기본 제공)
        self.calendar = QCalendarWidget(self)
        self.calendar.setGridVisible(True)
        self.calendar.clicked.connect(self._on_date_clicked)
        layout.addWidget(self.calendar)

        # 날짜 클리어 버튼
        self.clear_date_btn = QPushButton("날짜 제거")
        self.clear_date_btn.setObjectName("clearBtn")
        self.clear_date_btn.clicked.connect(self._on_clear_date)
        layout.addWidget(self.clear_date_btn)

        # 선택된 날짜 표시
        self.selected_date_label = QLabel("선택된 날짜: 없음")
        self.selected_date_label.setObjectName("selectedDateLabel")
        layout.addWidget(self.selected_date_label)

        # 버튼 영역
        button_layout = QHBoxLayout()
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

        layout.addLayout(button_layout)

        # 내용 입력창에 포커스
        self.content_edit.setFocus()

    def set_todo(self, todo_id: Optional[str], content: str = "", due_date: Optional[str] = None):
        """TODO 정보 설정

        Args:
            todo_id: TODO ID (None이면 신규 추가 모드)
            content: TODO 내용 (빈 문자열 가능)
            due_date: 납기일 (ISO 문자열, None 가능)
        """
        self.todo_id = todo_id

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
            self.calendar.setSelectedDate(QDate.currentDate())
            self._update_date_label(None)

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

        # 시그널 발생 (todo_id가 None이면 신규, 아니면 수정)
        # 시그널 타입이 str이므로 None을 빈 문자열로 변환
        todo_id_str = self.todo_id if self.todo_id is not None else ""
        self.save_requested.emit(todo_id_str, content, due_date)

        # 다이얼로그 닫기
        self.accept()

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
        """)
