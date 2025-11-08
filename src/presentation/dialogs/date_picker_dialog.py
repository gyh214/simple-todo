# -*- coding: utf-8 -*-
"""
재사용 가능한 날짜 선택 다이얼로그
EditDialog의 중복 코드를 제거하기 위한 공통 컴포넌트
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                            QCalendarWidget)
from PyQt6.QtCore import Qt, QDate
from datetime import datetime
from typing import Optional
import config


class DatePickerDialog(QDialog):
    """재사용 가능한 날짜 선택 다이얼로그

    캘린더 위젯을 통한 날짜 선택 기능 제공.
    초기 날짜 설정, 최소 날짜 제한, 날짜 제거 버튼 등 옵션 지원.
    """

    def __init__(
        self,
        parent=None,
        title: str = "날짜 선택",
        initial_date: Optional[datetime] = None,
        min_date: Optional[QDate] = None,
        show_clear_button: bool = True
    ):
        """날짜 선택 다이얼로그 초기화

        Args:
            parent: 부모 위젯
            title: 다이얼로그 제목
            initial_date: 초기 선택 날짜 (None이면 오늘)
            min_date: 최소 선택 가능 날짜 (None이면 제한 없음)
            show_clear_button: "날짜 제거" 버튼 표시 여부
        """
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)

        self._show_clear_button = show_clear_button
        self._selected_date: Optional[datetime] = None

        self._setup_ui(initial_date, min_date)
        self._apply_styles()

    def _setup_ui(self, initial_date: Optional[datetime], min_date: Optional[QDate]):
        """UI 구성

        Args:
            initial_date: 초기 선택 날짜
            min_date: 최소 선택 가능 날짜
        """
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 캘린더 위젯
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)

        # 최소 날짜 설정
        if min_date:
            self.calendar.setMinimumDate(min_date)

        # 초기 날짜 설정
        if initial_date:
            try:
                qdate = QDate(initial_date.year, initial_date.month, initial_date.day)
                self.calendar.setSelectedDate(qdate)
            except (ValueError, AttributeError):
                # 변환 실패 시 오늘 날짜 사용
                self.calendar.setSelectedDate(QDate.currentDate())
        else:
            # 초기 날짜가 없으면 오늘 날짜
            self.calendar.setSelectedDate(QDate.currentDate())

        layout.addWidget(self.calendar)

        # 버튼 영역
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        # 날짜 제거 버튼 (옵션)
        if self._show_clear_button:
            self.clear_btn = QPushButton("날짜 제거")
            self.clear_btn.setObjectName("clearBtn")
            self.clear_btn.clicked.connect(self._on_clear_clicked)
            btn_layout.addWidget(self.clear_btn)

        btn_layout.addStretch()

        # 확인 버튼
        self.ok_btn = QPushButton("확인")
        self.ok_btn.setObjectName("okBtn")
        self.ok_btn.clicked.connect(self._on_ok_clicked)
        btn_layout.addWidget(self.ok_btn)

        # 취소 버튼
        self.cancel_btn = QPushButton("취소")
        self.cancel_btn.setObjectName("cancelBtn")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        layout.addLayout(btn_layout)

    def _on_ok_clicked(self):
        """확인 버튼 클릭 - 선택된 날짜 저장"""
        selected_qdate = self.calendar.selectedDate()
        self._selected_date = datetime(
            selected_qdate.year(),
            selected_qdate.month(),
            selected_qdate.day()
        )
        self.accept()

    def _on_clear_clicked(self):
        """날짜 제거 버튼 클릭 - 날짜 없음으로 설정"""
        self._selected_date = None
        self.accept()

    def get_selected_date(self) -> Optional[datetime]:
        """선택된 날짜 반환

        Returns:
            선택된 날짜 (datetime 객체) 또는 None (날짜 제거된 경우)
        """
        return self._selected_date

    def keyPressEvent(self, event):
        """키보드 이벤트: ESC로 닫기"""
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)

    def _apply_styles(self):
        """스타일 시트 적용 (EditDialog와 동일한 스타일)"""
        self.setStyleSheet(f"""
            QDialog {{
                background: {config.COLORS['secondary_bg']};
                border-radius: {config.UI_METRICS['border_radius']['xl']}px;
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

            /* 버튼 스타일 (EditDialog와 동일) */
            QPushButton#okBtn {{
                background: {config.COLORS['accent']};
                color: white;
                border: none;
                border-radius: {config.UI_METRICS['border_radius']['lg']}px;
                padding: {config.UI_METRICS['padding']['lg'][0]}px {config.UI_METRICS['padding']['lg'][1]}px;
                font-weight: 500;
                font-size: {config.FONT_SIZES['base']}px;
                min-width: 60px;
            }}

            QPushButton#okBtn:hover {{
                background: {config.COLORS['accent_hover']};
            }}

            QPushButton#okBtn:pressed {{
                background: #B56B4A;
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

            QPushButton#cancelBtn:pressed {{
                background: rgba(64, 64, 64, 0.1);
            }}

            QPushButton#clearBtn {{
                background: transparent;
                border: {config.UI_METRICS['border_width']['thin']}px solid {config.COLORS['border']};
                border-radius: {config.UI_METRICS['border_radius']['lg']}px;
                padding: {config.UI_METRICS['padding']['lg'][0]}px {config.UI_METRICS['padding']['lg'][1]}px;
                color: {config.COLORS['text_secondary']};
                font-size: {config.FONT_SIZES['base']}px;
                min-width: 80px;
            }}

            QPushButton#clearBtn:hover {{
                border-color: {config.COLORS['accent']};
                color: {config.COLORS['text_primary']};
            }}

            QPushButton#clearBtn:pressed {{
                background: rgba(64, 64, 64, 0.1);
            }}
        """)
