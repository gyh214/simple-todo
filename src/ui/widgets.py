"""
재사용 가능한 UI 위젯 모듈
"""

import tkinter as tk
from tkinter import messagebox
import re
import webbrowser
import os
from pathlib import Path
from typing import Dict, Any, Callable, Optional
from tooltip import ToolTip
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

    def __init__(self, parent, text_content: str, font_info=('Segoe UI', 9),
                 anchor='w', justify='left', debug: bool = False):
        super().__init__(parent)

        self.text_content = text_content
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
        colors = DARK_COLORS

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
        colors = DARK_COLORS

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

        # 다시 읽기 전용으로 변경
        self.text_widget.configure(state='disabled')

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

            colors = DARK_COLORS
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

            # 5. 파일 열기
            if os.name == 'nt':
                os.startfile(str(file_path_obj))
            else:
                # 다른 OS의 경우
                import subprocess
                subprocess.run(['xdg-open', str(file_path_obj)])

            if self._debug:
                try:
                    print(f"[DEBUG] 파일 열기 성공: {file_path}")
                except UnicodeEncodeError:
                    print(f"[DEBUG] File opened successfully: {file_path}")

        except Exception as e:
            error_msg = f"파일을 열 수 없습니다: {e}"
            if self._debug:
                print(f"[DEBUG] 파일 열기 오류: {error_msg}")
            messagebox.showerror("파일 오류", error_msg)

    def _open_folder(self, folder_path: str):
        """폴더 열기"""
        try:
            folder_path_obj = Path(folder_path)

            if not folder_path_obj.exists():
                error_msg = f"폴더를 찾을 수 없습니다: {folder_path}"
                messagebox.showerror("폴더 오류", error_msg)
                return

            if not folder_path_obj.is_dir():
                error_msg = f"지정된 경로는 폴더가 아닙니다: {folder_path}"
                messagebox.showerror("경로 오류", error_msg)
                return

            # 폴더 열기
            if os.name == 'nt':
                os.startfile(str(folder_path_obj))
            else:
                import subprocess
                subprocess.run(['xdg-open', str(folder_path_obj)])

        except Exception as e:
            messagebox.showerror("폴더 오류", f"폴더를 열 수 없습니다: {e}")


class TodoItemWidget(tk.Frame, DragDropMixin):
    """개별 TODO 항목을 표시하는 위젯 (납기일 표시 기능 포함)"""

    def __init__(self, parent, todo_data: Dict[str, Any],
                 on_update: Callable, on_delete: Callable, on_reorder: Callable, debug: bool = False):
        tk.Frame.__init__(self, parent)
        DragDropMixin.__init__(self)

        self.todo_data = todo_data
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
        colors = DARK_COLORS

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

        # 편집 버튼
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

        # 중앙: 텍스트와 납기일 표시 영역
        text_frame = tk.Frame(self, bg=colors['bg_secondary'])
        text_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4), pady=3)

        # 클릭 가능한 텍스트 위젯 (URL 링크 지원)
        self.text_widget = ClickableTextWidget(
            text_frame,
            self.todo_data['text'],
            font_info=('Segoe UI', 9),
            debug=self._debug
        )
        self.text_widget.pack(side=tk.TOP, fill=tk.X, expand=True)

        # 납기일 표시 라벨
        self.due_date_label = tk.Label(
            text_frame,
            text="",
            font=('Segoe UI', 7),
            bg=colors['bg_secondary'],
            fg=colors['text_secondary'],
            anchor='w'
        )
        # 납기일이 있을 때만 표시
        self._update_due_date_display()

        # 호환성을 위해 text_label 참조 유지
        self.text_label = self.text_widget

        # 완료 상태에 따른 스타일 적용
        self._update_completion_style()

        # 드래그 앤 드롭 설정
        self.setup_drag_drop(self, self.drag_handle, self._handle_reorder)

    def _update_due_date_display(self):
        """납기일 표시 업데이트"""
        due_date = self.todo_data.get('due_date')

        if not due_date:
            # 납기일이 없으면 라벨 숨기기
            self.due_date_label.pack_forget()
            return

        # 날짜 상태 정보 가져오기
        date_info = DateUtils.get_date_status_info(due_date)

        if not date_info['has_due_date']:
            self.due_date_label.pack_forget()
            return

        # 날짜 표시 텍스트
        display_text = f"📅 {date_info['display_text']}"

        # 남은 일수 정보 추가
        days_until = date_info['days_until_due']
        if days_until is not None:
            if days_until == 0:
                display_text += " (오늘)"
            elif days_until > 0:
                display_text += f" ({days_until}일 남음)"
            else:
                display_text += f" ({abs(days_until)}일 지남)"

        # 상태에 따른 색상 설정
        colors = DARK_COLORS
        if date_info['status_color'] == 'expired':
            fg_color = colors['danger']  # 빨간색
            bg_color = '#4a1a1a'  # 어두운 빨간 배경
        elif date_info['status_color'] == 'today':
            fg_color = colors['warning']  # 주황색
            bg_color = '#4a3c1a'  # 어두운 주황 배경
        elif date_info['status_color'] == 'upcoming':
            fg_color = '#ffd700'  # 노란색
            bg_color = '#4a4a1a'  # 어두운 노란 배경
        else:
            fg_color = colors['text_secondary']
            bg_color = colors['bg_secondary']

        # 라벨 업데이트
        self.due_date_label.configure(
            text=display_text,
            fg=fg_color,
            bg=bg_color
        )

        # 라벨 표시
        self.due_date_label.pack(side=tk.TOP, fill=tk.X, pady=(2, 0))

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
        colors = DARK_COLORS
        # 배경색 변경
        self.configure(bg=colors['bg_hover'],
                      highlightcolor=colors['accent'],
                      highlightbackground=colors['accent'],
                      relief='solid')
        self.text_widget.text_widget.configure(bg=colors['bg_hover'])
        self.checkbox.configure(bg=colors['bg_hover'])
        self.drag_handle.configure(bg=colors['bg_hover'])
        if hasattr(self, 'due_date_label'):
            self.due_date_label.configure(bg=colors['bg_hover'])

    def _on_leave(self, event):
        """마우스 호버 해제 시"""
        colors = DARK_COLORS
        self.configure(bg=colors['bg_secondary'],
                      highlightcolor=colors['border'],
                      highlightbackground=colors['border'])
        self.text_widget.text_widget.configure(bg=colors['bg_secondary'])
        self.checkbox.configure(bg=colors['bg_secondary'])
        self.drag_handle.configure(bg=colors['bg_secondary'])
        if hasattr(self, 'due_date_label'):
            self.due_date_label.configure(bg=colors['bg_secondary'])

    def _toggle_completed(self):
        """완료 상태 토글"""
        completed = self.check_var.get()
        self.todo_data['completed'] = completed
        self._update_completion_style()
        self.on_update(self.todo_data['id'], completed=completed)

    def _update_completion_style(self):
        """완료 상태에 따른 스타일 업데이트"""
        colors = DARK_COLORS
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
        colors = DARK_COLORS

        # 기존 텍스트 위젯 숨기기
        self.text_widget.pack_forget()

        # 편집용 Entry 생성
        self.edit_entry = tk.Entry(self.text_widget.master,
                                  font=('Segoe UI', 9),
                                  bg=colors['entry_bg'],
                                  fg=colors['text'],
                                  borderwidth=1,
                                  relief='solid')
        self.edit_entry.pack(side=tk.TOP, fill=tk.X, expand=True)

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

        self.text_widget.pack(side=tk.TOP, fill=tk.X, expand=True)

    def _delete_todo(self):
        """TODO 항목 삭제"""
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
        self._update_due_date_display()  # 납기일 표시도 업데이트