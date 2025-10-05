# -*- coding: utf-8 -*-
"""
메인 윈도우 UI 컴포넌트
"""
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QCloseEvent
from typing import Optional
import logging

import config
from src.presentation.widgets.header_widget import HeaderWidget
from src.presentation.widgets.section_widget import SectionWidget
from src.presentation.widgets.footer_widget import FooterWidget
from src.presentation.widgets.custom_splitter import CustomSplitter
from src.presentation.system.window_manager import WindowManager

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """
    Simple ToDo 메인 윈도우

    Phase 5-1: 헤더 UI 구현 (타이틀, 정렬, 입력창, 추가 버튼)
    Phase 5-3: 진행중/완료 섹션 및 분할바 구현 (QSplitter 사용)
    Phase 6-3: 윈도우 관리 구현 (크기/위치/항상위 상태 저장)
    """

    def __init__(self, repository=None):
        """MainWindow 초기화

        Args:
            repository: TODO 및 설정 저장을 위한 Repository (DI)
        """
        super().__init__()

        # Repository 저장
        self.repository = repository

        # WindowManager 초기화
        self.window_manager: Optional[WindowManager] = None
        if self.repository:
            self.window_manager = WindowManager(self, self.repository)

        # TodoService 초기화 (DI Container에서 조회)
        from src.core.container import Container, ServiceNames
        self.todo_service = Container.resolve(ServiceNames.TODO_SERVICE)

        self.setup_window()
        self.setup_ui()
        self.apply_styles()

        # EventHandler 초기화 (setup_ui 이후에 생성)
        from .event_handlers.main_window_event_handler import MainWindowEventHandler
        self.event_handler = MainWindowEventHandler(
            main_window=self,
            repository=self.repository,
            todo_service=self.todo_service,
            header_widget=self.header_widget,
            in_progress_section=self.in_progress_section,
            completed_section=self.completed_section,
            footer_widget=self.footer_widget,
            splitter=self.splitter
        )

        # 시그널 연결 (EventHandler에 위임)
        self.event_handler.connect_signals()

        # SystemTrayManager 초기화
        from src.presentation.system.tray_manager import SystemTrayManager
        self.tray_manager = SystemTrayManager(self)

        # 저장된 분할 비율 복원 (레이아웃 완료 후 적용)
        if self.repository:
            # QTimer로 레이아웃이 완료된 후 비율 복원
            QTimer.singleShot(100, self._restore_split_ratio)

        # 초기 TODO 로드 (EventHandler에 위임)
        self.event_handler.load_todos()

    def setup_window(self):
        """윈도우 기본 설정"""
        self.setWindowTitle(config.APP_NAME)

        # 윈도우 아이콘 설정 (타이틀바 아이콘)
        from PyQt6.QtGui import QIcon
        icon_path = config.get_resource_path(config.ICON_FILE)
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
            logger.info(f"Window icon set: {icon_path}")
        else:
            logger.warning(f"Icon file not found: {icon_path}")

        # WindowManager를 통한 윈도우 설정
        if self.window_manager:
            self.window_manager.setup_window(
                min_width=config.MIN_WINDOW_WIDTH,
                min_height=config.MIN_WINDOW_HEIGHT,
                default_width=config.WINDOW_WIDTH,
                default_height=config.WINDOW_HEIGHT
            )
        else:
            # Repository 없이 실행 시 기본 설정
            self.setMinimumSize(config.MIN_WINDOW_WIDTH, config.MIN_WINDOW_HEIGHT)
            self.resize(config.WINDOW_WIDTH, config.WINDOW_HEIGHT)

    def setup_ui(self):
        """UI 구성"""
        # 중앙 위젯 생성
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 메인 레이아웃 (수직)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 헤더 위젯 추가
        self.header_widget = HeaderWidget()
        main_layout.addWidget(self.header_widget)

        # 컨텐츠 영역 (QSplitter 사용)
        self.content_widget = QWidget()
        self.content_widget.setObjectName("contentWidget")

        # 컨텐츠 레이아웃 (수직) - 여백 축소
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(*config.LAYOUT_MARGINS['main_window_content'])
        self.content_layout.setSpacing(config.LAYOUT_SPACING['main_window'])

        # 진행중 섹션
        self.in_progress_section = SectionWidget("진행중")

        # 완료 섹션
        self.completed_section = SectionWidget("완료")

        # CustomSplitter 생성 (수직 방향)
        self.splitter = CustomSplitter(Qt.Orientation.Vertical)
        self.splitter.setObjectName("sectionSplitter")
        self.splitter.addWidget(self.in_progress_section)
        self.splitter.addWidget(self.completed_section)

        # Splitter 설정 - handle 축소
        self.splitter.setHandleWidth(config.WIDGET_SIZES['splitter_handle_width'])
        self.splitter.setChildrenCollapsible(False)  # 섹션 완전 축소 방지

        # 컨텐츠 레이아웃에 Splitter 추가
        self.content_layout.addWidget(self.splitter, 1)

        main_layout.addWidget(self.content_widget, 1)  # stretch factor 1

        # 푸터 위젯 (Phase 5-4: TODO 카운트 실시간 표시) - 간소화
        self.footer_widget = FooterWidget()
        self.footer_widget.setMinimumHeight(config.WIDGET_SIZES['footer_min_height'])
        main_layout.addWidget(self.footer_widget)


    def _restore_split_ratio(self) -> None:
        """저장된 분할 비율을 복원합니다"""
        if not self.repository:
            return

        try:
            settings = self.repository.get_settings()
            split_ratio = settings.get("splitRatio", [9, 1])  # 기본값: 진행중 90%, 완료 10%

            if len(split_ratio) == 2:
                # Splitter의 전체 높이 가져오기
                total_height = self.splitter.height()

                if total_height > 0:
                    # 비율을 픽셀 크기로 변환
                    in_progress_height = int(total_height * split_ratio[0] / sum(split_ratio))
                    completed_height = int(total_height * split_ratio[1] / sum(split_ratio))

                    # Splitter에 적용
                    self.splitter.setSizes([in_progress_height, completed_height])

                    logger.info(f"Split ratio restored: {split_ratio}, heights=[{in_progress_height}, {completed_height}]")
                else:
                    logger.warning(f"Splitter height is 0, cannot restore split ratio yet")
        except Exception as e:
            logger.error(f"Failed to restore split ratio: {e}")


    def toggle_always_on_top(self) -> None:
        """항상 위 기능 토글

        메뉴나 단축키에서 호출 가능
        """
        if self.window_manager:
            self.window_manager.toggle_always_on_top()
        else:
            logger.warning("WindowManager not initialized, cannot toggle always on top")

    def closeEvent(self, event: QCloseEvent) -> None:
        """윈도우 닫기 이벤트 핸들러

        종료 시 윈도우 상태를 저장합니다.

        Args:
            event: 닫기 이벤트
        """
        # 윈도우 상태 저장
        if self.window_manager:
            self.window_manager.save_window_state()
            logger.info("Window state saved on close")

        # 기본 동작 수행
        event.accept()

    def apply_styles(self):
        """QSS 스타일시트 적용"""
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {config.COLORS['body_bg']};
            }}

            #contentWidget {{
                background-color: {config.COLORS['primary_bg']};
                border-radius: {config.UI_METRICS['border_radius']['xxl']}px;
            }}

            #footerWidget {{
                background-color: {config.COLORS['secondary_bg']};
                border-top: 1px solid {config.COLORS['border']};
            }}
        """)
