# -*- coding: utf-8 -*-
"""
시스템 트레이 관리자

Simple ToDo 애플리케이션의 시스템 트레이 통합을 담당합니다.
- 트레이 아이콘 표시
- 최소화 시 트레이로 이동
- 좌클릭: 창 표시/숨김 토글
- 우클릭: 컨텍스트 메뉴 표시
"""
import webbrowser
from typing import TYPE_CHECKING

from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QAction
from PyQt6.QtCore import Qt

if TYPE_CHECKING:
    from src.presentation.ui.main_window import MainWindow


class SystemTrayManager:
    """
    시스템 트레이 관리자

    Simple ToDo 애플리케이션의 시스템 트레이 통합을 담당합니다.
    최소화 시 트레이로 이동하고, 트레이 아이콘 클릭으로 창 표시/숨김을 토글합니다.
    """

    def __init__(self, main_window: 'MainWindow'):
        """
        시스템 트레이 관리자 초기화

        Args:
            main_window: 메인 윈도우 인스턴스
        """
        self.main_window = main_window
        self.tray_icon = QSystemTrayIcon()
        self.setup_tray()

    def setup_tray(self) -> None:
        """트레이 아이콘 및 메뉴 설정"""
        # 트레이 아이콘 설정 (SimpleTodo.ico 사용, 없으면 프로그래밍 방식으로 생성)
        import config
        icon_path = config.get_resource_path(config.ICON_FILE)
        if icon_path.exists():
            icon = QIcon(str(icon_path))
            self.tray_icon.setIcon(icon)
        else:
            # 아이콘 파일이 없으면 프로그래밍 방식으로 생성
            icon = self._create_checkmark_icon()
            self.tray_icon.setIcon(icon)

        # 툴팁 설정
        self.tray_icon.setToolTip("Simple ToDo")

        # 컨텍스트 메뉴 설정
        menu = self.create_menu()
        self.tray_icon.setContextMenu(menu)

        # 트레이 아이콘 클릭 이벤트 연결
        self.tray_icon.activated.connect(self._on_tray_activated)

        # 트레이 아이콘 표시
        self.tray_icon.show()

    def create_menu(self) -> QMenu:
        """
        컨텍스트 메뉴 생성

        Returns:
            QMenu: 트레이 아이콘의 컨텍스트 메뉴
        """
        menu = QMenu()

        # "TODO Panel 표시" 액션
        show_action = QAction("TODO Panel 표시", self.main_window)
        show_action.triggered.connect(self.show_window)
        menu.addAction(show_action)

        # "TODO Panel 숨기기" 액션
        hide_action = QAction("TODO Panel 숨기기", self.main_window)
        hide_action.triggered.connect(self.hide_window)
        menu.addAction(hide_action)

        # 구분선
        menu.addSeparator()

        # "더 많은 유용한 도구들" 액션 (kochim.com 홍보)
        tools_action = QAction("더 많은 유용한 도구들", self.main_window)
        tools_action.triggered.connect(self._open_kochim_website)
        menu.addAction(tools_action)

        # 구분선
        menu.addSeparator()

        # "종료" 액션
        quit_action = QAction("종료", self.main_window)
        quit_action.triggered.connect(self.quit_application)
        menu.addAction(quit_action)

        return menu

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        """
        트레이 아이콘 클릭 이벤트 핸들러

        Args:
            reason: 트레이 아이콘 활성화 이유 (좌클릭, 더블클릭, 우클릭 등)
        """
        # 좌클릭 또는 더블클릭: 창 표시/숨김 토글
        if reason == QSystemTrayIcon.ActivationReason.Trigger or \
           reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.toggle_window()

    def toggle_window(self) -> None:
        """창 표시/숨김 토글"""
        if self.main_window.isVisible():
            self.hide_window()
        else:
            self.show_window()

    def show_window(self) -> None:
        """윈도우 표시"""
        self.main_window.show()
        self.main_window.activateWindow()  # 창을 포커스
        self.main_window.raise_()  # 창을 최상위로

    def hide_window(self) -> None:
        """윈도우 숨김"""
        self.main_window.hide()

    def quit_application(self) -> None:
        """애플리케이션 종료"""
        # 트레이 아이콘 숨김
        self.tray_icon.hide()

        # 애플리케이션 종료
        from PyQt6.QtWidgets import QApplication
        QApplication.quit()

    def _open_kochim_website(self) -> None:
        """kochim.com 웹사이트 브라우저에서 열기"""
        webbrowser.open("https://kochim.com")

    def _create_checkmark_icon(self, size: int = 32) -> QIcon:
        """
        파란색 체크마크 아이콘 생성 (명세서 8.1 요구사항)

        Args:
            size: 아이콘 크기 (픽셀)

        Returns:
            QIcon: 생성된 체크마크 아이콘
        """
        # QPixmap 생성
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)  # 투명 배경

        # QPainter로 체크마크 그리기
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 파란색 설정 (밝은 파란색)
        blue_color = QColor(76, 175, 230)  # #4CAFE6
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(blue_color)

        # 원형 배경 그리기
        margin = 2
        painter.drawEllipse(margin, margin, size - 2 * margin, size - 2 * margin)

        # 체크마크 그리기 (흰색)
        painter.setPen(Qt.GlobalColor.white)
        painter.setBrush(Qt.GlobalColor.white)

        # 체크마크 경로 설정
        from PyQt6.QtGui import QPainterPath
        check_path = QPainterPath()

        # 체크마크 좌표 (상대적 위치)
        center_x = size / 2
        center_y = size / 2
        scale = size / 32  # 32px 기준 스케일

        # 체크마크 시작점 (왼쪽 아래)
        check_path.moveTo(center_x - 6 * scale, center_y)
        # 중간점 (아래)
        check_path.lineTo(center_x - 2 * scale, center_y + 4 * scale)
        # 끝점 (오른쪽 위)
        check_path.lineTo(center_x + 6 * scale, center_y - 4 * scale)

        # 선 두께 설정
        from PyQt6.QtGui import QPen
        pen = QPen(Qt.GlobalColor.white)
        pen.setWidth(int(3 * scale))
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        # 체크마크 그리기
        painter.drawPath(check_path)

        painter.end()

        return QIcon(pixmap)

    def show_message(self, title: str, message: str, icon: QSystemTrayIcon.MessageIcon = QSystemTrayIcon.MessageIcon.Information) -> None:
        """
        트레이 알림 메시지 표시

        Args:
            title: 알림 제목
            message: 알림 메시지
            icon: 알림 아이콘 타입
        """
        self.tray_icon.showMessage(title, message, icon, 3000)  # 3초 동안 표시
