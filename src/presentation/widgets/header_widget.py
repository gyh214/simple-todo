# -*- coding: utf-8 -*-
"""
헤더 위젯 - 검색창, 정렬, 추가 버튼
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QComboBox
from PyQt6.QtCore import Qt

import config


class HeaderWidget(QWidget):
    """
    헤더 위젯

    구성:
    - 상단바: 검색창 + 추가 버튼 + 정렬 드롭다운
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

        # === 상단바 (검색창 + 정렬 드롭다운 + 추가 버튼) ===
        header_top_layout = QHBoxLayout()
        header_top_layout.setSpacing(config.LAYOUT_SPACING['header_top'])

        # 검색창 (타이틀 대신) - stretch factor로 남은 공간 차지
        self.search_input = QLineEdit()
        self.search_input.setObjectName("searchInput")
        self.search_input.setPlaceholderText("할일 검색...")
        self.search_input.setClearButtonEnabled(True)  # 'x' 클리어 버튼
        header_top_layout.addWidget(self.search_input, 1)  # stretch factor = 1

        # 정렬 드롭다운 - 고정 너비
        self.sort_combo = QComboBox()
        self.sort_combo.setObjectName("sortCombo")
        self.sort_combo.addItem("납기일 빠른순", "dueDate_asc")
        self.sort_combo.addItem("납기일 늦은순", "dueDate_desc")
        self.sort_combo.addItem("오늘 납기 우선", "today_first")
        self.sort_combo.addItem("수동 순서", "manual")
        self.sort_combo.setFixedWidth(145)  # 고정 너비 145px (텍스트 완전 표시)
        header_top_layout.addWidget(self.sort_combo)

        # 추가 버튼 - 고정 너비
        self.add_button = QPushButton("할일추가")
        self.add_button.setObjectName("addButton")
        self.add_button.setFixedWidth(85)  # 고정 너비로 크기 제한
        header_top_layout.addWidget(self.add_button)

        main_layout.addLayout(header_top_layout)

    def apply_styles(self):
        """QSS 스타일시트 적용"""
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

            /* Search Input */
            #searchInput {{
                background-color: {config.COLORS['secondary_bg']};
                border: {config.UI_METRICS['border_width']['thin']}px solid {config.COLORS['border']};
                border-radius: {config.UI_METRICS['border_radius']['lg']}px;
                padding: {config.UI_METRICS['padding']['md'][0]}px {config.UI_METRICS['padding']['md'][1]}px;
                color: {config.COLORS['text_primary']};
                font-size: {config.FONT_SIZES['lg']}px;
            }}

            #searchInput:hover {{
                border-color: {config.COLORS['accent']};
            }}

            #searchInput:focus {{
                border-color: {config.COLORS['accent']};
                outline: none;
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
