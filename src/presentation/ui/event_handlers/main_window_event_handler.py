# -*- coding: utf-8 -*-
"""
MainWindow 이벤트 핸들러

MainWindow의 모든 이벤트 처리 로직을 담당합니다.
- TODO 추가/수정/삭제/체크박스
- 정렬 변경
- 드래그앤드롭
- Splitter 이동 (throttle)
- 백업 관리 다이얼로그
"""
from typing import Optional, List
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QDialog
import logging

from src.domain.entities.todo import Todo
from src.infrastructure.utils.debounce_manager import DebounceManager
from src.presentation.dialogs.backup_manager_dialog import BackupManagerDialog

logger = logging.getLogger(__name__)


class MainWindowEventHandler:
    """MainWindow 이벤트 핸들러

    MainWindow의 모든 이벤트 처리 로직을 담당합니다.
    """

    def __init__(
        self,
        main_window,
        repository,
        todo_service,
        header_widget,
        in_progress_section,
        completed_section,
        footer_widget,
        splitter
    ):
        """EventHandler 초기화

        Args:
            main_window: MainWindow 인스턴스
            repository: TODO 및 설정 저장을 위한 Repository
            todo_service: TODO 비즈니스 로직 서비스
            header_widget: 헤더 위젯
            in_progress_section: 진행중 섹션 위젯
            completed_section: 완료 섹션 위젯
            footer_widget: 푸터 위젯
            splitter: 섹션 분할 Splitter
        """
        self.main_window = main_window
        self.repository = repository
        self.todo_service = todo_service
        self.header_widget = header_widget
        self.in_progress_section = in_progress_section
        self.completed_section = completed_section
        self.footer_widget = footer_widget
        self.splitter = splitter

        # EditDialog 인스턴스 (재사용)
        self.edit_dialog = None

        # Splitter throttle (100ms)
        self._pending_split_ratio: Optional[tuple[float, float]] = None
        self._split_throttler = DebounceManager(
            delay_ms=100,
            callback=self._execute_split_ratio_save
        )

    def connect_signals(self) -> None:
        """시그널과 슬롯 연결"""
        # 헤더: 할일 추가 (추가 버튼만 사용)
        self.header_widget.add_button.clicked.connect(self.on_add_todo)

        # 헤더: 정렬 변경
        self.header_widget.sort_combo.currentIndexChanged.connect(self.on_sort_changed)

        # 섹션: TODO 이벤트
        self.in_progress_section.todo_deleted.connect(self.on_todo_delete)
        self.in_progress_section.todo_check_toggled.connect(self.on_todo_check_toggled)
        self.in_progress_section.todo_edit_requested.connect(self.on_todo_edit)
        self.in_progress_section.todo_reordered.connect(self.on_todo_reorder)

        self.completed_section.todo_deleted.connect(self.on_todo_delete)
        self.completed_section.todo_check_toggled.connect(self.on_todo_check_toggled)
        self.completed_section.todo_edit_requested.connect(self.on_todo_edit)
        self.completed_section.todo_reordered.connect(self.on_todo_reorder)

        # Splitter 이동
        self.splitter.splitterMoved.connect(self.on_splitter_moved)

        # Footer: 관리 버튼 연결
        self.footer_widget.manage_clicked.connect(self._on_manage_clicked)

    def on_splitter_moved(self, pos: int, index: int) -> None:
        """Splitter 이동 이벤트 (Throttle 100ms)

        Args:
            pos: Splitter 핸들의 위치
            index: Splitter 핸들의 인덱스
        """
        # 현재 섹션 크기 가져오기
        sizes = self.splitter.sizes()
        total = sum(sizes)

        if total > 0:
            # 비율 계산
            in_progress_ratio = sizes[0] / total
            completed_ratio = sizes[1] / total

            # Pending 비율 저장 (마지막 값만 유지)
            self._pending_split_ratio = (in_progress_ratio, completed_ratio)

            # Throttle: is_active()면 무시
            if not self._split_throttler.is_active():
                self._split_throttler.schedule()
                logger.debug(f"Splitter save queued (throttle 100ms): sizes={sizes}, ratios=[{in_progress_ratio:.2f}, {completed_ratio:.2f}]")

    def _execute_split_ratio_save(self, data=None) -> None:
        """Throttle 완료 시 실제 저장"""
        if not self._pending_split_ratio:
            logger.debug("No pending split ratio to save")
            return

        in_progress_ratio, completed_ratio = self._pending_split_ratio
        self._pending_split_ratio = None

        # repository를 통한 저장
        try:
            self.repository.update_settings({
                "splitRatio": [in_progress_ratio, completed_ratio]
            })
            logger.debug(f"Throttled save executed: [{in_progress_ratio:.2f}, {completed_ratio:.2f}]")
        except Exception as e:
            logger.error(f"Failed to save split ratio: {e}")

    def load_todos(self) -> None:
        """초기 TODO 로드 및 UI 업데이트"""
        try:
            # 저장된 정렬 순서 가져오기
            sort_order = "dueDate_asc"  # 기본값
            if self.repository:
                settings = self.repository.get_settings()
                sort_order = settings.get("sortOrder", "dueDate_asc")

            # 드롭다운 선택 (시그널 발생 방지)
            index = self.header_widget.sort_combo.findData(sort_order)
            if index >= 0:
                # currentIndexChanged 시그널 일시 차단
                self.header_widget.sort_combo.blockSignals(True)
                self.header_widget.sort_combo.setCurrentIndex(index)
                self.header_widget.sort_combo.blockSignals(False)

            # DI Container에서 TodoSortUseCase 조회
            from src.core.container import Container, ServiceNames
            sort_use_case = Container.resolve(ServiceNames.TODO_SORT_USE_CASE)

            # 정렬 실행
            in_progress_todos, completed_todos = sort_use_case.execute(sort_order)

            # UI 갱신
            self._refresh_ui(in_progress_todos, completed_todos)

            logger.info(f"Todos loaded and sorted: {len(in_progress_todos) + len(completed_todos)} total, order: {sort_order}")

        except Exception as e:
            logger.error(f"Failed to load todos: {e}", exc_info=True)

    def _refresh_ui(self, in_progress_todos: List[Todo], completed_todos: List[Todo]) -> None:
        """정렬된 TODO 리스트를 UI에 반영 (DRY 원칙 - 중복 제거)

        Args:
            in_progress_todos: 진행중 TODO 리스트
            completed_todos: 완료 TODO 리스트
        """
        # 섹션 초기화
        self.in_progress_section.clear_all()
        self.completed_section.clear_all()

        # 정렬된 TODO 추가
        for todo in in_progress_todos:
            self.in_progress_section.add_todo(todo)

        for todo in completed_todos:
            self.completed_section.add_todo(todo)

        # Footer 카운트 업데이트
        in_progress_count = len(self.in_progress_section.todo_items)
        completed_count = len(self.completed_section.todo_items)
        self.footer_widget.update_counts(in_progress_count, completed_count)

    def _refresh_ui_without_sorting(self) -> None:
        """현재 order대로 UI 갱신 (정렬 없음 - 드래그 앤 드롭용)

        Repository에서 TODO를 조회하여 order 필드 순서대로 UI를 갱신합니다.
        정렬 설정(sortOrder)을 적용하지 않으므로 드래그 앤 드롭 후 위치가 유지됩니다.
        """
        # Repository에서 모든 TODO 조회
        all_todos = self.repository.find_all()

        # 섹션별로 분리하고 order 순으로 정렬
        in_progress = sorted(
            [todo for todo in all_todos if not todo.completed],
            key=lambda t: t.order
        )
        completed = sorted(
            [todo for todo in all_todos if todo.completed],
            key=lambda t: t.order
        )

        # UI 갱신 (DRY - _refresh_ui 재사용)
        self._refresh_ui(in_progress, completed)

        logger.debug(f"UI refreshed without sorting: {len(in_progress) + len(completed)} todos")

    def on_sort_changed(self, index: int) -> None:
        """정렬 순서 변경 핸들러

        Args:
            index: 드롭다운 인덱스
        """
        try:
            # 드롭다운에서 정렬 순서 가져오기
            sort_order = self.header_widget.sort_combo.currentData()

            if not sort_order:
                logger.warning("No sort order selected")
                return

            logger.debug(f"Sort order changed to: {sort_order}")

            # DI Container에서 ChangeSortOrderUseCase 조회
            from src.core.container import Container, ServiceNames
            change_sort_order_use_case = Container.resolve(ServiceNames.CHANGE_SORT_ORDER_USE_CASE)

            # ChangeSortOrderUseCase 호출하여 order 동기화
            change_sort_order_use_case.execute(sort_order)
            logger.info(f"Order synchronized via ChangeSortOrderUseCase for: {sort_order}")

            # DI Container에서 TodoSortUseCase 조회
            sort_use_case = Container.resolve(ServiceNames.TODO_SORT_USE_CASE)

            # 정렬 실행
            in_progress_todos, completed_todos = sort_use_case.execute(sort_order)

            # UI 갱신
            self._refresh_ui(in_progress_todos, completed_todos)

            # 정렬 순서를 설정에 저장
            if self.repository:
                self.repository.update_settings({"sortOrder": sort_order})

            logger.info(f"Todos sorted by: {sort_order}")

        except Exception as e:
            logger.error(f"Failed to sort todos: {e}", exc_info=True)

    def on_add_todo(self) -> None:
        """할일 추가 핸들러 (다이얼로그 사용)"""
        try:
            # EditDialog 생성 (없으면) 또는 재사용
            if not self.edit_dialog:
                from src.presentation.dialogs.edit_dialog import EditDialog
                self.edit_dialog = EditDialog(self.main_window)
                # save_requested 시그널 연결
                self.edit_dialog.save_requested.connect(self.on_edit_save)

            # 다이얼로그에 초기 데이터 설정 (todo_id=None이면 신규 추가 모드, content는 빈 문자열)
            self.edit_dialog.set_todo(None, "", None)

            # 다이얼로그 표시 (모달)
            self.edit_dialog.exec()

        except Exception as e:
            logger.error(f"Failed to open add dialog: {e}", exc_info=True)

    def on_todo_delete(self, todo_id: str) -> None:
        """TODO 삭제 핸들러"""
        try:
            # 삭제 확인 (나중에 다이얼로그 추가)
            self.todo_service.delete_todo(todo_id)
            logger.info(f"Todo deleted: {todo_id}")

            # UI에서 제거
            self.in_progress_section.remove_todo(todo_id)
            self.completed_section.remove_todo(todo_id)

            # Footer 카운트 업데이트
            in_progress_count = len(self.in_progress_section.todo_items)
            completed_count = len(self.completed_section.todo_items)
            self.footer_widget.update_counts(in_progress_count, completed_count)

            logger.debug("Todo removed from UI")
        except Exception as e:
            logger.error(f"Failed to delete todo: {e}", exc_info=True)

    def on_todo_check_toggled(self, todo_id: str, completed: bool) -> None:
        """TODO 체크박스 토글 핸들러"""
        try:
            # 완료 상태 토글
            self.todo_service.toggle_complete(todo_id)
            logger.info(f"Todo completion toggled: {todo_id}, completed: {completed}")

            # TODO 다시 로드하여 UI 업데이트
            self.load_todos()
        except Exception as e:
            logger.error(f"Failed to toggle todo completion: {e}", exc_info=True)

    def on_todo_edit(self, todo_id: str) -> None:
        """TODO 편집 핸들러

        Args:
            todo_id: 편집할 TODO ID
        """
        try:
            # 1. TodoService에서 해당 TODO 조회
            todo = None
            for t in self.todo_service.get_all_todos():
                if str(t.id) == todo_id:
                    todo = t
                    break

            if not todo:
                logger.error(f"TODO not found for edit: {todo_id}")
                return

            # 2. EditDialog 생성 (없으면) 또는 재사용
            if not self.edit_dialog:
                from src.presentation.dialogs.edit_dialog import EditDialog
                self.edit_dialog = EditDialog(self.main_window)
                # save_requested 시그널 연결
                self.edit_dialog.save_requested.connect(self.on_edit_save)

            # 3. 다이얼로그에 TODO 데이터 설정
            due_date_str = todo.due_date.value.isoformat() if todo.due_date else None
            self.edit_dialog.set_todo(todo_id, str(todo.content), due_date_str)

            # 4. 다이얼로그 표시 (모달)
            self.edit_dialog.exec()

        except Exception as e:
            logger.error(f"Failed to open edit dialog: {e}", exc_info=True)

    def on_edit_save(self, todo_id: str, content: str, due_date: str) -> None:
        """편집/추가 저장 핸들러

        Args:
            todo_id: TODO ID (빈 문자열이면 신규 추가)
            content: 새 내용
            due_date: 새 납기일 (ISO 문자열, 빈 문자열이면 None)
        """
        try:
            # due_date가 빈 문자열이면 None으로 변환
            due_date_value = due_date if due_date else None

            # todo_id가 빈 문자열이면 신규 추가
            if not todo_id:
                # 신규 TODO 생성
                new_todo = self.todo_service.create_todo(content, due_date_value)
                logger.info(f"New todo created: {new_todo.id}, content: {content}, due_date: {due_date_value}")

                # UI 갱신 (정렬 순서 유지)
                self.load_todos()
            else:
                # 기존 TODO 수정
                self.todo_service.update_todo(todo_id, content, due_date_value)
                logger.info(f"Todo updated: {todo_id}")

                # UI 갱신
                self.load_todos()

        except Exception as e:
            logger.error(f"Failed to save todo: {e}", exc_info=True)

    def on_todo_reorder(self, todo_id: str, new_position: int, section: str) -> None:
        """TODO 순서 변경 핸들러

        드래그 앤 드롭으로 순서 변경 시 order 필드를 업데이트하고,
        자동으로 MANUAL 모드로 전환합니다.

        Args:
            todo_id: 이동할 TODO ID
            new_position: 새 위치
            section: 섹션 타입 ("in_progress" 또는 "completed")
        """
        try:
            from src.core.container import Container, ServiceNames
            reorder_use_case = Container.resolve(ServiceNames.REORDER_TODO_USE_CASE)

            # 순서 변경 실행 (order 업데이트 + sortOrder를 'manual'로 자동 전환)
            reorder_use_case.execute(todo_id, new_position, section)
            logger.info(f"Todo reordered successfully, switched to MANUAL mode")

            # 드롭다운 UI를 "manual"로 변경 (시그널 발생 방지)
            index = self.header_widget.sort_combo.findData("manual")
            if index >= 0:
                self.header_widget.sort_combo.blockSignals(True)
                self.header_widget.sort_combo.setCurrentIndex(index)
                self.header_widget.sort_combo.blockSignals(False)

            # UI 갱신 (order 순서대로 표시)
            QTimer.singleShot(0, self._refresh_ui_without_sorting)

        except Exception as e:
            logger.error(f"Failed to reorder todo: {e}", exc_info=True)

    def _on_manage_clicked(self) -> None:
        """관리 버튼 클릭 → BackupManagerDialog 표시

        다이얼로그가 Accepted로 닫히면 TODO 목록을 갱신합니다.
        (백업 복구 또는 삭제 작업 후)
        """
        try:
            dialog = BackupManagerDialog(
                parent=self.main_window,
                repository=self.repository,
                todo_service=self.todo_service
            )

            result = dialog.exec()

            if result == QDialog.DialogCode.Accepted:
                # 변경사항이 있으면 UI 갱신
                logger.info("BackupManagerDialog closed with changes, refreshing UI")
                self.load_todos()

        except Exception as e:
            logger.error(f"Failed to open backup manager dialog: {e}", exc_info=True)
