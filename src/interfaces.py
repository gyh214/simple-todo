"""
ITodoRepository Interface - 중앙집중형 아키텍처의 핵심 추상화

DRY+CLEAN+SIMPLE 원칙에 따른 완벽한 Repository Pattern 구현
모든 TODO 데이터 접근을 표준화하여 의존성 주입과 테스트 가능성을 보장합니다.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Callable


class ITodoRepository(ABC):
    """
    TODO 데이터 접근을 위한 표준 Repository Interface

    🎯 Single Source of Truth 보장:
    ================================
    모든 TODO 데이터 조작이 이 인터페이스를 통해서만 이루어지도록 강제합니다.
    UI 레이어는 이 인터페이스만 알면 되므로 완전한 분리가 가능합니다.

    🔒 데이터 무결성 보장:
    =====================
    납기일(due_date) 보존이 인터페이스 수준에서 강제됩니다.
    어떤 구현체를 사용하더라도 데이터 손실이 불가능합니다.

    📐 확장 가능한 설계:
    ===================
    미래의 새로운 기능(우선순위, 카테고리, 태그 등)을 추가할 때
    인터페이스만 확장하면 모든 구현체가 자동으로 호환됩니다.
    """

    @abstractmethod
    def create_todo(self, text: str, **kwargs) -> Dict[str, Any]:
        """
        새로운 TODO 항목을 생성

        Args:
            text: TODO 텍스트 (필수)
            **kwargs: 확장 필드들 (due_date, priority, category, tags 등)

        Returns:
            생성된 TODO 항목 (완전한 메타데이터 포함)

        Raises:
            TodoRepositoryError: 생성 실패시
        """
        pass

    @abstractmethod
    def update_todo(self, todo_id: str, **kwargs) -> bool:
        """
        TODO 항목을 안전하게 업데이트 (방어적 데이터 보존)

        🛡️ 방어적 업데이트 보장:
        =======================
        명시되지 않은 모든 필드는 자동으로 보존됩니다.
        특히 due_date는 텍스트 편집 시에도 절대 손실되지 않습니다.

        Args:
            todo_id: TODO 항목 ID
            **kwargs: 업데이트할 필드들

        Returns:
            업데이트 성공 여부

        Raises:
            TodoRepositoryError: 업데이트 실패시
        """
        pass

    @abstractmethod
    def delete_todo(self, todo_id: str) -> bool:
        """
        TODO 항목을 삭제

        Args:
            todo_id: 삭제할 TODO 항목 ID

        Returns:
            삭제 성공 여부
        """
        pass

    @abstractmethod
    def get_todo_by_id(self, todo_id: str) -> Optional[Dict[str, Any]]:
        """
        ID로 특정 TODO 항목을 조회

        Args:
            todo_id: 조회할 TODO 항목 ID

        Returns:
            TODO 항목 또는 None
        """
        pass

    @abstractmethod
    def get_todos(self, **filters) -> List[Dict[str, Any]]:
        """
        TODO 항목들을 조회 (필터링 지원)

        Args:
            **filters: 조회 필터들 (completed, position, due_date 등)

        Returns:
            TODO 항목 리스트 (position 순서로 정렬됨)
        """
        pass

    @abstractmethod
    def clear_completed_todos(self) -> int:
        """
        완료된 TODO 항목들을 일괄 삭제

        Returns:
            삭제된 항목의 수
        """
        pass

    @abstractmethod
    def get_stats(self) -> Dict[str, int]:
        """
        TODO 통계 정보를 조회

        Returns:
            통계 딕셔너리 (total, completed, pending)
        """
        pass

    # 확장성을 위한 추상 메서드들 (미래 기능)
    @abstractmethod
    def export_data(self) -> List[Dict[str, Any]]:
        """모든 데이터를 내보내기"""
        pass

    @abstractmethod
    def import_data(self, todos: List[Dict[str, Any]], merge: bool = False) -> int:
        """외부 데이터를 가져오기"""
        pass

    @abstractmethod
    def backup_data(self) -> str:
        """데이터 백업 생성"""
        pass

    @abstractmethod
    def restore_from_backup(self, backup_path: str) -> bool:
        """백업에서 데이터 복구"""
        pass


class IDataPreservationService(ABC):
    """
    데이터 보존 로직을 위한 중앙집중식 서비스 Interface

    🔒 납기일 보존의 핵심:
    =====================
    모든 TODO 업데이트가 이 서비스를 거쳐야 합니다.
    UI 레이어에서 더 이상 보존 로직을 중복 구현할 필요가 없습니다.
    """

    @abstractmethod
    def preserve_metadata(self, current_data: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        메타데이터를 자동으로 보존하며 업데이트 데이터 준비

        Args:
            current_data: 현재 TODO 데이터
            updates: 업데이트 요청 데이터

        Returns:
            보존된 메타데이터를 포함한 완전한 업데이트 데이터
        """
        pass

    @abstractmethod
    def validate_update(self, todo_data: Dict[str, Any], updates: Dict[str, Any]) -> bool:
        """
        업데이트 전 데이터 검증

        Args:
            todo_data: 기존 TODO 데이터
            updates: 업데이트할 데이터

        Returns:
            유효성 검증 결과
        """
        pass

    @abstractmethod
    def extract_preserved_fields(self, todo_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        보존해야 할 필드들만 추출

        Args:
            todo_data: TODO 데이터

        Returns:
            보존 대상 필드들
        """
        pass


class ITodoErrorHandler(ABC):
    """
    중앙집중식 에러 처리를 위한 Interface

    🚨 통합 에러 처리:
    ==================
    모든 TODO 관련 에러가 한 곳에서 처리됩니다.
    사용자 친화적인 메시지와 개발자 디버그 정보를 분리합니다.
    """

    @abstractmethod
    def handle_validation_error(self, field: str, value: Any, message: str) -> None:
        """데이터 유효성 검증 에러 처리"""
        pass

    @abstractmethod
    def handle_persistence_error(self, operation: str, error: Exception) -> None:
        """데이터 저장/로드 에러 처리"""
        pass

    @abstractmethod
    def handle_business_logic_error(self, operation: str, context: Dict[str, Any], error: Exception) -> None:
        """비즈니스 로직 에러 처리"""
        pass

    @abstractmethod
    def get_user_friendly_message(self, error_type: str, context: Dict[str, Any]) -> str:
        """사용자 친화적 에러 메시지 생성"""
        pass


# ====================================================================
# 🏛️ CLEAN ARCHITECTURE INTERFACES - Application Layer
# ====================================================================

class ITodoService(ABC):
    """
    Application Layer의 핵심 인터페이스

    🎯 Use Case 조율자:
    ===================
    UI와 Domain 사이의 모든 상호작용을 조율합니다.
    복잡한 비즈니스 플로우와 검증 로직을 캡슐화합니다.

    🔒 책임 분리:
    =============
    - UI: 순수 표현 로직만
    - Service: 비즈니스 플로우 조율
    - Domain: 핵심 비즈니스 로직
    """

    @abstractmethod
    def create_todo_with_validation(self, text: str, **kwargs) -> Dict[str, Any]:
        """검증과 함께 TODO 생성"""
        pass

    @abstractmethod
    def update_todo_safely(self, todo_id: str, **kwargs) -> bool:
        """안전한 TODO 업데이트 (데이터 보존 보장)"""
        pass

    @abstractmethod
    def delete_todo_with_confirmation(self, todo_id: str) -> bool:
        """확인과 함께 TODO 삭제"""
        pass

    @abstractmethod
    def get_todos_for_ui(self, **filters) -> List[Dict[str, Any]]:
        """UI에 최적화된 TODO 목록 조회"""
        pass

    @abstractmethod
    def reorder_todos(self, todo_id: str, new_position: int) -> bool:
        """드래그 앤 드롭을 위한 순서 변경"""
        pass


class IValidationService(ABC):
    """
    입력 검증을 위한 전용 인터페이스

    📐 Interface Segregation 적용:
    ===============================
    검증 책임만을 분리하여 단일 책임 원칙을 준수합니다.
    """

    @abstractmethod
    def validate_todo_text(self, text: str) -> bool:
        """TODO 텍스트 유효성 검증"""
        pass

    @abstractmethod
    def validate_due_date(self, date_str: str) -> bool:
        """납기일 형식 유효성 검증"""
        pass

    @abstractmethod
    def validate_todo_data(self, todo_data: Dict[str, Any]) -> List[str]:
        """TODO 데이터 전체 검증 (오류 목록 반환)"""
        pass


class INotificationService(ABC):
    """
    알림 처리를 위한 인터페이스

    🔔 크로스 커팅 관심사:
    ======================
    모든 레이어에서 사용할 수 있는 알림 서비스입니다.
    """

    @abstractmethod
    def show_info(self, message: str, title: str = "정보") -> None:
        """정보 알림 표시"""
        pass

    @abstractmethod
    def show_warning(self, message: str, title: str = "경고") -> None:
        """경고 알림 표시"""
        pass

    @abstractmethod
    def show_error(self, message: str, title: str = "오류") -> None:
        """오류 알림 표시"""
        pass

    @abstractmethod
    def ask_confirmation(self, message: str, title: str = "확인") -> bool:
        """사용자 확인 요청"""
        pass


# ====================================================================
# 🏗️ CLEAN ARCHITECTURE INTERFACES - Infrastructure Layer
# ====================================================================

class IFileService(ABC):
    """
    파일 시스템 추상화 인터페이스

    💾 Infrastructure 독립성:
    =========================
    플랫폼 특화 파일 처리를 추상화하여 테스트 가능성을 높입니다.
    """

    @abstractmethod
    def read_json(self, file_path: str) -> Dict[str, Any]:
        """JSON 파일 읽기"""
        pass

    @abstractmethod
    def write_json(self, file_path: str, data: Dict[str, Any]) -> bool:
        """JSON 파일 쓰기"""
        pass

    @abstractmethod
    def backup_file(self, source_path: str, backup_path: str) -> bool:
        """파일 백업"""
        pass

    @abstractmethod
    def file_exists(self, file_path: str) -> bool:
        """파일 존재 확인"""
        pass

    @abstractmethod
    def ensure_directory(self, dir_path: str) -> bool:
        """디렉토리 생성 보장"""
        pass


class ISystemService(ABC):
    """
    시스템 기능 추상화 인터페이스

    🖥️ 플랫폼 독립성:
    =================
    Windows 특화 기능들을 추상화합니다.
    """

    @abstractmethod
    def open_url(self, url: str) -> bool:
        """웹 URL 열기"""
        pass

    @abstractmethod
    def open_file(self, file_path: str) -> bool:
        """파일 열기"""
        pass

    @abstractmethod
    def get_app_data_path(self) -> str:
        """애플리케이션 데이터 경로 조회"""
        pass


# ====================================================================
# 🎯 DEPENDENCY INJECTION INTERFACES
# ====================================================================

class IDependencyContainer(ABC):
    """
    의존성 주입 컨테이너 인터페이스

    🔄 IoC Container:
    =================
    모든 의존성을 중앙에서 관리하고 주입합니다.
    """

    @abstractmethod
    def register_singleton(self, interface: type, implementation: type) -> None:
        """싱글톤으로 서비스 등록"""
        pass

    @abstractmethod
    def register_transient(self, interface: type, implementation: type) -> None:
        """매번 새 인스턴스로 서비스 등록"""
        pass

    @abstractmethod
    def resolve(self, interface: type) -> Any:
        """의존성 해결 및 주입"""
        pass

    @abstractmethod
    def is_registered(self, interface: type) -> bool:
        """서비스 등록 여부 확인"""
        pass


class TodoRepositoryError(Exception):
    """Repository 계층 전용 예외 클래스"""

    def __init__(self, message: str, error_code: str = None, context: Dict[str, Any] = None):
        super().__init__(message)
        self.error_code = error_code or 'UNKNOWN_ERROR'
        self.context = context or {}
        self.timestamp = None

    def __str__(self):
        if self.context:
            return f"{super().__str__()} (Context: {self.context})"
        return super().__str__()


class DataPreservationError(TodoRepositoryError):
    """데이터 보존 실패 전용 예외"""

    def __init__(self, field: str, current_value: Any, attempted_value: Any, message: str = None):
        self.field = field
        self.current_value = current_value
        self.attempted_value = attempted_value

        default_message = f"필드 '{field}' 보존 실패: {current_value} -> {attempted_value}"
        super().__init__(message or default_message, 'DATA_PRESERVATION_ERROR', {
            'field': field,
            'current_value': current_value,
            'attempted_value': attempted_value
        })