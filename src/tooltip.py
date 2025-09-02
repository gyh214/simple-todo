"""
Tkinter 툴팁 컴포넌트

버튼이나 위젯에 마우스를 올렸을 때 설명을 표시하는 툴팁 기능
"""

import tkinter as tk
from tkinter import ttk


class ToolTip:
    """
    위젯에 툴팁을 추가하는 클래스
    
    사용법:
        button = ttk.Button(parent, text="클릭")
        ToolTip(button, "이 버튼을 클릭하세요")
    """
    
    def __init__(self, widget, text='widget info', delay=500):
        """
        툴팁 초기화
        
        Args:
            widget: 툴팁을 추가할 위젯
            text: 표시할 텍스트
            delay: 툴팁 표시 지연 시간 (밀리초)
        """
        self.widget = widget
        self.text = text
        self.delay = delay
        self.tooltip_window = None
        self.id = None
        self.x = self.y = 0
        
        # 이벤트 바인딩
        self.widget.bind('<Enter>', self.on_enter, add='+')
        self.widget.bind('<Leave>', self.on_leave, add='+')
        self.widget.bind('<ButtonPress>', self.on_leave, add='+')
    
    def on_enter(self, event=None):
        """마우스가 위젯에 들어왔을 때"""
        self.schedule()
    
    def on_leave(self, event=None):
        """마우스가 위젯을 벗어났을 때"""
        self.unschedule()
        self.hide()
    
    def schedule(self):
        """툴팁 표시 예약"""
        self.unschedule()
        self.id = self.widget.after(self.delay, self.show)
    
    def unschedule(self):
        """툴팁 표시 예약 취소"""
        id_ = self.id
        self.id = None
        if id_:
            self.widget.after_cancel(id_)
    
    def show(self):
        """툴팁 표시"""
        if self.tooltip_window or not self.text:
            return
        
        # 마우스 위치 가져오기
        x = self.widget.winfo_rootx()
        y = self.widget.winfo_rooty()
        
        # 위젯 크기 가져오기
        w = self.widget.winfo_width()
        h = self.widget.winfo_height()
        
        # 툴팁 위치 계산 (위젯 아래쪽)
        x = x + w // 2
        y = y + h + 2
        
        # 툴팁 윈도우 생성
        self.tooltip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)  # 윈도우 장식 제거
        
        # 테마에 따른 색상 설정
        try:
            # 다크 테마 감지 시도
            bg = self.widget.winfo_toplevel().cget('bg')
            is_dark = bg and (bg.lower() == '#1e1e1e' or bg.lower().startswith('#2'))
            
            if is_dark:
                # 다크 테마
                bg_color = '#3e3e42'
                fg_color = '#ffffff'
                border_color = '#525252'
            else:
                # 라이트 테마
                bg_color = '#ffffdd'
                fg_color = '#000000'
                border_color = '#000000'
        except:
            # 기본값 (라이트 테마)
            bg_color = '#ffffdd'
            fg_color = '#000000'
            border_color = '#000000'
        
        # 프레임 생성 (테두리 효과)
        frame = tk.Frame(tw, 
                        background=border_color,
                        highlightbackground=border_color,
                        highlightcolor=border_color,
                        highlightthickness=1,
                        bd=1)
        frame.pack()
        
        # 라벨 생성
        label = tk.Label(frame,
                        text=self.text,
                        justify=tk.LEFT,
                        background=bg_color,
                        foreground=fg_color,
                        relief=tk.FLAT,
                        padx=6,
                        pady=4,
                        font=('Segoe UI', 9))
        label.pack()
        
        # 툴팁 위치 설정
        tw.wm_geometry(f"+{x}+{y}")
        
        # 화면 밖으로 나가지 않도록 조정
        tw.update_idletasks()
        
        # 화면 크기 가져오기
        screen_width = tw.winfo_screenwidth()
        screen_height = tw.winfo_screenheight()
        
        # 툴팁 크기 가져오기
        tw_width = tw.winfo_width()
        tw_height = tw.winfo_height()
        
        # 화면 밖으로 나가는 경우 위치 조정
        if x + tw_width > screen_width:
            x = screen_width - tw_width - 5
        
        if y + tw_height > screen_height:
            # 위젯 위쪽에 표시
            y = self.widget.winfo_rooty() - tw_height - 2
        
        tw.wm_geometry(f"+{x}+{y}")
    
    def hide(self):
        """툴팁 숨기기"""
        tw = self.tooltip_window
        self.tooltip_window = None
        if tw:
            tw.destroy()
    
    def update_text(self, new_text):
        """툴팁 텍스트 업데이트"""
        self.text = new_text


def add_tooltip(widget, text, delay=500):
    """
    위젯에 툴팁을 추가하는 헬퍼 함수
    
    Args:
        widget: 툴팁을 추가할 위젯
        text: 표시할 텍스트
        delay: 툴팁 표시 지연 시간 (밀리초)
    
    Returns:
        ToolTip 객체
    """
    return ToolTip(widget, text, delay)