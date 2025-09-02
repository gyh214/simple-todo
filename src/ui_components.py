"""
Windows TODO 패널 앱의 UI 컴포넌트 모듈

Tkinter를 사용한 모던한 TODO 패널 UI 구현.
다크/라이트 테마, 드래그 앤 드롭, 항상 위 기능 등을 포함한 완전한 UI 시스템.
"""

import tkinter as tk
from tkinter import ttk, messagebox, font
import json
import os
import re
import webbrowser
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from tooltip import ToolTip
# 기본 TodoManager 또는 AsyncTodoManager 사용
try:
    from async_todo_manager import AsyncTodoManager as TodoManager, AsyncTodoManagerError as TodoManagerError
except ImportError:
    # AsyncTodoManager가 없으면 기본 TodoManager 사용
    from todo_manager import TodoManager, TodoManagerError


class ThemeManager:
    """다크/라이트 테마를 관리하는 클래스"""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.style = ttk.Style()
        self.is_dark_theme = True
        self._setup_themes()
        self.apply_theme()
    
    
    def _setup_themes(self):
        """다크 테마 스타일 설정"""
        # 다크 테마 색상
        self.dark_colors = {
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
    
    def apply_theme(self):
        """다크 테마 적용"""
        colors = self.dark_colors
        
        # 메인 윈도우 배경색
        self.root.configure(bg=colors['bg'])
        
        # ttk 스타일 설정
        self.style.theme_use('clam')
        
        # Frame 스타일
        self.style.configure('Card.TFrame', 
                           background=colors['bg_secondary'],
                           borderwidth=1,
                           relief='solid',
                           bordercolor=colors['border'])
        
        self.style.configure('Main.TFrame', 
                           background=colors['bg'])
        
        # Label 스타일
        self.style.configure('Main.TLabel',
                           background=colors['bg'],
                           foreground=colors['text'],
                           font=('Segoe UI', 9))
        
        self.style.configure('Card.TLabel',
                           background=colors['bg_secondary'],
                           foreground=colors['text'],
                           font=('Segoe UI', 9))
        
        self.style.configure('Secondary.TLabel',
                           background=colors['bg_secondary'],
                           foreground=colors['text_secondary'],
                           font=('Segoe UI', 8))
        
        # Button 스타일
        self.style.configure('Modern.TButton',
                           background=colors['button_bg'],
                           foreground=colors['text'],
                           borderwidth=1,
                           focuscolor='none',
                           font=('Segoe UI', 8))
        
        self.style.map('Modern.TButton',
                      background=[('active', colors['button_hover']),
                                ('pressed', colors['accent'])])
        
        self.style.configure('Accent.TButton',
                           background=colors['accent'],
                           foreground='#ffffff',
                           borderwidth=0,
                           focuscolor='none',
                           font=('Segoe UI', 9, 'bold'),
                           relief='flat')
        
        self.style.map('Accent.TButton',
                      background=[('active', colors.get('accent_hover', colors['accent'])),
                                ('pressed', colors['accent'])])
        
        self.style.configure('Danger.TButton',
                           background=colors['danger'],
                           foreground='#ffffff',
                           borderwidth=0,
                           focuscolor='none',
                           font=('Segoe UI', 8))
        
        # Entry 스타일
        self.style.configure('Modern.TEntry',
                           fieldbackground=colors['entry_bg'],
                           background=colors['entry_bg'],
                           foreground=colors['text'],
                           bordercolor=colors['entry_border'],
                           insertcolor=colors['text'],
                           font=('Segoe UI', 9))
        
        # Checkbutton 스타일
        self.style.configure('Modern.TCheckbutton',
                           background=colors['bg_secondary'],
                           foreground=colors['text'],
                           focuscolor='none',
                           font=('Segoe UI', 9))
        
        # Scrollbar 스타일
        self.style.configure('Modern.Vertical.TScrollbar',
                           background=colors['bg_secondary'],
                           troughcolor=colors['bg'],
                           bordercolor=colors['border'],
                           arrowcolor=colors['text_secondary'],
                           darkcolor=colors['bg_secondary'],
                           lightcolor=colors['bg_secondary'])
        
    
    
    def get_colors(self) -> Dict[str, str]:
        """다크 테마의 색상 반환"""
        return self.dark_colors


class DragDropMixin:
    """드래그 앤 드롭 기능을 제공하는 믹스인 클래스"""
    
    def __init__(self):
        self.drag_start_y = 0
        self.drag_widget = None
        self.drag_preview = None
        self.is_dragging = False
    
    def setup_drag_drop(self, widget, drag_handle, callback: Callable[[int, int], None]):
        """드래그 앤 드롭 설정"""
        self.drag_callback = callback
        
        # 드래그 핸들에 이벤트 바인딩
        drag_handle.bind('<Button-1>', lambda e: self._start_drag(e, widget))
        drag_handle.bind('<B1-Motion>', self._drag_motion)
        drag_handle.bind('<ButtonRelease-1>', self._end_drag)
        
        # 마우스 커서 변경
        drag_handle.bind('<Enter>', lambda e: drag_handle.config(cursor='hand2'))
        drag_handle.bind('<Leave>', lambda e: drag_handle.config(cursor=''))
    
    def _start_drag(self, event, widget):
        """드래그 시작"""
        self.drag_start_y = event.y_root
        self.drag_widget = widget
        self.is_dragging = True
        
        # 시각적 피드백을 위한 위젯 스타일 변경
        widget.configure(relief='raised', borderwidth=2)
    
    def _drag_motion(self, event):
        """드래그 중"""
        if not self.is_dragging or not self.drag_widget:
            return
        
        # 드래그 거리 계산
        drag_distance = event.y_root - self.drag_start_y
        
        # 일정 거리 이상 드래그하면 시각적 효과 추가
        if abs(drag_distance) > 5:
            self.drag_widget.configure(bg='#e3f2fd')
    
    def _end_drag(self, event):
        """드래그 종료"""
        if not self.is_dragging or not self.drag_widget:
            return
        
        # 드래그 종료 위치 계산
        drag_distance = event.y_root - self.drag_start_y
        
        # 위젯 스타일 복원
        self.drag_widget.configure(relief='flat', borderwidth=1, bg='')
        
        # 드래그 콜백 호출 (이동할 항목 수 계산)
        if abs(drag_distance) > 20:  # 최소 드래그 거리
            move_steps = int(drag_distance / 40)  # 40px당 1 스텝
            if hasattr(self, 'drag_callback'):
                self.drag_callback(self.drag_widget, move_steps)
        
        # 드래그 상태 초기화
        self.is_dragging = False
        self.drag_widget = None


class ClickableTextWidget(tk.Frame):
    """클릭 가능한 URL이 포함된 텍스트를 표시하는 위젯"""
    
    def __init__(self, parent, text_content: str, theme_manager, font_info=('Segoe UI', 9), 
                 anchor='w', justify='left', debug: bool = False):
        super().__init__(parent)
        
        self.text_content = text_content
        self.theme_manager = theme_manager
        self.font_info = font_info
        self.anchor = anchor
        self.justify = justify
        self._debug = debug
        
        # URL 패턴 (http, https, www로 시작하는 URL들)
        self.url_pattern = re.compile(r'https?://[^\s]+|www\.[^\s]+')
        
        self._setup_widget()
        self._setup_clickable_text()
    
    def _setup_widget(self):
        """위젯 UI 설정"""
        colors = self.theme_manager.get_colors()
        
        # Text 위젯 생성 (읽기 전용) - 한 줄 고정
        self.text_widget = tk.Text(
            self, 
            wrap='none',  # 텍스트 줄바꿈 없음
            height=1,     # 한 줄로 고정
            bg=colors['bg_secondary'],
            fg=colors['text'],
            font=self.font_info,
            relief='flat',
            borderwidth=0,
            highlightthickness=0,
            cursor='arrow',
            state='disabled',  # 편집 불가
            takefocus=0  # 포커스 받지 않음
        )
        self.text_widget.pack(fill='x', expand=True)
    
    
    def _setup_clickable_text(self):
        """텍스트에서 URL을 찾아 클릭 가능하게 만들기"""
        colors = self.theme_manager.get_colors()
        
        # Text 위젯을 편집 가능하게 임시 변경
        self.text_widget.configure(state='normal')
        
        # 기존 내용 삭제
        self.text_widget.delete('1.0', tk.END)
        
        # 텍스트 삽입
        self.text_widget.insert('1.0', self.text_content)
        
        # URL 패턴 검색
        urls = list(self.url_pattern.finditer(self.text_content))
        
        if self._debug:
            print(f"[DEBUG] 텍스트에서 {len(urls)}개 URL 발견: {self.text_content}")
        
        # 각 URL에 태그 적용
        for i, match in enumerate(urls):
            start_pos = f"1.{match.start()}"
            end_pos = f"1.{match.end()}"
            tag_name = f"url_{i}"
            url = match.group()
            
            # URL에 태그 적용
            self.text_widget.tag_add(tag_name, start_pos, end_pos)
            
            # URL 스타일링
            self.text_widget.tag_configure(
                tag_name,
                foreground=colors['accent'],
                underline=True,
                font=self.font_info + ('underline',)
            )
            
            # 클릭 이벤트 바인딩
            self.text_widget.tag_bind(
                tag_name, 
                "<Button-1>", 
                lambda e, link=url: self._open_url(link)
            )
            
            # 마우스 호버 효과
            self.text_widget.tag_bind(
                tag_name,
                "<Enter>",
                lambda e: self.text_widget.configure(cursor='hand2')
            )
            
            self.text_widget.tag_bind(
                tag_name,
                "<Leave>",
                lambda e: self.text_widget.configure(cursor='arrow')
            )
            
            if self._debug:
                print(f"[DEBUG] URL 태그 생성: {tag_name} = {url}")
        
        # 다시 읽기 전용으로 변경 (높이는 이미 1로 고정)
        self.text_widget.configure(state='disabled')
    
    def update_theme(self):
        """테마 변경 시 색상 업데이트"""
        colors = self.theme_manager.get_colors()
        
        # 배경과 기본 텍스트 색상 업데이트
        self.configure(bg=colors['bg_secondary'])
        self.text_widget.configure(
            bg=colors['bg_secondary'],
            fg=colors['text']
        )
        
        # URL 태그 색상 업데이트
        for tag in self.text_widget.tag_names():
            if tag.startswith('url_'):
                self.text_widget.tag_configure(
                    tag,
                    foreground=colors['accent']
                )
    
    def update_text(self, new_text: str):
        """텍스트 내용 업데이트"""
        self.text_content = new_text
        self._setup_clickable_text()
    
    def _open_url(self, url: str):
        """URL을 기본 브라우저에서 열기"""
        try:
            # www로 시작하는 경우 http:// 추가
            if url.startswith('www.'):
                url = 'http://' + url
            
            webbrowser.open(url)
            
            if self._debug:
                print(f"[DEBUG] URL 열기: {url}")
                
        except Exception as e:
            if self._debug:
                print(f"[DEBUG] URL 열기 실패: {e}")
            messagebox.showerror("링크 오류", f"링크를 열 수 없습니다: {url}\n\n오류: {e}")
    
    def update_text(self, new_text: str):
        """텍스트 내용 업데이트"""
        self.text_content = new_text
        self._setup_clickable_text()
    
    def configure_colors(self):
        """테마 색상 업데이트"""
        colors = self.theme_manager.get_colors()
        self.text_widget.configure(
            bg=colors['bg_secondary'],
            fg=colors['text']
        )
        # URL 태그들도 새 색상으로 업데이트
        self._setup_clickable_text()


class TodoItemWidget(tk.Frame, DragDropMixin):
    """개별 TODO 항목을 표시하는 위젯"""
    
    def __init__(self, parent, todo_data: Dict[str, Any], theme_manager: ThemeManager,
                 on_update: Callable, on_delete: Callable, on_reorder: Callable, debug: bool = False):
        tk.Frame.__init__(self, parent)
        DragDropMixin.__init__(self)
        
        self.todo_data = todo_data
        self.theme_manager = theme_manager
        self.on_update = on_update
        self.on_delete = on_delete
        self.on_reorder = on_reorder
        self._debug = debug
        
        self.is_editing = False
        self.edit_entry = None
        
        self._setup_widget()
        self._setup_events()
    
    def _setup_widget(self):
        """위젯 UI 설정"""
        colors = self.theme_manager.get_colors()
        
        # 메인 프레임 설정 (Magic UI 카드 스타일)
        self.configure(bg=colors['bg_secondary'], 
                      relief='solid', 
                      borderwidth=1,
                      highlightthickness=1,
                      highlightcolor=colors['border'],
                      highlightbackground=colors['border'])
        
        # 좌측: 드래그 핸들
        self.drag_handle = tk.Label(self, 
                                   text='☰',
                                   font=('Segoe UI', 9),
                                   bg=colors['bg_secondary'],
                                   fg=colors['text_secondary'],
                                   width=2,
                                   cursor='hand2')
        self.drag_handle.pack(side=tk.LEFT, padx=(4, 2), pady=3)
        ToolTip(self.drag_handle, "드래그하여 순서 변경")
        
        # 체크박스
        self.check_var = tk.BooleanVar(value=self.todo_data['completed'])
        self.checkbox = tk.Checkbutton(self,
                                      variable=self.check_var,
                                      command=self._toggle_completed,
                                      bg=colors['bg_secondary'],
                                      fg=colors['text'],
                                      selectcolor=colors['bg_secondary'],
                                      activebackground=colors['bg_hover'],
                                      font=('Segoe UI', 9))
        self.checkbox.pack(side=tk.LEFT, padx=(0, 4), pady=3)
        ToolTip(self.checkbox, "완료 표시")
        
        # 우측: 삭제 버튼
        self.delete_btn = tk.Button(self,
                                   text='✕',
                                   font=('Segoe UI', 9),
                                   bg=colors['danger'],
                                   fg='white',
                                   border=0,
                                   width=2,
                                   height=1,
                                   command=self._delete_todo,
                                   cursor='hand2',
                                   relief='flat',
                                   activebackground='#dc2626')
        self.delete_btn.pack(side=tk.RIGHT, padx=(2, 4), pady=3)
        ToolTip(self.delete_btn, "삭제")
        
        # 편집 버튼 (Magic UI 스타일)
        self.edit_btn = tk.Button(self,
                                 text='✎',
                                 font=('Segoe UI', 9),
                                 bg=colors['accent'],
                                 fg='white',
                                 border=0,
                                 width=2,
                                 height=1,
                                 command=self._start_edit,
                                 cursor='hand2',
                                 relief='flat',
                                 activebackground=colors.get('accent_hover', colors['accent']))
        self.edit_btn.pack(side=tk.RIGHT, padx=(2, 0), pady=3)
        ToolTip(self.edit_btn, "편집 (더블클릭도 가능)")
        
        # 클릭 가능한 텍스트 위젯 (URL 링크 지원)
        self.text_widget = ClickableTextWidget(
            self,
            self.todo_data['text'],
            self.theme_manager,
            font_info=('Segoe UI', 9),
            debug=self._debug
        )
        self.text_widget.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4), pady=3)
        
        # 호환성을 위해 text_label 참조 유지
        self.text_label = self.text_widget
        
        # 완료 상태에 따른 스타일 적용
        self._update_completion_style()
        
        # 드래그 앤 드롭 설정
        self.setup_drag_drop(self, self.drag_handle, self._handle_reorder)
    
    def _setup_events(self):
        """이벤트 설정"""
        # 더블클릭으로 편집 모드 (ClickableTextWidget의 text_widget에 바인딩)
        self.text_widget.text_widget.bind('<Double-Button-1>', lambda e: self._start_edit())
        
        # 호버 효과
        widgets = [self, self.text_widget, self.checkbox]
        for widget in widgets:
            widget.bind('<Enter>', self._on_enter)
            widget.bind('<Leave>', self._on_leave)
    
    def _on_enter(self, event):
        """마우스 호버 시 (Magic UI elevation 효과)"""
        colors = self.theme_manager.get_colors()
        # 배경색 변경
        self.configure(bg=colors['bg_hover'], 
                      highlightcolor=colors['accent'],
                      highlightbackground=colors['accent'],
                      relief='solid')
        self.text_widget.text_widget.configure(bg=colors['bg_hover'])
        self.checkbox.configure(bg=colors['bg_hover'])
        self.drag_handle.configure(bg=colors['bg_hover'])
    
    def _on_leave(self, event):
        """마우스 호버 해제 시"""
        colors = self.theme_manager.get_colors()
        self.configure(bg=colors['bg_secondary'],
                      highlightcolor=colors['border'],
                      highlightbackground=colors['border'])
        self.text_widget.text_widget.configure(bg=colors['bg_secondary'])
        self.checkbox.configure(bg=colors['bg_secondary'])
        self.drag_handle.configure(bg=colors['bg_secondary'])
    
    def _toggle_completed(self):
        """완료 상태 토글"""
        completed = self.check_var.get()
        self.todo_data['completed'] = completed
        self._update_completion_style()
        self.on_update(self.todo_data['id'], completed=completed)
    
    def _update_completion_style(self):
        """완료 상태에 따른 스타일 업데이트"""
        colors = self.theme_manager.get_colors()
        if self.todo_data['completed']:
            # 완료된 항목: 취소선과 흐린 텍스트
            self.text_widget.text_widget.configure(
                fg=colors['text_secondary']
            )
            # 취소선은 Text 위젯의 폰트 설정으로 적용
            self.text_widget.font_info = ('Segoe UI', 9, 'overstrike')
            self.text_widget.text_widget.configure(font=self.text_widget.font_info)
        else:
            # 미완료 항목: 일반 스타일
            self.text_widget.text_widget.configure(
                fg=colors['text']
            )
            self.text_widget.font_info = ('Segoe UI', 9)
            self.text_widget.text_widget.configure(font=self.text_widget.font_info)
        
        # URL 스타일도 다시 적용
        self.text_widget._setup_clickable_text()
    
    def _start_edit(self):
        """편집 모드 시작"""
        if self.is_editing:
            return
        
        self.is_editing = True
        colors = self.theme_manager.get_colors()
        
        # 기존 텍스트 위젯 숨기기
        self.text_widget.pack_forget()
        
        # 편집용 Entry 생성
        self.edit_entry = tk.Entry(self,
                                  font=('Segoe UI', 9),
                                  bg=colors['entry_bg'],
                                  fg=colors['text'],
                                  borderwidth=1,
                                  relief='solid')
        self.edit_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4), pady=3)
        
        # 기존 텍스트 설정 및 선택
        self.edit_entry.insert(0, self.todo_data['text'])
        self.edit_entry.selection_range(0, tk.END)
        self.edit_entry.focus()
        
        # 이벤트 바인딩
        self.edit_entry.bind('<Return>', self._confirm_edit)
        self.edit_entry.bind('<Escape>', self._cancel_edit)
        self.edit_entry.bind('<FocusOut>', self._confirm_edit)
    
    def _confirm_edit(self, event=None):
        """편집 확인"""
        if not self.is_editing or not self.edit_entry:
            return
        
        new_text = self.edit_entry.get().strip()
        
        if new_text and new_text != self.todo_data['text']:
            self.todo_data['text'] = new_text
            # 텍스트 위젯 내용 업데이트 (URL 감지 포함)
            self.text_widget.update_text(new_text)
            self.on_update(self.todo_data['id'], text=new_text)
        
        self._end_edit()
    
    def _cancel_edit(self, event=None):
        """편집 취소"""
        self._end_edit()
    
    def _end_edit(self):
        """편집 모드 종료"""
        if not self.is_editing:
            return
        
        self.is_editing = False
        
        # Entry 제거하고 텍스트 위젯 복원
        if self.edit_entry:
            self.edit_entry.destroy()
            self.edit_entry = None
        
        self.text_widget.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4), pady=3)
    
    def _delete_todo(self):
        """TODO 항목 삭제 (x 버튼 - 확인창 없이 바로 삭제)"""
        try:
            self.on_delete(self.todo_data['id'])
        except Exception as e:
            messagebox.showerror("삭제 오류", f"항목 삭제 중 오류가 발생했습니다: {e}")
            if self._debug:
                print(f"[DEBUG] 삭제 오류: {e}")
                import traceback
                traceback.print_exc()
    
    def _handle_reorder(self, widget, move_steps):
        """드래그 앤 드롭으로 순서 변경"""
        if move_steps != 0:
            self.on_reorder(self.todo_data['id'], move_steps)
    
    def update_data(self, todo_data: Dict[str, Any]):
        """TODO 데이터 업데이트"""
        self.todo_data = todo_data
        self.text_widget.update_text(todo_data['text'])
        self.check_var.set(todo_data['completed'])
        self._update_completion_style()
    
    def update_colors(self):
        """테마 변경 시 색상 업데이트"""
        colors = self.theme_manager.get_colors()
        
        # 메인 프레임 색상 업데이트
        self.configure(bg=colors['bg_secondary'])
        
        # 드래그 핸들 색상 업데이트
        if hasattr(self, 'drag_handle'):
            self.drag_handle.configure(bg=colors['bg_secondary'], fg=colors['text_secondary'])
        
        # 체크박스 배경 색상 업데이트
        if hasattr(self, 'checkbox'):
            self.checkbox.configure(bg=colors['bg_secondary'])
        
        # ClickableTextWidget 테마 업데이트
        if hasattr(self, 'text_widget'):
            self.text_widget.update_theme()


class TodoPanelApp:
    """메인 TODO 패널 애플리케이션"""
    
    def __init__(self):
        self.root = tk.Tk()
        # AsyncTodoManager를 우선 사용 (비동기 저장 및 개선된 에러 처리)
        try:
            self.todo_manager = TodoManager(debug=True, batch_save=True)
        except TypeError:
            # batch_save 파라미터가 없는 기본 TodoManager의 경우
            self.todo_manager = TodoManager(debug=True)
        self.theme_manager = ThemeManager(self.root)
        
        self.todo_widgets: Dict[str, TodoItemWidget] = {}
        self.always_on_top = False
        
        self._setup_window()
        self._setup_ui()
        self._load_todos()
        
        # 창 닫기 이벤트 처리
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _setup_window(self):
        """메인 윈도우 설정"""
        self.root.title("TODO Panel")
        self.root.geometry("400x600")
        self.root.minsize(300, 400)
        
        # 아이콘 설정 (유니코드 문자 사용)
        try:
            # Windows에서 작동하는 기본 아이콘 설정
            self.root.iconbitmap(default='')
        except:
            pass
        
        # 시스템 트레이를 위한 설정
        self.root.resizable(True, True)
    
    def _setup_ui(self):
        """UI 구성 요소 설정"""
        colors = self.theme_manager.get_colors()
        
        # 메인 컨테이너
        main_frame = ttk.Frame(self.root, style='Main.TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=6, pady=4)
        
        # 상단 통합 제어 패널 (입력 + 제어 버튼들)
        self._setup_control_panel(main_frame)
        
        # TODO 리스트 섹션
        self._setup_list_section(main_frame)
        
        # 하단 상태바
        self._setup_status_bar(main_frame)
    
    def _setup_control_panel(self, parent):
        """상단 통합 제어 패널 설정 (입력 + 제어 버튼들)"""
        control_frame = ttk.Frame(parent, style='Main.TFrame')
        control_frame.pack(fill=tk.X, pady=(0, 4))
        
        # 좌측: TODO 입력 영역
        # 입력 필드
        self.entry_var = tk.StringVar()
        self.todo_entry = ttk.Entry(control_frame,
                                   textvariable=self.entry_var,
                                   font=('Segoe UI', 9),
                                   style='Modern.TEntry')
        self.todo_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        
        # 추가 버튼 
        self.add_btn = ttk.Button(control_frame,
                                 text='추가',
                                 command=self._add_todo,
                                 style='Accent.TButton')
        self.add_btn.pack(side=tk.LEFT, padx=(0, 8))
        ToolTip(self.add_btn, "새 할일 추가 (Enter키로도 가능)")
        
        # 우측 제어 버튼들
        # 항상 위 토글
        self.top_btn = ttk.Button(control_frame,
                                 text='📌',
                                 width=3,
                                 command=self._toggle_always_on_top,
                                 style='Modern.TButton')
        self.top_btn.pack(side=tk.RIGHT, padx=(4, 0))
        ToolTip(self.top_btn, "항상 위에 표시")
        
        # 완료된 항목 정리 버튼
        self.clear_btn = ttk.Button(control_frame,
                                   text='🗑️',
                                   width=3,
                                   command=self._clear_completed,
                                   style='Modern.TButton')
        self.clear_btn.pack(side=tk.RIGHT, padx=(4, 0))
        ToolTip(self.clear_btn, "완료된 항목 모두 삭제")
        
        # 입력 필드 이벤트 설정
        # 엔터키로 추가
        self.todo_entry.bind('<Return>', lambda e: self._add_todo())
        
        # 플레이스홀더 효과
        self.todo_entry.bind('<FocusIn>', self._on_entry_focus_in)
        self.todo_entry.bind('<FocusOut>', self._on_entry_focus_out)
        self._set_entry_placeholder()
    
    def _setup_list_section(self, parent):
        """TODO 리스트 섹션 설정"""
        # 스크롤 가능한 프레임 컨테이너
        list_container = ttk.Frame(parent, style='Main.TFrame')
        list_container.pack(fill=tk.BOTH, expand=True, pady=(0, 8))
        
        # 캔버스와 스크롤바
        self.canvas = tk.Canvas(list_container, 
                               highlightthickness=0,
                               bg=self.theme_manager.get_colors()['bg'])
        self.scrollbar = ttk.Scrollbar(list_container, 
                                      orient=tk.VERTICAL,
                                      command=self.canvas.yview,
                                      style='Modern.Vertical.TScrollbar')
        
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # 스크롤 가능한 프레임
        self.scrollable_frame = ttk.Frame(self.canvas, style='Main.TFrame')
        self.canvas_frame = self.canvas.create_window((0, 0), 
                                                     window=self.scrollable_frame,
                                                     anchor="nw")
        
        # 패킹
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 스크롤 이벤트
        self.scrollable_frame.bind('<Configure>', self._on_frame_configure)
        self.canvas.bind('<Configure>', self._on_canvas_configure)
        self.canvas.bind_all('<MouseWheel>', self._on_mousewheel)
    
    def _setup_status_bar(self, parent):
        """하단 상태바 설정"""
        status_frame = ttk.Frame(parent, style='Main.TFrame')
        status_frame.pack(fill=tk.X)
        
        self.status_label = ttk.Label(status_frame,
                                     text="",
                                     style='Secondary.TLabel')
        self.status_label.pack(side=tk.LEFT)
        
        self._update_status()
    
    def _set_entry_placeholder(self):
        """입력 필드 플레이스홀더 설정"""
        if not self.entry_var.get():
            self.todo_entry.configure(foreground='gray')
            self.entry_var.set("새 할 일을 입력하세요...")
    
    def _on_entry_focus_in(self, event):
        """입력 필드 포커스 시"""
        if self.entry_var.get() == "새 할 일을 입력하세요...":
            self.entry_var.set("")
            colors = self.theme_manager.get_colors()
            self.todo_entry.configure(foreground=colors['text'])
    
    def _on_entry_focus_out(self, event):
        """입력 필드 포커스 해제 시"""
        if not self.entry_var.get():
            self._set_entry_placeholder()
    
    def _on_frame_configure(self, event):
        """스크롤 프레임 크기 변경 시"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def _on_canvas_configure(self, event):
        """캔버스 크기 변경 시"""
        self.canvas.itemconfig(self.canvas_frame, width=event.width)
    
    def _on_mousewheel(self, event):
        """마우스 휠 스크롤"""
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    def _load_todos(self):
        """TODO 목록 로드 및 표시"""
        try:
            todos = self.todo_manager.read_todos()
            
            # 기존 위젯들 정리
            for widget in self.todo_widgets.values():
                widget.destroy()
            self.todo_widgets.clear()
            
            # 새 위젯들 생성
            for todo in todos:
                self._create_todo_widget(todo)
            
            self._update_status()
            
        except TodoManagerError as e:
            messagebox.showerror("오류", f"TODO 목록을 불러오는데 실패했습니다: {e}")
    
    def _create_todo_widget(self, todo_data: Dict[str, Any]):
        """TODO 위젯 생성"""
        widget = TodoItemWidget(
            self.scrollable_frame,
            todo_data,
            self.theme_manager,
            self._update_todo,
            self._delete_todo,
            self._reorder_todo,
            debug=getattr(self.todo_manager, '_debug', False)
        )
        widget.pack(fill=tk.X, pady=1)
        self.todo_widgets[todo_data['id']] = widget
    
    def _add_todo(self):
        """새 TODO 추가"""
        text = self.entry_var.get().strip()
        if not text or text == "새 할 일을 입력하세요...":
            return
        
        try:
            # TodoManager가 제대로 초기화되었는지 확인
            if not hasattr(self, 'todo_manager') or self.todo_manager is None:
                messagebox.showerror("오류", "TODO 관리자가 초기화되지 않았습니다.")
                return
            
            todo = self.todo_manager.create_todo(text)
            self._create_todo_widget(todo)
            
            # 입력 필드 초기화
            self.entry_var.set("")
            self._set_entry_placeholder()
            
            # 스크롤을 맨 아래로
            self.root.after(10, lambda: self.canvas.yview_moveto(1.0))
            
            self._update_status()
            
        except Exception as e:
            messagebox.showerror("오류", f"TODO 추가에 실패했습니다: {e}")
    
    def _update_todo(self, todo_id: str, **kwargs):
        """TODO 업데이트"""
        try:
            success = self.todo_manager.update_todo(todo_id, **kwargs)
            if success:
                # 위젯 업데이트
                if todo_id in self.todo_widgets:
                    updated_todo = self.todo_manager.get_todo_by_id(todo_id)
                    if updated_todo:
                        self.todo_widgets[todo_id].update_data(updated_todo)
                
                self._update_status()
            else:
                messagebox.showerror("오류", "TODO 업데이트에 실패했습니다.")
                
        except TodoManagerError as e:
            messagebox.showerror("오류", f"TODO 업데이트에 실패했습니다: {e}")
    
    def _delete_todo(self, todo_id: str):
        """TODO 삭제"""
        debug_mode = getattr(self.todo_manager, '_debug', False)
        if debug_mode:
            print(f"[DEBUG] 삭제 요청: todo_id={todo_id}")
            
        try:
            # todo_id 유효성 검사
            if not todo_id or todo_id not in self.todo_widgets:
                raise ValueError(f"유효하지 않은 todo_id: {todo_id}")
            
            success = self.todo_manager.delete_todo(todo_id)
            if debug_mode:
                print(f"[DEBUG] todo_manager.delete_todo() 결과: {success}")
                
            if success:
                # UI에서 위젯 제거
                if todo_id in self.todo_widgets:
                    self.todo_widgets[todo_id].destroy()
                    del self.todo_widgets[todo_id]
                    if debug_mode:
                        print(f"[DEBUG] 위젯 제거 완료: {todo_id}")
                
                self._update_status()
                if debug_mode:
                    print(f"[DEBUG] 상태 업데이트 완료")
            else:
                error_msg = f"TODO 삭제에 실패했습니다. (ID: {todo_id})"
                messagebox.showerror("삭제 실패", error_msg)
                if debug_mode:
                    print(f"[DEBUG] {error_msg}")
                
        except TodoManagerError as e:
            error_msg = f"TODO 삭제 중 오류 발생: {e}"
            messagebox.showerror("삭제 오류", error_msg)
            if debug_mode:
                print(f"[DEBUG] TodoManagerError: {e}")
                import traceback
                traceback.print_exc()
        except Exception as e:
            error_msg = f"예상치 못한 오류 발생: {e}"
            messagebox.showerror("시스템 오류", error_msg)
            if debug_mode:
                print(f"[DEBUG] Unexpected error: {e}")
                import traceback
                traceback.print_exc()
    
    def _reorder_todo(self, todo_id: str, move_steps: int):
        """TODO 순서 변경"""
        try:
            # 현재 위치 찾기
            todos = self.todo_manager.read_todos()
            current_pos = None
            for i, todo in enumerate(todos):
                if todo['id'] == todo_id:
                    current_pos = i
                    break
            
            if current_pos is None:
                return
            
            # 새 위치 계산
            new_pos = max(0, min(len(todos) - 1, current_pos + move_steps))
            
            if new_pos != current_pos:
                success = self.todo_manager.reorder_todos(todo_id, new_pos)
                if success:
                    self._load_todos()  # 전체 리스트 다시 로드
                
        except TodoManagerError as e:
            messagebox.showerror("오류", f"TODO 순서 변경에 실패했습니다: {e}")
    
    def _clear_completed(self):
        """완료된 항목들 정리 (확인창 표시)"""
        try:
            # 완료된 항목 개수 확인
            stats = self.todo_manager.get_stats()
            completed_count = stats.get('completed', 0)
            
            if completed_count == 0:
                messagebox.showinfo("정보", "삭제할 완료된 항목이 없습니다.")
                return
            
            # 확인창 표시
            confirm = messagebox.askyesno(
                "완료된 항목 일괄 삭제", 
                f"완료된 {completed_count}개의 항목을 모두 삭제하시겠습니까?\n\n삭제 후 복구할 수 없습니다.",
                parent=self.root,
                icon='warning'
            )
            
            if confirm:
                count = self.todo_manager.clear_completed_todos()
                if count > 0:
                    self._load_todos()
                    messagebox.showinfo("완료", f"{count}개의 완료된 항목을 삭제했습니다.")
                    
        except TodoManagerError as e:
            messagebox.showerror("오류", f"완료된 항목 정리에 실패했습니다: {e}")
    
    
    def _toggle_always_on_top(self):
        """항상 위 토글"""
        self.always_on_top = not self.always_on_top
        self.root.wm_attributes('-topmost', self.always_on_top)
        
        # 버튼 스타일 변경
        style = 'Accent.TButton' if self.always_on_top else 'Modern.TButton'
        self.top_btn.configure(style=style)
    
    
    def _update_status(self):
        """상태바 업데이트"""
        try:
            stats = self.todo_manager.get_stats()
            status_text = f"전체: {stats['total']}, 완료: {stats['completed']}, 남은 일: {stats['pending']}"
            self.status_label.configure(text=status_text)
        except:
            self.status_label.configure(text="상태 정보를 불러올 수 없습니다")
    
    def _on_closing(self):
        """앱 종료 시"""
        try:
            # AsyncTodoManager의 경우 shutdown 메소드 호출
            if hasattr(self.todo_manager, 'shutdown'):
                self.todo_manager.shutdown()
            # 기본 TodoManager의 경우 save_data 호출
            elif hasattr(self.todo_manager, 'save_data'):
                self.todo_manager.save_data()
        except Exception as e:
            print(f"종료 중 오류: {e}")
        finally:
            self.root.destroy()
    
    def run(self):
        """애플리케이션 실행"""
        # 창을 중앙에 배치
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        
        # 메인 루프 시작
        self.root.mainloop()


def main():
    """메인 함수"""
    try:
        app = TodoPanelApp()
        app.run()
    except Exception as e:
        messagebox.showerror("치명적 오류", f"애플리케이션을 시작할 수 없습니다:\n{e}")


if __name__ == "__main__":
    main()