# -*- coding: utf-8 -*-
"""
윈도우 관리 시스템

윈도우 크기, 위치, 상태(항상 위) 관리를 담당합니다.
"""
from typing import Optional, Dict, Any
from PyQt6.QtCore import Qt, QRect
from PyQt6.QtWidgets import QMainWindow, QApplication
from PyQt6.QtGui import QScreen
import logging

logger = logging.getLogger(__name__)


class WindowManager:
    """윈도우 관리 클래스

    Features:
    - 최소/초기 크기 설정
    - 화면 중앙 배치
    - 항상 위 토글
    - 윈도우 상태 저장/복원
    """

    def __init__(self, main_window: QMainWindow, repository):
        """WindowManager 초기화

        Args:
            main_window: 관리할 메인 윈도우
            repository: 설정 저장을 위한 Repository
        """
        self.main_window = main_window
        self.repository = repository
        self.is_always_on_top = False

    def setup_window(self,
                     min_width: int = 300,
                     min_height: int = 400,
                     default_width: int = 420,
                     default_height: int = 600) -> None:
        """윈도우 초기 설정

        Args:
            min_width: 최소 너비
            min_height: 최소 높이
            default_width: 기본 너비
            default_height: 기본 높이
        """
        # 최소 크기 설정
        self.main_window.setMinimumSize(min_width, min_height)

        # 저장된 상태 복원 시도
        restored = self._restore_window_state()

        if not restored:
            # 저장된 상태가 없으면 기본값 사용
            self.main_window.resize(default_width, default_height)
            self._center_on_screen()

        logger.info(f"Window setup completed: size={self.main_window.size()}, pos={self.main_window.pos()}")

    def toggle_always_on_top(self) -> None:
        """항상 위 기능 토글

        Qt WindowFlags를 조작하여 항상 위 상태를 변경합니다.
        변경 후 설정을 저장합니다.
        """
        current_flags = self.main_window.windowFlags()

        if self.is_always_on_top:
            # 항상 위 비활성화
            new_flags = current_flags & ~Qt.WindowType.WindowStaysOnTopHint
            self.is_always_on_top = False
            logger.info("Always on top: disabled")
        else:
            # 항상 위 활성화
            new_flags = current_flags | Qt.WindowType.WindowStaysOnTopHint
            self.is_always_on_top = True
            logger.info("Always on top: enabled")

        # 윈도우 플래그 적용
        self.main_window.setWindowFlags(new_flags)
        self.main_window.show()  # 플래그 변경 후 재표시 필요

        # 상태 저장
        self.save_window_state()

    def save_window_state(self) -> None:
        """현재 윈도우 상태를 저장합니다

        저장 항목:
        - 위치 (x, y)
        - 크기 (width, height)
        - 항상 위 상태
        """
        try:
            # 현재 윈도우 geometry 가져오기
            geometry = self.main_window.geometry()

            window_state = {
                "windowGeometry": {
                    "x": geometry.x(),
                    "y": geometry.y(),
                    "width": geometry.width(),
                    "height": geometry.height()
                },
                "alwaysOnTop": self.is_always_on_top
            }

            # Repository를 통해 설정 저장
            self.repository.update_settings(window_state)
            logger.info(f"Window state saved: {window_state}")

        except Exception as e:
            logger.error(f"Failed to save window state: {e}")

    def _restore_window_state(self) -> bool:
        """저장된 윈도우 상태를 복원합니다

        Returns:
            bool: 복원 성공 여부
        """
        try:
            settings = self.repository.get_settings()

            # windowGeometry 복원
            geometry = settings.get("windowGeometry")
            if geometry:
                x = geometry.get("x", 0)
                y = geometry.get("y", 0)
                width = geometry.get("width", 420)
                height = geometry.get("height", 600)

                # 저장된 위치/크기가 화면 범위 내인지 확인
                if self._is_geometry_valid(x, y, width, height):
                    self.main_window.setGeometry(x, y, width, height)
                    logger.info(f"Window geometry restored: x={x}, y={y}, w={width}, h={height}")
                else:
                    logger.warning("Saved geometry is invalid, using default position")
                    return False
            else:
                logger.info("No saved geometry found")
                return False

            # alwaysOnTop 복원
            always_on_top = settings.get("alwaysOnTop", False)
            if always_on_top:
                self.is_always_on_top = False  # toggle_always_on_top이 반전시키므로 반대값 설정
                self.toggle_always_on_top()

            return True

        except Exception as e:
            logger.error(f"Failed to restore window state: {e}")
            return False

    def _center_on_screen(self) -> None:
        """윈도우를 화면 중앙에 배치합니다"""
        # 현재 화면 가져오기
        screen = self._get_current_screen()
        if not screen:
            logger.warning("Failed to get screen geometry")
            return

        screen_geometry = screen.availableGeometry()
        window_geometry = self.main_window.frameGeometry()

        # 중앙 위치 계산
        center_x = screen_geometry.center().x() - window_geometry.width() // 2
        center_y = screen_geometry.center().y() - window_geometry.height() // 2

        self.main_window.move(center_x, center_y)
        logger.info(f"Window centered at: x={center_x}, y={center_y}")

    def _get_current_screen(self) -> Optional[QScreen]:
        """현재 마우스 커서가 있는 스크린을 반환합니다

        Returns:
            Optional[QScreen]: 현재 스크린 (실패 시 기본 스크린)
        """
        try:
            # QApplication에서 현재 스크린 가져오기
            cursor_pos = QApplication.primaryScreen().availableGeometry().center()
            screen = QApplication.screenAt(cursor_pos)

            if screen:
                return screen
            else:
                # 기본 스크린 반환
                return QApplication.primaryScreen()

        except Exception as e:
            logger.error(f"Failed to get current screen: {e}")
            return QApplication.primaryScreen()

    def _is_geometry_valid(self, x: int, y: int, width: int, height: int) -> bool:
        """주어진 geometry가 화면 범위 내에 있는지 검증합니다

        Args:
            x: X 좌표
            y: Y 좌표
            width: 너비
            height: 높이

        Returns:
            bool: 유효하면 True, 아니면 False
        """
        try:
            # 모든 스크린 확인
            screens = QApplication.screens()
            window_rect = QRect(x, y, width, height)

            for screen in screens:
                screen_rect = screen.availableGeometry()
                # 윈도우가 스크린과 교차하는지 확인 (최소 50% 이상 보여야 함)
                if screen_rect.intersects(window_rect):
                    intersection = screen_rect.intersected(window_rect)
                    # 교차 영역이 윈도우의 50% 이상인지 확인
                    window_area = width * height
                    intersection_area = intersection.width() * intersection.height()
                    if intersection_area >= window_area * 0.5:
                        return True

            logger.warning(f"Geometry is outside screen bounds: x={x}, y={y}, w={width}, h={height}")
            return False

        except Exception as e:
            logger.error(f"Failed to validate geometry: {e}")
            return False
