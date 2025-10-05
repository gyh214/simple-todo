# -*- coding: utf-8 -*-
"""FooterWidget - TODO 카운트 실시간 표시

Phase 5-4: Footer 상태 표시 구현
docs/todo-app-ui.html의 .footer 구조를 정확히 재현합니다.
"""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt

import config


class FooterWidget(QWidget):
    """Footer 위젯 - TODO 카운트 실시간 표시

    UI 구조:
    - 수평 레이아웃
    - 카운트 레이블: "진행중: X개 | 완료: Y개 | 전체: Z개"

    표시 형식:
    - 기본 텍스트: #B0B0B0 (config.COLORS['text_secondary'])
    - 숫자 강조: #CC785C (config.COLORS['accent']), font-weight: 600
    """

    def __init__(self, parent=None):
        """FooterWidget 초기화

        Args:
            parent: 부모 위젯
        """
        super().__init__(parent)

        self.setup_ui()
        self.apply_styles()

        # 초기 카운트 설정
        self.update_counts(0, 0)

    def setup_ui(self) -> None:
        """UI 요소 생성 및 배치"""
        # 메인 레이아웃 (수평) - 패딩 축소
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(*config.LAYOUT_MARGINS['footer'])
        main_layout.setSpacing(config.LAYOUT_SPACING['footer_main'])

        # 카운트 레이블 (Rich Text 사용)
        self.count_label = QLabel()
        self.count_label.setObjectName("statusLabel")
        self.count_label.setTextFormat(Qt.TextFormat.RichText)

        main_layout.addWidget(self.count_label)
        main_layout.addStretch()

    def update_counts(self, in_progress: int, completed: int) -> None:
        """카운트 업데이트 (MainWindow에서 호출)

        Args:
            in_progress: 진행중 TODO 개수
            completed: 완료 TODO 개수
        """
        total = in_progress + completed

        # Rich Text로 스타일 적용
        # 기본 텍스트: text_secondary, 숫자: accent + font-weight: 600
        html = f'''
        <span style="color: {config.COLORS['text_secondary']};">
            진행중: <span style="color: {config.COLORS['accent']}; font-weight: 600;">{in_progress}개</span> |
            완료: <span style="color: {config.COLORS['accent']}; font-weight: 600;">{completed}개</span> |
            전체: <span style="color: {config.COLORS['accent']}; font-weight: 600;">{total}개</span>
        </span>
        '''

        self.count_label.setText(html)

    def apply_styles(self) -> None:
        """QSS 스타일 적용 (프로토타입 정확히 재현)"""
        style_sheet = f"""
        QWidget {{
            background-color: {config.COLORS['secondary_bg']};
            border-top: {config.UI_METRICS['border_width']['thin']}px solid {config.COLORS['border']};
        }}

        QLabel#statusLabel {{
            background: transparent;
            font-size: {config.FONT_SIZES['sm']}px;
        }}
        """

        self.setStyleSheet(style_sheet)
