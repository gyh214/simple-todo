"""
날짜 선택 다이얼로그 모듈

TODO 아이템의 납기일 선택을 위한 팝업 다이얼로그 클래스를 포함합니다.
"""

import tkinter as tk
from datetime import datetime

from ..widgets import DARK_COLORS, StandardTodoDisplay, get_button_style


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

        # DRY 원칙: 색상을 인스턴스 변수로 정의
        self.colors = DARK_COLORS

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("할일 수정" if edit_mode else "할일 추가")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # 다크 테마 색상 적용
        self.dialog.configure(bg=self.colors["bg"])

        # 모든 UI 섹션 구성
        self._setup_ui_sections()
        self._setup_calendar()

        # UI 구성 완료 후 동적 크기 조정 및 위치 설정
        self._apply_dynamic_sizing()

        # ESC 키로 취소
        self.dialog.bind("<Escape>", lambda e: self._cancel())
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
        self.main_frame = tk.Frame(self.dialog, bg=self.colors["bg"])
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    def _setup_header(self):
        """제목 섹션 구성"""
        title_label = tk.Label(
            self.main_frame,
            text="📝 할일 추가",
            font=("Segoe UI", 14, "bold"),
            bg=self.colors["bg"],
            fg=self.colors["text"],
        )
        title_label.pack(pady=(0, 10))

    def _setup_todo_display(self):
        """TODO 텍스트 표시 섹션 구성 - StandardTodoDisplay 사용"""
        if self.todo_text:
            # StandardTodoDisplay가 사용 가능한지 확인
            if StandardTodoDisplay is not None:
                # StandardTodoDisplay로 일관된 TODO 렌더링
                # 임시 TODO 데이터 생성 (표시용)
                temp_todo = {
                    "id": "preview",
                    "content": self.todo_text,
                    "completed": False,
                    "created_at": datetime.now().isoformat(),
                    "due_date": None,  # 아직 설정되지 않음
                }

                # StandardTodoDisplay 컴포넌트 사용
                display_frame = StandardTodoDisplay(
                    self.main_frame, todo_data=temp_todo, read_only=True  # 읽기전용 모드
                )
                display_frame.pack(fill=tk.X, pady=(0, 15))
            else:
                # StandardTodoDisplay가 없는 경우 기본 라벨로 대체
                preview_label = tk.Label(
                    self.main_frame,
                    text=f"📝 {self.todo_text}",
                    font=("Segoe UI", 10),
                    bg=self.colors["bg_secondary"],
                    fg=self.colors["text"],
                    anchor="w",
                    justify="left",
                    relief="solid",
                    borderwidth=1,
                    padx=8,
                    pady=6,
                )
                preview_label.pack(fill=tk.X, pady=(0, 15))

    def _setup_text_input(self):
        """편집 모드에서 할일 텍스트 입력 섹션 구성"""
        # 할일 텍스트 입력 섹션 라벨
        text_label = tk.Label(
            self.main_frame,
            text="📝 할일 내용",
            font=("Segoe UI", 12, "bold"),
            bg=self.colors["bg"],
            fg=self.colors["text"],
        )
        text_label.pack(pady=(0, 10))

        # 텍스트 입력 필드
        self.text_entry = tk.Entry(
            self.main_frame,
            font=("Segoe UI", 10),
            bg=self.colors["entry_bg"],
            fg=self.colors["text"],
            borderwidth=1,
            relief="solid",
            insertbackground=self.colors["text"],
        )
        self.text_entry.pack(fill=tk.X, pady=(0, 15), padx=10)

        # 기존 텍스트 설정
        if self.todo_text:
            self.text_entry.insert(0, self.todo_text)
            self.text_entry.selection_range(0, tk.END)

        # 포커스 설정
        self.text_entry.focus()

        # 이벤트 바인딩
        self.text_entry.bind("<Return>", self._on_text_change)
        self.text_entry.bind("<KeyRelease>", self._on_text_change)

    def _on_text_change(self, event=None):
        """텍스트 변경 시 updated_text 업데이트"""
        if hasattr(self, "text_entry"):
            self.updated_text = self.text_entry.get().strip()

    def _setup_calendar_section(self):
        """캘린더 섹션 구성"""
        # 납기일 선택 섹션 라벨
        date_label = tk.Label(
            self.main_frame,
            text="📅 납기일 선택",
            font=("Segoe UI", 12, "bold"),
            bg=self.colors["bg"],
            fg=self.colors["text"],
        )
        date_label.pack(pady=(0, 10))

        # 캘린더 프레임
        self.calendar_frame = tk.Frame(self.main_frame, bg=self.colors["bg"])
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
        # 버튼 프레임
        button_frame = tk.Frame(self.main_frame, bg=self.colors["bg"])
        button_frame.pack(fill=tk.X, pady=(10, 0))

        # 버튼들 (편집 모드에 따라 텍스트 변경)
        no_date_style = get_button_style("secondary")
        no_date_text = "납기일 없이 수정" if self.edit_mode else "납기일 없이 추가"
        self.no_date_btn = tk.Button(
            button_frame, text=no_date_text, command=self._add_without_date, **no_date_style
        )
        self.no_date_btn.pack(side=tk.LEFT, padx=(0, 10))

        # 납기일과 함께 추가/수정 버튼 (Primary 스타일)
        with_date_style = get_button_style("primary")
        with_date_text = "납기일과 함께 수정" if self.edit_mode else "납기일과 함께 추가"
        self.with_date_btn = tk.Button(
            button_frame,
            text=with_date_text,
            command=self._add_with_date,
            state="disabled",
            **with_date_style,
        )
        self.with_date_btn.pack(side=tk.RIGHT)

        # 편집 모드에서 납기일 제거 버튼 추가
        if self.edit_mode:
            remove_date_style = get_button_style("danger")
            self.remove_date_btn = tk.Button(
                button_frame, text="납기일 제거", command=self._remove_date, **remove_date_style
            )
            self.remove_date_btn.pack(side=tk.RIGHT, padx=(10, 0))

    def _setup_calendar(self):
        """간단한 캘린더 UI 구성"""
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
        month_year_frame = tk.Frame(self.calendar_frame, bg=self.colors["bg"])
        month_year_frame.pack(pady=(0, 10))

        # 이전 달 버튼
        prev_btn = tk.Button(
            month_year_frame,
            text="<",
            font=("Segoe UI", 10),
            bg=self.colors["button_bg"],
            fg=self.colors["text"],
            command=self._prev_month,
            width=3,
        )
        prev_btn.pack(side=tk.LEFT, padx=(0, 10))

        # 월/년 표시
        self.month_year_label = tk.Label(
            month_year_frame,
            text=f"{self.current_year}년 {self.current_month}월",
            font=("Segoe UI", 11, "bold"),
            bg=self.colors["bg"],
            fg=self.colors["text"],
        )
        self.month_year_label.pack(side=tk.LEFT, padx=10)

        # 다음 달 버튼
        next_btn = tk.Button(
            month_year_frame,
            text=">",
            font=("Segoe UI", 10),
            bg=self.colors["button_bg"],
            fg=self.colors["text"],
            command=self._next_month,
            width=3,
        )
        next_btn.pack(side=tk.LEFT, padx=(10, 0))

        # 요일 헤더
        days_frame = tk.Frame(self.calendar_frame, bg=self.colors["bg"])
        days_frame.pack()

        day_names = ["일", "월", "화", "수", "목", "금", "토"]
        for day_name in day_names:
            day_label = tk.Label(
                days_frame,
                text=day_name,
                font=("Segoe UI", 9, "bold"),
                bg=self.colors["bg"],
                fg=self.colors["text_secondary"],
                width=4,
                height=1,
            )
            day_label.grid(row=0, column=day_names.index(day_name), padx=1, pady=1)

        # 날짜 버튼들을 위한 프레임
        self.dates_frame = tk.Frame(self.calendar_frame, bg=self.colors["bg"])
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
        # 월/년 라벨 업데이트
        self.month_year_label.configure(text=f"{self.current_year}년 {self.current_month}월")

        # 기존 날짜 버튼들 제거
        for widget in self.dates_frame.winfo_children():
            widget.destroy()

        # 해당 월의 첫째 날과 마지막 날
        import calendar

        first_day = datetime(self.current_year, self.current_month, 1)
        last_day = datetime(
            self.current_year,
            self.current_month,
            calendar.monthrange(self.current_year, self.current_month)[1],
        )

        # 첫째 날의 요일 (0=월요일, 6=일요일) -> (0=일요일, 6=토요일)로 변환
        first_weekday = (first_day.weekday() + 1) % 7

        # 오늘 날짜
        today = datetime.now().date()

        # 기존 선택된 날짜 파싱 (편집 모드용)
        selected_day = None
        if self.selected_date:
            try:
                selected_parsed = datetime.fromisoformat(self.selected_date).date()
                if (
                    selected_parsed.year == self.current_year
                    and selected_parsed.month == self.current_month
                ):
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
            is_selected = day == selected_day  # 기존 선택된 날짜

            # 버튼 색상 설정
            if is_past:
                bg_color = self.colors["bg_secondary"]
                fg_color = self.colors["text_secondary"]
                state = "normal"  # 과거 날짜도 활성화
            elif is_selected:  # 기존 선택된 날짜
                bg_color = self.colors["accent"]
                fg_color = "white"
                state = "normal"
            elif is_today:
                bg_color = self.colors["warning"]
                fg_color = self.colors["bg"]
                state = "normal"
            else:
                bg_color = self.colors["button_bg"]
                fg_color = self.colors["text"]
                state = "normal"

            date_btn = tk.Button(
                self.dates_frame,
                text=str(day),
                font=("Segoe UI", 9),
                bg=bg_color,
                fg=fg_color,
                width=4,
                height=2,
                state=state,
                command=lambda d=day: self._select_date(d),
            )

            # 모든 날짜에 호버 효과 적용
            date_btn.bind("<Enter>", lambda e, btn=date_btn: btn.configure(bg=self.colors["bg_hover"]))
            date_btn.bind(
                "<Leave>", lambda e, btn=date_btn, orig_bg=bg_color: btn.configure(bg=orig_bg)
            )

            date_btn.grid(row=row, column=col, padx=1, pady=1)

            col += 1
            if col > 6:
                col = 0
                row += 1

        # 편집 모드에서 기존 날짜가 선택되어 있으면 버튼 활성화
        if self.edit_mode and selected_day:
            self.with_date_btn.configure(state="normal")
            # Primary 스타일로 활성화
            primary_style = get_button_style("primary")
            for key, value in primary_style.items():
                if key != "state":
                    self.with_date_btn.configure({key: value})

            # 선택된 날짜 표시 업데이트
            selected_text = f"선택: {self.current_year}년 {self.current_month}월 {selected_day}일"
            action_text = "납기일과 함께 수정" if self.edit_mode else "납기일과 함께 추가"
            self.with_date_btn.configure(text=f"{action_text}\n({selected_text})")

    def _select_date(self, day):
        """날짜 선택"""
        self.selected_date = f"{self.current_year:04d}-{self.current_month:02d}-{day:02d}"

        # "납기일과 함께 추가/수정" 버튼 활성화 및 스타일 업데이트
        self.with_date_btn.configure(state="normal")
        # Primary 스타일로 활성화
        primary_style = get_button_style("primary")
        for key, value in primary_style.items():
            if key != "state":  # state는 별도 관리
                self.with_date_btn.configure({key: value})

        # 선택된 날짜 표시 업데이트
        selected_text = f"선택: {self.current_year}년 {self.current_month}월 {day}일"
        action_text = "납기일과 함께 수정" if self.edit_mode else "납기일과 함께 추가"
        self.with_date_btn.configure(text=f"{action_text}\n({selected_text})")

    def _add_without_date(self):
        """납기일 없이 추가/수정"""
        # 편집 모드에서 텍스트 검증
        if self.edit_mode and hasattr(self, "text_entry"):
            text = self.text_entry.get().strip()
            if not text:
                import tkinter.messagebox as messagebox

                messagebox.showerror("입력 오류", "할일 내용을 입력해주세요.")
                return
            self.updated_text = text

        self.result = "without_date"
        self.selected_date = None
        self.dialog.destroy()

    def _add_with_date(self):
        """납기일과 함께 추가/수정"""
        # 편집 모드에서 텍스트 검증
        if self.edit_mode and hasattr(self, "text_entry"):
            text = self.text_entry.get().strip()
            if not text:
                import tkinter.messagebox as messagebox

                messagebox.showerror("입력 오류", "할일 내용을 입력해주세요.")
                return
            self.updated_text = text

        if self.selected_date:
            self.result = "with_date"
            self.dialog.destroy()

    def _remove_date(self):
        """납기일 제거 (편집 모드에서만 사용)"""
        if self.edit_mode and hasattr(self, "text_entry"):
            text = self.text_entry.get().strip()
            if not text:
                import tkinter.messagebox as messagebox

                messagebox.showerror("입력 오류", "할일 내용을 입력해주세요.")
                return
            self.updated_text = text

        self.result = "without_date"
        self.selected_date = None
        self.dialog.destroy()

    def _cancel(self):
        """취소"""
        self.result = "cancelled"
        self.selected_date = None
        self.dialog.destroy()

    def show(self):
        """다이얼로그 표시 및 결과 반환"""
        self.dialog.wait_window()
        if self.edit_mode:
            return self.result, self.selected_date, self.updated_text
        else:
            return self.result, self.selected_date
