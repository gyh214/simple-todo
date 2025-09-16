"""
TODO Panel 메인 애플리케이션 모듈 (섹션 분할 및 새로운 기능 포함)
"""

import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from .widgets import DARK_COLORS, TodoItemWidget
from .sort_manager import SortManager
from .date_utils import DateUtils
from tooltip import ToolTip

# 기본 TodoManager 또는 AsyncTodoManager 사용
try:
    from async_todo_manager import AsyncTodoManager as TodoManager, AsyncTodoManagerError as TodoManagerError
except ImportError:
    # AsyncTodoManager가 없으면 기본 TodoManager 사용
    from todo_manager import TodoManager, TodoManagerError


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

    def __init__(self, parent, todo_text="", initial_date=None):
        self.parent = parent
        self.todo_text = todo_text
        self.selected_date = None
        self.result = None  # 'with_date', 'without_date', 'cancelled'

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("할일 추가")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # 색상 테마
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
        """TODO 텍스트 표시 섹션 구성"""
        if self.todo_text:
            colors = DARK_COLORS
            text_frame = tk.Frame(self.main_frame, bg=colors['bg_secondary'],
                                 relief='solid', borderwidth=1)
            text_frame.pack(fill=tk.X, pady=(0, 15))

            # 현재 다이얼로그 크기에 따른 동적 wraplength 계산
            dialog_width = int(self.dialog.winfo_reqwidth() or 350)
            wrap_length = max(250, dialog_width - 80)  # 여백 고려

            text_label = tk.Label(text_frame,
                                 text=f'"{self.todo_text}"',
                                 font=('Segoe UI', 10),
                                 bg=colors['bg_secondary'],
                                 fg=colors['text'],
                                 wraplength=wrap_length,
                                 justify='center',
                                 padx=10, pady=8)
            text_label.pack()

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

        # 납기일 없이 추가 버튼
        self.no_date_btn = tk.Button(button_frame,
                                    text="납기일 없이 추가",
                                    font=('Segoe UI', 10),
                                    bg=colors['button_bg'],
                                    fg=colors['text'],
                                    command=self._add_without_date,
                                    padx=20, pady=8)
        self.no_date_btn.pack(side=tk.LEFT, padx=(0, 10))

        # 납기일과 함께 추가 버튼
        self.with_date_btn = tk.Button(button_frame,
                                      text="납기일과 함께 추가",
                                      font=('Segoe UI', 10, 'bold'),
                                      bg=colors['accent'],
                                      fg='white',
                                      command=self._add_with_date,
                                      state='disabled',
                                      padx=20, pady=8)
        self.with_date_btn.pack(side=tk.RIGHT)

    def _setup_calendar(self):
        """간단한 캘린더 UI 구성"""
        colors = DARK_COLORS

        # 현재 날짜
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

        row = 1
        col = first_weekday

        for day in range(1, last_day.day + 1):
            current_date = datetime(self.current_year, self.current_month, day).date()

            # 과거 날짜는 비활성화
            is_past = current_date < today
            is_today = current_date == today

            # 버튼 색상 설정
            if is_past:
                bg_color = colors['bg_secondary']
                fg_color = colors['text_secondary']
                state = 'disabled'
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

            if not is_past:
                date_btn.bind('<Enter>', lambda e, btn=date_btn: btn.configure(bg=colors['bg_hover']))
                date_btn.bind('<Leave>', lambda e, btn=date_btn, orig_bg=bg_color: btn.configure(bg=orig_bg))

            date_btn.grid(row=row, column=col, padx=1, pady=1)

            col += 1
            if col > 6:
                col = 0
                row += 1

    def _select_date(self, day):
        """날짜 선택"""
        self.selected_date = f"{self.current_year:04d}-{self.current_month:02d}-{day:02d}"

        # "납기일과 함께 추가" 버튼 활성화
        self.with_date_btn.configure(state='normal')

        # 선택된 날짜 표시 업데이트
        selected_text = f"선택: {self.current_year}년 {self.current_month}월 {day}일"
        self.with_date_btn.configure(text=f"납기일과 함께 추가\n({selected_text})")

    def _add_without_date(self):
        """납기일 없이 추가"""
        self.result = 'without_date'
        self.selected_date = None
        self.dialog.destroy()

    def _add_with_date(self):
        """납기일과 함께 추가"""
        if self.selected_date:
            self.result = 'with_date'
            self.dialog.destroy()

    def _cancel(self):
        """취소"""
        self.result = 'cancelled'
        self.selected_date = None
        self.dialog.destroy()

    def show(self):
        """다이얼로그 표시 및 결과 반환"""
        self.dialog.wait_window()
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

    def __init__(self):
        self.root = tk.Tk()

        # TodoManager 초기화
        try:
            self.todo_manager = TodoManager(debug=True, batch_save=True)
        except TypeError:
            # batch_save 파라미터가 없는 기본 TodoManager의 경우
            self.todo_manager = TodoManager(debug=True)

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

        # 정렬 버튼
        self.sort_btn = tk.Button(control_frame,
                                 text='🔄',
                                 command=self._toggle_sort,
                                 font=('Segoe UI', 9),
                                 bg=DARK_COLORS['button_bg'],
                                 fg=DARK_COLORS['text'],
                                 width=3, padx=5, pady=5)
        self.sort_btn.pack(side=tk.RIGHT, padx=(4, 0))
        self._update_sort_button()

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
        """섹션 분할된 TODO 리스트 설정"""
        # 섹션 컨테이너
        sections_container = tk.Frame(parent, bg=DARK_COLORS['bg'])
        sections_container.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        # 진행중인 할일 섹션
        self.pending_section = CollapsibleSection(
            sections_container,
            "📋 진행중인 할일 (0개)",
            initial_collapsed=False
        )
        self.pending_section.pack(fill=tk.BOTH, expand=True, pady=(0, 5))

        # 진행중 할일을 위한 스크롤 가능한 영역
        self._setup_scrollable_area(
            self.pending_section.get_content_frame(),
            'pending'
        )

        # 완료된 할일 섹션 (기본적으로 접힘)
        self.completed_section = CollapsibleSection(
            sections_container,
            "✅ 완료된 할일 (0개)",
            initial_collapsed=True
        )
        self.completed_section.pack(fill=tk.X, pady=(5, 0))

        # 완료된 할일을 위한 스크롤 가능한 영역
        self._setup_scrollable_area(
            self.completed_section.get_content_frame(),
            'completed'
        )

    def _setup_scrollable_area(self, parent, section_type):
        """스크롤 가능한 영역 설정"""
        colors = DARK_COLORS

        # 스크롤 컨테이너
        scroll_container = tk.Frame(parent, bg=colors['bg'])
        scroll_container.pack(fill=tk.BOTH, expand=True)

        # 캔버스와 스크롤바
        canvas = tk.Canvas(scroll_container,
                          highlightthickness=0,
                          bg=colors['bg'],
                          height=200 if section_type == 'pending' else 150)
        scrollbar = tk.Scrollbar(scroll_container,
                                orient=tk.VERTICAL,
                                command=canvas.yview,
                                bg=colors['bg_secondary'])

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
            canvas.configure(scrollregion=canvas.bbox("all"))

        def configure_canvas_width(event):
            canvas.itemconfig(canvas_window, width=event.width)

        def on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        scrollable_frame.bind('<Configure>', configure_scroll_region)
        canvas.bind('<Configure>', configure_canvas_width)
        canvas.bind_all('<MouseWheel>', on_mousewheel)

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
                # 수동으로 due_date 필드 추가 후 업데이트
                self.todo_manager.update_todo(todo['id'], due_date=due_date)
                todo['due_date'] = due_date
            return todo

    def _update_sort_button(self):
        """정렬 버튼 상태 업데이트"""
        sort_info = self.sort_manager.get_current_sort_info()
        self.sort_btn.configure(text=sort_info['icon'])
        ToolTip(self.sort_btn, sort_info['tooltip'])

    def _toggle_sort(self):
        """정렬 토글"""
        self.sort_manager.get_next_sort_state()
        self._update_sort_button()
        self._load_todos()  # 정렬 적용을 위해 다시 로드

    def _load_todos(self):
        """TODO 목록 로드 및 표시 (섹션별 분리)"""
        try:
            todos = self.todo_manager.read_todos()

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

        except TodoManagerError as e:
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
        """TODO 업데이트 (섹션 이동 처리)"""
        try:
            success = self.todo_manager.update_todo(todo_id, **kwargs)
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

        except TodoManagerError as e:
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

        except TodoManagerError as e:
            messagebox.showerror("오류", f"TODO 삭제 중 오류가 발생했습니다: {e}")

    def _reorder_todo(self, todo_id: str, move_steps: int):
        """TODO 순서 변경"""
        try:
            # 현재 위치 찾기 (섹션 내에서)
            widget = self.todo_widgets.get(todo_id)
            if not widget:
                return

            is_completed = widget.todo_data.get('completed', False)
            current_section_todos = [w.todo_data for w in
                                   (self.completed_widgets.values() if is_completed
                                    else self.pending_widgets.values())]

            current_pos = None
            for i, todo in enumerate(current_section_todos):
                if todo['id'] == todo_id:
                    current_pos = i
                    break

            if current_pos is None:
                return

            # 새 위치 계산
            new_pos = max(0, min(len(current_section_todos) - 1, current_pos + move_steps))

            if new_pos != current_pos:
                success = self.todo_manager.reorder_todos(todo_id, new_pos)
                if success:
                    self._load_todos()  # 전체 리스트 다시 로드

        except TodoManagerError as e:
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

        except TodoManagerError as e:
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
            website_btn = tk.Button(main_frame,
                                   text="🌐 kochim.com 방문하기",
                                   command=self._open_kochim_website,
                                   font=('Segoe UI', 10, 'bold'),
                                   bg=colors['accent'],
                                   fg='white',
                                   padx=20, pady=10)
            website_btn.pack(pady=15)

            # 닫기 버튼
            close_btn = tk.Button(main_frame,
                                 text="닫기",
                                 command=about_window.destroy,
                                 font=('Segoe UI', 9),
                                 bg=colors['button_bg'],
                                 fg=colors['text'],
                                 padx=20, pady=5)
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