# -*- coding: utf-8 -*-
"""
색상 유틸리티 모듈

QPalette 생성 및 색상 파싱을 위한 중앙집중식 유틸리티 함수 제공
"""

from PyQt6.QtGui import QPalette, QColor, QBrush
from PyQt6.QtWidgets import QWidget
import config


def parse_color(color_str: str) -> QColor:
    """
    색상 문자열을 QColor 객체로 변환 (안전한 파싱)

    Args:
        color_str: rgba(r, g, b, a) 또는 #RRGGBB 형식의 색상 문자열

    Returns:
        QColor: 변환된 QColor 객체 (실패 시 흰색 반환)

    Examples:
        >>> parse_color('rgba(255, 255, 255, 0.92)')
        QColor(255, 255, 255, 235)
        >>> parse_color('#CC785C')
        QColor(204, 120, 92)
        >>> parse_color('invalid')  # 실패 시 폴백
        QColor(255, 255, 255)
    """
    import logging

    try:
        if color_str.startswith('rgba'):
            # rgba(255, 255, 255, 0.92) -> QColor
            parts = color_str.replace('rgba(', '').replace(')', '').split(',')
            if len(parts) != 4:
                raise ValueError(f"Expected 4 parts in rgba, got {len(parts)}")

            # 값 범위 제한 (0-255)
            r = max(0, min(255, int(parts[0].strip())))
            g = max(0, min(255, int(parts[1].strip())))
            b = max(0, min(255, int(parts[2].strip())))
            a = max(0, min(255, int(float(parts[3].strip()) * 255)))
            return QColor(r, g, b, a)
        else:
            # #RRGGBB -> QColor
            color = QColor(color_str)
            if not color.isValid():
                raise ValueError(f"Invalid color format: {color_str}")
            return color
    except (ValueError, IndexError) as e:
        # 폴백: 흰색 반환 (크래시 방지)
        logging.warning(f"Color parsing failed for '{color_str}': {e}. Using default white.")
        return QColor(255, 255, 255)


def create_dialog_palette() -> QPalette:
    """
    다이얼로그용 QPalette 생성 (config.COLORS 기반)

    Returns:
        QPalette: 다크 모드 색상이 적용된 팔레트 객체

    Usage:
        >>> palette = create_dialog_palette()
        >>> dialog.setPalette(palette)
        >>> dialog.setAutoFillBackground(True)
    """
    palette = QPalette()

    # 배경 색상
    palette.setColor(QPalette.ColorRole.Window, parse_color(config.COLORS['secondary_bg']))
    palette.setColor(QPalette.ColorRole.Base, parse_color(config.COLORS['card']))
    palette.setColor(QPalette.ColorRole.AlternateBase, parse_color(config.COLORS['card_hover']))

    # 텍스트 색상
    palette.setColor(QPalette.ColorRole.WindowText, parse_color(config.COLORS['text_primary']))
    palette.setColor(QPalette.ColorRole.Text, parse_color(config.COLORS['text_primary']))
    palette.setColor(QPalette.ColorRole.ButtonText, parse_color(config.COLORS['text_primary']))
    palette.setColor(QPalette.ColorRole.BrightText, parse_color(config.COLORS['text_primary']))

    # 버튼 배경
    palette.setColor(QPalette.ColorRole.Button, parse_color(config.COLORS['card']))

    # 하이라이트 (선택 영역)
    palette.setColor(QPalette.ColorRole.Highlight, parse_color(config.COLORS['accent']))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor('#FFFFFF'))

    # 링크
    palette.setColor(QPalette.ColorRole.Link, parse_color(config.COLORS['accent']))
    palette.setColor(QPalette.ColorRole.LinkVisited, parse_color(config.COLORS['accent_hover']))

    # 비활성화 상태 (Disabled 그룹)
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText,
                     parse_color(config.COLORS['text_disabled']))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text,
                     parse_color(config.COLORS['text_disabled']))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText,
                     parse_color(config.COLORS['text_disabled']))

    # 테두리 관련 색상
    palette.setColor(QPalette.ColorRole.Dark, parse_color(config.COLORS['border_strong']))
    palette.setColor(QPalette.ColorRole.Shadow, parse_color(config.COLORS['border']))

    # 툴팁 색상
    palette.setColor(QPalette.ColorRole.ToolTipBase, parse_color(config.COLORS['secondary_bg']))
    palette.setColor(QPalette.ColorRole.ToolTipText, parse_color(config.COLORS['text_primary']))

    # 플레이스홀더 색상 (QLineEdit, QTextEdit)
    palette.setColor(QPalette.ColorRole.PlaceholderText, parse_color(config.COLORS['text_disabled']))

    # Disabled 그룹 Button 색상
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Button,
                     parse_color(config.COLORS['card']))

    return palette


def apply_palette_recursive(widget: QWidget, palette: QPalette = None):
    """
    위젯과 모든 자식 위젯에 palette를 재귀적으로 적용

    Args:
        widget: 대상 위젯 (QWidget)
        palette: 적용할 QPalette (None이면 create_dialog_palette() 사용)

    Usage:
        >>> dialog = QDialog()
        >>> apply_palette_recursive(dialog)  # 기본 palette 사용
        >>>
        >>> custom_palette = create_dialog_palette()
        >>> apply_palette_recursive(dialog, custom_palette)  # 커스텀 palette 사용
    """
    if palette is None:
        palette = create_dialog_palette()

    # 현재 위젯에 palette 적용
    widget.setPalette(palette)
    widget.setAutoFillBackground(True)

    # 모든 자식 위젯에 재귀 적용
    for child in widget.children():
        if isinstance(child, QWidget):
            apply_palette_recursive(child, palette)
