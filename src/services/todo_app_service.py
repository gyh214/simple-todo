"""
TodoAppService - CLEAN 아키텍처 Application Layer 핵심

🎯 Use Case 조율자:
==================
UI와 Domain 사이의 복잡한 비즈니스 플로우를 조율합니다.
모든 검증 로직과 에러 처리를 중앙집중화하여 UI의 순수성을 보장합니다.

🔒 책임 분리:
=============
- UI Layer: 순수 표현 로직만 (사용자 입력 수집, 화면 표시)
- Application Layer: Use Case 구현 (여기!)
- Domain Layer: 핵심 비즈니스 로직 (UnifiedTodoManager)
- Infrastructure Layer: 외부 의존성 (파일 시스템, 네트워크)

⚡ 핵심 기능:
=============
- 검증을 포함한 안전한 TODO 생성/수정/삭제
- UI 최적화된 데이터 조회
- 에러 처리 및 사용자 알림
- 드래그 앤 드롭 순서 변경
- 완료된 TODO 일괄 삭제
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from interfaces import (
    ITodoService,
    IValidationService,
    INotificationService,
    ITodoRepository,
    TodoRepositoryError
)

logger = logging.getLogger(__name__)


class TodoAppService(ITodoService):
    """
    Application Layer의 핵심 구현체

    🎯 Dependency Injection:
    ========================
    모든 의존성을 Interface를 통해 주입받아 완전한 테스트 가능성을 보장합니다.

    🔒 데이터 보존 보장:
    ===================
    모든 업데이트 경로에서 납기일과 메타데이터가 자동으로 보존됩니다.
    UI에서는 더 이상 보존 로직을 신경쓸 필요가 없습니다.
    """

    def __init__(self,
                 todo_repository: ITodoRepository,
                 validation_service: IValidationService,
                 notification_service: INotificationService):
        """
        의존성 주입을 통한 초기화

        Args:
            todo_repository: Domain Layer 데이터 접근
            validation_service: 입력 검증 서비스
            notification_service: 사용자 알림 서비스
        """
        self._todo_repository = todo_repository
        self._validation_service = validation_service
        self._notification_service = notification_service

        logger.info("TodoAppService 초기화 완료 - CLEAN 아키텍처 적용")

    def create_todo_with_validation(self, text: str, **kwargs) -> Dict[str, Any]:
        """
        검증과 함께 TODO 생성

        🛡️ 완전한 검증:
        ===============
        - 텍스트 유효성 검증
        - 납기일 형식 검증
        - 전체 데이터 무결성 검증
        - 중복 생성 방지

        Args:
            text: TODO 텍스트
            **kwargs: 추가 메타데이터 (due_date, priority 등)

        Returns:
            생성된 TODO 데이터

        Raises:
            TodoRepositoryError: 생성 실패시
        """
        try:
            # 1. 필수 필드 검증
            if not self._validation_service.validate_todo_text(text):
                self._notification_service.show_error("유효하지 않은 TODO 텍스트입니다.")
                raise TodoRepositoryError("Invalid todo text", "VALIDATION_ERROR")

            # 2. 납기일 검증 (선택사항)
            due_date = kwargs.get('due_date')
            if due_date and not self._validation_service.validate_due_date(due_date):
                self._notification_service.show_error("유효하지 않은 납기일 형식입니다.")
                raise TodoRepositoryError("Invalid due date format", "VALIDATION_ERROR")

            # 3. 전체 데이터 검증
            todo_data = {'text': text, **kwargs}
            validation_errors = self._validation_service.validate_todo_data(todo_data)
            if validation_errors:
                error_message = "\\n".join(validation_errors)
                self._notification_service.show_error(f"데이터 검증 실패:\\n{error_message}")
                raise TodoRepositoryError("Data validation failed", "VALIDATION_ERROR",
                                         {"errors": validation_errors})

            # 4. Domain Layer에서 TODO 생성
            created_todo = self._todo_repository.create_todo(text, **kwargs)

            # 5. 성공 알림
            self._notification_service.show_info(f"TODO가 성공적으로 생성되었습니다: {text[:30]}...")

            logger.info(f"TODO 생성 성공: {created_todo.get('id', 'unknown')}")
            return created_todo

        except TodoRepositoryError:
            # 이미 처리된 에러는 재발생
            raise
        except Exception as e:
            # 예상치 못한 에러 처리
            error_msg = f"TODO 생성 중 오류 발생: {str(e)}"
            self._notification_service.show_error(error_msg)
            logger.error(error_msg, exc_info=True)
            raise TodoRepositoryError(error_msg, "UNEXPECTED_ERROR")

    def update_todo_safely(self, todo_id: str, **kwargs) -> bool:
        """
        안전한 TODO 업데이트 (데이터 보존 보장)

        🔒 납기일 보존 보장:
        ===================
        명시되지 않은 모든 필드는 자동으로 보존됩니다.
        UnifiedTodoManager의 DataPreservationService가 구조적으로 보장합니다.

        Args:
            todo_id: 업데이트할 TODO ID
            **kwargs: 업데이트할 필드들

        Returns:
            업데이트 성공 여부
        """
        try:
            # 1. TODO 존재 확인
            existing_todo = self._todo_repository.get_todo_by_id(todo_id)
            if not existing_todo:
                self._notification_service.show_error("존재하지 않는 TODO입니다.")
                return False

            # 2. 업데이트 데이터 검증
            if 'text' in kwargs:
                if not self._validation_service.validate_todo_text(kwargs['text']):
                    self._notification_service.show_error("유효하지 않은 TODO 텍스트입니다.")
                    return False

            if 'due_date' in kwargs and kwargs['due_date']:
                if not self._validation_service.validate_due_date(kwargs['due_date']):
                    self._notification_service.show_error("유효하지 않은 납기일 형식입니다.")
                    return False

            # 3. 전체 업데이트 데이터 검증
            merged_data = {**existing_todo, **kwargs}
            validation_errors = self._validation_service.validate_todo_data(merged_data)
            if validation_errors:
                error_message = "\\n".join(validation_errors)
                self._notification_service.show_error(f"업데이트 검증 실패:\\n{error_message}")
                return False

            # 4. Domain Layer에서 안전한 업데이트 실행
            # UnifiedTodoManager가 DataPreservationService를 통해 모든 필드를 자동 보존
            success = self._todo_repository.update_todo(todo_id, **kwargs)

            if success:
                logger.info(f"TODO 업데이트 성공: {todo_id}")
            else:
                self._notification_service.show_error("TODO 업데이트에 실패했습니다.")

            return success

        except Exception as e:
            error_msg = f"TODO 업데이트 중 오류 발생: {str(e)}"
            self._notification_service.show_error(error_msg)
            logger.error(error_msg, exc_info=True)
            return False

    def delete_todo_with_confirmation(self, todo_id: str) -> bool:
        """
        확인과 함께 TODO 삭제

        🗑️ 안전한 삭제:
        ===============
        사용자 확인 후에만 삭제를 실행합니다.

        Args:
            todo_id: 삭제할 TODO ID

        Returns:
            삭제 성공 여부
        """
        try:
            # 1. TODO 존재 확인
            existing_todo = self._todo_repository.get_todo_by_id(todo_id)
            if not existing_todo:
                self._notification_service.show_error("존재하지 않는 TODO입니다.")
                return False

            # 2. 사용자 확인
            todo_text = existing_todo.get('text', '알 수 없는 TODO')[:50]
            if not self._notification_service.ask_confirmation(
                f"다음 TODO를 삭제하시겠습니까?\\n\\n'{todo_text}'"):
                return False

            # 3. 삭제 실행
            success = self._todo_repository.delete_todo(todo_id)

            if success:
                self._notification_service.show_info("TODO가 삭제되었습니다.")
                logger.info(f"TODO 삭제 성공: {todo_id}")
            else:
                self._notification_service.show_error("TODO 삭제에 실패했습니다.")

            return success

        except Exception as e:
            error_msg = f"TODO 삭제 중 오류 발생: {str(e)}"
            self._notification_service.show_error(error_msg)
            logger.error(error_msg, exc_info=True)
            return False

    def get_todos_for_ui(self, **filters) -> List[Dict[str, Any]]:
        """
        UI에 최적화된 TODO 목록 조회

        📱 UI 최적화:
        ============
        - 정렬 및 필터링 적용
        - 표시용 메타데이터 추가
        - 성능 최적화된 데이터 구조

        Args:
            **filters: 조회 필터 (completed, due_date 등)

        Returns:
            UI 표시용 TODO 목록
        """
        try:
            todos = self._todo_repository.get_todos(**filters)

            # UI 최적화 처리
            for todo in todos:
                # 표시용 날짜 형식 변환
                if todo.get('due_date'):
                    try:
                        # ISO 형식을 사용자 친화적 형식으로 변환
                        due_date_obj = datetime.fromisoformat(todo['due_date'].replace('Z', '+00:00'))
                        todo['display_due_date'] = due_date_obj.strftime('%Y-%m-%d')
                    except:
                        todo['display_due_date'] = todo.get('due_date', '')
                else:
                    todo['display_due_date'] = ''

                # 완료 상태 텍스트 변환
                todo['status_text'] = '완료' if todo.get('completed', False) else '진행중'

                # 긴급도 표시 (납기일 기반)
                todo['is_urgent'] = self._is_urgent(todo.get('due_date'))

            logger.debug(f"UI용 TODO 목록 조회 완료: {len(todos)}개")
            return todos

        except Exception as e:
            error_msg = f"TODO 목록 조회 중 오류 발생: {str(e)}"
            self._notification_service.show_error(error_msg)
            logger.error(error_msg, exc_info=True)
            return []

    def reorder_todos(self, todo_id: str, new_position: int) -> bool:
        """
        드래그 앤 드롭을 위한 순서 변경

        🔄 순서 변경:
        ============
        안전한 위치 변경과 충돌 방지를 보장합니다.

        Args:
            todo_id: 이동할 TODO ID
            new_position: 새로운 위치 (0부터 시작)

        Returns:
            이동 성공 여부
        """
        try:
            # 유효성 검증
            if new_position < 0:
                self._notification_service.show_error("잘못된 위치입니다.")
                return False

            # Domain Layer에서 순서 변경
            success = self._todo_repository.reorder_todo(todo_id, new_position)

            if success:
                logger.info(f"TODO 순서 변경 성공: {todo_id} -> position {new_position}")
            else:
                self._notification_service.show_error("순서 변경에 실패했습니다.")

            return success

        except Exception as e:
            error_msg = f"TODO 순서 변경 중 오류 발생: {str(e)}"
            self._notification_service.show_error(error_msg)
            logger.error(error_msg, exc_info=True)
            return False

    def clear_completed_todos(self) -> int:
        """
        완료된 TODO 일괄 삭제

        🧹 일괄 정리:
        =============
        사용자 확인 후 완료된 모든 TODO를 삭제합니다.

        Returns:
            삭제된 TODO 개수
        """
        try:
            # 완료된 TODO 개수 확인
            completed_todos = self._todo_repository.get_todos(completed=True)
            count = len(completed_todos)

            if count == 0:
                self._notification_service.show_info("삭제할 완료된 TODO가 없습니다.")
                return 0

            # 사용자 확인
            if not self._notification_service.ask_confirmation(
                f"{count}개의 완료된 TODO를 모두 삭제하시겠습니까?"):
                return 0

            # 일괄 삭제 실행
            deleted_count = self._todo_repository.clear_completed_todos()

            if deleted_count > 0:
                self._notification_service.show_info(f"{deleted_count}개의 TODO가 삭제되었습니다.")
                logger.info(f"완료된 TODO 일괄 삭제: {deleted_count}개")

            return deleted_count

        except Exception as e:
            error_msg = f"완료된 TODO 삭제 중 오류 발생: {str(e)}"
            self._notification_service.show_error(error_msg)
            logger.error(error_msg, exc_info=True)
            return 0

    def get_todo_stats(self) -> Dict[str, Any]:
        """
        TODO 통계 정보 조회 (UI 대시보드용)

        Returns:
            통계 정보 딕셔너리
        """
        try:
            stats = self._todo_repository.get_stats()

            # UI 친화적 추가 통계
            stats['completion_rate'] = (
                (stats['completed'] / stats['total'] * 100) if stats['total'] > 0 else 0
            )
            stats['completion_rate_text'] = f"{stats['completion_rate']:.1f}%"

            return stats

        except Exception as e:
            logger.error(f"통계 조회 중 오류: {str(e)}", exc_info=True)
            return {'total': 0, 'completed': 0, 'pending': 0, 'completion_rate': 0}

    def _is_urgent(self, due_date: Optional[str]) -> bool:
        """
        납기일 기반 긴급도 판정

        Args:
            due_date: 납기일 문자열

        Returns:
            긴급 여부
        """
        if not due_date:
            return False

        try:
            due_date_obj = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
            days_until_due = (due_date_obj - datetime.now()).days
            return days_until_due <= 1  # 1일 이내면 긴급
        except:
            return False