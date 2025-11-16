# -*- coding: utf-8 -*-
"""
하위할일 목록 편집 다이얼로그
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                            QPushButton, QScrollArea, QWidget, QCheckBox,
                            QMessageBox, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal
import config
from ..utils.color_utils import create_dialog_palette, apply_palette_recursive


class SubTaskListDialog(QDialog):
    """하위할일 목록 편집 다이얼로그"""
    subtasks_updated = pyqtSignal()  # 하위할일 변경 시 발생

    def __init__(self, todo, todo_service, parent=None):
        """초기화

        Args:
            todo: 부모 TODO 객체
            todo_service: 저장을 위한 서비스
            parent: 부모 위젯
        """
        super().__init__(parent)
        self.todo = todo
        self.todo_service = todo_service
        self._palette_applied = False
        self.setModal(True)

        # 제목 설정 (내용 일부 표시)
        content_preview = str(todo.content)[:30]
        if len(str(todo.content)) > 30:
            content_preview += "..."
        self.setWindowTitle(f"하위 할일 관리 - {content_preview}")

        # 크기 설정 (리사이즈 가능)
        self.setMinimumSize(500, 600)
        self.resize(500, 600)

        self._setup_ui()
        self._apply_styles()
        self._load_subtasks()

    def _setup_ui(self):
        """UI 구성"""
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # 상단: 제목
        title_label = QLabel("하위 할일 목록")
        title_label.setObjectName("titleLabel")
        layout.addWidget(title_label)

        # 설명
        desc_label = QLabel(f"총 {len(self.todo.subtasks)}개의 하위 할일이 있습니다.")
        desc_label.setObjectName("descLabel")
        self.desc_label = desc_label
        layout.addWidget(desc_label)

        # 중간: 하위할일 리스트 (스크롤 영역)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # 리스트 컨테이너
        self.list_container = QWidget()
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(8)
        self.list_layout.addStretch(1)  # 아이템 추가 시 위쪽 정렬

        scroll_area.setWidget(self.list_container)
        layout.addWidget(scroll_area, 1)  # stretch factor

        # 하단: 추가/닫기 버튼
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)

        self.add_btn = QPushButton("+ 하위 할일 추가")
        self.add_btn.setObjectName("addSubtaskBtn")
        self.add_btn.clicked.connect(self._on_add_subtask)
        button_layout.addWidget(self.add_btn)

        button_layout.addStretch()

        self.close_btn = QPushButton("닫기")
        self.close_btn.setObjectName("closeBtn")
        self.close_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.close_btn)

        layout.addLayout(button_layout)

    def _load_subtasks(self):
        """하위할일 목록 로드 및 표시"""
        # 기존 아이템 제거 (stretch 제외)
        while self.list_layout.count() > 1:
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 하위할일 추가 (인덱스와 총 개수 전달)
        total = len(self.todo.subtasks)
        for index, subtask in enumerate(self.todo.subtasks):
            self._add_subtask_item(subtask, index, total)

        # 설명 라벨 업데이트
        completed_count = sum(1 for st in self.todo.subtasks if st.completed)
        self.desc_label.setText(f"총 {len(self.todo.subtasks)}개의 하위 할일 ({completed_count}개 완료)")

    def _add_subtask_item(self, subtask, index, total):
        """개별 하위할일 아이템 위젯 생성

        Args:
            subtask: SubTask 객체
            index: 현재 아이템의 인덱스 (0부터 시작)
            total: 전체 하위 할일 개수
        """
        item_widget = QWidget()
        item_widget.setObjectName("subtaskItemWidget")
        item_layout = QHBoxLayout(item_widget)
        item_layout.setContentsMargins(12, 8, 12, 8)
        item_layout.setSpacing(10)

        # 순서 변경 버튼 (위/아래)
        order_layout = QVBoxLayout()
        order_layout.setSpacing(2)
        order_layout.setContentsMargins(0, 0, 0, 0)

        up_btn = QPushButton("▲")
        up_btn.setObjectName("subtaskMoveUpBtn")
        up_btn.setToolTip("위로 이동")
        up_btn.setFixedSize(20, 16)  # 최소 크기로 설정
        up_btn.setEnabled(index > 0)  # 첫 번째 아이템은 비활성화
        up_btn.clicked.connect(lambda checked, st=subtask: self._on_move_up(st.id))
        order_layout.addWidget(up_btn)

        down_btn = QPushButton("▼")
        down_btn.setObjectName("subtaskMoveDownBtn")
        down_btn.setToolTip("아래로 이동")
        down_btn.setFixedSize(20, 16)  # 최소 크기로 설정
        down_btn.setEnabled(index < total - 1)  # 마지막 아이템은 비활성화
        down_btn.clicked.connect(lambda checked, st=subtask: self._on_move_down(st.id))
        order_layout.addWidget(down_btn)

        item_layout.addLayout(order_layout)

        # 체크박스 (완료 상태)
        checkbox = QCheckBox()
        checkbox.setChecked(subtask.completed)
        checkbox.setObjectName("subtaskCheckbox")
        checkbox.stateChanged.connect(lambda state, st=subtask: self._on_toggle_subtask(st.id, state == Qt.CheckState.Checked.value))
        item_layout.addWidget(checkbox)

        # 내용 텍스트
        content_label = QLabel(str(subtask.content))
        content_label.setObjectName("subtaskContentLabel")
        content_label.setWordWrap(True)
        if subtask.completed:
            content_label.setStyleSheet(f"text-decoration: line-through; color: {config.COLORS['text_disabled']};")
        else:
            content_label.setStyleSheet(f"color: {config.COLORS['text_primary']};")
        item_layout.addWidget(content_label, 1)

        # 납기일 표시 (있는 경우) - 메인 할일과 동일한 배지 스타일
        if subtask.due_date:
            due_label = QLabel(subtask.due_date.format_display_text())
            due_label.setObjectName("subtaskDueLabel")
            due_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

            # 상태 계산 및 색상 적용
            status = subtask.due_date.calculate_status()
            bg_color = config.DUE_DATE_COLORS.get(status, config.DUE_DATE_COLORS['normal'])['bg']
            text_color = config.DUE_DATE_COLORS.get(status, config.DUE_DATE_COLORS['normal'])['color']

            # 메인 할일과 동일한 배지 스타일 적용
            due_label.setStyleSheet(f"""
                background: {bg_color};
                color: {text_color};
                font-size: {config.FONT_SIZES['sm']}px;
                padding: {config.UI_METRICS['padding']['sm'][0]}px {config.UI_METRICS['padding']['sm'][1]}px;
                border-radius: {config.UI_METRICS['border_radius']['sm']}px;
                font-weight: 500;
            """)
            item_layout.addWidget(due_label)

        # 편집 버튼
        edit_btn = QPushButton("편집")
        edit_btn.setObjectName("subtaskEditBtn")
        edit_btn.clicked.connect(lambda checked, st=subtask: self._on_edit_subtask(st.id))
        item_layout.addWidget(edit_btn)

        # 삭제 버튼
        delete_btn = QPushButton("삭제")
        delete_btn.setObjectName("subtaskDeleteBtn")
        delete_btn.clicked.connect(lambda checked, st=subtask: self._on_delete_subtask(st.id))
        item_layout.addWidget(delete_btn)

        # 리스트에 추가 (stretch 앞에)
        self.list_layout.insertWidget(self.list_layout.count() - 1, item_widget)

    def _on_add_subtask(self):
        """하위할일 추가"""
        from .edit_dialog import SubTaskEditDialog
        dialog = SubTaskEditDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            content, due_date = dialog.get_data()

            # DueDate 변환
            from ...domain.value_objects.due_date import DueDate
            due_date_vo = DueDate.from_string(due_date) if due_date else None

            # 서비스를 통해 추가
            self.todo_service.add_subtask(
                parent_todo_id=self.todo.id,
                content_str=content,
                due_date=due_date_vo
            )

            # TODO 객체 갱신
            self._refresh_todo()

            # UI 새로고침
            self._load_subtasks()

            # 시그널 발생
            self.subtasks_updated.emit()

    def _on_edit_subtask(self, subtask_id):
        """하위할일 편집

        Args:
            subtask_id: 하위할일 ID (TodoId 객체)
        """
        # 해당 subtask 찾기
        subtask = self.todo.get_subtask(subtask_id)
        if not subtask:
            return

        from .edit_dialog import SubTaskEditDialog
        dialog = SubTaskEditDialog(self)
        due_date_str = subtask.due_date.value.isoformat() if subtask.due_date else None
        dialog.set_data(str(subtask.content), due_date_str)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            content, due_date = dialog.get_data()

            # DueDate 변환
            from ...domain.value_objects.due_date import DueDate
            due_date_vo = DueDate.from_string(due_date) if due_date else None

            # 서비스를 통해 업데이트
            self.todo_service.update_subtask(
                parent_todo_id=self.todo.id,
                subtask_id=subtask_id,
                content_str=content,
                due_date=due_date_vo
            )

            # TODO 객체 갱신
            self._refresh_todo()

            # UI 새로고침
            self._load_subtasks()

            # 시그널 발생
            self.subtasks_updated.emit()

    def _on_delete_subtask(self, subtask_id):
        """하위할일 삭제

        Args:
            subtask_id: 하위할일 ID (TodoId 객체)
        """
        # 확인 다이얼로그
        reply = QMessageBox.question(
            self,
            "삭제 확인",
            "이 하위 할일을 삭제하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # 서비스를 통해 삭제
            self.todo_service.delete_subtask(self.todo.id, subtask_id)

            # TODO 객체 갱신
            self._refresh_todo()

            # UI 새로고침
            self._load_subtasks()

            # 시그널 발생
            self.subtasks_updated.emit()

    def _on_move_up(self, subtask_id):
        """하위할일을 위로 이동

        Args:
            subtask_id: 하위할일 ID (TodoId 객체)
        """
        # 현재 순서에서 인덱스 찾기
        current_ids = [st.id for st in self.todo.subtasks]
        current_index = None
        for i, sid in enumerate(current_ids):
            if str(sid) == str(subtask_id):
                current_index = i
                break

        if current_index is None or current_index == 0:
            return  # 이동 불가

        # 순서 교환
        current_ids[current_index], current_ids[current_index - 1] =             current_ids[current_index - 1], current_ids[current_index]

        # 서비스를 통해 순서 저장
        self.todo_service.reorder_subtasks(self.todo.id, current_ids)

        # TODO 객체 갱신
        self._refresh_todo()

        # UI 새로고침
        self._load_subtasks()

        # 시그널 발생
        self.subtasks_updated.emit()

    def _on_move_down(self, subtask_id):
        """하위할일을 아래로 이동

        Args:
            subtask_id: 하위할일 ID (TodoId 객체)
        """
        # 현재 순서에서 인덱스 찾기
        current_ids = [st.id for st in self.todo.subtasks]
        current_index = None
        for i, sid in enumerate(current_ids):
            if str(sid) == str(subtask_id):
                current_index = i
                break

        if current_index is None or current_index >= len(current_ids) - 1:
            return  # 이동 불가

        # 순서 교환
        current_ids[current_index], current_ids[current_index + 1] =             current_ids[current_index + 1], current_ids[current_index]

        # 서비스를 통해 순서 저장
        self.todo_service.reorder_subtasks(self.todo.id, current_ids)

        # TODO 객체 갱신
        self._refresh_todo()

        # UI 새로고침
        self._load_subtasks()

        # 시그널 발생
        self.subtasks_updated.emit()

    def _on_toggle_subtask(self, subtask_id, checked):
        """하위할일 완료 상태 토글

        Args:
            subtask_id: 하위할일 ID (TodoId 객체)
            checked: 체크 상태
        """
        # 서비스를 통해 토글
        self.todo_service.toggle_subtask_complete(self.todo.id, subtask_id)

        # TODO 객체 갱신
        self._refresh_todo()

        # UI 새로고침
        self._load_subtasks()

        # 시그널 발생
        self.subtasks_updated.emit()

    def _refresh_todo(self):
        """TODO 객체를 저장소에서 다시 조회"""
        # 저장소에서 최신 상태 조회
        from src.core.container import Container, ServiceNames
        repository = Container.resolve(ServiceNames.TODO_REPOSITORY)
        updated_todo = repository.find_by_id(self.todo.id)
        if updated_todo:
            self.todo = updated_todo

    def showEvent(self, event):
        """다이얼로그 표시 시 QPalette 적용"""
        super().showEvent(event)
        if not self._palette_applied:
            palette = create_dialog_palette()
            apply_palette_recursive(self, palette)
            self._palette_applied = True

    def keyPressEvent(self, event):
        """ESC로 닫기"""
        if event.key() == Qt.Key.Key_Escape:
            self.accept()
        else:
            super().keyPressEvent(event)

    def _apply_styles(self):
        """스타일 적용"""
        self.setStyleSheet(f"""
            QDialog {{
                background: {config.COLORS['secondary_bg']};
                border-radius: {config.UI_METRICS['border_radius']['xl']}px;
            }}

            /* Scroll Area */
            QScrollArea {{
                background: transparent;
                border: none;
            }}

            QScrollBar:vertical {{
                background: {config.COLORS['secondary_bg']};
                width: 10px;
                border-radius: 5px;
                margin: 0px;
            }}

            QScrollBar::handle:vertical {{
                background: {config.COLORS['border_strong']};
                min-height: 20px;
                border-radius: 5px;
            }}

            QScrollBar::handle:vertical:hover {{
                background: {config.COLORS['accent']};
            }}

            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}

            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}

            QLabel#titleLabel {{
                color: {config.COLORS['text_primary']};
                font-size: {config.FONT_SIZES['xxl']}px;
                font-weight: 600;
            }}

            QLabel#descLabel {{
                color: {config.COLORS['text_secondary']};
                font-size: {config.FONT_SIZES['base']}px;
            }}

            QWidget#subtaskItemWidget {{
                background: {config.COLORS['card']};
                border: {config.UI_METRICS['border_width']['thin']}px solid {config.COLORS['border']};
                border-radius: {config.UI_METRICS['border_radius']['lg']}px;
            }}

            QWidget#subtaskItemWidget:hover {{
                border-color: {config.COLORS['accent']};
            }}

            QPushButton#addSubtaskBtn {{
                background: transparent;
                border: {config.UI_METRICS['border_width']['thin']}px dashed {config.COLORS['border']};
                border-radius: {config.UI_METRICS['border_radius']['lg']}px;
                padding: {config.UI_METRICS['padding']['md'][0]}px {config.UI_METRICS['padding']['md'][1]}px;
                color: {config.COLORS['text_secondary']};
                font-size: {config.FONT_SIZES['base']}px;
                min-width: 150px;
            }}

            QPushButton#addSubtaskBtn:hover {{
                border-color: {config.COLORS['accent']};
                color: {config.COLORS['text_primary']};
            }}

            QPushButton#closeBtn {{
                background: {config.COLORS['accent']};
                color: white;
                border: none;
                border-radius: {config.UI_METRICS['border_radius']['lg']}px;
                padding: {config.UI_METRICS['padding']['lg'][0]}px {config.UI_METRICS['padding']['lg'][1]}px;
                font-weight: 500;
                font-size: {config.FONT_SIZES['base']}px;
                min-width: 80px;
            }}

            QPushButton#closeBtn:hover {{
                background: {config.COLORS['accent_hover']};
            }}

            QPushButton#closeBtn:pressed {{
                background: #B56B4A;
            }}

            QPushButton#subtaskEditBtn, QPushButton#subtaskDeleteBtn {{
                background: transparent;
                border: {config.UI_METRICS['border_width']['thin']}px solid {config.COLORS['border']};
                border-radius: {config.UI_METRICS['border_radius']['sm']}px;
                padding: 4px 12px;
                color: {config.COLORS['text_secondary']};
                font-size: {config.FONT_SIZES['sm']}px;
                min-width: 50px;
            }}

            QPushButton#subtaskEditBtn:hover {{
                border-color: {config.COLORS['accent']};
                color: {config.COLORS['text_primary']};
            }}

            QPushButton#subtaskDeleteBtn:hover {{
                border-color: #ef5350;
                color: #ef5350;
            }}

            QPushButton#subtaskMoveUpBtn, QPushButton#subtaskMoveDownBtn {{
                background: transparent;
                border: {config.UI_METRICS['border_width']['thin']}px solid {config.COLORS['border']};
                border-radius: {config.UI_METRICS['border_radius']['sm']}px;
                padding: 0px 2px;
                color: {config.COLORS['text_secondary']};
                font-size: {config.FONT_SIZES['xs']}px;
                min-width: 20px;
                max-width: 20px;
                min-height: 16px;
                max-height: 16px;
            }}

            QPushButton#subtaskMoveUpBtn:hover, QPushButton#subtaskMoveDownBtn:hover {{
                border-color: {config.COLORS['accent']};
                color: {config.COLORS['accent']};
                background: {config.COLORS['secondary_bg']};
            }}

            QPushButton#subtaskMoveUpBtn:disabled, QPushButton#subtaskMoveDownBtn:disabled {{
                color: {config.COLORS['text_disabled']};
                border-color: {config.COLORS['border']};
                background: transparent;
            }}

            QCheckBox#subtaskCheckbox {{
                spacing: 8px;
            }}

            QCheckBox#subtaskCheckbox::indicator {{
                width: 18px;
                height: 18px;
                border: {config.UI_METRICS['border_width']['thin']}px solid {config.COLORS['border']};
                background: {config.COLORS['secondary_bg']};
                border-radius: {config.UI_METRICS['border_radius']['sm']}px;
            }}

            QCheckBox#subtaskCheckbox::indicator:hover {{
                border-color: {config.COLORS['accent']};
            }}

            QCheckBox#subtaskCheckbox::indicator:checked {{
                background: {config.COLORS['accent']};
                border-color: {config.COLORS['accent']};
            }}
        """)
