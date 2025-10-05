"""
Manager 인터페이스 패키지

DRY+CLEAN+Simple 원칙에 따라 Manager들의 인터페이스를 정의하는 패키지입니다.
"""

from .manager_interfaces import (
    IControlPanelManager,
    IEventHandler,
    IManagerContainer,
    ISettingsManager,
    ITodoDisplayManager,
    IUILayoutManager,
)

__all__ = [
    "IManagerContainer",
    "IUILayoutManager",
    "IControlPanelManager",
    "ITodoDisplayManager",
    "IEventHandler",
    "ISettingsManager",
]
