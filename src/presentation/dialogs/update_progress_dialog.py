# -*- coding: utf-8 -*-
"""UpdateProgressDialog - 다운로드 진행률 다이얼로그"""

import logging
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QProgressBar, QPushButton, QApplication
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

        # 업데이트 단계 정의
        self.update_stages = {
            'preparing': {'weight': 5, 'name': '준비 중...'},
            'downloading': {'weight': 70, 'name': '다운로드 중...'},
            'verifying': {'weight': 15, 'name': '파일 검증 중...'},
            'installing': {'weight': 10, 'name': '설치 중...'}
        }
        self.current_stage = 'preparing'
        self.stage_progress = {'preparing': 0, 'downloading': 0, 'verifying': 0, 'installing': 0}

        self._setup_ui()
        self._apply_styles()

        # 모달 설정
        self.setModal(True)
        self.setWindowTitle("SimpleTodo 업데이트 중...")
        self.setFixedSize(450, 250)

        logger.info(f"UpdateProgressDialog 생성: {release.asset_name}")

    def _setup_ui(self):
        """UI 구성"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(16)

        # 제목
        title_label = QLabel("SimpleTodo 업데이트 중...")
        title_label.setObjectName("titleLabel")
        main_layout.addWidget(title_label)

        # 메인 진행률 바
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("progressBar")
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p%")
        main_layout.addWidget(self.progress_bar)

        # 현재 단계 표시
        self.stage_label = QLabel("준비 중...")
        self.stage_label.setObjectName("stageLabel")
        self.stage_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.stage_label)

        # 단계별 진행률 표시 (수평 레이아웃)
        stages_layout = QVBoxLayout()
        stages_layout.setSpacing(8)

        # 각 단계의 진행률 바
        self.stage_bars = {}
        for stage_key, stage_info in self.update_stages.items():
            stage_container = QHBoxLayout()
            stage_container.setSpacing(8)

            # 단계 이름
            stage_name_label = QLabel(stage_info['name'])
            stage_name_label.setObjectName("stageNameLabel")
            stage_name_label.setFixedWidth(100)

            # 단계 진행률 바
            stage_bar = QProgressBar()
            stage_bar.setObjectName(f"stageBar_{stage_key}")
            stage_bar.setMinimum(0)
            stage_bar.setMaximum(100)
            stage_bar.setValue(0)
            stage_bar.setTextVisible(False)
            stage_bar.setFixedHeight(8)

            # 단계 상태 아이콘
            stage_icon = QLabel("○")
            stage_icon.setObjectName(f"stageIcon_{stage_key}")
            stage_icon.setFixedWidth(20)
            stage_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)

            stage_container.addWidget(stage_icon)
            stage_container.addWidget(stage_name_label)
            stage_container.addWidget(stage_bar)

            stages_layout.addLayout(stage_container)

            # 저장
            self.stage_bars[stage_key] = {
                'bar': stage_bar,
                'icon': stage_icon,
                'label': stage_name_label
            }

        main_layout.addLayout(stages_layout)

        # 상세 정보 (속도/남은 시간/파일 크기)
        self.details_label = QLabel("준비를 시작합니다...")
        self.details_label.setObjectName("detailsLabel")
        self.details_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.details_label)

        # 취소 버튼 (현재는 비활성화)
        # self.cancel_btn = QPushButton("취소")
        # self.cancel_btn.setObjectName("cancelBtn")
        # self.cancel_btn.clicked.connect(self._on_cancel_clicked)
        # self.cancel_btn.setEnabled(False)  # 취소 기능 미구현
        # main_layout.addWidget(self.cancel_btn)

    def set_stage(self, stage_name: str):
        """현재 업데이트 단계를 설정합니다.

        Args:
            stage_name: 단계 이름 ('preparing', 'downloading', 'verifying', 'installing')
        """
        if stage_name not in self.update_stages:
            logger.error(f"알 수 없는 단계: {stage_name}")
            return

        # 이전 단계 완료 표시
        if self.current_stage in self.stage_bars:
            self.stage_bars[self.current_stage]['icon'].setText("✓")
            self.stage_bars[self.current_stage]['icon'].setStyleSheet(
                "color: #4CAF50; font-weight: bold;"
            )

        # 새 단계 설정
        self.current_stage = stage_name
        self.stage_label.setText(self.update_stages[stage_name]['name'])

        # 현재 단계 아이콘 업데이트
        self.stage_bars[stage_name]['icon'].setText("⟳")
        self.stage_bars[stage_name]['icon'].setStyleSheet(
            "color: #2196F3; font-weight: bold;"
        )

        logger.info(f"업데이트 단계 변경: {stage_name}")

    def update_stage_progress(self, stage_name: str, progress: int):
        """특정 단계의 진행률을 업데이트합니다.

        Args:
            stage_name: 단계 이름
            progress: 진행률 (0-100)
        """
        if stage_name not in self.stage_bars:
            return

        # 진행률 제한
        progress = max(0, min(100, progress))
        self.stage_progress[stage_name] = progress

        # 단계 진행률 바 업데이트
        self.stage_bars[stage_name]['bar'].setValue(progress)

        # 전체 진행률 계산
        self._update_overall_progress()

    def _update_overall_progress(self):
        """전체 진행률을 계산하고 업데이트합니다."""
        total_progress = 0
        total_weight = 0

        for stage_key, stage_info in self.update_stages.items():
            weight = stage_info['weight']
            stage_progress = self.stage_progress.get(stage_key, 0)

            # 가중치 적용된 진행률 계산
            total_progress += (stage_progress * weight / 100)
            total_weight += weight

        # 전체 진행률 계산
        if total_weight > 0:
            overall_progress = int((total_progress / total_weight) * 100)
            self.progress_bar.setValue(overall_progress)

    def update_progress(self, downloaded: int, total: int):
        """다운로드 진행률을 업데이트합니다.

        Args:
            downloaded: 다운로드된 바이트 수
            total: 전체 파일 크기 (바이트)
        """
        if total <= 0:
            return

        # 다운로드 단계로 설정
        if self.current_stage != 'downloading':
            self.set_stage('downloading')

        # 다운로드 진행률 계산
        download_progress = int((downloaded / total) * 100)
        self.update_stage_progress('downloading', download_progress)

        # 크기 표시
        downloaded_mb = downloaded / (1024 * 1024)
        total_mb = total / (1024 * 1024)

        # 속도 및 남은 시간 계산
        current_time = time.time()
        time_diff = current_time - self.last_update_time

        speed_text = ""
        time_text = ""

        # 0.5초마다 속도 업데이트 (너무 자주 업데이트하면 깜빡임)
        if time_diff >= 0.5:
            downloaded_diff = downloaded - self.last_downloaded
            speed_bps = downloaded_diff / time_diff if time_diff > 0 else 0

            # 속도 표시
            if speed_bps > 0:
                speed_mbps = speed_bps / (1024 * 1024)
                if speed_mbps >= 1.0:
                    speed_text = f"{speed_mbps:.1f} MB/s"
                else:
                    speed_kbps = speed_bps / 1024
                    speed_text = f"{speed_kbps:.1f} KB/s"

                # 남은 시간 계산
                remaining_bytes = total - downloaded
                remaining_seconds = remaining_bytes / speed_bps

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
                    time_text = "곧 완료"

            # 다음 계산을 위해 저장
            self.last_update_time = current_time
            self.last_downloaded = downloaded

        # 상세 정보 업데이트
        details = []
        details.append(f"{downloaded_mb:.1f} MB / {total_mb:.1f} MB")
        if speed_text:
            details.append(f"속도: {speed_text}")
        if time_text:
            details.append(time_text)

        self.details_label.setText(" | ".join(details))

    def set_verifying(self):
        """파일 검증 단계로 설정합니다."""
        self.set_stage('verifying')
        self.details_label.setText("다운로드된 파일의 무결성을 검증합니다...")

        # 검증 진행률 시뮬레이션
        for i in range(0, 101, 20):
            self.update_stage_progress('verifying', i)
            QApplication.processEvents()  # UI 업데이트를 위한 이벤트 처리

    def set_installing(self):
        """설치 단계로 설정합니다."""
        self.set_stage('installing')
        self.details_label.setText("업데이트를 설치하고 있습니다...")

    def set_complete(self):
        """업데이트 완료 표시"""
        # 모든 단계 완료 표시
        for stage_key in self.stage_bars:
            self.stage_bars[stage_key]['icon'].setText("✓")
            self.stage_bars[stage_key]['icon'].setStyleSheet(
                "color: #4CAF50; font-weight: bold;"
            )
            self.stage_bars[stage_key]['bar'].setValue(100)

        # 전체 진행률 100%
        self.progress_bar.setValue(100)
        self.stage_label.setText("업데이트 완료!")
        self.details_label.setText("SimpleTodo가 성공적으로 업데이트되었습니다.")

        logger.info("업데이트 완료")

    def set_error(self, error_message: str):
        """오류 발생 표시

        Args:
            error_message: 오류 메시지
        """
        # 현재 단계 아이콘을 에러 표시로 변경
        if self.current_stage in self.stage_bars:
            self.stage_bars[self.current_stage]['icon'].setText("✗")
            self.stage_bars[self.current_stage]['icon'].setStyleSheet(
                "color: #F44336; font-weight: bold;"
            )

        self.stage_label.setText("업데이트 실패")
        self.details_label.setText(f"오류: {error_message}")

        logger.error(f"업데이트 오류: {error_message}")

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

            QLabel#stageLabel {{
                color: {config.COLORS['text_primary']};
                font-size: {config.FONT_SIZES['lg']}px;
                font-weight: 500;
                padding: 8px 0;
            }}

            QLabel#stageNameLabel {{
                color: {config.COLORS['text_secondary']};
                font-size: {config.FONT_SIZES['sm']}px;
            }}

            QLabel#detailsLabel {{
                color: {config.COLORS['text_secondary']};
                font-size: {config.FONT_SIZES['base']}px;
                padding: 8px;
                background: {config.COLORS['card']};
                border-radius: {config.UI_METRICS['border_radius']['md']}px;
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

            QProgressBar[objectName^="stageBar_"] {{
                background: {config.COLORS['border']};
                border: none;
                border-radius: 4px;
            }}

            QProgressBar[objectName^="stageBar_"]::chunk {{
                background: {config.COLORS['accent']};
                border-radius: 4px;
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
