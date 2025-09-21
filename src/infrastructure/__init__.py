"""
Infrastructure Layer - CLEAN 아키텍처 외부 의존성 처리

🏗️ Infrastructure Layer:
=========================
모든 외부 의존성(파일 시스템, 네트워크, UI 프레임워크 등)을
Interface로 추상화하여 Domain Layer의 순수성을 보장합니다.

📦 포함된 서비스들:
==================
- FileService: 파일 시스템 추상화
- SystemService: 운영체제 기능 추상화
- 향후 확장: NetworkService, CacheService 등
"""

from .file_service import WindowsFileService
from .system_service import WindowsSystemService

__all__ = [
    'WindowsFileService',
    'WindowsSystemService'
]