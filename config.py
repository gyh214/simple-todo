# -*- coding: utf-8 -*-
"""
Simple ToDo 애플리케이션 설정

모든 경로는 Windows 절대 경로로 설정
"""
import os
import sys
from pathlib import Path

# 프로젝트 루트 디렉토리 (절대 경로)
# PyInstaller로 빌드된 경우 exe 파일과 같은 디렉토리 사용
if getattr(sys, 'frozen', False):
    # PyInstaller로 빌드된 실행 파일인 경우
    PROJECT_ROOT = Path(sys.executable).parent.absolute()
else:
    # 일반 Python 스크립트로 실행된 경우
    PROJECT_ROOT = Path(__file__).parent.absolute()

# 데이터 디렉토리 (절대 경로)
DATA_DIR = PROJECT_ROOT / "TodoPanel_Data"
BACKUP_DIR = DATA_DIR / "backups"

# 데이터 파일 경로
DATA_FILE = DATA_DIR / "data.json"

# 디렉토리 생성 (존재하지 않을 경우)
DATA_DIR.mkdir(exist_ok=True)
BACKUP_DIR.mkdir(exist_ok=True)

# 애플리케이션 기본 설정
APP_NAME = "Simple ToDo"
APP_VERSION = "2.6.2"

# GitHub Repository 정보 (자동 업데이트용)
GITHUB_REPO_OWNER = "gyh214"
GITHUB_REPO_NAME = "simple-todo"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}"

# 업데이트 설정
UPDATE_CHECK_INTERVAL_HOURS = 1  # 1시간마다 업데이트 확인

# 윈도우 설정
WINDOW_WIDTH = 420
WINDOW_HEIGHT = 600
MIN_WINDOW_WIDTH = 420  # 텍스트 최소 너비(220px) + 좌우 여백(200px) 보장
MIN_WINDOW_HEIGHT = 400

# 데이터 기본 설정
DEFAULT_SETTINGS = {
    "sortOrder": "dueDate_asc",  # "dueDate_asc" | "dueDate_desc"
    "splitRatio": [9, 1],        # [진행중 비율, 완료 비율] - 진행중 섹션 최대화
    "alwaysOnTop": False
}

# 백업 설정
MAX_BACKUP_COUNT = None  # 무제한 백업 보관 (삭제 안 함)
BACKUP_DISPLAY_DAYS = 5  # 기본 표시 일수 (최근 5일)

# 색상 테마 (Dark Mode)
COLORS = {
    'body_bg': '#0D0D0D',
    'primary_bg': '#1A1A1A',
    'secondary_bg': '#2A2A2A',
    'card': '#2D2D2D',  # 카드 배경 - 디자인 명세
    'card_hover': '#353535',  # 카드 호버
    'text_primary': 'rgba(255, 255, 255, 0.92)',
    'text_secondary': '#B0B0B0',
    'text_disabled': '#6B6B6B',
    'accent': '#CC785C',
    'accent_hover': '#E08B6F',
    'border': 'rgba(64, 64, 64, 0.3)',
    'border_strong': 'rgba(64, 64, 64, 0.5)'  # 강한 테두리
}

# 날짜 표시 색상 (배경 + 글자 색상 조합)
# 위험도에 따른 명확한 시각적 계층 (alpha 0.1 ~ 1.0)
DUE_DATE_COLORS = {
    'overdue_severe': {
        'bg': 'rgba(204, 120, 92, 1.0)',     # 완전 불투명 (가장 강력한 경고)
        'color': '#FFFFFF'                    # 순백색 (최대 대비)
    },
    'overdue_moderate': {
        'bg': 'rgba(204, 120, 92, 0.85)',    # 매우 진함 (강한 경고)
        'color': '#FFF5F0'                    # 밝은 흰색
    },
    'overdue_mild': {
        'bg': 'rgba(204, 120, 92, 0.65)',    # 중간 (주의)
        'color': '#FFE4D6'                    # 밝은 살구색
    },
    'today': {
        'bg': 'rgba(204, 120, 92, 0.75)',    # 진함 (긴급)
        'color': '#FFFFFF'                    # 흰색 (명확한 대비)
    },
    'upcoming': {
        'bg': 'rgba(204, 120, 92, 0.35)',    # 연함 (1-10일 남음)
        'color': '#D99880'                    # 밝은 주황
    },
    'normal': {
        'bg': 'rgba(64, 64, 64, 0.10)',      # 매우 연함 (11일+ 남음)
        'color': '#B0B0B0'                    # 회색
    }
}

# 섹션 UI 설정
SECTION_UI = {
    'in_progress_min_height': 100,  # 진행중 섹션 최소 높이
    'completed_min_height': 40,     # 완료 섹션 최소 높이 (헤더만 보이도록)
}

# 단일 인스턴스 설정
SINGLE_INSTANCE_PORT = 65432

# 정규식 패턴
URL_PATTERN = r'(https?://[^\s]+)|(www\.[^\s]+)'
PATH_PATTERN = r'([A-Za-z]:\\[\\\w\s\-\.]+)|(\\\\[\w\-\.]+\\[\\\w\s\-\.]+)'

# 반복 관련 아이콘/색상
RECURRENCE_ICON = "🔁"  # 반복 아이콘
RECURRENCE_ICON_COLOR = COLORS['accent']  # 반복 아이콘 색상

# ============================================================================
# UI 레이아웃 및 스타일 설정
# ============================================================================

# 레이아웃 여백 설정 (ContentsMargins)
LAYOUT_MARGINS = {
    'main_window_content': (10, 10, 10, 10),
    'todo_item': (10, 8, 10, 8),
    'section_header': (4, 0, 4, 6),
    'section_items': (0, 0, 4, 0),
    'header': (16, 10, 16, 10),
    'footer': (16, 6, 16, 6),
    'edit_dialog': (20, 20, 20, 20),
    'backup_dialog': (20, 20, 20, 20),
    'backup_dialog_tab': (15, 15, 15, 15),
}

# 레이아웃 간격 설정 (Spacing)
LAYOUT_SPACING = {
    'main_window': 0,
    'todo_item_main': 10,
    'todo_item_content': 4,
    'section_title': 6,
    'section_items': 4,
    'header_top': 8,
    'header_main': 0,
    'edit_dialog_main': 15,
    'edit_dialog_buttons': 10,
    'footer_main': 0,
    'backup_dialog_tab': 12,
    'backup_dialog_buttons': 10,
}

# 위젯 고정 크기 설정
WIDGET_SIZES = {
    'drag_handle_width': 14,
    'checkbox_size': (18, 18),
    'delete_btn_size': (24, 24),
    'splitter_handle_width': 12,
    'footer_min_height': 28,
    'edit_dialog_size': (450, 800),  # 스크롤 가능하도록 800으로 설정
    'content_edit_height_min': 120,
    'content_edit_height_max': 150,
    'backup_dialog_size': (520, 680),
    'manage_btn_size': (60, 24),
    'todo_text_line_height': 22,  # RichTextWidget 1줄 고정 높이 (base font 13px * 1.4 line-height + padding)
    'expand_btn_size': 16,  # 펼치기/접기 버튼 크기
    'subtask_indent': 24,  # 하위 할일 들여쓰기
}

# 레이아웃 동적 계산 설정 (윈도우 기본 너비 420px 기준)
LAYOUT_SIZES = {
    'window_default_width': 420,
    'todo_text_base_max_width': 220,    # TODO 텍스트 최소 너비 (반응형: 윈도우 확장 시 자동 확장)
    'subtask_text_max_width': 196,      # SubTask 텍스트 최소 너비 (220 - 24 들여쓰기, 반응형)
    'left_margin_total': 52,            # 좌측 여백 합계 (드래그 14 + 체크박스 18 + 여백 20)
    'right_margin_total': 184,          # 우측 여백 합계 (펼치기 16 + 반복 20 + 납기 100 + 삭제 24 + 여백 24)
}

# 폰트 크기 설정
FONT_SIZES = {
    'xs': 9,     # section count
    'sm': 11,    # date badge, footer
    'md': 12,    # section title, dialog labels
    'base': 13,  # todo text, dialog content
    'lg': 14,    # buttons, drag handle, input
    'xl': 16,    # splitter dots
    'xxl': 18,   # dialog title
    'xxxl': 20,  # app title
    'dialog_tab': 14,  # dialog tab text
}

# UI 메트릭 (padding, border-radius, border-width)
UI_METRICS = {
    'border_radius': {
        'sm': 4,   # date badge, drag handle hover
        'md': 6,   # section count badge
        'lg': 8,   # buttons, cards, inputs
        'xl': 12,  # dialog
        'xxl': 16, # content widget
    },
    'border_width': {
        'thin': 1,    # default borders
        'medium': 2,  # checkbox
        'thick': 3,   # hover states
    },
    'padding': {
        'xs': (1, 5),    # section count badge
        'sm': (2, 6),    # date badge, delete button
        'md': (10, 14),  # buttons, combo box
        'lg': (10, 24),  # dialog buttons
    },
}

# Splitter 전용 설정
SPLITTER_CONFIG = {
    'margin': 6,                  # 위아래 여백
    'line_height_normal': 2,      # 기본 라인 높이
    'line_height_hover': 3,       # 호버 시 라인 높이
    'dots_font_size': 16,         # 점 3개('⋯') 폰트 크기
}

# 백업 다이얼로그 전용 설정
BACKUP_DIALOG_LAYOUT = {
    'file_list_ratio': 40,        # 백업 파일 목록 너비 비율 (%)
    'preview_ratio': 60,          # TODO 미리보기 너비 비율 (%)
    'checkbox_margins': (5, 5, 5, 5),  # 체크박스 영역 여백
    'checkbox_spacing': 8,        # 체크박스 간격
}

# 투명도 값 설정
OPACITY_VALUES = {
    'completed_item': 0.6,  # 완료된 TODO 아이템
    'hidden': 0.0,          # 숨김 상태 (delete button)
    'visible': 1.0,         # 표시 상태
}

# ============================================================================
# 리소스 파일 경로 설정
# ============================================================================

# 아이콘 파일 경로 (상대 경로)
ICON_FILE = "simple-todo.ico"


def get_resource_path(relative_path):
    """
    리소스 파일 경로를 반환합니다 (EXE 단독 배포 지원).

    개발 환경과 PyInstaller로 빌드된 환경 모두에서 올바른 경로를 반환합니다.
    빌드 환경에서는 _MEIPASS에 추출된 리소스 파일을 사용합니다.

    Args:
        relative_path: 프로젝트 루트 기준 상대 경로 (Path 또는 str)

    Returns:
        Path: 리소스 파일의 절대 경로
    """
    # 파일명 추출
    if isinstance(relative_path, Path):
        filename = relative_path.name
    else:
        filename = str(relative_path)

    # 빌드 환경 (PyInstaller)
    if getattr(sys, 'frozen', False):
        # _MEIPASS에서 리소스 파일 찾기
        base_path = Path(getattr(sys, '_MEIPASS', Path(sys.executable).parent))
        resource_path = base_path / filename
        if resource_path.exists():
            return resource_path

    # 개발 환경
    dev_path = PROJECT_ROOT / filename
    return dev_path
