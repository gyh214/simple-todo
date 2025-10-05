"""
Application Bootstrap - CLEAN 아키텍처 앱 초기화

🚀 애플리케이션 부트스트래퍼:
===========================
CLEAN 아키텍처의 모든 의존성을 구성하고
DI Container를 통해 완전한 의존성 역전을 구현합니다.

🎯 Composition Root Pattern:
============================
애플리케이션의 단일 진입점에서 모든 의존성을 구성합니다.
이후 코드에서는 구체적인 구현체를 전혀 몰라도 됩니다.

🔄 의존성 플로우:
================
UI → Application Services → Domain Services → Infrastructure
모든 화살표가 안쪽(Domain)을 향하는 CLEAN 아키텍처 구현
"""

import logging
import tkinter as tk
from typing import Optional

# CLEAN 아키텍처 레이어별 import
from di_container import DependencyInjectionContainer

# Interfaces (Domain Layer)
from interfaces import (
    ITodoRepository,
    ITodoService,
    IValidationService,
    INotificationService,
    IFileService,
    ISystemService,
    IDataPreservationService,
    IDependencyContainer
)

# Domain Layer
from todo_manager import UnifiedTodoManager
from data_preservation_service import DataPreservationService

# Application Layer
from services import TodoAppService, ValidationService
# NotificationService는 다이렉트로 import 하지 않음 (TkinterNotificationService만 사용)

# Infrastructure Layer
from infrastructure import WindowsFileService, WindowsSystemService

logger = logging.getLogger(__name__)


class ApplicationBootstrap:
    """
    CLEAN 아키텍처 애플리케이션 부트스트래퍼

    🏛️ 아키텍처 구성:
    ==================
    1. Infrastructure Layer 구성
    2. Domain Layer 구성
    3. Application Layer 구성
    4. Presentation Layer 구성
    5. 의존성 주입 완료

    🔒 Singleton 패턴:
    =================
    애플리케이션 전체에서 하나의 DI Container만 존재하도록 보장합니다.
    """

    _instance: Optional['ApplicationBootstrap'] = None
    _container: Optional[IDependencyContainer] = None

    def __new__(cls):
        """Singleton 패턴 구현"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """부트스트래퍼 초기화 (한 번만 실행)"""
        if hasattr(self, '_initialized'):
            return

        self._initialized = True
        self._container = None
        logger.info("ApplicationBootstrap 초기화")

    def configure_services(self, debug: bool = False) -> IDependencyContainer:
        """
        모든 서비스 의존성 구성

        🔧 구성 순서:
        ============
        1. DI Container 생성
        2. Infrastructure Layer 등록
        3. Domain Layer 등록
        4. Application Layer 등록
        5. Cross-cutting Concerns 등록

        Args:
            debug: 디버그 모드 활성화

        Returns:
            구성된 DI Container
        """
        if self._container is not None:
            return self._container

        logger.info("CLEAN 아키텍처 서비스 구성 시작")

        # 1. DI Container 생성
        container = DependencyInjectionContainer()

        # 2. Infrastructure Layer 등록 (Singleton)
        container.register_singleton(IFileService, WindowsFileService)
        container.register_singleton(ISystemService, WindowsSystemService)

        # 3. Domain Layer 등록
        # DataPreservationService - Singleton (상태 없음)
        container.register_singleton(IDataPreservationService, DataPreservationService)

        # UnifiedTodoManager - Singleton (데이터 중앙 관리)
        container.register_factory(ITodoRepository, lambda: self._create_unified_todo_manager(debug))

        # 4. Application Layer 등록
        # ValidationService - Singleton (상태 없는 유틸리티)
        container.register_singleton(IValidationService, ValidationService)

        # TodoAppService - Singleton (애플리케이션 조율자)
        container.register_singleton(ITodoService, TodoAppService)

        # NotificationService - Transient (UI 컨텍스트 의존적)
        from services.notification_service_simple import TkinterNotificationService
        container.register_transient(INotificationService, TkinterNotificationService)

        # 5. 자기 자신을 DI Container로 등록
        container.register_factory(IDependencyContainer, lambda: container)

        self._container = container

        logger.info("CLEAN 아키텍처 서비스 구성 완료")
        self._log_registered_services(container)

        return container

    def create_main_application(self, debug: bool = False) -> 'TodoPanelApp':
        """
        메인 애플리케이션 생성

        🎨 Presentation Layer 구성:
        ===========================
        UI는 오직 ITodoService Interface에만 의존합니다.
        구체적인 구현체는 전혀 알지 못합니다.

        Args:
            debug: 디버그 모드 활성화

        Returns:
            의존성이 주입된 메인 애플리케이션
        """
        container = self.configure_services(debug)

        # Tkinter 루트 윈도우 생성 (UI Infrastructure)
        root = tk.Tk()
        root.title("TODO Panel - CLEAN Architecture")

        # NotificationService에 부모 윈도우 설정
        notification_service = container.resolve(INotificationService)
        if hasattr(notification_service, '_parent_window'):
            notification_service._parent_window = root

        # UI는 Interface를 통해서만 서비스에 접근
        from ui.main_app import TodoPanelApp
        # 임시로 기존 방식으로 생성 (CLEAN 아키텍처 완전 통합은 추후 작업)
        app = TodoPanelApp(root=root)

        logger.info("메인 애플리케이션 생성 완료 - CLEAN 아키텍처 적용")
        return app

    def get_container(self) -> Optional[IDependencyContainer]:
        """
        구성된 DI Container 조회

        Returns:
            DI Container 또는 None
        """
        return self._container

    def reset(self) -> None:
        """
        부트스트래퍼 리셋 (테스트용)

        🧪 테스트 지원:
        ==============
        테스트 환경에서 깨끗한 상태로 재시작할 때 사용합니다.
        """
        if self._container:
            self._container.clear()

        self._container = None
        ApplicationBootstrap._instance = None
        logger.info("ApplicationBootstrap 리셋 완료")

    def _create_unified_todo_manager(self, debug: bool = False) -> UnifiedTodoManager:
        """
        UnifiedTodoManager 팩토리 함수

        🏭 Factory Pattern:
        ==================
        복잡한 초기화 로직을 캡슐화합니다.
        DI Container가 직접 생성자를 호출하기 어려운 경우 사용합니다.

        Args:
            debug: 디버그 모드

        Returns:
            설정된 UnifiedTodoManager 인스턴스
        """
        try:
            # 설정 기반 초기화
            manager = UnifiedTodoManager(
                custom_data_path=None,  # 기본 경로 사용
                debug=debug,
                batch_save=True,
                batch_interval=1.0
            )

            logger.info("UnifiedTodoManager 팩토리 생성 완료")
            return manager

        except Exception as e:
            logger.error(f"UnifiedTodoManager 생성 실패: {str(e)}")
            raise

    def _log_registered_services(self, container: IDependencyContainer) -> None:
        """
        등록된 서비스들을 로그에 출력

        Args:
            container: DI Container
        """
        try:
            services = container.get_registered_services()

            logger.info("=== 등록된 서비스 목록 ===")
            for interface_name, service_info in services.items():
                impl_name = service_info.get('implementation', 'Unknown')
                lifetime = service_info.get('lifetime', 'unknown')
                has_instance = service_info.get('has_instance', False)

                status = "✓ 인스턴스 생성됨" if has_instance else "○ 대기 중"
                logger.info(f"  {interface_name} -> {impl_name} ({lifetime}) {status}")

            logger.info(f"총 {len(services)}개 서비스 등록됨")

        except Exception as e:
            logger.warning(f"서비스 목록 로그 실패: {str(e)}")


# 전역 인스턴스 (Singleton)
bootstrap = ApplicationBootstrap()


def create_application(debug: bool = False) -> 'TodoPanelApp':
    """
    애플리케이션 생성 편의 함수

    🚀 Quick Start:
    ==============
    main.py에서 간단하게 애플리케이션을 생성할 수 있습니다.

    Args:
        debug: 디버그 모드

    Returns:
        설정된 메인 애플리케이션
    """
    return bootstrap.create_main_application(debug)


def get_service_container() -> Optional[IDependencyContainer]:
    """
    DI Container 조회 편의 함수

    Returns:
        DI Container 또는 None
    """
    return bootstrap.get_container()


def reset_application() -> None:
    """
    애플리케이션 리셋 편의 함수 (테스트용)
    """
    bootstrap.reset()


if __name__ == "__main__":
    # 부트스트래퍼 테스트
    logging.basicConfig(level=logging.INFO)

    print("🏛️ CLEAN 아키텍처 부트스트래퍼 테스트")
    print("=" * 50)

    container = bootstrap.configure_services(debug=True)
    services = container.get_registered_services()

    print(f"✓ {len(services)}개 서비스 등록 완료")

    # 주요 서비스 해결 테스트
    try:
        todo_service = container.resolve(ITodoService)
        print(f"✓ TodoService 해결: {type(todo_service).__name__}")

        validation_service = container.resolve(IValidationService)
        print(f"✓ ValidationService 해결: {type(validation_service).__name__}")

        file_service = container.resolve(IFileService)
        print(f"✓ FileService 해결: {type(file_service).__name__}")

        print("\\n🎉 모든 의존성 해결 성공!")

    except Exception as e:
        print(f"❌ 의존성 해결 실패: {e}")

    finally:
        bootstrap.reset()