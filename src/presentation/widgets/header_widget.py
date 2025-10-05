# -*- coding: utf-8 -*-
"""
헤더 위젯 - 타이틀, 정렬, 입력창, 추가 버튼
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox
from PyQt6.QtCore import Qt

import config


class HeaderWidget(QWidget):
    """
    헤더 위젯

    구성:
    - 상단바: 타이틀 "Simple ToDo" + 정렬 드롭다운
    - 입력 영역: 입력창 + 추가 버튼

    docs/todo-app-ui.html 프로토타입의 레이아웃을 정확히 재현
    """

    def __init__(self):
        super().__init__()
        self.setObjectName("headerWidget")
        self.setup_ui()
        self.apply_styles()

    def setup_ui(self):
        """UI 구성"""
        # 메인 레이아웃 (수직)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(*config.LAYOUT_MARGINS['header'])
        main_layout.setSpacing(config.LAYOUT_SPACING['header_main'])

        # === 상단바 (타이틀 + 추가 버튼 + 정렬 드롭다운) ===
        header_top_layout = QHBoxLayout()
        header_top_layout.setSpacing(config.LAYOUT_SPACING['header_top'])

        # 타이틀
        self.title_label = QLabel("Simple ToDo")
        self.title_label.setObjectName("titleLabel")
        header_top_layout.addWidget(self.title_label)

        # Spacer (flex)
        header_top_layout.addStretch(1)

        # 추가 버튼
        self.add_button = QPushButton("추가")
        self.add_button.setObjectName("addButton")
        header_top_layout.addWidget(self.add_button)

        # 정렬 드롭다운
        self.sort_combo = QComboBox()
        self.sort_combo.setObjectName("sortCombo")
        self.sort_combo.addItem("정렬: 납기일 빠른순", "dueDate_asc")
        self.sort_combo.addItem("정렬: 납기일 늦은순", "dueDate_desc")
        self.sort_combo.addItem("정렬: 오늘 납기 우선", "today_first")
        self.sort_combo.addItem("정렬: 수동 순서", "manual")
        header_top_layout.addWidget(self.sort_combo)

        main_layout.addLayout(header_top_layout)

    def apply_styles(self):
        """QSS 스타일시트 적용 - HTML 프로토타입과 동일한 스타일"""
        self.setStyleSheet(f"""
            /* Header Widget */
            #headerWidget {{
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 {config.COLORS['card']},
                    stop: 1 {config.COLORS['primary_bg']}
                );
                border-bottom: 1px solid {config.COLORS['border']};
            }}

            /* Title Label */
            #titleLabel {{
                color: {config.COLORS['text_primary']};
                font-size: {config.FONT_SIZES['xxxl']}px;
                font-weight: 600;
            }}

            /* Sort ComboBox */
            #sortCombo {{
                background-color: {config.COLORS['secondary_bg']};
                border: {config.UI_METRICS['border_width']['thin']}px solid {config.COLORS['border']};
                border-radius: {config.UI_METRICS['border_radius']['lg']}px;
                padding: {config.UI_METRICS['padding']['md'][0]}px {config.UI_METRICS['padding']['md'][1]}px;
                color: {config.COLORS['text_secondary']};
                font-size: {config.FONT_SIZES['lg']}px;
            }}

            #sortCombo:hover {{
                border-color: {config.COLORS['accent']};
            }}

            #sortCombo:focus {{
                border-color: {config.COLORS['accent']};
                outline: none;
            }}

            #sortCombo::drop-down {{
                border: none;
                width: 20px;
                subcontrol-origin: padding;
                subcontrol-position: center right;
            }}

            #sortCombo::down-arrow {{
                image: none;
                width: 0;
                height: 0;
                border-left: {config.UI_METRICS['border_radius']['sm']}px solid transparent;
                border-right: {config.UI_METRICS['border_radius']['sm']}px solid transparent;
                border-top: 5px solid {config.COLORS['text_secondary']};
            }}

            #sortCombo QAbstractItemView {{
                background-color: {config.COLORS['secondary_bg']};
                border: {config.UI_METRICS['border_width']['thin']}px solid {config.COLORS['border']};
                selection-background-color: {config.COLORS['accent']};
                selection-color: white;
                color: {config.COLORS['text_primary']};
                padding: {config.UI_METRICS['border_radius']['sm']}px;
            }}

            /* Add Button */
            #addButton {{
                background-color: {config.COLORS['accent']};
                border: none;
                border-radius: {config.UI_METRICS['border_radius']['lg']}px;
                padding: {config.UI_METRICS['padding']['md'][0]}px {config.UI_METRICS['padding']['md'][1]}px;
                color: white;
                font-size: {config.FONT_SIZES['lg']}px;
                font-weight: 500;
            }}

            #addButton:hover {{
                background-color: {config.COLORS['accent_hover']};
            }}

            #addButton:pressed {{
                background-color: {config.COLORS['accent']};
            }}
        """)
