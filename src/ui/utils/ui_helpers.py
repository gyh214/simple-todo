"""
공통 UI 헬퍼 함수 모듈 (DRY 원칙 적용)

Manager들에서 중복되는 UI 생성 및 스타일링 로직을 통합하여
코드 중복을 제거하고 일관된 UI 경험을 제공합니다.
"""

import tkinter as tk
from tkinter import ttk
from typing import Any, Callable, Dict, Optional

from .constants import DARK_COLORS, DEFAULT_FONTS, UI_SIZES

# ToolTip 안전 import
try:
    from tooltip import ToolTip
except ImportError:
    # ToolTip fallback
    class ToolTip:
        def __init__(self, widget, text):
            pass


def create_styled_button(
    parent: tk.Widget,
    text: str,
    command: Callable = None,
    tooltip_text: str = "",
    style_type: str = "secondary",
    width: int = None,
    **kwargs,
) -> tk.Button:
    """DRY 원칙: 스타일이 적용된 버튼 생성 (공통 로직 통합)

    Args:
        parent: 부모 위젯
        text: 버튼 텍스트
        command: 버튼 클릭 콜백
        tooltip_text: 툴팁 텍스트
        style_type: 버튼 스타일 ('primary', 'secondary', 'danger', 'warning')
        width: 버튼 너비 (선택사항)
        **kwargs: 추가 버튼 옵션

    Returns:
        생성된 tk.Button 인스턴스
    """
    # 스타일별 색상 설정
    style_config = {
        "primary": {
            "bg": DARK_COLORS["accent"],
            "fg": "white",
            "font": DEFAULT_FONTS["bold"],
            "padx": UI_SIZES["button_padding_x"],
            "pady": UI_SIZES["button_padding_y"],
        },
        "secondary": {
            "bg": DARK_COLORS["button_bg"],
            "fg": DARK_COLORS["text"],
            "font": DEFAULT_FONTS["small"],
            "padx": 5,
            "pady": UI_SIZES["button_padding_y"],
        },
        "danger": {
            "bg": DARK_COLORS["danger"],
            "fg": "white",
            "font": DEFAULT_FONTS["default"],
            "padx": UI_SIZES["button_padding_x"],
            "pady": UI_SIZES["button_padding_y"],
        },
        "warning": {
            "bg": DARK_COLORS["warning"],
            "fg": "white",
            "font": DEFAULT_FONTS["default"],
            "padx": UI_SIZES["button_padding_x"],
            "pady": UI_SIZES["button_padding_y"],
        },
    }

    # 기본 버튼 설정
    button_config = {
        "relief": "flat",
        "borderwidth": 0,
        "cursor": "hand2",
        **style_config.get(style_type, style_config["secondary"]),
    }

    # 추가 옵션 적용
    if width is not None:
        button_config["width"] = width
    if command is not None:
        button_config["command"] = command

    # kwargs로 전달된 추가 옵션들 적용
    button_config.update(kwargs)

    # 버튼 생성
    button = tk.Button(parent, text=text, **button_config)

    # 호버 이펙트 적용
    if style_type == "primary":
        bind_hover_effects(button, DARK_COLORS["accent_hover"], DARK_COLORS["accent"])
    elif style_type == "secondary":
        bind_hover_effects(button, DARK_COLORS["button_hover"], DARK_COLORS["button_bg"])

    # 툴팁 추가
    if tooltip_text and ToolTip:
        ToolTip(button, tooltip_text)

    return button


def bind_hover_effects(
    widget: tk.Widget,
    enter_color: str,
    leave_color: str,
    enter_cursor: str = "hand2",
    leave_cursor: str = "",
) -> None:
    """DRY 원칙: 호버 이펙트 바인딩 (중복 제거)

    Args:
        widget: 호버 이펙트를 적용할 위젯
        enter_color: 마우스 진입시 배경색
        leave_color: 마우스 떠날때 배경색
        enter_cursor: 마우스 진입시 커서
        leave_cursor: 마우스 떠날때 커서
    """

    def on_enter(event):
        widget.configure(bg=enter_color, cursor=enter_cursor)

    def on_leave(event):
        widget.configure(bg=leave_color, cursor=leave_cursor)

    widget.bind("<Enter>", on_enter)
    widget.bind("<Leave>", on_leave)


def create_scrollable_frame(parent: tk.Widget, bg_color: str = None) -> tuple[tk.Canvas, tk.Frame]:
    """DRY 원칙: 스크롤 가능한 프레임 생성 (중복 제거)

    Args:
        parent: 부모 위젯
        bg_color: 배경색 (None이면 기본 다크테마 사용)

    Returns:
        (canvas, scrollable_frame) 튜플
    """
    if bg_color is None:
        bg_color = DARK_COLORS["bg"]

    # 캔버스 생성
    canvas = tk.Canvas(parent, bg=bg_color, highlightthickness=0)
    canvas.pack(fill=tk.BOTH, expand=True)

    # 스크롤바 생성
    scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=canvas.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # 캔버스에 스크롤바 연결
    canvas.configure(yscrollcommand=scrollbar.set)

    # 스크롤 가능한 프레임 생성
    scrollable_frame = tk.Frame(canvas, bg=bg_color)
    canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

    # 프레임 크기 변경시 스크롤 영역 업데이트
    def configure_scroll_region(event=None):
        canvas.configure(scrollregion=canvas.bbox("all"))

    def configure_canvas_width(event=None):
        canvas_width = canvas.winfo_width()
        canvas.itemconfig(canvas_window, width=canvas_width)

    scrollable_frame.bind("<Configure>", configure_scroll_region)
    canvas.bind("<Configure>", configure_canvas_width)

    # 마우스 휠 스크롤 바인딩
    def on_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def bind_mousewheel(event):
        canvas.bind_all("<MouseWheel>", on_mousewheel)

    def unbind_mousewheel(event):
        canvas.unbind_all("<MouseWheel>")

    canvas.bind("<Enter>", bind_mousewheel)
    canvas.bind("<Leave>", unbind_mousewheel)

    return canvas, scrollable_frame


def get_button_style(button_type: str = "primary") -> Dict[str, Any]:
    """기존 호환성을 위한 버튼 스타일 반환 함수

    Args:
        button_type: 버튼 타입 ('primary' 또는 'secondary')

    Returns:
        버튼 스타일 딕셔너리
    """
    base_style = {
        "font": DEFAULT_FONTS["default"],
        "border": 0,
        "relief": "flat",
        "cursor": "hand2",
    }

    if button_type == "primary":
        base_style.update(
            {"bg": DARK_COLORS["accent"], "fg": "white", "font": DEFAULT_FONTS["bold"]}
        )
    else:
        base_style.update({"bg": DARK_COLORS["button_bg"], "fg": DARK_COLORS["text"]})

    return base_style


def create_entry_with_placeholder(
    parent: tk.Widget, placeholder: str, textvariable: tk.StringVar = None, **kwargs
) -> tk.Entry:
    """플레이스홀더가 있는 Entry 위젯 생성

    Args:
        parent: 부모 위젯
        placeholder: 플레이스홀더 텍스트
        textvariable: 텍스트 변수
        **kwargs: 추가 Entry 옵션

    Returns:
        생성된 tk.Entry 인스턴스
    """
    entry_config = {
        "font": DEFAULT_FONTS["default"],
        "bg": DARK_COLORS["entry_bg"],
        "fg": DARK_COLORS["text"],
        "borderwidth": 1,
        "relief": "solid",
    }
    entry_config.update(kwargs)

    if textvariable:
        entry_config["textvariable"] = textvariable

    entry = tk.Entry(parent, **entry_config)

    # 플레이스홀더 로직
    def set_placeholder():
        if not (textvariable and textvariable.get()):
            entry.configure(foreground="gray")
            if textvariable:
                textvariable.set(placeholder)

    def clear_placeholder(event):
        if textvariable and textvariable.get() == placeholder:
            textvariable.set("")
            entry.configure(foreground=DARK_COLORS["text"])

    def restore_placeholder(event):
        if not (textvariable and textvariable.get()):
            set_placeholder()

    entry.bind("<FocusIn>", clear_placeholder)
    entry.bind("<FocusOut>", restore_placeholder)

    # 초기 플레이스홀더 설정
    set_placeholder()

    return entry


def create_label_with_style(
    parent: tk.Widget, text: str, style_type: str = "default", **kwargs
) -> tk.Label:
    """스타일이 적용된 라벨 생성

    Args:
        parent: 부모 위젯
        text: 라벨 텍스트
        style_type: 스타일 타입 ('default', 'title', 'subtitle', 'small')
        **kwargs: 추가 라벨 옵션

    Returns:
        생성된 tk.Label 인스턴스
    """
    style_config = {
        "default": {"font": DEFAULT_FONTS["default"], "fg": DARK_COLORS["text"]},
        "title": {"font": DEFAULT_FONTS["large"], "fg": DARK_COLORS["text"]},
        "subtitle": {"font": DEFAULT_FONTS["bold"], "fg": DARK_COLORS["text_secondary"]},
        "small": {"font": DEFAULT_FONTS["small"], "fg": DARK_COLORS["text_secondary"]},
    }

    label_config = {
        "bg": DARK_COLORS["bg"],
        **style_config.get(style_type, style_config["default"]),
    }
    label_config.update(kwargs)

    return tk.Label(parent, text=text, **label_config)
