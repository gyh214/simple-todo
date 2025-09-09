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
import socket
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
        
        # 파일 경로 패턴들 (확장자가 있는 경로)
        self.file_patterns = {
            'absolute': re.compile(r'[A-Za-z]:[\\\/](?:[^\\\/\n\r<>"|*?]+[\\\/])*[^\\\/\n\r<>"|*?]+\.[A-Za-z0-9]{1,10}'),
            'relative': re.compile(r'(?:\.{1,2}[\\\/])+(?:[^\\\/\n\r<>"|*?]+[\\\/])*[^\\\/\n\r<>"|*?]+\.[A-Za-z0-9]{1,10}'),
            'network': re.compile(r'\\\\[^\\\/\n\r<>"|*?]+\\(?:[^\\\/\n\r<>"|*?]+\\)*[^\\\/\n\r<>"|*?]+\.[A-Za-z0-9]{1,10}')
        }
        
        # 폴더 경로 패턴들 (확장자가 없는 경로)
        self.folder_patterns = {
            # 슬래시로 끝나는 명확한 폴더 경로
            'trailing_slash_absolute': re.compile(r'[A-Za-z]:[\\\/](?:[^\\\/\n\r<>"|*?]+[\\\/])+'),
            'trailing_slash_relative': re.compile(r'(?:\.{0,2}[\\\/])+(?:[^\\\/\n\r<>"|*?]+[\\\/])+'),
            'trailing_slash_network': re.compile(r'\\\\[^\\\/\n\r<>"|*?]+\\(?:[^\\\/\n\r<>"|*?]+[\\\/])+'),
            # 확장자 없는 경로 (추정 폴더)
            'no_extension_absolute': re.compile(r'[A-Za-z]:[\\\/](?:[^\\\/\n\r<>"|*?]+[\\\/])*[^\\\/\n\r<>"|*?]+(?!\.[A-Za-z0-9])'),
            'no_extension_relative': re.compile(r'(?:\.{1,2}[\\\/])+(?:[^\\\/\n\r<>"|*?]+[\\\/])*[^\\\/\n\r<>"|*?]+(?!\.[A-Za-z0-9])'),
            'no_extension_network': re.compile(r'\\\\[^\\\/\n\r<>"|*?]+\\(?:[^\\\/\n\r<>"|*?]+[\\\/])*[^\\\/\n\r<>"|*?]+(?!\.[A-Za-z0-9])')
        }
        
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
    
    
    def _get_link_type_and_matches(self, text):
        """텍스트에서 URL, 파일 경로, 폴더 경로를 찾아 타입과 함께 반환"""
        matches = []
        
        # 1. URL 패턴 검색 (최우선)
        for match in self.url_pattern.finditer(text):
            matches.append({
                'match': match,
                'type': 'url',
                'content': match.group()
            })
        
        # 2. 파일 경로 패턴 검색 (확장자가 있는 경로)
        for pattern_name, pattern in self.file_patterns.items():
            for match in pattern.finditer(text):
                # 기존 매치와 겹치지 않는지 확인
                is_overlap = False
                for existing_match in matches:
                    if (match.start() < existing_match['match'].end() and 
                        match.end() > existing_match['match'].start()):
                        is_overlap = True
                        break
                
                if not is_overlap:
                    matches.append({
                        'match': match,
                        'type': 'file',
                        'content': match.group(),
                        'pattern_type': pattern_name
                    })
        
        # 3. 폴더 경로 패턴 검색 (확장자가 없는 경로)
        for pattern_name, pattern in self.folder_patterns.items():
            for match in pattern.finditer(text):
                # 기존 매치와 겹치지 않는지 확인
                is_overlap = False
                for existing_match in matches:
                    if (match.start() < existing_match['match'].end() and 
                        match.end() > existing_match['match'].start()):
                        is_overlap = True
                        break
                
                if not is_overlap:
                    matches.append({
                        'match': match,
                        'type': 'folder',
                        'content': match.group(),
                        'pattern_type': pattern_name
                    })
        
        # 시작 위치로 정렬
        matches.sort(key=lambda x: x['match'].start())
        return matches
    
    def _setup_clickable_text(self):
        """텍스트에서 URL과 파일 경로를 찾아 클릭 가능하게 만들기"""
        colors = self.theme_manager.get_colors()
        
        # Text 위젯을 편집 가능하게 임시 변경
        self.text_widget.configure(state='normal')
        
        # 기존 내용 삭제
        self.text_widget.delete('1.0', tk.END)
        
        # 텍스트 삽입
        self.text_widget.insert('1.0', self.text_content)
        
        # URL과 파일 경로 검색
        all_matches = self._get_link_type_and_matches(self.text_content)
        
        if self._debug:
            try:
                print(f"[DEBUG] 텍스트에서 {len(all_matches)}개 링크 발견: {self.text_content}")
            except UnicodeEncodeError:
                print(f"[DEBUG] Found {len(all_matches)} links in text (encoding issue prevented full display)")
        
        # 각 링크에 태그 적용
        for i, link_info in enumerate(all_matches):
            match = link_info['match']
            link_type = link_info['type']
            content = link_info['content']
            
            start_pos = f"1.{match.start()}"
            end_pos = f"1.{match.end()}"
            tag_name = f"{link_type}_{i}"
            
            # 링크에 태그 적용
            self.text_widget.tag_add(tag_name, start_pos, end_pos)
            
            # 링크 타입에 따른 스타일링
            if link_type == 'url':
                # 웹 링크: 파란색
                color = colors['accent']
                tooltip_text = f"웹사이트 열기: {content}"
                click_handler = lambda e, link=content: self._open_url(link)
            elif link_type == 'file':
                # 파일 링크: 주황색
                color = colors.get('warning', '#ff9800')
                tooltip_text = f"파일 열기: {content}"
                click_handler = lambda e, path=content: self._open_file(path)
            elif link_type == 'folder':
                # 폴더 링크: 녹색
                color = colors.get('success', '#4caf50')
                tooltip_text = f"폴더 열기: {content}"
                click_handler = lambda e, path=content: self._open_folder(path)
            else:
                # 기본값 (예상치 못한 케이스)
                color = colors.get('text_secondary', '#cccccc')
                tooltip_text = f"링크: {content}"
                click_handler = lambda e: None
            
            self.text_widget.tag_configure(
                tag_name,
                foreground=color,
                underline=True,
                font=self.font_info + ('underline',)
            )
            
            # 클릭 이벤트 바인딩
            self.text_widget.tag_bind(tag_name, "<Button-1>", click_handler)
            
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
            
            # 툴팁 추가
            self._add_tooltip_to_tag(tag_name, tooltip_text)
            
            if self._debug:
                try:
                    print(f"[DEBUG] {link_type.upper()} 태그 생성: {tag_name} = {content}")
                except UnicodeEncodeError:
                    print(f"[DEBUG] {link_type.upper()} tag created: {tag_name}")
        
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
        
        # 링크 태그 색상 업데이트
        for tag in self.text_widget.tag_names():
            if tag.startswith('url_'):
                # 웹 링크: 파란색
                self.text_widget.tag_configure(
                    tag,
                    foreground=colors['accent']
                )
            elif tag.startswith('file_'):
                # 파일 링크: 주황색
                self.text_widget.tag_configure(
                    tag,
                    foreground=colors.get('warning', '#ff9800')
                )
            elif tag.startswith('folder_'):
                # 폴더 링크: 녹색
                self.text_widget.tag_configure(
                    tag,
                    foreground=colors.get('success', '#4caf50')
                )
    
    def update_text(self, new_text: str):
        """텍스트 내용 업데이트"""
        self.text_content = new_text
        self._setup_clickable_text()
    
    def _add_tooltip_to_tag(self, tag_name: str, tooltip_text: str):
        """태그에 툴팁 추가"""
        def show_tooltip(event):
            # 툴팁 생성 (간단한 구현)
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root + 10}+{event.y_root + 10}")
            
            colors = self.theme_manager.get_colors()
            label = tk.Label(
                tooltip,
                text=tooltip_text,
                background=colors.get('tooltip_bg', '#333333'),
                foreground=colors.get('tooltip_fg', '#ffffff'),
                font=('Segoe UI', 8),
                relief='solid',
                borderwidth=1,
                padx=5,
                pady=2
            )
            label.pack()
            
            # 일정 시간 후 툴팁 삭제
            tooltip.after(3000, tooltip.destroy)
            
            # 마우스가 태그를 벗어나면 툴팁 삭제
            def hide_tooltip(e):
                tooltip.destroy()
            
            self.text_widget.tag_bind(tag_name, "<Leave>", hide_tooltip)
        
        self.text_widget.tag_bind(tag_name, "<Enter>", show_tooltip)
    
    def _open_url(self, url: str):
        """URL을 기본 브라우저에서 열기"""
        try:
            # www로 시작하는 경우 http:// 추가
            if url.startswith('www.'):
                url = 'http://' + url
            
            webbrowser.open(url)
            
            if self._debug:
                try:
                    print(f"[DEBUG] URL 열기: {url}")
                except UnicodeEncodeError:
                    print(f"[DEBUG] Opening URL: {url}")
                
        except Exception as e:
            if self._debug:
                try:
                    print(f"[DEBUG] URL 열기 실패: {e}")
                except UnicodeEncodeError:
                    print(f"[DEBUG] Failed to open URL: {e}")
            messagebox.showerror("링크 오류", f"링크를 열 수 없습니다: {url}\n\n오류: {e}")
    
    def _open_file(self, file_path: str):
        """보안 검증을 포함한 파일 열기"""
        try:
            # 1. 파일 경로를 Path 객체로 변환
            file_path_obj = Path(file_path)
            
            # 2. 파일 존재 여부 검증
            if not file_path_obj.exists():
                error_msg = f"파일을 찾을 수 없습니다: {file_path}"
                if self._debug:
                    print(f"[DEBUG] {error_msg}")
                messagebox.showerror("파일 오류", error_msg)
                return
            
            # 3. 파일 확장자 추출 및 보안 검증
            file_extension = file_path_obj.suffix.lower()
            dangerous_extensions = {
                '.exe', '.bat', '.cmd', '.scr', '.com', '.pif', 
                '.msi', '.ps1', '.vbs', '.js', '.jar', '.app'
            }
            
            # 4. 실행 파일 보안 확인 대화상자
            if file_extension in dangerous_extensions:
                if self._debug:
                    try:
                        print(f"[DEBUG] 위험한 실행 파일 감지: {file_path} (확장자: {file_extension})")
                    except UnicodeEncodeError:
                        print(f"[DEBUG] Dangerous executable detected: {file_path} (ext: {file_extension})")
                
                # 사용자 확인 대화상자
                confirm_msg = (
                    f"실행 파일을 열려고 합니다. 계속하시겠습니까?\n\n"
                    f"파일: {file_path}\n"
                    f"확장자: {file_extension}\n\n"
                    f"⚠️ 신뢰할 수 없는 파일은 시스템에 해를 끼칠 수 있습니다."
                )
                
                user_confirmed = messagebox.askyesno(
                    "보안 확인", 
                    confirm_msg,
                    icon='warning',
                    default='no'  # 기본값을 'No'로 설정하여 안전성 강화
                )
                
                if not user_confirmed:
                    if self._debug:
                        try:
                            print(f"[DEBUG] 사용자가 실행 파일 열기를 취소함: {file_path}")
                        except UnicodeEncodeError:
                            print(f"[DEBUG] User cancelled executable opening: {file_path}")
                    return
                
                if self._debug:
                    try:
                        print(f"[DEBUG] 사용자가 실행 파일 열기를 승인함: {file_path}")
                    except UnicodeEncodeError:
                        print(f"[DEBUG] User approved executable opening: {file_path}")
            
            # 5. 파일 접근 권한 검증 및 열기
            try:
                # Windows 환경에서 파일 열기
                if os.name == 'nt':
                    os.startfile(str(file_path_obj))
                else:
                    # 다른 OS의 경우 (향후 확장성을 위해)
                    import subprocess
                    subprocess.run(['xdg-open', str(file_path_obj)])
                
                if self._debug:
                    try:
                        print(f"[DEBUG] 파일 열기 성공: {file_path}")
                    except UnicodeEncodeError:
                        print(f"[DEBUG] File opened successfully: {file_path}")
                    
            except PermissionError:
                error_msg = f"파일에 접근할 수 없습니다: {file_path}"
                if self._debug:
                    print(f"[DEBUG] {error_msg} (권한 오류)")
                messagebox.showerror("권한 오류", error_msg)
                
            except OSError as e:
                # Windows의 os.startfile()에서 발생할 수 있는 특정 오류들
                if e.winerror == 2:  # 파일을 찾을 수 없음
                    error_msg = f"파일을 찾을 수 없습니다: {file_path}"
                elif e.winerror == 5:  # 접근이 거부됨
                    error_msg = f"파일에 접근할 수 없습니다: {file_path}"
                else:
                    error_msg = f"파일을 열 수 없습니다: {e}"
                
                if self._debug:
                    print(f"[DEBUG] OSError: {error_msg} (winerror: {getattr(e, 'winerror', 'N/A')})")
                messagebox.showerror("시스템 오류", error_msg)
                
        except Exception as e:
            error_msg = f"파일을 열 수 없습니다: {e}"
            if self._debug:
                print(f"[DEBUG] 예상치 못한 오류: {error_msg}")
                import traceback
                traceback.print_exc()
            messagebox.showerror("파일 오류", error_msg)
    
    def _is_safe_folder_path(self, folder_path_obj: Path) -> tuple[bool, str]:
        """폴더 경로의 안전성을 검증
        
        Returns:
            tuple: (is_safe: bool, warning_message: str)
        """
        try:
            folder_path_str = str(folder_path_obj).lower()
            
            # 위험한 시스템 폴더들
            dangerous_system_paths = {
                'c:\\windows\\system32',
                'c:\\windows\\syswow64',
                'c:\\windows\\winsxs',
                'c:\\windows\\boot',
                'c:\\system volume information',
                'c:\\recovery',
                'c:\\$recycle.bin'
            }
            
            # 민감한 프로그램 폴더들
            sensitive_program_paths = {
                'c:\\program files\\windows defender',
                'c:\\program files (x86)\\windows defender',
                'c:\\program files\\internet explorer',
                'c:\\program files (x86)\\internet explorer',
                'c:\\programdata\\microsoft\\windows defender'
            }
            
            # 사용자 프로필의 민감한 폴더들
            user_sensitive_paths = {
                '\\appdata\\local\\microsoft\\credentials',
                '\\appdata\\roaming\\microsoft\\credentials',
                '\\ntuser.dat',
                '\\cookies'
            }
            
            # 1. 직접적인 위험한 시스템 경로 확인
            for dangerous_path in dangerous_system_paths:
                if folder_path_str == dangerous_path or folder_path_str.startswith(dangerous_path + '\\'):
                    return False, f"시스템 폴더에 접근하려고 합니다: {folder_path_obj}\n\n⚠️ 이 폴더는 시스템에 중요한 파일들이 있어 수정 시 문제가 발생할 수 있습니다."
            
            # 2. 민감한 프로그램 폴더 확인 (경고만)
            for sensitive_path in sensitive_program_paths:
                if folder_path_str == sensitive_path or folder_path_str.startswith(sensitive_path + '\\'):
                    return True, f"민감한 프로그램 폴더에 접근합니다: {folder_path_obj}\n\n⚠️ 이 폴더의 파일을 변경하지 마세요."
            
            # 3. 사용자 프로필 내 민감한 폴더 확인
            for sensitive_pattern in user_sensitive_paths:
                if sensitive_pattern in folder_path_str:
                    return True, f"민감한 사용자 폴더에 접근합니다: {folder_path_obj}\n\n⚠️ 개인 정보가 포함될 수 있습니다."
            
            return True, ""  # 안전함
            
        except Exception as e:
            if self._debug:
                try:
                    print(f"[DEBUG] 안전성 검증 중 오류: {e}")
                except UnicodeEncodeError:
                    print(f"[DEBUG] Error during safety check: {e}")
            return True, ""  # 오류 시 허용 (보수적 접근)
    
    def _check_network_path_connectivity(self, folder_path_obj: Path) -> bool:
        """네트워크 경로의 연결 상태를 확인
        
        Returns:
            bool: 네트워크 경로가 연결 가능한지 여부
        """
        folder_path_str = str(folder_path_obj)
        
        # 네트워크 경로가 아니면 항상 True 반환
        if not folder_path_str.startswith('\\\\'):
            return True
        
        try:
            # UNC 경로에서 서버 이름 추출
            path_parts = folder_path_str.split('\\')
            if len(path_parts) >= 4:  # \\server\share 형태
                server_name = path_parts[2]
                
                # 서버 연결 테스트 (간단한 소켓 연결 시도)
                try:
                    # SMB 포트(445) 또는 NetBIOS 포트(139)에 연결 시도
                    for port in [445, 139]:
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.settimeout(2)  # 2초 타임아웃
                        result = sock.connect_ex((server_name, port))
                        sock.close()
                        if result == 0:
                            return True
                    return False
                except:
                    return False
            return False
        except Exception as e:
            if self._debug:
                try:
                    print(f"[DEBUG] 네트워크 연결 확인 중 오류: {e}")
                except UnicodeEncodeError:
                    print(f"[DEBUG] Network connectivity check error: {e}")
            return True  # 오류 시 허용
    
    def _safe_message_box(self, msg_type: str, title: str, message: str, **kwargs):
        """한국어 인코딩 안전화된 메시지박스"""
        try:
            if msg_type == 'error':
                return messagebox.showerror(title, message, **kwargs)
            elif msg_type == 'warning':
                return messagebox.showwarning(title, message, **kwargs)
            elif msg_type == 'info':
                return messagebox.showinfo(title, message, **kwargs)
            elif msg_type == 'askyesno':
                return messagebox.askyesno(title, message, **kwargs)
            else:
                return messagebox.showinfo(title, message, **kwargs)
        except UnicodeEncodeError:
            # 한국어 출력 실패 시 영어로 대체
            try:
                english_title = "Folder Access"
                english_message = f"Cannot access folder: {Path(message.split(':')[-1].strip()) if ':' in message else 'Unknown path'}"
                if msg_type == 'error':
                    return messagebox.showerror(english_title, english_message, **kwargs)
                elif msg_type == 'warning':
                    return messagebox.showwarning(english_title, english_message, **kwargs)
                elif msg_type == 'askyesno':
                    return messagebox.askyesno(english_title, "Do you want to continue?", **kwargs)
                else:
                    return messagebox.showinfo(english_title, english_message, **kwargs)
            except:
                # 최종 대체안
                return messagebox.showerror("Error", "Folder access error occurred.")
    
    def _open_folder(self, folder_path: str):
        """강화된 보안 검증을 포함한 폴더 열기 - Windows 탐색기에서 폴더 열기"""
        try:
            # 1. 폴더 경로를 Path 객체로 변환
            folder_path_obj = Path(folder_path)
            
            if self._debug:
                try:
                    print(f"[DEBUG] 폴더 열기 요청: {folder_path}")
                except UnicodeEncodeError:
                    print(f"[DEBUG] Folder open request: {folder_path}")
            
            # 2. 네트워크 경로 연결 상태 확인
            if str(folder_path_obj).startswith('\\\\'):
                if not self._check_network_path_connectivity(folder_path_obj):
                    error_msg = f"네트워크 폴더에 연결할 수 없습니다: {folder_path}\n\n서버가 응답하지 않거나 네트워크 연결에 문제가 있습니다."
                    if self._debug:
                        try:
                            print(f"[DEBUG] 네트워크 연결 실패: {folder_path}")
                        except UnicodeEncodeError:
                            print(f"[DEBUG] Network connection failed: {folder_path}")
                    self._safe_message_box('error', '네트워크 오류', error_msg)
                    return
            
            # 3. 폴더 존재 여부 검증
            if not folder_path_obj.exists():
                error_msg = f"폴더를 찾을 수 없습니다: {folder_path}"
                if self._debug:
                    try:
                        print(f"[DEBUG] {error_msg}")
                    except UnicodeEncodeError:
                        print(f"[DEBUG] Folder not found: {folder_path}")
                self._safe_message_box('error', '폴더 오류', error_msg)
                return
            
            # 4. 폴더인지 확인 (파일이 아닌지 검증)
            if not folder_path_obj.is_dir():
                error_msg = f"지정된 경로는 폴더가 아닙니다: {folder_path}"
                if self._debug:
                    try:
                        print(f"[DEBUG] {error_msg}")
                    except UnicodeEncodeError:
                        print(f"[DEBUG] Path is not a directory: {folder_path}")
                self._safe_message_box('error', '경로 오류', error_msg)
                return
            
            # 5. 폴더 안전성 검증
            is_safe, warning_msg = self._is_safe_folder_path(folder_path_obj)
            
            if not is_safe:
                # 위험한 시스템 폴더: 접근 금지
                if self._debug:
                    try:
                        print(f"[DEBUG] 위험한 시스템 폴더 접근 차단: {folder_path}")
                    except UnicodeEncodeError:
                        print(f"[DEBUG] Dangerous system folder access blocked: {folder_path}")
                self._safe_message_box('error', '보안 경고', warning_msg)
                return
            elif warning_msg:
                # 민감한 폴더: 사용자 확인 필요
                if self._debug:
                    try:
                        print(f"[DEBUG] 민감한 폴더 접근, 사용자 확인 요청: {folder_path}")
                    except UnicodeEncodeError:
                        print(f"[DEBUG] Sensitive folder access, user confirmation required: {folder_path}")
                
                user_confirmed = self._safe_message_box(
                    'askyesno',
                    '폴더 접근 확인',
                    f"{warning_msg}\n\n그래도 폴더를 열기겠습니까?",
                    icon='warning',
                    default='no'
                )
                
                if not user_confirmed:
                    if self._debug:
                        try:
                            print(f"[DEBUG] 사용자가 민감한 폴더 접근을 취소함: {folder_path}")
                        except UnicodeEncodeError:
                            print(f"[DEBUG] User cancelled sensitive folder access: {folder_path}")
                    return
                
                if self._debug:
                    try:
                        print(f"[DEBUG] 사용자가 민감한 폴더 접근을 승인함: {folder_path}")
                    except UnicodeEncodeError:
                        print(f"[DEBUG] User approved sensitive folder access: {folder_path}")
            
            # 6. 폴더 접근 권한 검증 및 탐색기에서 열기
            try:
                # Windows 환경에서 폴더를 탐색기에서 열기
                if os.name == 'nt':
                    os.startfile(str(folder_path_obj))
                else:
                    # 다른 OS의 경우 (향후 확장성을 위해)
                    import subprocess
                    subprocess.run(['xdg-open', str(folder_path_obj)])
                
                if self._debug:
                    try:
                        print(f"[DEBUG] 폴더 열기 성공: {folder_path}")
                    except UnicodeEncodeError:
                        print(f"[DEBUG] Folder opened successfully: {folder_path}")
                    
            except PermissionError:
                error_msg = f"폴더에 접근할 수 없습니다: {folder_path}\n\n관리자 권한이 필요하거나 접근이 제한된 폴더입니다."
                if self._debug:
                    try:
                        print(f"[DEBUG] 권한 오류: {folder_path}")
                    except UnicodeEncodeError:
                        print(f"[DEBUG] Permission denied: {folder_path}")
                self._safe_message_box('error', '권한 오류', error_msg)
                
            except OSError as e:
                # Windows의 os.startfile()에서 발생할 수 있는 특정 오류들
                if hasattr(e, 'winerror'):
                    if e.winerror == 2:  # 폴더를 찾을 수 없음
                        error_msg = f"폴더를 찾을 수 없습니다: {folder_path}\n\n경로가 올바른지 확인해주세요."
                    elif e.winerror == 5:  # 접근이 거부됨
                        error_msg = f"폴더에 접근할 수 없습니다: {folder_path}\n\n접근 권한이 없거나 폴더가 사용 중입니다."
                    elif e.winerror == 21:  # 장치가 준비되지 않음
                        error_msg = f"네트워크 드라이브나 이동식 디스크를 사용할 수 없습니다: {folder_path}\n\n연결 상태를 확인해주세요."
                    else:
                        error_msg = f"폴더를 열 수 없습니다: {folder_path}\n\n시스템 오류: {e}"
                else:
                    error_msg = f"폴더를 열 수 없습니다: {folder_path}\n\n오류: {e}"
                
                if self._debug:
                    try:
                        print(f"[DEBUG] OSError: {error_msg} (winerror: {getattr(e, 'winerror', 'N/A')})")
                    except UnicodeEncodeError:
                        print(f"[DEBUG] OSError occurred: {getattr(e, 'winerror', 'N/A')}")
                self._safe_message_box('error', '시스템 오류', error_msg)
                
        except Exception as e:
            error_msg = f"폴더를 열 수 없습니다: {folder_path}\n\n예상치 못한 오류: {e}"
            if self._debug:
                try:
                    print(f"[DEBUG] 예상치 못한 오류: {error_msg}")
                except UnicodeEncodeError:
                    print(f"[DEBUG] Unexpected error occurred")
                import traceback
                traceback.print_exc()
            self._safe_message_box('error', '폴더 오류', error_msg)
    
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
        # 모든 링크 태그들(URL, 파일, 폴더)을 새 색상으로 업데이트
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
        
        # 정보 버튼
        self.info_btn = ttk.Button(control_frame,
                                  text='ⓘ',  # ⓘ기호
                                  width=3,
                                  command=self._show_about_dialog,
                                  style='Modern.TButton')
        self.info_btn.pack(side=tk.RIGHT, padx=(4, 0))
        ToolTip(self.info_btn, "개발자 정보 및 더 많은 도구들")
        
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
    
    
    def _show_about_dialog(self):
        """정보 대화상자 표시"""
        try:
            about_window = tk.Toplevel(self.root)
            about_window.title("TODO Panel 정보")
            about_window.geometry("400x300")
            about_window.resizable(False, False)
            about_window.transient(self.root)
            about_window.grab_set()
            
            # 색상 테마 설정
            colors = self.theme_manager.get_colors()
            about_window.configure(bg=colors['bg'])
            
            # 중앙 정렬
            x = (about_window.winfo_screenwidth() // 2) - 200
            y = (about_window.winfo_screenheight() // 2) - 150
            about_window.geometry(f"400x300+{x}+{y}")
            
            # 메인 프레임
            main_frame = ttk.Frame(about_window, style='Main.TFrame')
            main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
            
            # 제목
            title_label = ttk.Label(main_frame,
                                   text="📝 TODO Panel",
                                   font=('Segoe UI', 16, 'bold'),
                                   style='Main.TLabel')
            title_label.pack(pady=(0, 10))
            
            # 버전 정보
            version_label = ttk.Label(main_frame,
                                     text="Windows 데스크탑 TODO 관리 도구",
                                     font=('Segoe UI', 10),
                                     style='Secondary.TLabel')
            version_label.pack(pady=(0, 20))
            
            # 개발자 정보
            dev_frame = ttk.Frame(main_frame, style='Main.TFrame')
            dev_frame.pack(fill=tk.X, pady=(0, 20))
            
            dev_label = ttk.Label(dev_frame,
                                 text="개발자: kochim.com 팀",
                                 font=('Segoe UI', 10),
                                 style='Main.TLabel')
            dev_label.pack()
            
            # 추가 도구 안내
            tools_label = ttk.Label(main_frame,
                                   text="더 많은 유용한 도구들을 찾고 계신가요?",
                                   font=('Segoe UI', 10),
                                   style='Main.TLabel')
            tools_label.pack(pady=(0, 5))
            
            desc_label = ttk.Label(main_frame,
                                  text="AI 기반의 일상 불편함 해결 도구들:",
                                  font=('Segoe UI', 9),
                                  style='Secondary.TLabel')
            desc_label.pack()
            
            # kochim.com 버튼
            website_btn = ttk.Button(main_frame,
                                   text="🌐 kochim.com 방문하기",
                                   command=self._open_kochim_website,
                                   style='Accent.TButton')
            website_btn.pack(pady=15)
            
            # 설명 텍스트
            desc_text = ("LoveTune (커플 관계 개선), 성격테스트,\n"
                        "태국어 학습, 이미지 병합 등 다양한\n"
                        "생활 속 문제 해결 도구들을 제공합니다.")
            
            desc_final = ttk.Label(main_frame,
                                  text=desc_text,
                                  font=('Segoe UI', 8),
                                  style='Secondary.TLabel',
                                  justify='center')
            desc_final.pack(pady=(0, 15))
            
            # 닫기 버튼
            close_btn = ttk.Button(main_frame,
                                  text="닫기",
                                  command=about_window.destroy,
                                  style='Modern.TButton')
            close_btn.pack()
            
        except Exception as e:
            messagebox.showerror("오류", f"정보 창을 열 수 없습니다: {e}")
    
    def _open_kochim_website(self):
        """코침 웹사이트 열기"""
        try:
            webbrowser.open("https://kochim.com")
            # 성공 시 간단한 상태 업데이트 (선택적)
            if hasattr(self, 'status_label'):
                original_text = self.status_label.cget('text')
                self.status_label.configure(text="kochim.com이 브라우저에서 열렸습니다")
                # 3초 후 원래 상태로 복원
                self.root.after(3000, lambda: self.status_label.configure(text=original_text))
        except Exception as e:
            messagebox.showerror("웹사이트 열기 오류", 
                               f"브라우저에서 kochim.com을 열 수 없습니다.\n\n"
                               f"다음을 확인해주세요:\n"
                               f"• 인터넷 연결 상태\n"
                               f"• 기본 브라우저 설정\n\n"
                               f"오류 세부사항: {e}")
    
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