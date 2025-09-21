"""
TODO Panel 메인 애플리케이션 모듈 (섹션 분할 및 새로운 기능 포함)
"""

import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
# 안전한 import 처리
try:
    from .widgets import DARK_COLORS, TodoItemWidget, StandardTodoDisplay, get_button_style
except ImportError as e:
    print(f"Warning: Failed to import from widgets module: {e}")
    # 기본 fallback 정의
    DARK_COLORS = {
        'bg': '#1e1e1e', 'bg_secondary': '#2d2d30', 'bg_hover': '#3e3e42',
        'text': '#ffffff', 'text_secondary': '#cccccc', 'border': '#3e3e42',
        'accent': '#007acc', 'warning': '#ff9800', 'danger': '#f44336'
    }
    TodoItemWidget = None
    StandardTodoDisplay = None

    def get_button_style(button_type='primary'):
        return {
            'font': ('Segoe UI', 9), 'border': 0, 'relief': 'flat',
            'bg': DARK_COLORS['accent'] if button_type == 'primary' else DARK_COLORS['button_bg'],
            'fg': 'white' if button_type == 'primary' else DARK_COLORS['text']
        }

try:
    from .sort_manager import SortManager
    from .sort_dropdown_widget import SortDropdownWidget
except ImportError:
    SortManager = None
    SortDropdownWidget = None

try:
    from .date_utils import DateUtils
except ImportError:
    DateUtils = None

try:
    from tooltip import ToolTip
except ImportError:
    # ToolTip fallback
    class ToolTip:
        def __init__(self, widget, text):
            pass

# CLEAN 아키텍처 인터페이스 (Domain Layer)
try:
    from interfaces import ITodoService, INotificationService
except ImportError:
    # 인터페이스가 없는 경우 대체 구현
    ITodoService = None
    INotificationService = None


class DatePickerDialog:
    """
    납기일 선택을 위한 팝업 다이얼로그

    📱 확장 가능한 동적 크기 조정 다이얼로그:
    ==========================================

    이 클래스는 자동 크기 조정 시스템을 사용하여 새로운 기능 추가 시
    별도의 크기 계산 없이도 자동으로 최적 크기로 조정됩니다.

    🔧 새 기능 추가 방법:
    ---------------------
    1. 새 섹션 함수 작성: def _setup_새기능(self):
    2. _setup_ui_sections()에 호출 추가
    3. 필요시 결과 처리 로직 추가

    📐 자동 크기 조정 시스템:
    ------------------------
    - UI 구성 완료 후 실제 필요 크기를 자동 측정
    - 화면 크기에 맞춰 최적 크기 결정
    - 항상 화면 중앙에 배치
    - 최소/최대 크기 제한 적용

    🎨 UI 스타일 가이드:
    -------------------
    - 색상: DARK_COLORS 사용
    - 폰트: Segoe UI 계열
    - 여백: 일관된 패딩/마진 적용
    - 부모: self.main_frame 사용

    💡 예시 확장 기능들:
    -------------------
    - 우선순위 선택 (High/Medium/Low)
    - 카테고리 선택 (Work/Personal/Study)
    - 알림 설정 (시간/날짜)
    - 태그 입력 (#work #urgent)
    - 추가 메모 입력
    - 파일 첨부
    """

    def __init__(self, parent, todo_text="", initial_date=None, edit_mode=False):
        self.parent = parent
        self.todo_text = todo_text
        self.selected_date = initial_date  # 편집 모드에서 초기 날짜 설정
        self.result = None  # 'with_date', 'without_date', 'cancelled'
        self.edit_mode = edit_mode
        self.updated_text = todo_text  # 편집된 텍스트 저장

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("할일 수정" if edit_mode else "할일 추가")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # 다크 테마 색상 적용
        colors = DARK_COLORS
        self.dialog.configure(bg=colors['bg'])

        # 모든 UI 섹션 구성
        self._setup_ui_sections()
        self._setup_calendar()

        # UI 구성 완료 후 동적 크기 조정 및 위치 설정
        self._apply_dynamic_sizing()

        # ESC 키로 취소
        self.dialog.bind('<Escape>', lambda e: self._cancel())
        self.dialog.protocol("WM_DELETE_WINDOW", self._cancel)

    def _calculate_dynamic_size(self):
        """
        동적 크기 계산 (UI 구성 완료 후)

        🔄 자동 크기 조정 시스템:
        ---------------------------
        이 함수는 모든 UI 요소가 구성된 후 실제 필요한 크기를 자동으로 계산합니다.
        새 기능을 추가해도 별도의 크기 계산 로직을 추가할 필요가 없습니다.

        작동 원리:
        1. geometry("")로 자동 크기 조정 활성화
        2. update_idletasks()로 UI 레이아웃 완료 대기
        3. winfo_reqwidth/height()로 실제 필요 크기 측정
        4. 화면 크기 제한 및 최소 크기 보장

        ⚙️ 크기 조정 파라미터:
        - 최소 크기: 350x400 (기본 캘린더 크기)
        - 최대 크기: 화면의 80%
        - 여백: +50px (내용이 충분히 보이도록)
        """
        # 1단계: 자동 크기 조정 활성화
        self.dialog.geometry("")
        self.dialog.update_idletasks()

        # 2단계: 실제 필요한 크기 측정
        req_width = self.dialog.winfo_reqwidth()
        req_height = self.dialog.winfo_reqheight()

        # 3단계: 화면 크기 고려한 제한 적용
        screen_width = self.parent.winfo_screenwidth()
        screen_height = self.parent.winfo_screenheight()

        # 화면의 80% 이내, 최소 크기 보장
        max_width = int(screen_width * 0.8)
        max_height = int(screen_height * 0.8)
        min_width = 350  # 최소 너비 (캘린더 기본 크기)
        min_height = 400  # 최소 높이 (캘린더 기본 크기)

        # 🔧 새 기능 추가 시 크기 조정이 필요하다면:
        # min_width, min_height 값을 조정하거나
        # 특정 기능에 따른 추가 크기 계산 로직을 여기에 추가

        # 4단계: 최적 크기 결정 (여백 고려)
        final_width = max(min_width, min(req_width + 50, max_width))
        final_height = max(min_height, min(req_height + 50, max_height))

        return final_width, final_height

    def _apply_dynamic_sizing(self):
        """
        동적 크기 계산 및 적용

        📍 위치 및 크기 설정:
        ----------------------
        - 크기: _calculate_dynamic_size()에서 계산된 최적 크기
        - 위치: 화면 중앙, 최소 50px 여백 보장
        - 크기 조정 불가: 일관된 사용자 경험을 위해 고정
        """
        width, height = self._calculate_dynamic_size()

        # 화면 중앙에 배치
        screen_width = self.parent.winfo_screenwidth()
        screen_height = self.parent.winfo_screenheight()
        x = (screen_width - width) // 2
        y = max(50, (screen_height - height) // 2)

        self.dialog.geometry(f"{width}x{height}+{x}+{y}")
        self.dialog.resizable(False, False)


    def _setup_ui_sections(self):
        """
        모든 UI 섹션을 순차적으로 구성

        📋 새 기능 추가 시 확장 가이드:
        ---------------------------------------
        새로운 UI 섹션을 추가하려면 이 함수에 섹션을 추가하면 됩니다.
        다이얼로그 크기는 자동으로 조정되므로 크기 계산을 따로 할 필요가 없습니다.

        예시: 우선순위 선택 기능 추가
        1. def _setup_priority_selector(self): 함수 구현
        2. 아래 순서에 맞게 self._setup_priority_selector() 호출 추가

        추가 예시들:
        - self._setup_priority_selector()    # 우선순위 선택 (High/Medium/Low)
        - self._setup_category_selector()    # 카테고리 선택 (Work/Personal/etc)
        - self._setup_reminder_options()     # 알림 설정 (시간/날짜)
        - self._setup_tags_input()          # 태그 입력 (#tag1 #tag2)
        - self._setup_notes_section()       # 추가 메모 입력
        - self._setup_attachment_section()  # 파일 첨부

        ⚠️ 주의사항:
        - _setup_buttons()는 항상 마지막에 위치해야 함
        - 각 섹션 함수는 self.main_frame을 부모로 사용
        - 일관된 색상과 폰트를 위해 DARK_COLORS 사용 권장
        """
        self._setup_main_frame()
        self._setup_header()

        # 편집 모드일 때 텍스트 입력 필드 추가
        if self.edit_mode:
            self._setup_text_input()
        else:
            self._setup_todo_display()

        self._setup_calendar_section()

        # 🔧 새 기능들을 여기에 추가하세요:
        # self._setup_priority_selector()    # 우선순위 선택 기능
        # self._setup_category_selector()    # 카테고리 선택 기능
        # self._setup_reminder_options()     # 알림 설정 기능

        self._setup_buttons()  # 항상 마지막에 위치

    def _setup_main_frame(self):
        """
        메인 프레임 생성

        🏗️ UI 구조의 기초:
        ------------------
        모든 UI 요소들의 부모가 되는 메인 프레임을 생성합니다.
        새 섹션을 추가할 때는 반드시 self.main_frame을 부모로 사용하세요.
        """
        colors = DARK_COLORS
        self.main_frame = tk.Frame(self.dialog, bg=colors['bg'])
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    def _setup_header(self):
        """제목 섹션 구성"""
        colors = DARK_COLORS
        title_label = tk.Label(self.main_frame,
                              text="📝 할일 추가",
                              font=('Segoe UI', 14, 'bold'),
                              bg=colors['bg'],
                              fg=colors['text'])
        title_label.pack(pady=(0, 10))

    def _setup_todo_display(self):
        """TODO 텍스트 표시 섹션 구성 - StandardTodoDisplay 사용"""
        if self.todo_text:
            # StandardTodoDisplay가 사용 가능한지 확인
            if StandardTodoDisplay is not None:
                # StandardTodoDisplay로 일관된 TODO 렌더링
                # 임시 TODO 데이터 생성 (표시용)
                temp_todo = {
                    'id': 'preview',
                    'text': self.todo_text,
                    'completed': False,
                    'created_at': datetime.now().isoformat(),
                    'due_date': None  # 아직 설정되지 않음
                }

                # StandardTodoDisplay 컴포넌트 사용
                display_frame = StandardTodoDisplay(
                    self.main_frame,
                    todo_data=temp_todo,
                    read_only=True  # 읽기전용 모드
                )
                display_frame.pack(fill=tk.X, pady=(0, 15))

                # 미리보기 표시를 위한 스타일 적용
                display_frame.configure(relief='solid', borderwidth=1)
            else:
                # StandardTodoDisplay가 없는 경우 기본 라벨로 대체
                preview_label = tk.Label(
                    self.main_frame,
                    text=f"📝 {self.todo_text}",
                    font=('Segoe UI', 10),
                    bg=DARK_COLORS['bg_secondary'],
                    fg=DARK_COLORS['text'],
                    anchor='w',
                    justify='left',
                    relief='solid',
                    borderwidth=1,
                    padx=8,
                    pady=6
                )
                preview_label.pack(fill=tk.X, pady=(0, 15))

    def _setup_text_input(self):
        """편집 모드에서 할일 텍스트 입력 섹션 구성"""
        colors = DARK_COLORS

        # 할일 텍스트 입력 섹션 라벨
        text_label = tk.Label(self.main_frame,
                             text="📝 할일 내용",
                             font=('Segoe UI', 12, 'bold'),
                             bg=colors['bg'],
                             fg=colors['text'])
        text_label.pack(pady=(0, 10))

        # 텍스트 입력 필드
        self.text_entry = tk.Entry(self.main_frame,
                                  font=('Segoe UI', 10),
                                  bg=colors['entry_bg'],
                                  fg=colors['text'],
                                  borderwidth=1,
                                  relief='solid',
                                  insertbackground=colors['text'])
        self.text_entry.pack(fill=tk.X, pady=(0, 15), padx=10)

        # 기존 텍스트 설정
        if self.todo_text:
            self.text_entry.insert(0, self.todo_text)
            self.text_entry.selection_range(0, tk.END)

        # 포커스 설정
        self.text_entry.focus()

        # 이벤트 바인딩
        self.text_entry.bind('<Return>', self._on_text_change)
        self.text_entry.bind('<KeyRelease>', self._on_text_change)

    def _on_text_change(self, event=None):
        """텍스트 변경 시 updated_text 업데이트"""
        if hasattr(self, 'text_entry'):
            self.updated_text = self.text_entry.get().strip()

    def _setup_calendar_section(self):
        """캘린더 섹션 구성"""
        colors = DARK_COLORS

        # 납기일 선택 섹션 라벨
        date_label = tk.Label(self.main_frame,
                             text="📅 납기일 선택",
                             font=('Segoe UI', 12, 'bold'),
                             bg=colors['bg'],
                             fg=colors['text'])
        date_label.pack(pady=(0, 10))

        # 캘린더 프레임
        self.calendar_frame = tk.Frame(self.main_frame, bg=colors['bg'])
        self.calendar_frame.pack(pady=(0, 20))

    def _setup_buttons(self):
        """
        버튼 섹션 구성

        🔘 다이얼로그 하단 버튼들:
        --------------------------
        ⚠️ 이 함수는 항상 _setup_ui_sections()에서 마지막에 호출되어야 합니다!

        새 기능을 추가할 때 버튼이 추가로 필요하다면:
        1. 기존 버튼들과 일관된 스타일 유지
        2. 적절한 command 함수 연결
        3. 필요시 버튼 상태(enabled/disabled) 관리 로직 추가

        예시: 미리보기 버튼 추가
        preview_btn = tk.Button(button_frame, text="미리보기", ...)
        preview_btn.pack(side=tk.LEFT, padx=(10, 0))
        """
        colors = DARK_COLORS

        # 버튼 프레임
        button_frame = tk.Frame(self.main_frame, bg=colors['bg'])
        button_frame.pack(fill=tk.X, pady=(10, 0))

        # 버튼들 (편집 모드에 따라 텍스트 변경)
        no_date_style = get_button_style('secondary')
        no_date_text = "납기일 없이 수정" if self.edit_mode else "납기일 없이 추가"
        self.no_date_btn = tk.Button(button_frame,
                                    text=no_date_text,
                                    command=self._add_without_date,
                                    **no_date_style)
        self.no_date_btn.pack(side=tk.LEFT, padx=(0, 10))

        # 납기일과 함께 추가/수정 버튼 (Primary 스타일)
        with_date_style = get_button_style('primary')
        with_date_text = "납기일과 함께 수정" if self.edit_mode else "납기일과 함께 추가"
        self.with_date_btn = tk.Button(button_frame,
                                      text=with_date_text,
                                      command=self._add_with_date,
                                      state='disabled',
                                      **with_date_style)
        self.with_date_btn.pack(side=tk.RIGHT)

        # 편집 모드에서 납기일 제거 버튼 추가
        if self.edit_mode:
            remove_date_style = get_button_style('danger')
            self.remove_date_btn = tk.Button(button_frame,
                                           text="납기일 제거",
                                           command=self._remove_date,
                                           **remove_date_style)
            self.remove_date_btn.pack(side=tk.RIGHT, padx=(10, 0))

    def _setup_calendar(self):
        """간단한 캘린더 UI 구성"""
        colors = DARK_COLORS

        # 현재 날짜 또는 초기 날짜 설정
        if self.selected_date:
            # 초기 날짜가 있으면 해당 년월로 설정
            try:
                initial_date = datetime.fromisoformat(self.selected_date)
                self.current_month = initial_date.month
                self.current_year = initial_date.year
            except:
                # 날짜 파싱 실패시 현재 날짜 사용
                today = datetime.now()
                self.current_month = today.month
                self.current_year = today.year
        else:
            # 초기 날짜가 없으면 현재 날짜 사용
            today = datetime.now()
            self.current_month = today.month
            self.current_year = today.year

        # 월/년 선택 프레임
        month_year_frame = tk.Frame(self.calendar_frame, bg=colors['bg'])
        month_year_frame.pack(pady=(0, 10))

        # 이전 달 버튼
        prev_btn = tk.Button(month_year_frame, text="<", font=('Segoe UI', 10),
                            bg=colors['button_bg'], fg=colors['text'],
                            command=self._prev_month, width=3)
        prev_btn.pack(side=tk.LEFT, padx=(0, 10))

        # 월/년 표시
        self.month_year_label = tk.Label(month_year_frame,
                                        text=f"{self.current_year}년 {self.current_month}월",
                                        font=('Segoe UI', 11, 'bold'),
                                        bg=colors['bg'], fg=colors['text'])
        self.month_year_label.pack(side=tk.LEFT, padx=10)

        # 다음 달 버튼
        next_btn = tk.Button(month_year_frame, text=">", font=('Segoe UI', 10),
                            bg=colors['button_bg'], fg=colors['text'],
                            command=self._next_month, width=3)
        next_btn.pack(side=tk.LEFT, padx=(10, 0))

        # 요일 헤더
        days_frame = tk.Frame(self.calendar_frame, bg=colors['bg'])
        days_frame.pack()

        day_names = ['일', '월', '화', '수', '목', '금', '토']
        for day_name in day_names:
            day_label = tk.Label(days_frame, text=day_name, font=('Segoe UI', 9, 'bold'),
                               bg=colors['bg'], fg=colors['text_secondary'],
                               width=4, height=1)
            day_label.grid(row=0, column=day_names.index(day_name), padx=1, pady=1)

        # 날짜 버튼들을 위한 프레임
        self.dates_frame = tk.Frame(self.calendar_frame, bg=colors['bg'])
        self.dates_frame.pack(pady=(5, 0))

        self._update_calendar()

    def _prev_month(self):
        """이전 달로 이동"""
        if self.current_month == 1:
            self.current_month = 12
            self.current_year -= 1
        else:
            self.current_month -= 1
        self._update_calendar()

    def _next_month(self):
        """다음 달로 이동"""
        if self.current_month == 12:
            self.current_month = 1
            self.current_year += 1
        else:
            self.current_month += 1
        self._update_calendar()

    def _update_calendar(self):
        """캘린더 업데이트"""
        colors = DARK_COLORS

        # 월/년 라벨 업데이트
        self.month_year_label.configure(text=f"{self.current_year}년 {self.current_month}월")

        # 기존 날짜 버튼들 제거
        for widget in self.dates_frame.winfo_children():
            widget.destroy()

        # 해당 월의 첫째 날과 마지막 날
        import calendar
        first_day = datetime(self.current_year, self.current_month, 1)
        last_day = datetime(self.current_year, self.current_month,
                           calendar.monthrange(self.current_year, self.current_month)[1])

        # 첫째 날의 요일 (0=월요일, 6=일요일) -> (0=일요일, 6=토요일)로 변환
        first_weekday = (first_day.weekday() + 1) % 7

        # 오늘 날짜
        today = datetime.now().date()

        # 기존 선택된 날짜 파싱 (편집 모드용)
        selected_day = None
        if self.selected_date:
            try:
                selected_parsed = datetime.fromisoformat(self.selected_date).date()
                if (selected_parsed.year == self.current_year and
                    selected_parsed.month == self.current_month):
                    selected_day = selected_parsed.day
            except:
                pass

        row = 1
        col = first_weekday

        for day in range(1, last_day.day + 1):
            current_date = datetime(self.current_year, self.current_month, day).date()

            # 과거 날짜도 선택 가능하되 시각적으로 구분
            is_past = current_date < today
            is_today = current_date == today
            is_selected = (day == selected_day)  # 기존 선택된 날짜

            # 버튼 색상 설정
            if is_past:
                bg_color = colors['bg_secondary']
                fg_color = colors['text_secondary']
                state = 'normal'  # 과거 날짜도 활성화
            elif is_selected:  # 기존 선택된 날짜
                bg_color = colors['accent']
                fg_color = 'white'
                state = 'normal'
            elif is_today:
                bg_color = colors['warning']
                fg_color = colors['bg']
                state = 'normal'
            else:
                bg_color = colors['button_bg']
                fg_color = colors['text']
                state = 'normal'

            date_btn = tk.Button(self.dates_frame, text=str(day),
                               font=('Segoe UI', 9),
                               bg=bg_color, fg=fg_color,
                               width=4, height=2,
                               state=state,
                               command=lambda d=day: self._select_date(d))

            # 모든 날짜에 호버 효과 적용
            date_btn.bind('<Enter>', lambda e, btn=date_btn: btn.configure(bg=colors['bg_hover']))
            date_btn.bind('<Leave>', lambda e, btn=date_btn, orig_bg=bg_color: btn.configure(bg=orig_bg))

            date_btn.grid(row=row, column=col, padx=1, pady=1)

            col += 1
            if col > 6:
                col = 0
                row += 1

        # 편집 모드에서 기존 날짜가 선택되어 있으면 버튼 활성화
        if self.edit_mode and selected_day:
            self.with_date_btn.configure(state='normal')
            # Primary 스타일로 활성화
            primary_style = get_button_style('primary')
            for key, value in primary_style.items():
                if key != 'state':
                    self.with_date_btn.configure({key: value})

            # 선택된 날짜 표시 업데이트
            selected_text = f"선택: {self.current_year}년 {self.current_month}월 {selected_day}일"
            action_text = "납기일과 함께 수정" if self.edit_mode else "납기일과 함께 추가"
            self.with_date_btn.configure(text=f"{action_text}\n({selected_text})")

    def _select_date(self, day):
        """날짜 선택"""
        self.selected_date = f"{self.current_year:04d}-{self.current_month:02d}-{day:02d}"

        # "납기일과 함께 추가/수정" 버튼 활성화 및 스타일 업데이트
        self.with_date_btn.configure(state='normal')
        # Primary 스타일로 활성화
        primary_style = get_button_style('primary')
        for key, value in primary_style.items():
            if key != 'state':  # state는 별도 관리
                self.with_date_btn.configure({key: value})

        # 선택된 날짜 표시 업데이트
        selected_text = f"선택: {self.current_year}년 {self.current_month}월 {day}일"
        action_text = "납기일과 함께 수정" if self.edit_mode else "납기일과 함께 추가"
        self.with_date_btn.configure(text=f"{action_text}\n({selected_text})")

    def _add_without_date(self):
        """납기일 없이 추가/수정"""
        # 편집 모드에서 텍스트 검증
        if self.edit_mode and hasattr(self, 'text_entry'):
            text = self.text_entry.get().strip()
            if not text:
                import tkinter.messagebox as messagebox
                messagebox.showerror("입력 오류", "할일 내용을 입력해주세요.")
                return
            self.updated_text = text

        self.result = 'without_date'
        self.selected_date = None
        self.dialog.destroy()

    def _add_with_date(self):
        """납기일과 함께 추가/수정"""
        # 편집 모드에서 텍스트 검증
        if self.edit_mode and hasattr(self, 'text_entry'):
            text = self.text_entry.get().strip()
            if not text:
                import tkinter.messagebox as messagebox
                messagebox.showerror("입력 오류", "할일 내용을 입력해주세요.")
                return
            self.updated_text = text

        if self.selected_date:
            self.result = 'with_date'
            self.dialog.destroy()

    def _remove_date(self):
        """납기일 제거 (편집 모드에서만 사용)"""
        if self.edit_mode and hasattr(self, 'text_entry'):
            text = self.text_entry.get().strip()
            if not text:
                import tkinter.messagebox as messagebox
                messagebox.showerror("입력 오류", "할일 내용을 입력해주세요.")
                return
            self.updated_text = text

        self.result = 'without_date'
        self.selected_date = None
        self.dialog.destroy()

    def _cancel(self):
        """취소"""
        self.result = 'cancelled'
        self.selected_date = None
        self.dialog.destroy()

    def show(self):
        """다이얼로그 표시 및 결과 반환"""
        self.dialog.wait_window()
        if self.edit_mode:
            return self.result, self.selected_date, self.updated_text
        else:
            return self.result, self.selected_date


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
        self.main_frame = tk.Frame(self.parent, bg=colors['bg'])

        # 헤더 프레임 (클릭 가능한 제목)
        self.header_frame = tk.Frame(self.main_frame,
                                   bg=colors['bg_secondary'],
                                   relief='solid',
                                   borderwidth=1,
                                   cursor='hand2')
        self.header_frame.pack(fill=tk.X, pady=(0, 2))

        # 제목 라벨
        arrow = "▼" if not self.is_collapsed else "▶"
        self.title_label = tk.Label(self.header_frame,
                                   text=f"{arrow} {self.title}",
                                   font=('Segoe UI', 10, 'bold'),
                                   bg=colors['bg_secondary'],
                                   fg=colors['text'],
                                   anchor='w',
                                   padx=10, pady=5)
        self.title_label.pack(fill=tk.X)

        # 내용 프레임
        self.content_frame = tk.Frame(self.main_frame, bg=colors['bg'])
        if not self.is_collapsed:
            self.content_frame.pack(fill=tk.BOTH, expand=True)

        # 클릭 이벤트
        self.header_frame.bind('<Button-1>', self._toggle_section)
        self.title_label.bind('<Button-1>', self._toggle_section)

    def _toggle_section(self, event=None):
        """섹션 접기/펼치기 토글"""
        self.is_collapsed = not self.is_collapsed

        arrow = "▼" if not self.is_collapsed else "▶"
        current_text = self.title_label.cget('text')
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


class TodoPanelApp:
    """메인 TODO 패널 애플리케이션 (섹션 분할 및 새로운 기능 포함)"""

    def __init__(self, root=None, todo_service=None, notification_service=None):
        # CLEAN 아키텍처 지원: 인터페이스 또는 기본 구현 사용
        if root is None:
            self.root = tk.Tk()
        else:
            self.root = root

        # 다크 테마 색상 사용

        # CLEAN 아키텍처 서비스 또는 기본 구현 사용
        if todo_service is not None:
            # CLEAN 아키텍처 서비스 사용
            self.todo_service = todo_service
            self.notification_service = notification_service
            self.todo_manager = None  # 서비스 패턴 사용시 직접 manager 사용 안함
        else:
            # 기존 TodoManager 초기화 (하위 호환성)
            try:
                from todo_manager import UnifiedTodoManager as TodoManager
                self.todo_manager = TodoManager(debug=True, batch_save=True)
            except (ImportError, TypeError):
                # batch_save 파라미터가 없는 기본 TodoManager의 경우
                self.todo_manager = TodoManager(debug=True)
            self.todo_service = None
            self.notification_service = None

        # 정렬 관리자
        self.sort_manager = SortManager()

        # UI 상태
        self.todo_widgets: Dict[str, TodoItemWidget] = {}
        self.always_on_top = False

        # 섹션별 위젯 관리
        self.pending_widgets: Dict[str, TodoItemWidget] = {}
        self.completed_widgets: Dict[str, TodoItemWidget] = {}

        self._setup_window()
        self._setup_ui()
        self._load_sort_settings()  # 정렬 설정 로드
        self._load_todos()

        # 창 닫기 이벤트 처리
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _setup_window(self):
        """메인 윈도우 설정"""
        self.root.title("TODO Panel")
        self.root.geometry("400x600")
        self.root.minsize(300, 400)

        # 다크테마 배경
        colors = DARK_COLORS
        self.root.configure(bg=colors['bg'])

        # 아이콘 설정
        try:
            self.root.iconbitmap(default='')
        except:
            pass

        self.root.resizable(True, True)

    def _setup_ui(self):
        """UI 구성 요소 설정"""
        colors = DARK_COLORS

        # 메인 컨테이너
        main_frame = tk.Frame(self.root, bg=colors['bg'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=6, pady=4)

        # 상단 통합 제어 패널
        self._setup_control_panel(main_frame)

        # TODO 리스트 섹션 (분할된 섹션들)
        self._setup_sections(main_frame)

        # 하단 상태바
        self._setup_status_bar(main_frame)

    def _setup_control_panel(self, parent):
        """상단 통합 제어 패널 설정"""
        control_frame = tk.Frame(parent, bg=DARK_COLORS['bg'])
        control_frame.pack(fill=tk.X, pady=(0, 4))

        # 좌측: TODO 입력 영역
        self.entry_var = tk.StringVar()
        self.todo_entry = tk.Entry(control_frame,
                                  textvariable=self.entry_var,
                                  font=('Segoe UI', 9),
                                  bg=DARK_COLORS['entry_bg'],
                                  fg=DARK_COLORS['text'],
                                  borderwidth=1,
                                  relief='solid')
        self.todo_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))

        # 추가 버튼
        self.add_btn = tk.Button(control_frame,
                                text='추가',
                                command=self._show_add_todo_dialog,
                                font=('Segoe UI', 9, 'bold'),
                                bg=DARK_COLORS['accent'],
                                fg='white',
                                padx=15, pady=5)
        self.add_btn.pack(side=tk.LEFT, padx=(0, 8))
        ToolTip(self.add_btn, "새 할일 추가")

        # 정렬 드롭다운 (기존 토글 버튼 교체)
        if SortDropdownWidget:
            self.sort_dropdown = SortDropdownWidget(
                control_frame,
                self.sort_manager,
                self._on_sort_changed
            )
            self.sort_dropdown.pack(side=tk.RIGHT, padx=(4, 0))
        else:
            # 폴백: 기본 정렬 버튼
            self.sort_btn = tk.Button(control_frame,
                                     text='🔄 정렬',
                                     font=('Segoe UI', 9),
                                     bg=DARK_COLORS['button_bg'],
                                     fg=DARK_COLORS['text'],
                                     padx=5, pady=5)
            self.sort_btn.pack(side=tk.RIGHT, padx=(4, 0))

        # 우측 제어 버튼들
        # 항상 위 토글
        self.top_btn = tk.Button(control_frame,
                                text='📌',
                                width=3,
                                command=self._toggle_always_on_top,
                                font=('Segoe UI', 8),
                                bg=DARK_COLORS['button_bg'],
                                fg=DARK_COLORS['text'],
                                padx=5, pady=5)
        self.top_btn.pack(side=tk.RIGHT, padx=(4, 0))
        ToolTip(self.top_btn, "항상 위에 표시")

        # 완료된 항목 정리 버튼
        self.clear_btn = tk.Button(control_frame,
                                  text='🗑️',
                                  width=3,
                                  command=self._clear_completed,
                                  font=('Segoe UI', 8),
                                  bg=DARK_COLORS['button_bg'],
                                  fg=DARK_COLORS['text'],
                                  padx=5, pady=5)
        self.clear_btn.pack(side=tk.RIGHT, padx=(4, 0))
        ToolTip(self.clear_btn, "완료된 항목 모두 삭제")

        # 정보 버튼
        self.info_btn = tk.Button(control_frame,
                                 text='ⓘ',
                                 width=3,
                                 command=self._show_about_dialog,
                                 font=('Segoe UI', 8),
                                 bg=DARK_COLORS['button_bg'],
                                 fg=DARK_COLORS['text'],
                                 padx=5, pady=5)
        self.info_btn.pack(side=tk.RIGHT, padx=(4, 0))
        ToolTip(self.info_btn, "개발자 정보 및 더 많은 도구들")

        # 입력 필드 이벤트 설정
        self.todo_entry.bind('<Return>', lambda e: self._show_add_todo_dialog())
        self.todo_entry.bind('<FocusIn>', self._on_entry_focus_in)
        self.todo_entry.bind('<FocusOut>', self._on_entry_focus_out)
        self._set_entry_placeholder()

    def _setup_sections(self, parent):
        """섹션 분할된 TODO 리스트 설정 (동적 크기조절 지원)"""
        colors = DARK_COLORS

        # PanedWindow로 동적 크기조절 구현
        self.sections_paned_window = tk.PanedWindow(
            parent,
            orient=tk.VERTICAL,  # 세로 방향 분할
            bg=colors['bg'],
            bd=0,
            sashwidth=6,  # 분할바 두께
            sashrelief=tk.FLAT,
            sashpad=2,
            handlesize=8,
            handlepad=10,
            showhandle=True
        )
        self.sections_paned_window.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        # 분할바 스타일링 (Magic UI 다크 테마)
        self._style_paned_window_sash()

        # 진행중인 할일 섹션 프레임
        pending_frame = tk.Frame(self.sections_paned_window, bg=colors['bg'])
        self.pending_section = CollapsibleSection(
            pending_frame,
            "📋 진행중인 할일 (0개)",
            initial_collapsed=False
        )
        self.pending_section.pack(fill=tk.BOTH, expand=True)

        # 진행중 할일을 위한 스크롤 가능한 영역
        self._setup_scrollable_area(
            self.pending_section.get_content_frame(),
            'pending'
        )

        # 완료된 할일 섹션 프레임
        completed_frame = tk.Frame(self.sections_paned_window, bg=colors['bg'])
        self.completed_section = CollapsibleSection(
            completed_frame,
            "✅ 완료된 할일 (0개)",
            initial_collapsed=False  # PanedWindow에서는 기본으로 펼쳐둠
        )
        self.completed_section.pack(fill=tk.BOTH, expand=True)

        # 완료된 할일을 위한 스크롤 가능한 영역
        self._setup_scrollable_area(
            self.completed_section.get_content_frame(),
            'completed'
        )

        # PanedWindow에 프레임들 추가
        self.sections_paned_window.add(pending_frame, minsize=100, sticky="nsew")
        self.sections_paned_window.add(completed_frame, minsize=40, sticky="nsew")

        # 기본 분할 비율 설정 (진행중 70%, 완료 30%)
        print("[DEBUG] 분할 비율 초기화 스케줄링...")
        self.root.after(100, lambda: self._set_initial_pane_ratio())
        # 대안: 즉시 호출도 추가
        print("[DEBUG] 즉시 분할 비율 복원 시도...")
        try:
            self._set_initial_pane_ratio()
        except Exception as e:
            print(f"[DEBUG] 즉시 호출 실패: {e}")

    def _setup_scrollable_area(self, parent, section_type):
        """스크롤 가능한 영역 설정 (멀티 플랫폼 마우스 휠 지원)"""
        import sys
        colors = DARK_COLORS

        # 스크롤 컨테이너
        scroll_container = tk.Frame(parent, bg=colors['bg'])
        scroll_container.pack(fill=tk.BOTH, expand=True)

        # 캔버스와 스크롤바 (동적 크기 조정)
        # 최소 높이와 최대 높이 설정
        min_height = 100
        max_height = 400 if section_type == 'pending' else 300
        default_height = 200 if section_type == 'pending' else 150

        canvas = tk.Canvas(scroll_container,
                          highlightthickness=0,
                          bg=colors['bg'],
                          height=default_height,
                          takefocus=True)  # ✅ 포커스 설정 추가
        scrollbar = tk.Scrollbar(scroll_container,
                                orient=tk.VERTICAL,
                                command=canvas.yview,
                                bg=colors['bg_secondary'],
                                troughcolor=colors['bg'],
                                activebackground=colors['accent'],
                                highlightthickness=0,
                                borderwidth=1,
                                elementborderwidth=1)

        canvas.configure(yscrollcommand=scrollbar.set)

        # 스크롤 가능한 프레임
        scrollable_frame = tk.Frame(canvas, bg=colors['bg'])
        canvas_window = canvas.create_window((0, 0),
                                           window=scrollable_frame,
                                           anchor="nw")

        # 패킹
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 이벤트 바인딩
        def configure_scroll_region(event):
            # 레이아웃 계산 완료 후 스크롤 영역 업데이트
            canvas.after_idle(lambda: _update_scroll_region(canvas))

        def _update_scroll_region(canvas_widget):
            """스크롤 영역을 안전하게 업데이트"""
            try:
                # 업데이트 전 잠시 대기 (레이아웃 완료 확보)
                canvas_widget.update_idletasks()

                # bbox("all")이 None을 반환할 수 있으므로 안전하게 처리
                bbox = canvas_widget.bbox("all")
                if bbox:
                    # ✅ 스크롤 영역 정확한 설정
                    canvas_widget.configure(scrollregion=bbox)
                    # 스크롤바 가시성 업데이트
                    _update_scrollbar_visibility(canvas_widget, scrollbar)
                else:
                    # 내용이 없으면 스크롤 영역 초기화
                    canvas_widget.configure(scrollregion=(0, 0, 0, 0))
                    scrollbar.pack_forget()  # 스크롤바 숨김
            except Exception as e:
                # 예외 발생 시 로그 출력 (디버깅용)
                if hasattr(self, '_debug') and self._debug:
                    print(f"[DEBUG] 스크롤 영역 업데이트 실패: {e}")

        def _update_scrollbar_visibility(canvas_widget, scrollbar_widget):
            """스크롤바 가시성을 동적으로 조정"""
            try:
                # 캔버스 크기와 내용 크기 비교
                canvas_height = canvas_widget.winfo_height()
                scroll_region = canvas_widget.cget('scrollregion')

                if scroll_region:
                    # scrollregion은 "x1 y1 x2 y2" 형식의 문자열
                    coords = scroll_region.split()
                    if len(coords) >= 4:
                        content_height = int(float(coords[3])) - int(float(coords[1]))

                        # 내용이 캔버스보다 클 때만 스크롤바 표시
                        if content_height > canvas_height:
                            scrollbar_widget.pack(side=tk.RIGHT, fill=tk.Y)
                        else:
                            scrollbar_widget.pack_forget()
            except Exception as e:
                # 에러 발생 시 기본적으로 스크롤바 표시
                scrollbar_widget.pack(side=tk.RIGHT, fill=tk.Y)

        def configure_canvas_width(event):
            canvas.itemconfig(canvas_window, width=event.width)

        def adjust_canvas_height():
            """내용에 따라 Canvas 높이를 동적으로 조정"""
            try:
                # 스크롤 가능한 프레임의 실제 높이 계산
                scrollable_frame.update_idletasks()
                content_height = scrollable_frame.winfo_reqheight()

                # 최소/최대 높이 제한 적용
                new_height = max(min_height, min(content_height + 20, max_height))

                # 현재 높이와 다르면 업데이트
                current_height = canvas.winfo_reqheight()
                if abs(new_height - current_height) > 5:  # 5px 이상 차이날 때만 업데이트
                    canvas.configure(height=new_height)

                    # Canvas 크기 변경 후 스크롤 영역도 업데이트
                    canvas.after_idle(lambda: _update_scroll_region(canvas))

            except Exception as e:
                if hasattr(self, '_debug') and self._debug:
                    print(f"[DEBUG] Canvas 높이 조정 실패: {e}")

        def on_content_change():
            """내용 변경 시 Canvas 높이 조정"""
            canvas.after_idle(adjust_canvas_height)

        # ✅ 공통 마우스 휠 핸들러 (Canvas 참조를 클로저로 캡처)
        def create_mousewheel_handler(target_canvas):
            """마우스 휠 핸들러 팩토리 함수 - Canvas 참조를 캡처"""
            def on_mousewheel(event):
                """마우스 휠 스크롤 처리 (멀티 플랫폼 지원)"""
                try:
                    # Windows/macOS에서 event.delta 사용
                    if sys.platform.startswith('win') or sys.platform == 'darwin':
                        delta = event.delta
                        if delta > 0:
                            target_canvas.yview_scroll(-1, "units")  # 위로 스크롤
                        elif delta < 0:
                            target_canvas.yview_scroll(1, "units")   # 아래로 스크롤
                    else:
                        # Linux: Button-4 (위) / Button-5 (아래)
                        if event.num == 4:
                            target_canvas.yview_scroll(-1, "units")  # 위로 스크롤
                        elif event.num == 5:
                            target_canvas.yview_scroll(1, "units")   # 아래로 스크롤

                    # 스크롤 후 포커스 유지
                    target_canvas.focus_set()
                    return "break"  # ✅ 이벤트 전파 중단
                except Exception as e:
                    if hasattr(self, '_debug') and self._debug:
                        print(f"[DEBUG] 마우스 휠 스크롤 처리 실패: {e}")
            return on_mousewheel

        def create_linux_mousewheel_handlers(target_canvas):
            """Linux용 마우스 휠 핸들러 팩토리 함수"""
            def on_linux_mousewheel_up(event):
                """Linux 마우스 휠 위로 스크롤"""
                target_canvas.yview_scroll(-1, "units")
                target_canvas.focus_set()
                return "break"

            def on_linux_mousewheel_down(event):
                """Linux 마우스 휠 아래로 스크롤"""
                target_canvas.yview_scroll(1, "units")
                target_canvas.focus_set()
                return "break"

            return on_linux_mousewheel_up, on_linux_mousewheel_down

        # 핸들러 인스턴스 생성
        mousewheel_handler = create_mousewheel_handler(canvas)
        linux_up_handler, linux_down_handler = create_linux_mousewheel_handlers(canvas)

        # ✅ 포커스 및 마우스 이벤트 관리
        def on_canvas_click(event):
            """캔버스 클릭 시 포커스 설정"""
            canvas.focus_set()

        def on_canvas_focus(event):
            """마우스가 캔버스 영역에 들어올 때 포커스 설정"""
            canvas.focus_set()

        # 기본 이벤트 바인딩
        scrollable_frame.bind('<Configure>', configure_scroll_region)
        canvas.bind('<Configure>', configure_canvas_width)

        # 동적 크기 조정 이벤트 바인딩
        scrollable_frame.bind('<Map>', lambda e: on_content_change())
        scrollable_frame.bind('<Unmap>', lambda e: on_content_change())

        # ✅ 정적 마우스 휠 이벤트 바인딩 (항상 활성화)
        if sys.platform.startswith('win') or sys.platform == 'darwin':
            canvas.bind('<MouseWheel>', mousewheel_handler)
        else:  # Linux
            canvas.bind('<Button-4>', linux_up_handler)
            canvas.bind('<Button-5>', linux_down_handler)

        # 포커스 이벤트 바인딩
        canvas.bind('<Enter>', on_canvas_focus)
        canvas.bind('<Button-1>', on_canvas_click)  # 클릭 시 포커스 설정

        # ✅ 외부에서 접근 가능한 마우스 휠 핸들러 저장 (TodoItemWidget에서 사용)
        canvas._mousewheel_handler = mousewheel_handler
        canvas._linux_up_handler = linux_up_handler
        canvas._linux_down_handler = linux_down_handler

        # 초기 Canvas 높이 조정
        canvas.after_idle(adjust_canvas_height)

        # 섹션별로 참조 저장
        if section_type == 'pending':
            self.pending_canvas = canvas
            self.pending_scrollable_frame = scrollable_frame
        else:
            self.completed_canvas = canvas
            self.completed_scrollable_frame = scrollable_frame

    def _setup_status_bar(self, parent):
        """하단 상태바 설정"""
        status_frame = tk.Frame(parent, bg=DARK_COLORS['bg'])
        status_frame.pack(fill=tk.X)

        self.status_label = tk.Label(status_frame,
                                    text="",
                                    font=('Segoe UI', 8),
                                    bg=DARK_COLORS['bg'],
                                    fg=DARK_COLORS['text_secondary'])
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
            self.todo_entry.configure(foreground=DARK_COLORS['text'])

    def _on_entry_focus_out(self, event):
        """입력 필드 포커스 해제 시"""
        if not self.entry_var.get():
            self._set_entry_placeholder()

    def _show_add_todo_dialog(self):
        """할일 추가 다이얼로그 표시"""
        text = self.entry_var.get().strip()
        if not text or text == "새 할 일을 입력하세요...":
            return

        # 날짜 선택 다이얼로그 표시
        dialog = DatePickerDialog(self.root, text)
        result, selected_date = dialog.show()

        if result == 'cancelled':
            return

        try:
            # TODO 생성 (due_date 포함)
            due_date = selected_date if result == 'with_date' else None
            todo = self._create_todo_with_date(text, due_date)

            if todo:
                self._create_todo_widget(todo)

                # 입력 필드 초기화
                self.entry_var.set("")
                self._set_entry_placeholder()

                self._update_status()
                self._update_section_titles()

        except Exception as e:
            messagebox.showerror("오류", f"TODO 추가에 실패했습니다: {e}")

    def _create_todo_with_date(self, text, due_date):
        """날짜가 포함된 TODO 생성"""
        # 기존 create_todo 메소드가 due_date 파라미터를 지원하는지 확인
        try:
            # 새로운 방식으로 시도 (due_date 파라미터 포함)
            todo = self.todo_manager.create_todo(text, due_date=due_date)
            return todo
        except TypeError:
            # 기존 방식으로 TODO 생성 후 수동으로 due_date 추가
            todo = self.todo_manager.create_todo(text)
            if due_date:
                # 🔒 안전한 업데이트로 due_date 추가 (데이터 보존 보장)
                update_method = getattr(self.todo_manager, 'update_todo_safe', self.todo_manager.update_todo)
                update_method(todo['id'], due_date=due_date)
                todo['due_date'] = due_date
            return todo

    def _on_sort_changed(self, option_key: str):
        """정렬 옵션 변경 시 처리 - position 자동 동기화 포함"""
        try:
            # 먼저 현재 TODO 목록을 새로운 정렬 기준으로 가져오기
            todos = self.todo_manager.get_todos()
            pending_todos, completed_todos = self.sort_manager.separate_by_completion(todos)

            # 🚀 NEW: 정렬 변경 후 position 자동 동기화
            print(f"[DEBUG] 정렬 변경됨: {option_key} - position 동기화 시작")

            # 미완료 항목들 position 동기화
            if pending_todos:
                sync_success = self.sort_manager.sync_positions_with_current_sort(
                    pending_todos, self.todo_manager
                )
                print(f"[DEBUG] 미완료 항목 position 동기화: {'성공' if sync_success else '실패'}")

            # 완료된 항목들 position 동기화
            if completed_todos:
                sync_success = self.sort_manager.sync_positions_with_current_sort(
                    completed_todos, self.todo_manager
                )
                print(f"[DEBUG] 완료 항목 position 동기화: {'성공' if sync_success else '실패'}")

            # 정렬 적용을 위해 TODO 목록 다시 로드
            self._load_todos()

            # 드롭다운 디스플레이 업데이트
            if hasattr(self, 'sort_dropdown') and self.sort_dropdown:
                self.sort_dropdown.update_display()

            # 🆕 정렬 변경 시 즉시 설정 저장
            self._save_all_ui_settings()
            print(f"[DEBUG] 정렬 변경 후 즉시 저장 완료: {option_key}")

        except Exception as e:
            print(f"[ERROR] 정렬 변경 처리 실패: {e}")
            # 폴백: 기본 로드만 수행
            self._load_todos()

    def _load_todos(self):
        """TODO 목록 로드 및 표시 (섹션별 분리)"""
        try:
            todos = self.todo_manager.get_todos()

            # 기존 위젯들 정리
            for widget in list(self.pending_widgets.values()) + list(self.completed_widgets.values()):
                widget.destroy()
            self.pending_widgets.clear()
            self.completed_widgets.clear()
            self.todo_widgets.clear()

            # 완료/미완료로 분리 후 정렬
            pending_todos, completed_todos = self.sort_manager.separate_by_completion(todos)

            # 위젯 생성
            for todo in pending_todos:
                self._create_todo_widget(todo, section='pending')

            for todo in completed_todos:
                self._create_todo_widget(todo, section='completed')

            self._update_status()
            self._update_section_titles()

        except Exception as e:
            messagebox.showerror("오류", f"TODO 목록을 불러오는데 실패했습니다: {e}")

    def _create_todo_widget(self, todo_data: Dict[str, Any], section=None):
        """TODO 위젯 생성 (섹션 지정)"""
        # 섹션 자동 결정
        if section is None:
            section = 'completed' if todo_data.get('completed', False) else 'pending'

        # 적절한 부모 프레임 선택
        parent_frame = self.pending_scrollable_frame if section == 'pending' else self.completed_scrollable_frame

        widget = TodoItemWidget(
            parent_frame,
            todo_data,
            self._update_todo,
            self._delete_todo,
            self._reorder_todo,
            debug=getattr(self.todo_manager, '_debug', False)
        )
        widget.pack(fill=tk.X, pady=1)

        # ✅ 마우스 휠 스크롤 바인딩 - 모든 자식 위젯에 Canvas 스크롤 적용
        target_canvas = self.pending_canvas if section == 'pending' else self.completed_canvas
        if target_canvas:
            widget.bind_mousewheel_to_canvas(target_canvas)

        # 섹션별 관리
        if section == 'pending':
            self.pending_widgets[todo_data['id']] = widget
        else:
            self.completed_widgets[todo_data['id']] = widget

        # 전체 관리용
        self.todo_widgets[todo_data['id']] = widget

    def _update_section_titles(self):
        """섹션 제목 업데이트 (개수 표시)"""
        pending_count = len(self.pending_widgets)
        completed_count = len(self.completed_widgets)

        self.pending_section.update_title(f"📋 진행중인 할일 ({pending_count}개)")
        self.completed_section.update_title(f"✅ 완료된 할일 ({completed_count}개)")

    def _update_todo(self, todo_id: str, **kwargs):
        """TODO 업데이트 (섹션 이동 처리) - 완전한 데이터 보존"""
        try:
            # 🔒 중앙집중식 데이터 보존을 위해 update_todo_safe 사용
            # 납기일, 우선순위 등 모든 메타데이터가 자동으로 보존
            success = getattr(self.todo_manager, 'update_todo_safe', self.todo_manager.update_todo)(todo_id, **kwargs)
            if success:
                # 완료 상태 변경 시 섹션 이동
                if 'completed' in kwargs:
                    self._move_todo_between_sections(todo_id, kwargs['completed'])

                # 위젯 데이터 업데이트
                if todo_id in self.todo_widgets:
                    updated_todo = self.todo_manager.get_todo_by_id(todo_id)
                    if updated_todo:
                        self.todo_widgets[todo_id].update_data(updated_todo)

                self._update_status()
                self._update_section_titles()
            else:
                messagebox.showerror("오류", "TODO 업데이트에 실패했습니다.")

        except Exception as e:
            messagebox.showerror("오류", f"TODO 업데이트에 실패했습니다: {e}")

    def _move_todo_between_sections(self, todo_id: str, completed: bool):
        """TODO를 섹션 간에 이동"""
        if todo_id not in self.todo_widgets:
            return

        widget = self.todo_widgets[todo_id]
        todo_data = widget.todo_data

        # 기존 섹션에서 제거
        if todo_id in self.pending_widgets:
            del self.pending_widgets[todo_id]
        if todo_id in self.completed_widgets:
            del self.completed_widgets[todo_id]

        # 위젯 제거
        widget.destroy()

        # 새로운 섹션에서 다시 생성
        section = 'completed' if completed else 'pending'
        self._create_todo_widget(todo_data, section)

    def _delete_todo(self, todo_id: str):
        """TODO 삭제"""
        try:
            success = self.todo_manager.delete_todo(todo_id)
            if success:
                # UI에서 위젯 제거
                if todo_id in self.todo_widgets:
                    self.todo_widgets[todo_id].destroy()
                    del self.todo_widgets[todo_id]

                # 섹션별 위젯 관리에서도 제거
                if todo_id in self.pending_widgets:
                    del self.pending_widgets[todo_id]
                if todo_id in self.completed_widgets:
                    del self.completed_widgets[todo_id]

                self._update_status()
                self._update_section_titles()
            else:
                messagebox.showerror("오류", "TODO 삭제에 실패했습니다.")

        except Exception as e:
            messagebox.showerror("오류", f"TODO 삭제 중 오류가 발생했습니다: {e}")

    def _reorder_todo(self, todo_id: str, move_steps: int):
        """TODO 순서 변경 (수동 모드 자동 전환) - 정리된 로직"""
        try:
            # 현재 TODO 찾기
            widget = self.todo_widgets.get(todo_id)
            if not widget:
                print(f"[WARNING] TODO 위젯을 찾을 수 없음: {todo_id}")
                return

            is_completed = widget.todo_data.get('completed', False)
            print(f"[DEBUG] TODO 이동 시작: {todo_id[:8]} ({'완료' if is_completed else '미완료'} 섹션)")

            # 🔄 올바른 화면 순서 가져오기 (정렬된 순서)
            todos = self.todo_manager.get_todos()
            pending_todos, completed_todos = self.sort_manager.separate_by_completion(todos)
            current_section_todos = completed_todos if is_completed else pending_todos

            # 현재 위치 찾기
            current_pos = None
            for i, todo in enumerate(current_section_todos):
                if todo['id'] == todo_id:
                    current_pos = i
                    break

            if current_pos is None:
                print(f"[WARNING] TODO 위치를 찾을 수 없음: {todo_id}")
                return

            # 새 위치 계산
            new_pos = max(0, min(len(current_section_todos) - 1, current_pos + move_steps))
            print(f"[DEBUG] 위치 변경: {current_pos} -> {new_pos}")

            if new_pos != current_pos:
                # 🚀 수동 이동 전 position 동기화 (MANUAL 모드가 아닌 경우에만)
                if not self.sort_manager.is_manual_mode():
                    print("[DEBUG] 수동 모드 전환 전 position 동기화 수행")
                    sync_success = self.sort_manager.sync_positions_with_current_sort(
                        current_section_todos, self.todo_manager
                    )
                    if not sync_success:
                        print("[WARNING] Position 동기화 실패, 계속 진행합니다.")

                # MANUAL 모드로 전환
                self.sort_manager.set_manual_mode()

                # 순서 변경
                success = self.todo_manager.reorder_todos(todo_id, new_pos)
                if success:
                    print(f"[DEBUG] TODO 순서 변경 성공: {todo_id[:8]}")
                    # UI 업데이트
                    if hasattr(self, 'sort_dropdown') and self.sort_dropdown:
                        self.sort_dropdown.update_display()
                    self._load_todos()

                    # 🆕 수동 모드 전환 및 순서 변경 후 즉시 설정 저장
                    self._save_all_ui_settings()
                    print("[DEBUG] 수동 모드 전환 후 즉시 저장 완료")
                else:
                    print(f"[ERROR] TODO 순서 변경 실패: {todo_id[:8]}")

        except Exception as e:
            print(f"[ERROR] _reorder_todo 실패: {e}")
            messagebox.showerror("오류", f"TODO 순서 변경에 실패했습니다: {e}")

    def _clear_completed(self):
        """완료된 항목들 정리"""
        try:
            completed_count = len(self.completed_widgets)

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

        except Exception as e:
            messagebox.showerror("오류", f"완료된 항목 정리에 실패했습니다: {e}")

    def _toggle_always_on_top(self):
        """항상 위 토글"""
        self.always_on_top = not self.always_on_top
        self.root.wm_attributes('-topmost', self.always_on_top)

        # 버튼 스타일 변경
        if self.always_on_top:
            self.top_btn.configure(bg=DARK_COLORS['accent'], fg='white')
        else:
            self.top_btn.configure(bg=DARK_COLORS['button_bg'], fg=DARK_COLORS['text'])

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
            colors = DARK_COLORS
            about_window.configure(bg=colors['bg'])

            # 중앙 정렬
            x = (about_window.winfo_screenwidth() // 2) - 200
            y = (about_window.winfo_screenheight() // 2) - 150
            about_window.geometry(f"400x300+{x}+{y}")

            # 메인 프레임
            main_frame = tk.Frame(about_window, bg=colors['bg'])
            main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

            # 제목
            title_label = tk.Label(main_frame,
                                  text="📝 TODO Panel",
                                  font=('Segoe UI', 16, 'bold'),
                                  bg=colors['bg'],
                                  fg=colors['text'])
            title_label.pack(pady=(0, 10))

            # 버전 정보
            version_label = tk.Label(main_frame,
                                    text="Windows 데스크탑 TODO 관리 도구",
                                    font=('Segoe UI', 10),
                                    bg=colors['bg'],
                                    fg=colors['text_secondary'])
            version_label.pack(pady=(0, 20))

            # 개발자 정보
            dev_frame = tk.Frame(main_frame, bg=colors['bg'])
            dev_frame.pack(fill=tk.X, pady=(0, 20))

            dev_label = tk.Label(dev_frame,
                                text="개발자: kochim.com 팀",
                                font=('Segoe UI', 10),
                                bg=colors['bg'],
                                fg=colors['text'])
            dev_label.pack()

            # kochim.com 버튼
            website_style = get_button_style('primary')
            website_btn = tk.Button(main_frame,
                                   text="🌐 kochim.com 방문하기",
                                   command=self._open_kochim_website,
                                   **website_style)
            website_btn.pack(pady=15)

            # 닫기 버튼
            close_style = get_button_style('secondary')
            close_btn = tk.Button(main_frame,
                                 text="닫기",
                                 command=about_window.destroy,
                                 **close_style)
            close_btn.pack()

        except Exception as e:
            messagebox.showerror("오류", f"정보 창을 열 수 없습니다: {e}")

    def _open_kochim_website(self):
        """코침 웹사이트 열기"""
        try:
            webbrowser.open("https://kochim.com")
            if hasattr(self, 'status_label'):
                original_text = self.status_label.cget('text')
                self.status_label.configure(text="kochim.com이 브라우저에서 열렸습니다")
                self.root.after(3000, lambda: self.status_label.configure(text=original_text))
        except Exception as e:
            messagebox.showerror("웹사이트 열기 오류",
                               f"브라우저에서 kochim.com을 열 수 없습니다.\n\n오류: {e}")

    def _style_paned_window_sash(self):
        """PanedWindow 분할바 스타일링 (Magic UI 다크 테마)"""
        try:
            colors = DARK_COLORS

            # 분할바 색상 설정
            self.sections_paned_window.configure(
                sashcursor='sb_v_double_arrow',  # 세로 리사이즈 커서
                bg=colors['border'],  # 분할바 기본 색상
                relief=tk.FLAT
            )

            # 분할바 호버 효과를 위한 바인딩
            self.sections_paned_window.bind('<Configure>', self._on_paned_window_configure)

        except Exception as e:
            if hasattr(self, '_debug') and self._debug:
                print(f"[DEBUG] 분할바 스타일링 실패: {e}")

    def _set_initial_pane_ratio(self):
        """초기 분할 비율 설정 (저장된 설정 또는 기본값 70%/30%)"""
        print("[DEBUG] _set_initial_pane_ratio 함수 실행 시작")
        try:
            # 창 높이 계산
            total_height = self.sections_paned_window.winfo_height()
            if total_height < 50:  # 아직 레이아웃이 완료되지 않았으면 나중에 다시 시도
                self.root.after(50, self._set_initial_pane_ratio)
                return

            # 저장된 분할 비율 불러오기 (기본값: 0.7)
            saved_ratio = self._load_pane_ratio()

            # 진행중인 할일 영역 높이 계산
            pending_height = int(total_height * saved_ratio)

            # sash 위치 설정 (첫 번째 구획의 높이)
            self.sections_paned_window.sash_place(0, pending_height, 0)

        except Exception as e:
            if hasattr(self, '_debug') and self._debug:
                print(f"[DEBUG] 초기 분할 비율 설정 실패: {e}")
            # 실패 시 나중에 다시 시도
            self.root.after(100, self._set_initial_pane_ratio)

    def _save_all_ui_settings(self):
        """모든 UI 설정을 통합 저장 (분할 비율 + 정렬 설정)"""
        try:
            import json
            from datetime import datetime

            # 공통 메서드로 설정 파일 경로 계산 (DRY 원칙)
            config_file = self._get_config_file_path()
            print(f"[DEBUG] UI 설정 파일 경로: {config_file}")

            # 기존 설정 로드
            settings = {}
            if config_file.exists():
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        settings = json.load(f)
                except:
                    settings = {}

            # 1. 분할 비율 저장
            total_height = self.sections_paned_window.winfo_height()
            if total_height >= 50:  # 유효한 크기인 경우에만 저장
                sash_coord = self.sections_paned_window.sash_coord(0)
                pending_height = sash_coord[1] if sash_coord else total_height * 0.7
                ratio = max(0.1, min(0.9, pending_height / total_height))
                settings['paned_window_ratio'] = ratio
                print(f"[DEBUG] 분할 비율 저장: {ratio:.2f}")

            # 2. 정렬 설정 저장
            if hasattr(self, 'sort_manager') and self.sort_manager:
                sort_info_before = self.sort_manager.get_current_sort_info()
                success = self.sort_manager.save_settings(settings)
                if success:
                    sort_settings = settings.get('sort_settings', {})
                    print(f"[DEBUG] 정렬 설정 저장 성공: {sort_settings.get('sort_criteria', 'N/A')} {sort_settings.get('sort_direction', 'N/A')}")
                else:
                    print("[WARNING] 정렬 설정 저장 실패")
            else:
                print("[WARNING] SortManager를 찾을 수 없음")

            # 3. 최종 저장 시간 업데이트
            settings['last_updated'] = datetime.now().isoformat()

            # 4. 설정 파일에 저장
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)

            # 5. 저장 검증
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    saved_settings = json.load(f)
                sort_verified = 'sort_settings' in saved_settings
                print(f"[DEBUG] 설정 저장 검증: 파일크기={config_file.stat().st_size}B, 정렬설정={'포함' if sort_verified else '누락'}")
            except Exception as verify_error:
                print(f"[WARNING] 저장 검증 실패: {verify_error}")

            print(f"[DEBUG] 모든 UI 설정 저장 완료: {config_file}")

        except Exception as e:
            print(f"[ERROR] UI 설정 저장 실패: {e}")
            # 재시도 로직
            import traceback
            print(f"[ERROR] 스택 트레이스: {traceback.format_exc()}")

    def _save_pane_ratio(self):
        """현재 분할 비율을 사용자 설정에 저장"""
        try:
            # 현재 분할 비율 계산
            total_height = self.sections_paned_window.winfo_height()
            if total_height < 50:
                return  # 너무 작으면 저장하지 않음

            # 첫 번째 패널(진행중 할일)의 높이 가져오기
            sash_coord = self.sections_paned_window.sash_coord(0)
            pending_height = sash_coord[1] if sash_coord else total_height * 0.7

            # 비율 계산 (0.1 ~ 0.9 범위로 제한)
            ratio = max(0.1, min(0.9, pending_height / total_height))

            # 설정 파일에 저장
            import json
            from pathlib import Path
            import os

            # 설정 디렉토리 생성
            config_dir = Path(os.path.expanduser("~")) / "AppData" / "Local" / "TodoPanel"
            config_dir.mkdir(parents=True, exist_ok=True)

            config_file = config_dir / "ui_settings.json"

            # 기존 설정 로드
            settings = {}
            if config_file.exists():
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        settings = json.load(f)
                except:
                    settings = {}

            # 분할 비율 업데이트
            settings['paned_window_ratio'] = ratio
            settings['last_updated'] = datetime.now().isoformat()

            # 설정 저장
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)

            if hasattr(self, '_debug') and self._debug:
                print(f"[DEBUG] 분할 비율 저장됨: {ratio:.2f}")

        except Exception as e:
            if hasattr(self, '_debug') and self._debug:
                print(f"[DEBUG] 분할 비율 저장 실패: {e}")

    def _load_sort_settings(self):
        """저장된 정렬 설정을 불러와서 SortManager에 적용"""
        try:
            import json
            import sys
            from pathlib import Path
            import os

            # 설정 파일 경로 설정 (실행 파일과 같은 위치의 TodoPanel_Data 사용)
            try:
                # 실행 파일의 경로 가져오기 (PyInstaller 대응)
                if getattr(sys, 'frozen', False):
                    # PyInstaller로 빌드된 경우
                    app_dir = Path(sys.executable).parent
                else:
                    # 개발 환경에서 실행하는 경우
                    app_dir = Path(__file__).parent.parent.parent

                config_file = app_dir / "TodoPanel_Data" / "ui_settings.json"
                print(f"[DEBUG] UI 설정 파일 로드 경로: {config_file}")

            except Exception as path_error:
                # 폴백: 기존 방식 사용
                print(f"[WARNING] 설정 경로 설정 실패, 기존 방식 사용: {path_error}")
                config_file = Path(os.path.expanduser("~")) / "AppData" / "Local" / "TodoPanel" / "ui_settings.json"

            if not config_file.exists():
                print("[DEBUG] 설정 파일 없음, 기본 정렬 설정 사용")
                return

            with open(config_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)

            # SortManager에 설정 로드
            if hasattr(self, 'sort_manager') and self.sort_manager:
                success = self.sort_manager.load_settings(settings)
                if success:
                    print("[DEBUG] 정렬 설정 로드 성공")

                    # 정렬 드롭다운 UI 업데이트
                    if hasattr(self, 'sort_dropdown') and self.sort_dropdown:
                        self.sort_dropdown.update_display()
                        print("[DEBUG] 정렬 드롭다운 UI 업데이트 완료")
                else:
                    print("[WARNING] 정렬 설정 로드 실패, 기본값 사용")

        except Exception as e:
            print(f"[ERROR] 정렬 설정 로드 중 오류: {e}")
            # 오류 시 기본값 사용 (SortManager는 이미 기본값으로 초기화됨)

    def _get_config_file_path(self):
        """설정 파일 경로를 공통으로 계산 (DRY 원칙 적용)"""
        try:
            import sys
            from pathlib import Path
            import os

            # 실행 파일의 경로 가져오기 (PyInstaller 대응)
            if getattr(sys, 'frozen', False):
                # PyInstaller로 빌드된 경우
                app_dir = Path(sys.executable).parent
            else:
                # 개발 환경에서 실행하는 경우
                app_dir = Path(__file__).parent.parent.parent

            config_dir = app_dir / "TodoPanel_Data"
            config_dir.mkdir(parents=True, exist_ok=True)

            return config_dir / "ui_settings.json"

        except Exception as path_error:
            # 폴백: 기존 방식 사용
            print(f"[WARNING] 설정 경로 설정 실패, 기존 방식 사용: {path_error}")
            config_dir = Path(os.path.expanduser("~")) / "AppData" / "Local" / "TodoPanel"
            config_dir.mkdir(parents=True, exist_ok=True)
            return config_dir / "ui_settings.json"

    def _load_pane_ratio(self):
        """저장된 분할 비율을 불러오기 (기본값: 0.7)"""
        try:
            import json

            config_file = self._get_config_file_path()
            print(f"[DEBUG] 설정 파일 경로: {config_file}")

            if not config_file.exists():
                print(f"[DEBUG] 설정 파일 없음, 기본값 0.8 사용")
                return 0.8  # 기본값

            with open(config_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)

            print(f"[DEBUG] 로드된 설정: {settings}")
            ratio = settings.get('paned_window_ratio', 0.8)
            print(f"[DEBUG] 원본 비율값: {ratio}")

            # 유효한 범위인지 검증 (0.1 ~ 0.9)
            ratio = max(0.1, min(0.9, ratio))
            print(f"[DEBUG] 검증된 비율값: {ratio}")

            return ratio

        except Exception as e:
            print(f"[DEBUG] 분할 비율 로드 실패, 기본값 사용: {e}")
            return 0.8  # 기본값

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
            # 1. 모든 UI 설정 저장 (분할 비율 + 정렬 설정)
            print("[DEBUG] 애플리케이션 종료: UI 설정 저장 중...")
            self._save_all_ui_settings()

            # 2. TODO 데이터 저장
            # AsyncTodoManager의 경우 shutdown 메소드 호출
            if hasattr(self.todo_manager, 'shutdown'):
                print("[DEBUG] AsyncTodoManager shutdown 호출")
                self.todo_manager.shutdown()
            # 기본 TodoManager의 경우 save_data 호출
            elif hasattr(self.todo_manager, 'save_data'):
                print("[DEBUG] TodoManager save_data 호출")
                self.todo_manager.save_data()

            print("[DEBUG] 애플리케이션 정상 종료")

        except Exception as e:
            print(f"[ERROR] 종료 중 오류: {e}")
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

    # 올바른 PanedWindow 이벤트 처리
    def _on_paned_window_configure(self, event):
        """PanedWindow 구조 변경 시 - 디바운싱으로 설정 저장"""
        # 기존 타이머가 있으면 취소
        if hasattr(self, '_save_timer'):
            self.root.after_cancel(self._save_timer)

        # 1초 후 설정 저장 (디바운싱)
        self._save_timer = self.root.after(1000, self._save_ui_settings_debounced)

    def _save_ui_settings_debounced(self):
        """디바운싱된 UI 설정 저장"""
        try:
            self._save_all_ui_settings()
            print("[DEBUG] 분할바 조절 후 설정 저장 완료")
        except Exception as e:
            print(f"[ERROR] 분할바 설정 저장 실패: {e}")