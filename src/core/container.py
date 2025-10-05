# -*- coding: utf-8 -*-
"""
의존성 주입 컨테이너 (DI Container)

싱글톤 패턴을 사용한 간단한 서비스 컨테이너
레이어별 서비스 등록 및 조회 기능 제공
"""
from typing import Dict, Any, Type, TypeVar, Optional

T = TypeVar('T')


class Container:
    """의존성 주입 컨테이너 (Singleton)"""

    _instance: Optional['Container'] = None
    _services: Dict[str, Any] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._services = {}
        return cls._instance

    @classmethod
    def register(cls, name: str, instance: Any) -> None:
        """
        서비스 등록

        Args:
            name: 서비스 이름 (고유 식별자)
            instance: 서비스 인스턴스
        """
        container = cls()
        container._services[name] = instance

    @classmethod
    def resolve(cls, name: str) -> Any:
        """
        서비스 조회

        Args:
            name: 서비스 이름

        Returns:
            등록된 서비스 인스턴스

        Raises:
            KeyError: 서비스가 등록되지 않은 경우
        """
        container = cls()
        if name not in container._services:
            raise KeyError(f"Service '{name}' not registered in container")
        return container._services[name]

    @classmethod
    def has(cls, name: str) -> bool:
        """
        서비스 존재 여부 확인

        Args:
            name: 서비스 이름

        Returns:
            서비스 등록 여부
        """
        container = cls()
        return name in container._services

    @classmethod
    def clear(cls) -> None:
        """모든 서비스 초기화 (테스트용)"""
        container = cls()
        container._services.clear()

    @classmethod
    def get_all(cls) -> Dict[str, Any]:
        """등록된 모든 서비스 반환 (디버깅용)"""
        container = cls()
        return container._services.copy()


# 서비스 이름 상수 (타입 안전성)
class ServiceNames:
    """서비스 이름 상수"""

    # Infrastructure Layer
    TODO_REPOSITORY = "todo_repository"
    BACKUP_SERVICE = "backup_service"
    MIGRATION_SERVICE = "migration_service"

    # Application Layer
    TODO_SERVICE = "todo_service"
    TODO_SORT_USE_CASE = "todo_sort_use_case"
    REORDER_TODO_USE_CASE = "reorder_todo_use_case"
    CHANGE_SORT_ORDER_USE_CASE = "change_sort_order_use_case"
    DATA_PRESERVATION_SERVICE = "data_preservation_service"

    # Domain Layer
    TODO_SORT_SERVICE = "todo_sort_service"
    LINK_DETECTION_SERVICE = "link_detection_service"

    # Presentation Layer
    MAIN_WINDOW = "main_window"
    SYSTEM_TRAY_MANAGER = "system_tray_manager"
    SINGLE_INSTANCE_MANAGER = "single_instance_manager"
    WINDOW_MANAGER = "window_manager"
