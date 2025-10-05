# -*- coding: utf-8 -*-
"""시스템 통합 (트레이, 윈도우 관리)"""

from .single_instance import SingleInstanceManager
from .tray_manager import SystemTrayManager

__all__ = [
    'SingleInstanceManager',
    'SystemTrayManager',
]
