"""
UI 유틸리티 패키지

DRY+CLEAN+Simple 원칙에 따라 공통 상수와 UI 헬퍼 함수들을 제공하는 패키지입니다.
"""

from .constants import DARK_COLORS
from .ui_helpers import (
    bind_hover_effects,
    create_entry_with_placeholder,
    create_label_with_style,
    create_scrollable_frame,
    create_styled_button,
    get_button_style,
)

__all__ = [
    "DARK_COLORS",
    "create_styled_button",
    "bind_hover_effects",
    "create_scrollable_frame",
    "get_button_style",
    "create_entry_with_placeholder",
    "create_label_with_style",
]
