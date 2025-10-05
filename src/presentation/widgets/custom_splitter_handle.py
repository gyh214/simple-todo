# -*- coding: utf-8 -*-
"""
커스텀 Splitter Handle 위젯

HTML 프로토타입처럼 중앙에 점('⋯') + 가로선을 표시하는 QSplitterHandle
"""
from PyQt6.QtWidgets import QSplitterHandle
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QPen, QColor, QFont

import config


class CustomSplitterHandle(QSplitterHandle):
    """
    커스텀 Splitter Handle

    중앙에 점 3개('⋯') + 가로선을 표시
    호버 시 색상 변경
    """

    def __init__(self, orientation: Qt.Orientation, parent):
        super().__init__(orientation, parent)
        self._is_hovered = False
        self.setMouseTracking(True)

    def enterEvent(self, event):
        """마우스가 핸들 위로 진입"""
        self._is_hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        """마우스가 핸들에서 벗어남"""
        self._is_hovered = False
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event):
        """핸들 그리기

        HTML 프로토타입의 .divider { margin: 6px 0; }를 재현하기 위해
        실제 그리기는 위아래 6px씩 여백을 두고 수행합니다.
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 배경색 (투명) - 전체 영역
        painter.fillRect(self.rect(), QColor(config.COLORS['primary_bg']))

        # 색상 결정 (호버 여부)
        if self._is_hovered:
            line_color = QColor(config.COLORS['accent'])
            line_height = config.SPLITTER_CONFIG['line_height_hover']
        else:
            line_color = QColor(config.COLORS['border'])
            line_height = config.SPLITTER_CONFIG['line_height_normal']

        # 실제 그리기 영역 (위아래 여백)
        margin_top = config.SPLITTER_CONFIG['margin']
        margin_bottom = config.SPLITTER_CONFIG['margin']
        draw_rect = self.rect().adjusted(0, margin_top, 0, -margin_bottom)

        # 가로선 그리기 (중앙)
        pen = QPen(line_color, line_height)
        painter.setPen(pen)

        center_y = draw_rect.center().y()
        painter.drawLine(0, center_y, self.rect().width(), center_y)

        # 점 3개 ('⋯') 그리기 (중앙)
        font = QFont('Segoe UI', config.SPLITTER_CONFIG['dots_font_size'])
        painter.setFont(font)
        painter.setPen(line_color)
        painter.drawText(draw_rect, Qt.AlignmentFlag.AlignCenter, '⋯')
