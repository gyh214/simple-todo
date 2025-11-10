# -*- coding: utf-8 -*-
"""백업 관리 및 TODO 일괄 삭제 다이얼로그"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QListWidget, QListWidgetItem, QPushButton, QLineEdit,
    QCheckBox, QScrollArea, QWidget, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIntValidator
from typing import List, Dict

import config
from ..utils.color_utils import create_dialog_palette, apply_palette_recursive


class BackupManagerDialog(QDialog):
    """백업 관리 및 TODO 일괄 삭제 다이얼로그

    3개 탭 구조:
    - 백업 관리: 백업 목록 조회 및 복구
    - 완료 정리: 완료된 TODO 일괄 삭제
    - 선택 삭제: 진행중 TODO 선택 삭제 (검색 + 체크박스)
    """

    def __init__(self, parent=None, repository=None, todo_service=None):
        super().__init__(parent)
        self.repository = repository
        self.todo_service = todo_service

        # BackupService는 repository에서 가져오기 (이미 초기화되어 있음)
        self.backup_service = repository.backup_service if repository else None

        # TodoSearchService import
        from src.domain.services.todo_search_service import TodoSearchService
        self.search_service = TodoSearchService()

        # 백업 표시 일수 (config에서 기본값)
        self.backup_display_days = config.BACKUP_DISPLAY_DAYS

        # Palette 적용 플래그
        self._palette_applied = False

        self.setup_ui()
        self.apply_styles()
        self.load_data()

        self.setModal(True)
        self.setWindowTitle("TODO 관리")
        self.setFixedSize(*config.WIDGET_SIZES['backup_dialog_size'])

    def setup_ui(self):
        """UI 구성"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(*config.LAYOUT_MARGINS['backup_dialog'])
        layout.setSpacing(config.LAYOUT_SPACING['backup_dialog_tab'])

        # 제목
        title_label = QLabel("TODO 관리")
        title_label.setObjectName("titleLabel")
        layout.addWidget(title_label)

        # 탭 위젯
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("mainTabWidget")

        # 탭 1: 백업 관리
        self.backup_tab = self._create_backup_tab()
        self.tab_widget.addTab(self.backup_tab, "백업 관리")

        # 탭 2: 완료 정리
        self.completed_tab = self._create_completed_tab()
        self.tab_widget.addTab(self.completed_tab, "완료 정리")

        # 탭 3: 선택 삭제
        self.select_tab = self._create_select_tab()
        self.tab_widget.addTab(self.select_tab, "선택 삭제")

        layout.addWidget(self.tab_widget)

        # 닫기 버튼
        close_layout = QHBoxLayout()
        close_layout.addStretch()

        self.close_btn = QPushButton("닫기")
        self.close_btn.setObjectName("closeBtn")
        self.close_btn.clicked.connect(self.accept)
        close_layout.addWidget(self.close_btn)

        layout.addLayout(close_layout)

    def _create_backup_tab(self) -> QWidget:
        """백업 관리 탭 생성 (수평 분할: 백업 목록 + TODO 미리보기)"""
        widget = QWidget()
        widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground)
        main_layout = QVBoxLayout(widget)
        main_layout.setContentsMargins(*config.LAYOUT_MARGINS['backup_dialog_tab'])
        main_layout.setSpacing(config.LAYOUT_SPACING['backup_dialog_tab'])

        # 수평 분할 레이아웃 (좌: 백업 목록 40%, 우: TODO 미리보기 60%)
        content_layout = QHBoxLayout()
        content_layout.setSpacing(config.LAYOUT_SPACING['backup_dialog_tab'])

        # === 왼쪽: 백업 파일 목록 ===
        left_widget = QWidget()
        left_widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground)
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)

        # === 상단: 일수 필터 + 검색 (한 줄) ===
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(config.LAYOUT_SPACING['backup_dialog_buttons'])

        # 일수 필터
        days_label = QLabel("최근")
        days_label.setObjectName("sectionLabel")
        filter_layout.addWidget(days_label)

        self.days_input = QLineEdit()
        self.days_input.setObjectName("searchInput")
        self.days_input.setText(str(self.backup_display_days))
        self.days_input.setFixedWidth(50)
        self.days_input.setValidator(QIntValidator(1, 365))
        self.days_input.textChanged.connect(self._on_days_changed)
        filter_layout.addWidget(self.days_input)

        days_suffix_label = QLabel("일")
        days_suffix_label.setObjectName("sectionLabel")
        filter_layout.addWidget(days_suffix_label)

        # 검색창
        self.backup_search_input = QLineEdit()
        self.backup_search_input.setObjectName("searchInput")
        self.backup_search_input.setPlaceholderText("백업 파일 내 할일 검색...")
        self.backup_search_input.returnPressed.connect(self._on_search_backups)
        filter_layout.addWidget(self.backup_search_input)

        # 검색 버튼 (크기 축소)
        backup_search_btn = QPushButton("검색")
        backup_search_btn.setObjectName("searchBtn")
        backup_search_btn.setFixedWidth(60)
        backup_search_btn.clicked.connect(self._on_search_backups)
        filter_layout.addWidget(backup_search_btn)

        left_layout.addLayout(filter_layout)

        self.backup_list = QListWidget()
        self.backup_list.setObjectName("backupList")
        self.backup_list.currentItemChanged.connect(self._on_backup_file_selected)
        left_layout.addWidget(self.backup_list)

        content_layout.addWidget(left_widget, config.BACKUP_DIALOG_LAYOUT['file_list_ratio'])

        # === 오른쪽: TODO 미리보기 ===
        right_widget = QWidget()
        right_widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground)
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(config.BACKUP_DIALOG_LAYOUT['checkbox_spacing'])

        right_label = QLabel("TODO 미리보기 (복구할 항목 선택)")
        right_label.setObjectName("sectionLabel")
        right_layout.addWidget(right_label)

        self.todo_preview_list = QListWidget()
        self.todo_preview_list.setObjectName("todoPreviewList")
        right_layout.addWidget(self.todo_preview_list)

        # 전체 선택 버튼
        select_all_btn = QPushButton("전체 선택")
        select_all_btn.setObjectName("selectAllBtn")
        select_all_btn.clicked.connect(self._on_select_all_preview_todos)
        right_layout.addWidget(select_all_btn)

        content_layout.addWidget(right_widget, config.BACKUP_DIALOG_LAYOUT['preview_ratio'])

        main_layout.addLayout(content_layout)

        # === 하단: 복구 버튼 ===
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(config.LAYOUT_SPACING['backup_dialog_buttons'])

        restore_all_btn = QPushButton("전체 복구")
        restore_all_btn.setObjectName("actionBtn")
        restore_all_btn.clicked.connect(self._on_restore_backup)
        buttons_layout.addWidget(restore_all_btn)

        restore_selected_btn = QPushButton("선택 복구")
        restore_selected_btn.setObjectName("actionBtn")
        restore_selected_btn.clicked.connect(self._on_restore_selected_todos)
        buttons_layout.addWidget(restore_selected_btn)

        main_layout.addLayout(buttons_layout)

        return widget

    def _create_completed_tab(self) -> QWidget:
        """완료 정리 탭 생성"""
        widget = QWidget()
        widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(*config.LAYOUT_MARGINS['backup_dialog_tab'])
        layout.setSpacing(config.LAYOUT_SPACING['backup_dialog_tab'])

        # 설명
        desc_label = QLabel("완료된 TODO를 일괄 삭제합니다")
        desc_label.setObjectName("sectionLabel")
        layout.addWidget(desc_label)

        layout.addStretch()

        # 개수 표시
        self.completed_count_label = QLabel("완료된 TODO: 0개")
        self.completed_count_label.setObjectName("countLabel")
        self.completed_count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.completed_count_label)

        layout.addStretch()

        # 삭제 버튼
        delete_btn = QPushButton("완료 항목 삭제")
        delete_btn.setObjectName("deleteBtn")
        delete_btn.clicked.connect(self._on_delete_completed)
        layout.addWidget(delete_btn)

        return widget

    def _create_select_tab(self) -> QWidget:
        """선택 삭제 탭 생성"""
        widget = QWidget()
        widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(*config.LAYOUT_MARGINS['backup_dialog_tab'])
        layout.setSpacing(config.LAYOUT_SPACING['backup_dialog_tab'])

        # 검색 영역
        search_layout = QHBoxLayout()
        search_layout.setSpacing(config.LAYOUT_SPACING['backup_dialog_buttons'])

        self.search_input = QLineEdit()
        self.search_input.setObjectName("searchInput")
        self.search_input.setPlaceholderText("할일 내용 검색...")
        self.search_input.returnPressed.connect(self._on_search)
        search_layout.addWidget(self.search_input)

        search_btn = QPushButton("검색")
        search_btn.setObjectName("searchBtn")
        search_btn.clicked.connect(self._on_search)
        search_layout.addWidget(search_btn)

        layout.addLayout(search_layout)

        # 전체 선택 버튼
        select_all_btn = QPushButton("검색결과 전체선택")
        select_all_btn.setObjectName("selectAllBtn")
        select_all_btn.clicked.connect(self._on_select_all)
        layout.addWidget(select_all_btn)

        # TODO 체크박스 목록 (스크롤 가능)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("todoScroll")

        self.checkbox_widget = QWidget()
        self.checkbox_widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground)
        self.checkbox_layout = QVBoxLayout(self.checkbox_widget)
        self.checkbox_layout.setContentsMargins(*config.BACKUP_DIALOG_LAYOUT['checkbox_margins'])
        self.checkbox_layout.setSpacing(config.BACKUP_DIALOG_LAYOUT['checkbox_spacing'])
        self.checkbox_layout.addStretch()

        scroll.setWidget(self.checkbox_widget)
        layout.addWidget(scroll)

        # 삭제 버튼
        delete_btn = QPushButton("선택 항목 삭제")
        delete_btn.setObjectName("deleteBtn")
        delete_btn.clicked.connect(self._on_delete_selected)
        layout.addWidget(delete_btn)

        # 체크박스 저장용
        self.todo_checkboxes: List[tuple] = []  # (checkbox, todo_id)

        return widget

    def _show_confirmation(self, title: str, message: str) -> bool:
        """확인 다이얼로그 표시 (공통 메서드).

        Args:
            title: 다이얼로그 제목
            message: 확인 메시지

        Returns:
            bool: 사용자가 "예"를 선택하면 True
        """
        reply = QMessageBox.question(
            self, title, message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        return reply == QMessageBox.StandardButton.Yes

    def _format_todo_display(self, todo) -> str:
        """TODO 표시 텍스트 포맷팅 (공통 메서드).

        Args:
            todo: Todo 엔티티

        Returns:
            str: 포맷팅된 표시 텍스트
        """
        status_text = "완료" if todo.completed else "진행중"
        display_text = f"{todo.content.value} ({status_text})"

        # 납기일이 있으면 추가
        if todo.due_date:
            display_text += f" [{todo.due_date.value.strftime('%Y-%m-%d')}]"

        return display_text

    def load_data(self):
        """데이터 로드"""
        self._load_backup_list()
        self._load_completed_count()
        self._load_todo_checkboxes()

    def _load_backup_list(self):
        """백업 목록 로드 (일수 필터 적용)"""
        if not self.backup_service:
            return

        # days_input이 있으면 값 읽기, 없거나 빈 값이면 기본값
        if hasattr(self, 'days_input'):
            days_text = self.days_input.text().strip()
            days = int(days_text) if days_text else self.backup_display_days
        else:
            days = self.backup_display_days

        backups = self.backup_service.get_backup_list(days=days)
        self._display_backup_list(backups)

    def _display_backup_list(self, backups: List[Dict]):
        """백업 목록 UI 표시 (공통 메서드)"""
        self.backup_list.clear()

        for backup in backups:
            filename = backup['filename']
            size_kb = backup['size'] / 1024
            display_text = f"{filename} ({size_kb:.1f}KB)"

            if not backup['is_valid']:
                display_text += " [손상됨]"

            self.backup_list.addItem(display_text)
            item = self.backup_list.item(self.backup_list.count() - 1)
            item.setData(Qt.ItemDataRole.UserRole, backup['path'])

    def _load_completed_count(self):
        """완료된 TODO 개수 로드"""
        if not self.todo_service:
            return

        todos = self.todo_service.get_all_todos()
        completed_count = sum(1 for t in todos if t.completed)

        self.completed_count_label.setText(f"완료된 TODO: {completed_count}개")

    def _load_todo_checkboxes(self):
        """진행중 TODO 체크박스 로드"""
        # 기존 체크박스 제거
        for checkbox, _ in self.todo_checkboxes:
            self.checkbox_layout.removeWidget(checkbox)
            checkbox.deleteLater()

        self.todo_checkboxes.clear()

        if not self.todo_service:
            return

        # 진행중 TODO만 가져오기
        todos = self.todo_service.get_all_todos()
        in_progress = [t for t in todos if not t.completed]

        # 체크박스 생성
        for todo in in_progress:
            checkbox = QCheckBox(todo.content.value)
            checkbox.setObjectName("todoCheckbox")
            self.checkbox_layout.insertWidget(self.checkbox_layout.count() - 1, checkbox)
            self.todo_checkboxes.append((checkbox, str(todo.id.value)))

    def _on_days_changed(self):
        """일수 변경 시 목록 재로드"""
        days_text = self.days_input.text().strip()
        if days_text:
            try:
                self.backup_display_days = int(days_text)
                self._load_backup_list()
            except ValueError:
                pass  # 유효하지 않은 입력은 무시

    def _on_search_backups(self):
        """백업 파일 검색 (TODO 내용 기반)"""
        query = self.backup_search_input.text()

        if not self.backup_service:
            return

        # 일수 필터 적용하여 백업 목록 가져오기
        days_text = self.days_input.text().strip()
        days = int(days_text) if days_text else self.backup_display_days
        all_backups = self.backup_service.get_backup_list(days=days)

        # 검색어가 없으면 전체 표시
        if not query.strip():
            self._display_backup_list(all_backups)
            return

        # 각 백업 파일 스캔
        filtered_backups = []
        for backup in all_backups:
            try:
                # 백업의 TODO 목록 로드 (기존 메서드 재사용)
                todos = self.backup_service.get_backup_todos(backup['path'])

                # TodoSearchService로 검색 (기존 서비스 재사용)
                matched = self.search_service.search_todos(query, todos)

                # 매칭되는 TODO가 있으면 포함
                if matched:
                    filtered_backups.append(backup)
            except Exception:
                # 손상된 파일은 스킵
                continue

        # 필터링된 결과 표시
        self._display_backup_list(filtered_backups)

    def _on_search(self):
        """검색 실행"""
        query = self.search_input.text()

        if not self.todo_service:
            return

        # 전체 진행중 TODO 가져오기
        todos = self.todo_service.get_all_todos()
        in_progress = [t for t in todos if not t.completed]

        # 검색
        filtered = self.search_service.search_todos(query, in_progress)
        filtered_ids = {str(t.id.value) for t in filtered}

        # 체크박스 표시/숨김
        for checkbox, todo_id in self.todo_checkboxes:
            checkbox.setVisible(todo_id in filtered_ids)

    def _on_select_all(self):
        """검색결과 전체선택"""
        for checkbox, _ in self.todo_checkboxes:
            if checkbox.isVisible():
                checkbox.setChecked(True)

    def _on_restore_backup(self):
        """백업 복구"""
        if not self.backup_service:
            QMessageBox.warning(self, "경고", "백업 서비스를 사용할 수 없습니다.")
            return

        current_item = self.backup_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "경고", "복구할 백업을 선택하세요.")
            return

        backup_path = current_item.data(Qt.ItemDataRole.UserRole)

        # 확인 (공통 메서드 재사용)
        if self._show_confirmation(
            "확인",
            "선택한 백업으로 복구하시겠습니까?\n현재 데이터는 백업됩니다."
        ):
            # 현재 데이터 백업
            self.backup_service.create_backup()

            # 복구
            if self.backup_service.restore_from_backup(backup_path):
                QMessageBox.information(self, "성공", "백업이 복구되었습니다.")
                self.accept()  # 다이얼로그 닫기 (UI 갱신 필요)
            else:
                QMessageBox.critical(self, "실패", "백업 복구에 실패했습니다.")

    def _on_delete_completed(self):
        """완료된 TODO 삭제"""
        if not self.todo_service:
            return

        # 개수 확인
        todos = self.todo_service.get_all_todos()
        completed_count = sum(1 for t in todos if t.completed)

        if completed_count == 0:
            QMessageBox.information(self, "알림", "삭제할 완료 항목이 없습니다.")
            return

        # 확인 (공통 메서드 재사용)
        if self._show_confirmation(
            "확인",
            f"완료된 TODO {completed_count}개를 삭제하시겠습니까?"
        ):
            deleted = self.todo_service.delete_completed_todos()
            QMessageBox.information(self, "완료", f"{deleted}개의 TODO가 삭제되었습니다.")

            # UI 갱신
            self._load_completed_count()
            self.accept()  # 다이얼로그 닫기

    def _on_delete_selected(self):
        """선택된 TODO 삭제"""
        if not self.todo_service:
            return

        # 체크된 항목 수집
        selected_ids = [
            todo_id for checkbox, todo_id in self.todo_checkboxes
            if checkbox.isChecked()
        ]

        if not selected_ids:
            QMessageBox.information(self, "알림", "삭제할 항목을 선택하세요.")
            return

        # 확인 (공통 메서드 재사용)
        if self._show_confirmation(
            "확인",
            f"선택한 TODO {len(selected_ids)}개를 삭제하시겠습니까?"
        ):
            deleted = self.todo_service.delete_selected_todos(selected_ids)
            QMessageBox.information(self, "완료", f"{deleted}개의 TODO가 삭제되었습니다.")

            # UI 갱신
            self._load_todo_checkboxes()
            self.accept()  # 다이얼로그 닫기

    def _on_backup_file_selected(self, current, previous):
        """백업 파일 선택 시 TODO 목록 로드"""
        self.todo_preview_list.clear()

        if not current or not self.backup_service:
            return

        # 백업 파일 경로 가져오기
        backup_path = current.data(Qt.ItemDataRole.UserRole)

        try:
            # BackupService에서 TODO 목록 로드
            todos = self.backup_service.get_backup_todos(backup_path)

            # 빈 백업 파일 처리
            if not todos:
                QMessageBox.information(
                    self, "알림",
                    "선택한 백업 파일에 TODO가 없습니다."
                )
                return

            # TODO 미리보기 목록에 추가 (체크박스 포함)
            for todo in todos:
                # 표시 텍스트 포맷팅 (공통 메서드 재사용)
                display_text = self._format_todo_display(todo)

                # QListWidgetItem 생성 (체크박스 포함)
                item = QListWidgetItem(display_text)
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(Qt.CheckState.Unchecked)

                # UserRole에 Todo 객체 저장 (복구 시 사용)
                item.setData(Qt.ItemDataRole.UserRole, todo)

                # 완료된 TODO는 흐릿하게 표시
                if todo.completed:
                    item.setForeground(Qt.GlobalColor.gray)

                self.todo_preview_list.addItem(item)

        except FileNotFoundError:
            QMessageBox.warning(
                self, "오류",
                "백업 파일을 찾을 수 없습니다."
            )
        except ValueError as e:
            QMessageBox.warning(
                self, "오류",
                f"백업 파일이 손상되었거나 형식이 올바르지 않습니다:\n{str(e)}"
            )
        except Exception as e:
            QMessageBox.warning(
                self, "오류",
                f"백업 파일을 읽을 수 없습니다:\n{str(e)}"
            )

    def _on_select_all_preview_todos(self):
        """TODO 미리보기 전체 선택"""
        for i in range(self.todo_preview_list.count()):
            item = self.todo_preview_list.item(i)
            item.setCheckState(Qt.CheckState.Checked)

    def _on_restore_selected_todos(self):
        """선택된 TODO만 복구"""
        if not self.todo_service or not self.backup_service:
            QMessageBox.warning(self, "경고", "서비스를 사용할 수 없습니다.")
            return

        # 체크된 TODO 수집
        selected_todos = []
        for i in range(self.todo_preview_list.count()):
            item = self.todo_preview_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                todo = item.data(Qt.ItemDataRole.UserRole)
                selected_todos.append(todo)

        if not selected_todos:
            QMessageBox.information(self, "알림", "복구할 TODO를 선택하세요.")
            return

        # 확인 (공통 메서드 재사용)
        if self._show_confirmation(
            "확인",
            f"선택한 {len(selected_todos)}개의 TODO를 복구하시겠습니까?"
        ):
            # 현재 데이터 백업
            self.backup_service.create_backup()

            # 선택된 TODO 복구
            selected_count = len(selected_todos)
            restored = self.todo_service.restore_selected_todos(selected_todos)
            skipped = selected_count - restored

            # 결과 메시지 생성
            if restored > 0 and skipped > 0:
                message = f"{selected_count}개 중 {restored}개 복구 완료 ({skipped}개 중복 스킵)"
            elif restored > 0 and skipped == 0:
                message = f"{restored}개의 TODO가 복구되었습니다."
            else:
                message = "선택한 TODO가 모두 중복되어 복구되지 않았습니다."

            QMessageBox.information(self, "복구 결과", message)
            self.accept()  # 다이얼로그 닫기 (UI 갱신 필요)

    def keyPressEvent(self, event):
        """키보드 이벤트: ESC로 닫기"""
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)

    def showEvent(self, event):
        """다이얼로그 표시 시 QPalette 적용 (한 번만 실행)"""
        super().showEvent(event)
        if not self._palette_applied:
            palette = create_dialog_palette()
            apply_palette_recursive(self, palette)
            self._palette_applied = True

    def apply_styles(self):
        """스타일 시트 적용"""
        self.setStyleSheet(f"""
            QDialog {{
                background: {config.COLORS['secondary_bg']};
            }}

            QLabel#titleLabel {{
                color: {config.COLORS['text_primary']};
                font-size: {config.FONT_SIZES['xxl']}px;
                font-weight: 600;
            }}

            QLabel#sectionLabel {{
                color: {config.COLORS['text_secondary']};
                font-size: {config.FONT_SIZES['md']}px;
            }}

            QLabel#countLabel {{
                color: {config.COLORS['accent']};
                font-size: {config.FONT_SIZES['xl']}px;
                font-weight: 600;
            }}

            QTabWidget::pane {{
                border: 1px solid {config.COLORS['border']};
                border-radius: {config.UI_METRICS['border_radius']['lg']}px;
                background: {config.COLORS['card']};
            }}

            QTabBar::tab {{
                background: {config.COLORS['card']};
                color: {config.COLORS['text_secondary']};
                padding: 8px 16px;
                border: 1px solid {config.COLORS['border']};
                border-bottom: none;
                border-top-left-radius: {config.UI_METRICS['border_radius']['lg']}px;
                border-top-right-radius: {config.UI_METRICS['border_radius']['lg']}px;
            }}

            QTabBar::tab:selected {{
                background: {config.COLORS['accent']};
                color: white;
            }}

            QListWidget#backupList, QListWidget#todoPreviewList {{
                background: {config.COLORS['secondary_bg']};
                border: 1px solid {config.COLORS['border']};
                border-radius: {config.UI_METRICS['border_radius']['lg']}px;
                padding: 8px;
                color: {config.COLORS['text_primary']};
            }}

            QListWidget#backupList::item, QListWidget#todoPreviewList::item {{
                padding: 6px;
                border-radius: 4px;
            }}

            QListWidget#backupList::item:selected, QListWidget#todoPreviewList::item:selected {{
                background: {config.COLORS['accent']};
            }}

            QListWidget#todoPreviewList::indicator {{
                width: 16px;
                height: 16px;
                border-radius: 3px;
                border: 2px solid {config.COLORS['border']};
                background: {config.COLORS['secondary_bg']};
            }}

            QListWidget#todoPreviewList::indicator:checked {{
                background: {config.COLORS['accent']};
                border-color: {config.COLORS['accent']};
            }}

            QLineEdit#searchInput {{
                background: {config.COLORS['secondary_bg']};
                border: 1px solid {config.COLORS['border']};
                border-radius: {config.UI_METRICS['border_radius']['lg']}px;
                padding: 8px;
                color: {config.COLORS['text_primary']};
                font-size: {config.FONT_SIZES['base']}px;
            }}

            QLineEdit#searchInput:focus {{
                border-color: {config.COLORS['accent']};
            }}

            QScrollArea#todoScroll {{
                border: 1px solid {config.COLORS['border']};
                border-radius: {config.UI_METRICS['border_radius']['lg']}px;
                background: {config.COLORS['secondary_bg']};
            }}

            QCheckBox#todoCheckbox {{
                color: {config.COLORS['text_primary']};
                font-size: {config.FONT_SIZES['base']}px;
                spacing: 8px;
            }}

            QPushButton#actionBtn, QPushButton#searchBtn, QPushButton#selectAllBtn {{
                background: {config.COLORS['accent']};
                color: white;
                border: none;
                border-radius: {config.UI_METRICS['border_radius']['lg']}px;
                padding: 10px 20px;
                font-size: {config.FONT_SIZES['base']}px;
                font-weight: 500;
            }}

            QPushButton#actionBtn:hover, QPushButton#searchBtn:hover, QPushButton#selectAllBtn:hover {{
                background: {config.COLORS['accent_hover']};
            }}

            QPushButton#deleteBtn {{
                background: rgba(204, 92, 92, 0.9);
                color: white;
                border: none;
                border-radius: {config.UI_METRICS['border_radius']['lg']}px;
                padding: 10px 20px;
                font-size: {config.FONT_SIZES['base']}px;
                font-weight: 500;
            }}

            QPushButton#deleteBtn:hover {{
                background: rgba(220, 100, 100, 1.0);
            }}

            QPushButton#closeBtn {{
                background: transparent;
                border: 1px solid {config.COLORS['border']};
                border-radius: {config.UI_METRICS['border_radius']['lg']}px;
                padding: 8px 20px;
                color: {config.COLORS['text_secondary']};
                font-size: {config.FONT_SIZES['base']}px;
            }}

            QPushButton#closeBtn:hover {{
                border-color: {config.COLORS['accent']};
                color: {config.COLORS['text_primary']};
            }}
        """)
