# -*- coding: utf-8 -*-
"""UpdateProgressDialog - 다운로드 진행률 다이얼로그"""

import logging
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QProgressBar, QPushButton
)
from PyQt6.QtCore import Qt
from typing import TYPE_CHECKING
import time

import config

if TYPE_CHECKING:
    from ...domain.entities.release import Release


logger = logging.getLogger(__name__)


class UpdateProgressDialog(QDialog):
    """다운로드 진행률 표시 다이얼로그

    업데이트 파일 다운로드 진행률을 실시간으로 표시합니다.
    진행률 바, 다운로드 상태, 속도, 남은 시간을 표시합니다.

    Examples:
        >>> dialog = UpdateProgressDialog(parent, release)
        >>> dialog.show()
        >>> dialog.update_progress(1024000, 10240000)  # 1MB / 10MB
        >>> dialog.set_complete()
    """

    def __init__(self, parent, release: 'Release'):
        """UpdateProgressDialog 초기화

        Args:
            parent: 부모 위젯
            release: 다운로드할 릴리스 정보
        """
        super().__init__(parent)

        # lazy import로 순환 참조 방지
        from ...domain.entities.release import Release

        if not isinstance(release, Release):
            raise TypeError(f"release는 Release여야 합니다")

        self.release = release

        # 진행률 계산용 변수
        self.start_time = time.time()
        self.last_update_time = time.time()
        self.last_downloaded = 0

        self._setup_ui()
        self._apply_styles()

        # 모달 설정
        self.setModal(True)
        self.setWindowTitle("업데이트 다운로드 중...")
        self.setFixedSize(400, 200)

        logger.info(f"UpdateProgressDialog 생성: {release.asset_name}")

    def _setup_ui(self):
        """UI 구성"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(16)

        # 제목
        title_label = QLabel("업데이트 다운로드 중...")
        title_label.setObjectName("titleLabel")
        main_layout.addWidget(title_label)

        # 진행률 바
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("progressBar")
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p%")
        main_layout.addWidget(self.progress_bar)

        # 상태 텍스트 (크기/속도)
        self.status_label = QLabel("준비 중...")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.status_label)

        # 속도 및 남은 시간
        self.speed_label = QLabel("")
        self.speed_label.setObjectName("speedLabel")
        self.speed_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.speed_label)

        # 취소 버튼 (현재는 비활성화)
        # self.cancel_btn = QPushButton("취소")
        # self.cancel_btn.setObjectName("cancelBtn")
        # self.cancel_btn.clicked.connect(self._on_cancel_clicked)
        # self.cancel_btn.setEnabled(False)  # 취소 기능 미구현
        # main_layout.addWidget(self.cancel_btn)

    def update_progress(self, downloaded: int, total: int):
        """다운로드 진행률을 업데이트합니다.

        Args:
            downloaded: 다운로드된 바이트 수
            total: 전체 파일 크기 (바이트)
        """
        if total <= 0:
            return

        # 진행률 계산 (0-100%)
        progress_percent = int((downloaded / total) * 100)
        self.progress_bar.setValue(progress_percent)

        # 크기 표시
        downloaded_mb = downloaded / (1024 * 1024)
        total_mb = total / (1024 * 1024)
        size_text = f"{downloaded_mb:.1f} MB / {total_mb:.1f} MB ({progress_percent}%)"
        self.status_label.setText(size_text)

        # 속도 및 남은 시간 계산
        current_time = time.time()
        time_diff = current_time - self.last_update_time

        # 0.5초마다 속도 업데이트 (너무 자주 업데이트하면 깜빡임)
        if time_diff >= 0.5:
            downloaded_diff = downloaded - self.last_downloaded
            speed_bps = downloaded_diff / time_diff if time_diff > 0 else 0
            speed_mbps = speed_bps / (1024 * 1024)

            # 남은 시간 계산
            remaining_bytes = total - downloaded
            remaining_seconds = remaining_bytes / speed_bps if speed_bps > 0 else 0

            # 속도 표시
            if speed_mbps >= 1.0:
                speed_text = f"{speed_mbps:.1f} MB/s"
            else:
                speed_kbps = speed_bps / 1024
                speed_text = f"{speed_kbps:.1f} KB/s"

            # 남은 시간 표시
            if remaining_seconds > 0:
                if remaining_seconds < 60:
                    time_text = f"약 {int(remaining_seconds)}초 남음"
                elif remaining_seconds < 3600:
                    minutes = int(remaining_seconds / 60)
                    time_text = f"약 {minutes}분 남음"
                else:
                    hours = int(remaining_seconds / 3600)
                    time_text = f"약 {hours}시간 남음"
            else:
                time_text = "계산 중..."

            self.speed_label.setText(f"{speed_text} - {time_text}")

            # 다음 계산을 위해 저장
            self.last_update_time = current_time
            self.last_downloaded = downloaded

    def set_status(self, message: str):
        """상태 메시지를 설정합니다.

        Args:
            message: 표시할 메시지
        """
        self.status_label.setText(message)
        logger.info(f"다운로드 상태: {message}")

    def set_complete(self):
        """다운로드 완료 표시"""
        self.progress_bar.setValue(100)
        self.status_label.setText("다운로드 완료!")
        self.speed_label.setText("파일 검증 중...")
        logger.info("다운로드 완료")

    def _on_cancel_clicked(self):
        """취소 버튼 클릭 (미구현)"""
        logger.warning("다운로드 취소 기능은 현재 지원되지 않습니다")
        # TODO: 다운로드 취소 기능 구현

    def keyPressEvent(self, event):
        """키보드 이벤트: ESC 비활성화 (다운로드 중 닫기 방지)"""
        if event.key() == Qt.Key.Key_Escape:
            # 다운로드 중에는 ESC로 닫기 비활성화
            logger.info("다운로드 중에는 창을 닫을 수 없습니다")
            event.ignore()
        else:
            super().keyPressEvent(event)

    def _apply_styles(self):
        """스타일 시트 적용"""
        self.setStyleSheet(f"""
            QDialog {{
                background: {config.COLORS['primary_bg']};
                border-radius: {config.UI_METRICS['border_radius']['xl']}px;
            }}

            QLabel#titleLabel {{
                color: {config.COLORS['text_primary']};
                font-size: {config.FONT_SIZES['xl']}px;
                font-weight: 600;
            }}

            QLabel#statusLabel {{
                color: {config.COLORS['text_primary']};
                font-size: {config.FONT_SIZES['base']}px;
            }}

            QLabel#speedLabel {{
                color: {config.COLORS['text_secondary']};
                font-size: {config.FONT_SIZES['sm']}px;
            }}

            QProgressBar#progressBar {{
                background: {config.COLORS['card']};
                border: {config.UI_METRICS['border_width']['thin']}px solid {config.COLORS['border']};
                border-radius: {config.UI_METRICS['border_radius']['lg']}px;
                text-align: center;
                color: {config.COLORS['text_primary']};
                font-size: {config.FONT_SIZES['base']}px;
                height: 30px;
            }}

            QProgressBar#progressBar::chunk {{
                background: {config.COLORS['accent']};
                border-radius: {config.UI_METRICS['border_radius']['lg']}px;
            }}

            QPushButton#cancelBtn {{
                background: transparent;
                border: {config.UI_METRICS['border_width']['thin']}px solid {config.COLORS['border']};
                border-radius: {config.UI_METRICS['border_radius']['lg']}px;
                padding: {config.UI_METRICS['padding']['lg'][0]}px {config.UI_METRICS['padding']['lg'][1]}px;
                color: {config.COLORS['text_secondary']};
                font-size: {config.FONT_SIZES['base']}px;
            }}

            QPushButton#cancelBtn:hover {{
                border-color: {config.COLORS['accent']};
                color: {config.COLORS['text_primary']};
            }}

            QPushButton#cancelBtn:disabled {{
                color: {config.COLORS['text_disabled']};
                border-color: {config.COLORS['border']};
            }}
        """)
