# -*- coding: utf-8 -*-
"""TodoService - TODO CRUD 비즈니스 로직"""

from typing import List, Optional
import logging
from ...domain.entities.todo import Todo
from ...domain.entities.subtask import SubTask
from ...domain.value_objects.todo_id import TodoId
from ...domain.value_objects.content import Content
from ...domain.value_objects.due_date import DueDate
from ...domain.value_objects.recurrence_rule import RecurrenceRule
from ...domain.services.recurrence_service import RecurrenceService
from ...domain.interfaces.repository_interface import ITodoRepository

# 로깅 설정
logger = logging.getLogger(__name__)


class TodoService:
    """Todo 비즈니스 로직을 처리하는 애플리케이션 서비스"""

    def __init__(self, repository: ITodoRepository):
        """TodoService 초기화

        Args:
            repository: TODO 리포지토리 구현체
        """
        self.repository = repository

    def _calculate_next_order(self) -> int:
        """진행중 TODO의 다음 order 값을 계산합니다 (공통 메서드).

        Returns:
            int: 다음 order 값
        """
        all_todos = self.repository.find_all()
        incomplete_todos = [todo for todo in all_todos if not todo.completed]

        if incomplete_todos:
            max_order = max(todo.order for todo in incomplete_todos)
            return max_order + 1
        return 0

    def _get_todo_or_raise(self, todo_id: TodoId) -> Todo:
        """Todo 조회 또는 에러 발생 (공통 헬퍼)

        Args:
            todo_id: Todo ID

        Returns:
            Todo: 찾은 Todo 인스턴스

        Raises:
            ValueError: Todo를 찾을 수 없는 경우
        """
        logger.info(f"[TodoService] TODO 조회: id={todo_id.value}")
        todo = self.repository.find_by_id(todo_id)
        if todo is None:
            logger.error(f"[TodoService] TODO 찾을 수 없음: id={todo_id.value}")
            raise ValueError(f"Todo with id {todo_id.value} not found")
        return todo

    def create_todo(self, content: str, due_date: Optional[str] = None) -> Todo:
        """새 TODO 생성

        Args:
            content: TODO 내용
            due_date: 납기일 (ISO 8601 문자열, 선택)

        Returns:
            Todo: 생성된 TODO

        Raises:
            ValueError: 유효하지 않은 입력인 경우
        """
        logger.info(f"[TodoService] TODO 생성 시작: content='{content[:50]}...', due_date={due_date}")

        # 다음 order 계산 (공통 메서드 재사용)
        next_order = self._calculate_next_order()

        # 새 TODO 생성
        new_todo = Todo.create(
            content=content,
            due_date=due_date,
            order=next_order
        )

        # 저장
        self.repository.save(new_todo)

        logger.info(f"[TodoService] TODO 생성 완료: id={new_todo.id.value}, order={next_order}")
        return new_todo

    def update_todo(self, todo_id: str, content: str, due_date: Optional[str] = None) -> None:
        """TODO 수정

        Args:
            todo_id: TODO ID (문자열)
            content: 새 내용
            due_date: 새 납기일 (ISO 8601 문자열, 선택)

        Raises:
            ValueError: TODO를 찾을 수 없는 경우
        """
        logger.info(f"[TodoService] TODO 수정 시작: id={todo_id}, content='{content[:50]}...', due_date={due_date}")

        # ID 변환
        todo_id_vo = TodoId.from_string(todo_id)

        # TODO 조회
        todo = self.repository.find_by_id(todo_id_vo)
        if todo is None:
            logger.error(f"[TodoService] TODO 찾을 수 없음: id={todo_id}")
            raise ValueError(f"TODO not found: {todo_id}")

        # 내용 수정
        content_vo = Content(value=content)
        todo.update_content(content_vo)

        # 납기일 수정
        due_date_vo = DueDate.from_string(due_date) if due_date else None
        todo.set_due_date(due_date_vo)

        # 저장
        self.repository.save(todo)

        logger.info(f"[TodoService] TODO 수정 완료: id={todo_id}")

    def delete_todo(self, todo_id: str) -> None:
        """TODO 삭제

        Args:
            todo_id: TODO ID (문자열)

        Raises:
            ValueError: TODO를 찾을 수 없는 경우
        """
        logger.info(f"[TodoService] TODO 삭제 시작: id={todo_id}")

        # ID 변환
        todo_id_vo = TodoId.from_string(todo_id)

        # 존재 확인
        todo = self.repository.find_by_id(todo_id_vo)
        if todo is None:
            logger.error(f"[TodoService] TODO 찾을 수 없음: id={todo_id}")
            raise ValueError(f"TODO not found: {todo_id}")

        # 삭제
        self.repository.delete(todo_id_vo)

        logger.info(f"[TodoService] TODO 삭제 완료: id={todo_id}")

    def toggle_complete(self, todo_id: str) -> None:
        """완료 상태 토글

        Notes:
            - 완료(False→True) 시 반복 할일이면 다음 인스턴스 자동 생성
            - 미완료(True→False) 시 아무 작업도 하지 않음
            - 하위 할일 복사 옵션(copy_subtasks)이 True면 하위 할일도 복사

        Args:
            todo_id: TODO ID (문자열)

        Raises:
            ValueError: TODO를 찾을 수 없는 경우
        """
        # ID 변환
        todo_id_vo = TodoId.from_string(todo_id)

        # TODO 조회
        todo = self.repository.find_by_id(todo_id_vo)
        if todo is None:
            logger.error(f"[TodoService] TODO 찾을 수 없음: id={todo_id}")
            raise ValueError(f"TODO not found: {todo_id}")

        # 완료 여부 확인 (토글 전)
        was_incomplete = not todo.completed

        # 완료 상태 토글
        if todo.completed:
            todo.uncomplete()
            logger.info(f"[TodoService] TODO 미완료로 변경: id={todo_id}")
        else:
            todo.complete()
            logger.info(f"[TodoService] TODO 완료로 변경: id={todo_id}")

        # 저장 (먼저 현재 TODO 저장)
        self.repository.save(todo)

        # 반복 할일 처리 (미완료 → 완료일 때만)
        if was_incomplete and todo.completed and todo.is_recurring():
            logger.info(f"[TodoService] 반복 할일 처리 시작: id={todo_id}, frequency={todo.recurrence.frequency}")

            # 다음 반복 날짜 계산
            next_due_date = RecurrenceService.calculate_next_occurrence(
                todo.due_date,
                todo.recurrence
            )

            # 새 TODO 생성
            next_order = self._calculate_next_order()
            new_todo = Todo.create(
                content=str(todo.content),
                due_date=str(next_due_date),
                order=next_order
            )

            # 반복 규칙 복사
            new_todo.set_recurrence(todo.recurrence)

            # 하위 할일 복사 (copy_subtasks가 True이고 하위 할일이 있을 때만)
            if todo.recurrence.copy_subtasks and todo.subtasks:
                # 메인 할일의 납기일 변경폭 계산 (상대적 조정용)
                delta = None
                if todo.due_date and next_due_date:
                    delta = next_due_date.value - todo.due_date.value

                for subtask in todo.subtasks:
                    # 하위 할일 납기일 상대적 조정
                    new_subtask_due_date = None
                    if subtask.due_date and delta:
                        # 납기일도 동일한 delta만큼 조정
                        adjusted_datetime = subtask.due_date.value + delta
                        new_subtask_due_date = DueDate(value=adjusted_datetime)

                    # SubTask 복사 (새 ID, completed=False로 초기화)
                    new_subtask = SubTask.create(
                        content=str(subtask.content),
                        due_date=str(new_subtask_due_date) if new_subtask_due_date else None,
                        order=subtask.order  # 순서는 유지
                    )
                    # P1-2 수정: add_subtask()는 반환값이 없으므로 재할당 불필요
                    new_todo.add_subtask(new_subtask)

                logger.info(
                    f"[TodoService] 반복 할일 생성 완료 (하위 할일 포함): "
                    f"new_id={new_todo.id.value}, subtasks={len(todo.subtasks)}, next_due_date={next_due_date}"
                )
            else:
                logger.info(
                    f"[TodoService] 반복 할일 생성 완료: "
                    f"new_id={new_todo.id.value}, next_due_date={next_due_date}"
                )

            # 새 TODO 저장
            self.repository.save(new_todo)

    def get_all_todos(self) -> List[Todo]:
        """전체 TODO 조회

        Returns:
            List[Todo]: 모든 TODO 리스트
        """
        return self.repository.find_all()

    def delete_completed_todos(self) -> int:
        """완료된 TODO만 일괄 삭제

        Returns:
            int: 삭제된 개수
        """
        logger.info("[TodoService] 완료된 TODO 일괄 삭제 시작")

        all_todos = self.repository.find_all()
        completed = [t for t in all_todos if t.completed]

        for todo in completed:
            self.repository.delete(todo.id)

        logger.info(f"[TodoService] 완료된 TODO 일괄 삭제 완료: {len(completed)}개")
        return len(completed)

    def delete_selected_todos(self, todo_ids: List[str]) -> int:
        """선택된 TODO 일괄 삭제

        Args:
            todo_ids: 삭제할 TODO ID 리스트 (문자열)

        Returns:
            int: 삭제된 개수
        """
        logger.info(f"[TodoService] 선택된 TODO 일괄 삭제 시작: {len(todo_ids)}개")

        count = 0
        for todo_id in todo_ids:
            try:
                self.delete_todo(todo_id)  # 기존 메서드 재사용
                count += 1
            except ValueError:
                # TODO를 찾을 수 없는 경우 건너뛰기
                logger.warning(f"[TodoService] TODO 찾을 수 없어 건너뜀: id={todo_id}")
                pass

        logger.info(f"[TodoService] 선택된 TODO 일괄 삭제 완료: {count}개")
        return count

    def restore_selected_todos(self, todos: List[Todo]) -> int:
        """선택된 TODO들을 현재 목록에 복구합니다.

        Args:
            todos: 복구할 TODO 리스트

        Returns:
            int: 실제로 복구된 개수
        """
        logger.info(f"[TodoService] TODO 복구 시작: {len(todos)}개")

        # 1. 현재 TODO 목록 조회
        all_todos = self.repository.find_all()

        # 2. 기존 ID 목록 (중복 체크용)
        existing_ids = {todo.id for todo in all_todos}

        # 3. 다음 order 계산 (공통 메서드 재사용)
        next_order = self._calculate_next_order()

        # 4. TODO 복구
        restored_count = 0
        for todo in todos:
            # 중복 체크
            if todo.id in existing_ids:
                logger.warning(f"[TodoService] TODO 이미 존재, 건너뜀: id={todo.id}")
                continue

            # order 재조정 (진행중 TODO만)
            if not todo.completed:
                todo.change_order(next_order)
                next_order += 1

            # 저장 (repository.save 재사용)
            self.repository.save(todo)
            restored_count += 1

        logger.info(f"[TodoService] TODO 복구 완료: {restored_count}개")
        return restored_count

    # ========================================
    # 반복 할일 관련 메서드
    # ========================================

    def set_recurrence(
        self,
        todo_id: str,
        recurrence_rule: Optional[RecurrenceRule]
    ) -> None:
        """TODO에 반복 규칙 설정

        Args:
            todo_id: TODO ID (문자열)
            recurrence_rule: 설정할 반복 규칙 (None이면 반복 제거)

        Raises:
            ValueError: todo_id에 해당하는 TODO를 찾을 수 없는 경우
            ValueError: recurrence_rule이 있는데 due_date가 없는 경우

        Notes:
            - 반복 할일은 반드시 납기일이 있어야 함
            - recurrence_rule이 None이면 반복 제거
        """
        logger.info(
            f"[TodoService] 반복 규칙 설정: id={todo_id}, "
            f"frequency={recurrence_rule.frequency if recurrence_rule else 'None'}"
        )

        # 1. ID 변환
        todo_id_vo = TodoId.from_string(todo_id)

        # 2. TODO 조회
        todo = self.repository.find_by_id(todo_id_vo)
        if todo is None:
            logger.error(f"[TodoService] TODO 찾을 수 없음: id={todo_id}")
            raise ValueError(f"TODO not found: {todo_id}")

        # 3. 반복 규칙이 있는데 납기일이 없으면 에러
        if recurrence_rule and todo.due_date is None:
            logger.error(f"[TodoService] 납기일 없는 TODO에 반복 규칙 설정 시도: id={todo_id}")
            raise ValueError("Cannot set recurrence on TODO without due date")

        # 4. 반복 규칙 설정
        todo.set_recurrence(recurrence_rule)

        # 5. 저장
        self.repository.save(todo)

        logger.info(f"[TodoService] 반복 규칙 설정 완료: id={todo_id}")

    def remove_recurrence(self, todo_id: str) -> None:
        """TODO의 반복 규칙 제거

        Args:
            todo_id: TODO ID (문자열)

        Raises:
            ValueError: todo_id에 해당하는 TODO를 찾을 수 없는 경우
        """
        logger.info(f"[TodoService] 반복 규칙 제거: id={todo_id}")
        # set_recurrence(todo_id, None)과 동일
        self.set_recurrence(todo_id, None)

    # ========================================
    # SubTask CRUD 메서드
    # ========================================

    def add_subtask(
        self,
        parent_todo_id: TodoId,
        content_str: str,
        due_date: Optional[DueDate] = None
    ) -> None:
        """하위 할일 추가

        Args:
            parent_todo_id: 메인 할일 ID
            content_str: 하위 할일 내용
            due_date: 납기일 (optional)

        Raises:
            ValueError: parent_todo_id에 해당하는 Todo를 찾을 수 없는 경우
        """
        logger.info(
            f"[TodoService] SubTask 추가: parent_id={parent_todo_id.value}, "
            f"content='{content_str[:50]}...', due_date={due_date}"
        )

        # 1. 메인 할일 조회 (헬퍼 메서드 사용)
        todo = self._get_todo_or_raise(parent_todo_id)

        # 2. SubTask 생성 (order는 자동 정렬되므로 0으로 설정)
        due_date_str = str(due_date) if due_date else None
        new_subtask = SubTask.create(
            content=content_str,
            due_date=due_date_str,
            order=0
        )

        # 3. Todo에 추가 (자동 정렬됨, add_subtask()는 반환값이 없으므로 재할당 불필요)
        todo.add_subtask(new_subtask)

        # 4. 저장
        self.repository.save(todo)

        logger.info(f"[TodoService] SubTask 추가 완료: subtask_id={new_subtask.id.value}")

    def update_subtask(
        self,
        parent_todo_id: TodoId,
        subtask_id: TodoId,
        content_str: Optional[str] = None,
        due_date: Optional[DueDate] = None
    ) -> None:
        """하위 할일 수정

        Args:
            parent_todo_id: 메인 할일 ID
            subtask_id: 하위 할일 ID
            content_str: 새 내용 (None이면 변경 안함)
            due_date: 새 납기일 (None이면 변경 안함)

        Raises:
            ValueError: Todo 또는 SubTask를 찾을 수 없는 경우
        """
        logger.info(
            f"[TodoService] SubTask 수정: parent_id={parent_todo_id.value}, "
            f"subtask_id={subtask_id.value}"
        )

        # 1. 메인 할일 조회 (헬퍼 메서드 사용)
        todo = self._get_todo_or_raise(parent_todo_id)

        # 2. 하위 할일 조회
        subtask = todo.get_subtask(subtask_id)
        if subtask is None:
            logger.error(
                f"[TodoService] SubTask 찾을 수 없음: "
                f"parent_id={parent_todo_id.value}, subtask_id={subtask_id.value}"
            )
            raise ValueError(
                f"SubTask with id {subtask_id.value} not found in todo {parent_todo_id.value}"
            )

        # 3. 내용 수정 (있는 경우)
        if content_str is not None:
            content_vo = Content(value=content_str)
            subtask.update_content(content_vo)

        # 4. 납기일 수정 (있는 경우)
        if due_date is not None:
            subtask.set_due_date(due_date)

        # 5. Todo에 업데이트 (재정렬됨)
        todo.update_subtask(subtask_id, subtask)

        # 6. 저장
        self.repository.save(todo)

        logger.info(f"[TodoService] SubTask 수정 완료: subtask_id={subtask_id.value}")

    def delete_subtask(
        self,
        parent_todo_id: TodoId,
        subtask_id: TodoId
    ) -> None:
        """하위 할일 삭제

        Args:
            parent_todo_id: 메인 할일 ID
            subtask_id: 하위 할일 ID

        Raises:
            ValueError: Todo를 찾을 수 없는 경우
        """
        logger.info(
            f"[TodoService] SubTask 삭제: parent_id={parent_todo_id.value}, "
            f"subtask_id={subtask_id.value}"
        )

        # 1. 메인 할일 조회 (헬퍼 메서드 사용)
        todo = self._get_todo_or_raise(parent_todo_id)

        # 2. 하위 할일 제거
        todo.remove_subtask(subtask_id)

        # 3. 저장
        self.repository.save(todo)

        logger.info(f"[TodoService] SubTask 삭제 완료: subtask_id={subtask_id.value}")

    def toggle_subtask_complete(
        self,
        parent_todo_id: TodoId,
        subtask_id: TodoId
    ) -> None:
        """하위 할일 완료 상태 토글

        Args:
            parent_todo_id: 메인 할일 ID
            subtask_id: 하위 할일 ID

        Raises:
            ValueError: Todo를 찾을 수 없는 경우
        """
        logger.info(
            f"[TodoService] SubTask 완료 토글: parent_id={parent_todo_id.value}, "
            f"subtask_id={subtask_id.value}"
        )

        # 1. 메인 할일 조회 (헬퍼 메서드 사용)
        todo = self._get_todo_or_raise(parent_todo_id)

        # 2. 완료 상태 토글
        todo.toggle_subtask_complete(subtask_id)

        # 3. 저장
        self.repository.save(todo)

        logger.info(f"[TodoService] SubTask 완료 토글 완료: subtask_id={subtask_id.value}")
