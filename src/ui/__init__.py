"""
UI 모듈 패키지 초기화
"""

# 하위 호환성을 위한 기존 클래스들 import
from .widgets import ClickableTextWidget, TodoItemWidget
from .main_app import TodoPanelApp
from .sort_manager import SortManager
from .date_utils import DateUtils

# 다크테마 색상 상수 (기존 ThemeManager 대체)
DARK_COLORS = {
    'bg': '#1e1e1e',
    'bg_secondary': '#2d2d30',
    'bg_hover': '#3e3e42',
    'text': '#ffffff',
    'text_secondary': '#cccccc',
    'border': '#3e3e42',
    'accent': '#007acc',
    'accent_hover': '#005a9e',
    'success': '#4caf50',
    'danger': '#f44336',
    'warning': '#ff9800',
    'button_bg': '#3e3e42',
    'button_hover': '#525252',
    'entry_bg': '#2d2d30',
    'entry_border': '#525252'
}

__all__ = [
    'ClickableTextWidget',
    'TodoItemWidget',
    'TodoPanelApp',
    'SortManager',
    'DateUtils',
    'DARK_COLORS'
]