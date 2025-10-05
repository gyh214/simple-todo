"""
UI 공통 상수 모듈 (DRY 원칙 적용)

모든 Manager에서 공통으로 사용되는 UI 관련 상수들을 중앙 집중화하여
코드 중복을 제거하고 일관성을 확보합니다.
"""

from typing import Any, Dict

# 다크테마 색상 상수 (기존 코드 100% 재사용)
DARK_COLORS: Dict[str, str] = {
    "bg": "#1e1e1e",
    "bg_secondary": "#2d2d30",
    "bg_hover": "#3e3e42",
    "text": "#ffffff",
    "text_secondary": "#cccccc",
    "border": "#3e3e42",
    "accent": "#007acc",
    "accent_hover": "#005a9e",
    "success": "#4caf50",
    "danger": "#f44336",
    "warning": "#ff9800",
    "button_bg": "#3e3e42",
    "button_hover": "#525252",
    "entry_bg": "#2d2d30",
    "entry_border": "#525252",
}

# 버튼 타입 상수
BUTTON_TYPES = {
    "primary": "primary",
    "secondary": "secondary",
    "danger": "danger",
    "warning": "warning",
}

# 기본 폰트 설정
DEFAULT_FONTS = {
    "default": ("Segoe UI", 9),
    "bold": ("Segoe UI", 9, "bold"),
    "small": ("Segoe UI", 8),
    "large": ("Segoe UI", 10),
}

# 공통 UI 크기 상수
UI_SIZES = {
    "button_padding_x": 15,
    "button_padding_y": 5,
    "control_padding": 4,
    "section_padding": 2,
    "widget_spacing": 1,
}

# Manager 타입 상수 (컨테이너 패턴용)
MANAGER_TYPES = {
    "ui_layout": "ui_layout",
    "control_panel": "control_panel",
    "todo_display": "todo_display",
    "event_handler": "event_handler",
    "settings": "settings",
}
