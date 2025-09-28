"""
CollapsibleSection 컴포넌트 모듈

접기/펼치기 가능한 섹션 UI 컴포넌트를 제공합니다.
DRY+CLEAN+Simple 원칙에 따라 재사용 가능한 독립 컴포넌트로 분리되었습니다.
"""

import tkinter as tk

from ..widgets import DARK_COLORS


class CollapsibleSection:
    """접기/펼치기 가능한 섹션"""

    def __init__(self, parent, title, initial_collapsed=False):
        self.parent = parent
        self.title = title
        self.is_collapsed = initial_collapsed

        self._setup_ui()

    def _setup_ui(self):
        """UI 구성"""
        colors = DARK_COLORS

        # 메인 프레임
        self.main_frame = tk.Frame(self.parent, bg=colors["bg"])

        # 헤더 프레임 (클릭 가능한 제목)
        self.header_frame = tk.Frame(
            self.main_frame,
            bg=colors["bg_secondary"],
            relief="solid",
            borderwidth=1,
            cursor="hand2",
        )
        self.header_frame.pack(fill=tk.X, pady=(0, 2))

        # 제목 라벨
        arrow = "▼" if not self.is_collapsed else "▶"
        self.title_label = tk.Label(
            self.header_frame,
            text=f"{arrow} {self.title}",
            font=("Segoe UI", 10, "bold"),
            bg=colors["bg_secondary"],
            fg=colors["text"],
            anchor="w",
            padx=10,
            pady=5,
        )
        self.title_label.pack(fill=tk.X)

        # 내용 프레임
        self.content_frame = tk.Frame(self.main_frame, bg=colors["bg"])
        if not self.is_collapsed:
            self.content_frame.pack(fill=tk.BOTH, expand=True)

        # 클릭 이벤트
        self.header_frame.bind("<Button-1>", self._toggle_section)
        self.title_label.bind("<Button-1>", self._toggle_section)

    def _toggle_section(self, event=None):
        """섹션 접기/펼치기 토글"""
        self.is_collapsed = not self.is_collapsed

        arrow = "▼" if not self.is_collapsed else "▶"
        current_text = self.title_label.cget("text")
        new_text = f"{arrow} {self.title}"
        self.title_label.configure(text=new_text)

        if self.is_collapsed:
            self.content_frame.pack_forget()
        else:
            self.content_frame.pack(fill=tk.BOTH, expand=True)

    def get_content_frame(self):
        """내용 프레임 반환"""
        return self.content_frame

    def pack(self, **kwargs):
        """메인 프레임 패킹"""
        self.main_frame.pack(**kwargs)

    def update_title(self, new_title):
        """제목 업데이트"""
        self.title = new_title
        arrow = "▼" if not self.is_collapsed else "▶"
        self.title_label.configure(text=f"{arrow} {new_title}")
