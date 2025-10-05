# -*- coding: utf-8 -*-
"""SectionWidget - TODO 섹션 위젯 (진행중/완료)

Phase 5-3: 진행중/완료 섹션 및 분할바 구현
docs/todo-app-ui.html의 .section 구조를 정확히 재현합니다.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDragMoveEvent, QDropEvent
from typing import List

import config
from ...domain.entities.todo import Todo
from .todo_item_widget import TodoItemWidget


class SectionWidget(QWidget):
    """TODO 섹션 위젯

    UI 구조:
    - 섹션 헤더 (타이틀 + 카운트)
    - QScrollArea (독립적 스크롤)
      - 컨테이너 위젯
        - TODO 아이템 리스트

    Signals:
        todo_deleted(str): TODO 삭제 요청 (todo_id)
        todo_check_toggled(str, bool): 체크박스 토글 (todo_id, completed)
        todo_edit_requested(str): TODO 편집 요청 (todo_id)
    """

    # 시그널 정의
    todo_deleted = pyqtSignal(str)
    todo_check_toggled = pyqtSignal(str, bool)
    todo_edit_requested = pyqtSignal(str)
    todo_reordered = pyqtSignal(str, int, str)  # (todo_id, new_position, section)

    def __init__(self, title: str, parent=None):
        """SectionWidget 초기화

        Args:
            title: 섹션 타이틀 ("진행중" 또는 "완료")
            parent: 부모 위젯
        """
        super().__init__(parent)
        self.title = title
        self.todo_items: List[TodoItemWidget] = []

        self.setup_ui()
        self.apply_styles()

    def setup_ui(self) -> None:
        """UI 요소 생성 및 배치"""
        # 메인 레이아웃 (수직)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. 섹션 헤더 (타이틀 + 카운트)
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(*config.LAYOUT_MARGINS['section_header'])
        header_layout.setSpacing(0)

        # 타이틀 + 카운트 컨테이너
        title_container = QHBoxLayout()
        title_container.setSpacing(config.LAYOUT_SPACING['section_title'])

        self.title_label = QLabel(self.title)
        self.title_label.setObjectName("sectionTitle")
        title_container.addWidget(self.title_label)

        self.count_label = QLabel("0")
        self.count_label.setObjectName("sectionCount")
        title_container.addWidget(self.count_label)
        title_container.addStretch()

        header_layout.addLayout(title_container)

        # 헤더 컨테이너 위젯
        header_widget = QWidget()
        header_widget.setObjectName("sectionHeader")
        header_widget.setLayout(header_layout)
        main_layout.addWidget(header_widget)

        # 2. 스크롤 영역 (독립적 스크롤)
        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("sectionScrollArea")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # 스크롤 영역 내부 컨테이너
        self.items_container = QWidget()
        self.items_container.setObjectName("itemsContainer")

        self.items_layout = QVBoxLayout(self.items_container)
        self.items_layout.setContentsMargins(*config.LAYOUT_MARGINS['section_items'])
        self.items_layout.setSpacing(config.LAYOUT_SPACING['section_items'])
        self.items_layout.addStretch()  # 하단 공간 확보

        self.scroll_area.setWidget(self.items_container)
        main_layout.addWidget(self.scroll_area, 1)  # stretch factor = 1

        # 위젯 자체 설정
        self.setObjectName("sectionWidget")
        # 섹션별 최소 높이 설정 (config에서 관리)
        min_height = config.SECTION_UI['completed_min_height'] if self.title == "완료" else config.SECTION_UI['in_progress_min_height']
        self.setMinimumHeight(min_height)

        # 드래그 앤 드롭 활성화
        self.setAcceptDrops(True)

    def add_todo(self, todo: Todo) -> None:
        """TODO 아이템 추가

        Args:
            todo: Todo Entity
        """
        # TodoItemWidget 생성
        todo_item = TodoItemWidget(todo)

        # 시그널 연결 (릴레이)
        todo_item.delete_requested.connect(self.todo_deleted.emit)
        todo_item.check_toggled.connect(self.todo_check_toggled.emit)
        todo_item.edit_requested.connect(self.todo_edit_requested.emit)

        # 레이아웃에 추가 (stretch 위에)
        self.items_layout.insertWidget(len(self.todo_items), todo_item)
        self.todo_items.append(todo_item)

        # 카운트 업데이트
        self.update_count()

    def remove_todo(self, todo_id: str) -> None:
        """TODO 아이템 제거

        Args:
            todo_id: TODO ID
        """
        for i, todo_item in enumerate(self.todo_items):
            if str(todo_item.todo.id) == todo_id:
                # 레이아웃에서 제거
                self.items_layout.removeWidget(todo_item)
                todo_item.deleteLater()

                # 리스트에서 제거
                self.todo_items.pop(i)

                # 카운트 업데이트
                self.update_count()
                break

    def update_count(self) -> None:
        """카운트 업데이트"""
        count = len(self.todo_items)
        self.count_label.setText(str(count))

    def clear_all(self) -> None:
        """모든 TODO 제거"""
        for todo_item in self.todo_items:
            self.items_layout.removeWidget(todo_item)
            todo_item.deleteLater()

        self.todo_items.clear()
        self.update_count()

    def get_todos(self) -> List[Todo]:
        """현재 섹션의 TODO 리스트 반환

        Returns:
            List[Todo]: TODO Entity 리스트
        """
        return [item.todo for item in self.todo_items]

    def apply_styles(self) -> None:
        """QSS 스타일 적용 (프로토타입 정확히 재현)"""
        style_sheet = f"""
        QWidget#sectionWidget {{
            background: transparent;
        }}

        QWidget#sectionHeader {{
            background: transparent;
            border-bottom: 1px solid {config.COLORS['border']};
            padding-bottom: 6px;
            margin-bottom: 8px;
        }}

        QLabel#sectionTitle {{
            color: {config.COLORS['text_primary']};
            font-size: {config.FONT_SIZES['md']}px;
            font-weight: 600;
        }}

        QLabel#sectionCount {{
            background: #363636;
            color: {config.COLORS['text_secondary']};
            font-size: {config.FONT_SIZES['xs']}px;
            padding: {config.UI_METRICS['padding']['xs'][0]}px {config.UI_METRICS['padding']['xs'][1]}px;
            border-radius: {config.UI_METRICS['border_radius']['md']}px;
            font-weight: 500;
        }}

        QScrollArea#sectionScrollArea {{
            background: transparent;
            border: none;
        }}

        QWidget#itemsContainer {{
            background: transparent;
        }}

        /* 스크롤바 스타일 */
        QScrollArea#sectionScrollArea QScrollBar:vertical {{
            width: {config.WIDGET_SIZES['splitter_handle_width'] // 2}px;
            background: transparent;
        }}

        QScrollArea#sectionScrollArea QScrollBar::handle:vertical {{
            background: rgba(64, 64, 64, 0.5);
            border-radius: {config.UI_METRICS['border_radius']['sm'] - 1}px;
            min-height: 20px;
        }}

        QScrollArea#sectionScrollArea QScrollBar::handle:vertical:hover {{
            background: rgba(64, 64, 64, 0.7);
        }}

        QScrollArea#sectionScrollArea QScrollBar::add-line:vertical,
        QScrollArea#sectionScrollArea QScrollBar::sub-line:vertical {{
            height: 0px;
        }}

        QScrollArea#sectionScrollArea QScrollBar::add-page:vertical,
        QScrollArea#sectionScrollArea QScrollBar::sub-page:vertical {{
            background: transparent;
        }}
        """

        self.setStyleSheet(style_sheet)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """드래그 진입 이벤트 핸들러

        Args:
            event: 드래그 이벤트
        """
        # Mime Data에 텍스트(TODO ID)가 있는지 확인
        if event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        """드래그 이동 이벤트 핸들러

        Args:
            event: 드래그 이벤트
        """
        # Mime Data에 텍스트(TODO ID)가 있는지 확인
        if event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        """드롭 이벤트 핸들러

        Args:
            event: 드롭 이벤트
        """
        import logging
        logger = logging.getLogger(__name__)

        # Mime Data에서 TODO ID 추출
        todo_id = event.mimeData().text()
        if not todo_id:
            event.ignore()
            return

        # 드롭 위치 계산
        drop_position = event.position().toPoint()
        new_position = self._calculate_drop_position(drop_position)

        # 섹션 타입 결정
        section = "in_progress" if self.title == "진행중" else "completed"

        logger.info(f"[DropEvent] todo_id={todo_id[:8]}..., new_position={new_position}, section={section}")

        # 순서 변경 시그널 발생
        self.todo_reordered.emit(todo_id, new_position, section)

        logger.info(f"[DropEvent] Signal emitted, accepting event")
        event.acceptProposedAction()

    def _calculate_drop_position(self, drop_pos) -> int:
        """드롭 위치를 TODO 리스트의 인덱스로 변환

        Args:
            drop_pos: 드롭 위치 (QPoint)

        Returns:
            int: 새로운 위치 (0부터 시작하는 인덱스)
        """
        # 스크롤 영역의 컨텐츠 위젯 내에서의 상대 위치 계산
        # scroll_area -> items_container 내에서의 위치
        scroll_pos = self.scroll_area.mapFrom(self, drop_pos)
        content_pos = self.items_container.mapFrom(self.scroll_area.viewport(), scroll_pos)

        # 각 TODO 아이템과 비교하여 삽입 위치 결정
        for i, todo_item in enumerate(self.todo_items):
            item_rect = todo_item.geometry()
            item_center_y = item_rect.top() + item_rect.height() / 2

            # 드롭 위치가 아이템의 중앙보다 위에 있으면 해당 인덱스에 삽입
            if content_pos.y() < item_center_y:
                return i

        # 모든 아이템보다 아래면 맨 뒤에 삽입
        return len(self.todo_items)
