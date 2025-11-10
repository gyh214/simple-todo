# -*- coding: utf-8 -*-
"""UpdateAvailableDialog - 업데이트 알림 다이얼로그"""

import logging
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QWidget
)
from PyQt6.QtCore import Qt
from typing import TYPE_CHECKING

import config

if TYPE_CHECKING:
    from ...domain.entities.release import Release
    from ...domain.value_objects.app_version import AppVersion


logger = logging.getLogger(__name__)


class UpdateAvailableDialog(QDialog):
    """업데이트 가능 알림 다이얼로그

    새로운 버전이 발견되었을 때 사용자에게 표시하는 다이얼로그입니다.
    버전 정보, 파일 크기, 릴리스 노트를 표시하고 사용자의 선택을 받습니다.

    Returns:
        - "update": 업데이트 버튼 클릭
        - "skip": 건너뛰기 버튼 클릭
        - "later": 나중에 버튼 클릭 또는 닫기

    Examples:
        >>> dialog = UpdateAvailableDialog(parent, release, current_version)
        >>> dialog.exec()
        >>> result = dialog.get_user_choice()
        >>> if result == "update":
        ...     start_download()
    """

    def __init__(
        self,
        parent,
        release: 'Release',
        current_version: 'AppVersion'
    ):
        """UpdateAvailableDialog 초기화

        Args:
            parent: 부모 위젯
            release: 새 릴리스 정보
            current_version: 현재 버전
        """
        super().__init__(parent)

        # lazy import로 순환 참조 방지
        from ...domain.entities.release import Release
        from ...domain.value_objects.app_version import AppVersion

        if not isinstance(release, Release):
            raise TypeError(f"release는 Release여야 합니다")

        if not isinstance(current_version, AppVersion):
            raise TypeError(f"current_version은 AppVersion이어야 합니다")

        self.release = release
        self.current_version = current_version
        self.user_choice = "later"  # 기본값: 나중에

        self._setup_ui()
        self._apply_styles()

        # 모달 설정
        self.setModal(True)
        self.setWindowTitle("업데이트 가능")
        self.setFixedSize(450, 600)

        logger.info(f"UpdateAvailableDialog 생성: v{release.version}")

    def _setup_ui(self):
        """UI 구성"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(16)

        # 제목
        title_label = QLabel("업데이트 가능")
        title_label.setObjectName("titleLabel")
        main_layout.addWidget(title_label)

        # 버전 정보 컨테이너
        version_container = QWidget()
        version_layout = QVBoxLayout(version_container)
        version_layout.setContentsMargins(0, 0, 0, 0)
        version_layout.setSpacing(8)

        # 현재 버전
        current_label = QLabel(f"현재: v{self.current_version}")
        current_label.setObjectName("versionLabel")
        version_layout.addWidget(current_label)

        # 새 버전 (accent 색상)
        new_label = QLabel(f"새 버전: v{self.release.version}")
        new_label.setObjectName("newVersionLabel")
        version_layout.addWidget(new_label)

        # 파일 크기
        size_label = QLabel(f"파일 크기: {self.release.format_file_size()}")
        size_label.setObjectName("sizeLabel")
        version_layout.addWidget(size_label)

        main_layout.addWidget(version_container)

        # 릴리스 노트 섹션
        notes_label = QLabel("릴리스 노트")
        notes_label.setObjectName("sectionLabel")
        main_layout.addWidget(notes_label)

        # 릴리스 노트 텍스트
        self.release_notes_text = QTextEdit()
        self.release_notes_text.setObjectName("releaseNotesText")
        self.release_notes_text.setReadOnly(True)
        self.release_notes_text.setPlainText(
            self.release.release_notes or "릴리스 노트가 없습니다."
        )
        self.release_notes_text.setMinimumHeight(250)
        main_layout.addWidget(self.release_notes_text)

        # 버튼 영역
        button_layout = QVBoxLayout()
        button_layout.setSpacing(10)

        # 주요 버튼 (업데이트, 나중에)
        primary_button_layout = QHBoxLayout()
        primary_button_layout.setSpacing(10)

        self.update_btn = QPushButton("지금 업데이트")
        self.update_btn.setObjectName("updateBtn")
        self.update_btn.clicked.connect(self._on_update_clicked)
        self.update_btn.setMinimumSize(120, 40)
        primary_button_layout.addWidget(self.update_btn)

        self.later_btn = QPushButton("나중에")
        self.later_btn.setObjectName("laterBtn")
        self.later_btn.clicked.connect(self._on_later_clicked)
        self.later_btn.setMinimumSize(120, 40)
        primary_button_layout.addWidget(self.later_btn)

        button_layout.addLayout(primary_button_layout)

        # 건너뛰기 버튼 (작은 텍스트 버튼)
        self.skip_btn = QPushButton("이 버전 건너뛰기")
        self.skip_btn.setObjectName("skipBtn")
        self.skip_btn.clicked.connect(self._on_skip_clicked)
        self.skip_btn.setMinimumHeight(30)
        button_layout.addWidget(self.skip_btn)

        main_layout.addLayout(button_layout)

        # 업데이트 버튼에 포커스
        self.update_btn.setFocus()

    def _on_update_clicked(self):
        """업데이트 버튼 클릭"""
        logger.info("사용자 선택: 업데이트")
        self.user_choice = "update"
        self.accept()

    def _on_later_clicked(self):
        """나중에 버튼 클릭"""
        logger.info("사용자 선택: 나중에")
        self.user_choice = "later"
        self.reject()

    def _on_skip_clicked(self):
        """건너뛰기 버튼 클릭"""
        logger.info("사용자 선택: 건너뛰기")
        self.user_choice = "skip"
        self.accept()

    def get_user_choice(self) -> str:
        """사용자 선택 반환

        Returns:
            str: "update", "skip", "later"
        """
        return self.user_choice

    def keyPressEvent(self, event):
        """키보드 이벤트: ESC로 닫기"""
        if event.key() == Qt.Key.Key_Escape:
            self._on_later_clicked()
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
                font-size: {config.FONT_SIZES['xxl']}px;
                font-weight: 600;
            }}

            QLabel#versionLabel {{
                color: {config.COLORS['text_secondary']};
                font-size: {config.FONT_SIZES['base']}px;
            }}

            QLabel#newVersionLabel {{
                color: {config.COLORS['accent']};
                font-size: {config.FONT_SIZES['lg']}px;
                font-weight: 600;
            }}

            QLabel#sizeLabel {{
                color: {config.COLORS['text_secondary']};
                font-size: {config.FONT_SIZES['sm']}px;
            }}

            QLabel#sectionLabel {{
                color: {config.COLORS['text_secondary']};
                font-size: {config.FONT_SIZES['base']}px;
                font-weight: 500;
                margin-top: 5px;
            }}

            QTextEdit#releaseNotesText {{
                background: {config.COLORS['card']};
                border: {config.UI_METRICS['border_width']['thin']}px solid {config.COLORS['border']};
                border-radius: {config.UI_METRICS['border_radius']['lg']}px;
                padding: 12px;
                color: {config.COLORS['text_primary']};
                font-size: {config.FONT_SIZES['base']}px;
                font-family: "Segoe UI", "Malgun Gothic", sans-serif;
            }}

            QPushButton#updateBtn {{
                background: {config.COLORS['accent']};
                color: white;
                border: none;
                border-radius: {config.UI_METRICS['border_radius']['lg']}px;
                padding: {config.UI_METRICS['padding']['lg'][0]}px {config.UI_METRICS['padding']['lg'][1]}px;
                font-weight: 600;
                font-size: {config.FONT_SIZES['lg']}px;
            }}

            QPushButton#updateBtn:hover {{
                background: {config.COLORS['accent_hover']};
            }}

            QPushButton#updateBtn:pressed {{
                background: #B56B4A;
            }}

            QPushButton#laterBtn {{
                background: transparent;
                border: {config.UI_METRICS['border_width']['thin']}px solid {config.COLORS['border']};
                border-radius: {config.UI_METRICS['border_radius']['lg']}px;
                padding: {config.UI_METRICS['padding']['lg'][0]}px {config.UI_METRICS['padding']['lg'][1]}px;
                color: {config.COLORS['text_secondary']};
                font-size: {config.FONT_SIZES['lg']}px;
            }}

            QPushButton#laterBtn:hover {{
                border-color: {config.COLORS['accent']};
                color: {config.COLORS['text_primary']};
            }}

            QPushButton#laterBtn:pressed {{
                background: rgba(64, 64, 64, 0.1);
            }}

            QPushButton#skipBtn {{
                background: transparent;
                border: none;
                color: {config.COLORS['text_disabled']};
                font-size: {config.FONT_SIZES['sm']}px;
                text-decoration: underline;
            }}

            QPushButton#skipBtn:hover {{
                color: {config.COLORS['text_secondary']};
            }}

            QPushButton#skipBtn:pressed {{
                color: {config.COLORS['text_disabled']};
            }}
        """)
