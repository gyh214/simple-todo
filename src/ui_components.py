"""
Windows TODO 패널 앱의 UI 컴포넌트 모듈 (하위 호환성 래퍼)

기존 코드와의 호환성을 위해 새로운 모듈화된 UI 컴포넌트들을 import합니다.
실제 구현은 ui/ 디렉토리의 모듈들에서 담당합니다.
"""

# 새로운 모듈화된 컴포넌트들을 import
from ui.widgets import (
    DARK_COLORS,
    DragDropMixin,
    ClickableTextWidget,
    TodoItemWidget
)
from ui.main_app import (
    TodoPanelApp,
    DatePickerDialog,
    CollapsibleSection
)
from ui.sort_manager import SortManager
from ui.date_utils import DateUtils

# 하위 호환성을 위한 ThemeManager 클래스 (기존 API 유지)
class ThemeManager:
    """하위 호환성을 위한 더미 ThemeManager 클래스"""

    def __init__(self, root):
        self.root = root

    def get_colors(self):
        """다크 테마 색상 반환"""
        return DARK_COLORS

# 메인 함수는 새로운 모듈의 것을 사용
def main():
    """메인 함수"""
    try:
        app = TodoPanelApp()
        app.run()
    except Exception as e:
        import tkinter.messagebox as messagebox
        messagebox.showerror("치명적 오류", f"애플리케이션을 시작할 수 없습니다:\n{e}")

# 기존 코드와의 호환성을 위한 __all__ 선언
__all__ = [
    'ThemeManager',
    'DragDropMixin',
    'ClickableTextWidget',
    'TodoItemWidget',
    'TodoPanelApp',
    'DatePickerDialog',
    'CollapsibleSection',
    'SortManager',
    'DateUtils',
    'DARK_COLORS',
    'main'
]

if __name__ == "__main__":
    main()