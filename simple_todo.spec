# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Simple ToDo Application

이 파일은 PyInstaller가 Simple ToDo 애플리케이션을 빌드할 때 사용하는
설정 파일입니다.

사용법:
pyinstaller simple_todo.spec
"""

import sys
import os
from pathlib import Path

# 현재 디렉토리와 소스 디렉토리 설정
spec_dir = Path(SPECPATH)
src_dir = spec_dir / 'src'

# 메인 스크립트 파일
main_script = str(spec_dir / 'main.py')

# 아이콘 파일 경로
icon_file = str(spec_dir / 'simple-todo.ico')

# 버전 정보 파일 경로
version_file = str(spec_dir / 'version_info.txt')

# 애플리케이션 데이터 수집
a = Analysis(
    # 메인 스크립트
    [main_script],

    # 추가 경로 (소스 디렉토리 포함)
    pathex=[str(src_dir), str(spec_dir)],

    # 바이너리 파일들
    binaries=[],

    # 데이터 파일들 (아이콘 파일 자동 포함)
    datas=[(str(icon_file), '.')] if os.path.exists(icon_file) else [],

    # 숨겨진 imports (자동 감지되지 않는 모듈들)
    hiddenimports=[
        # 외부 라이브러리들 - PyQt6
        'PyQt6',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'PyQt6.sip',

        # 외부 라이브러리들 - 기타
        'psutil',
        'dateutil',
        'dateutil.parser',
        'uuid',
        'json',
        'logging',
        'threading',
        'datetime',
        'pathlib',

        # 프로젝트 루트 모듈
        'config',
        'main',

        # src 패키지
        'src',
        'src.__init__',

        # Core 모듈
        'src.core',
        'src.core.__init__',
        'src.core.container',

        # Domain Layer
        'src.domain',
        'src.domain.__init__',

        # Domain - Entities
        'src.domain.entities',
        'src.domain.entities.__init__',
        'src.domain.entities.todo',

        # Domain - Interfaces
        'src.domain.interfaces',
        'src.domain.interfaces.__init__',
        'src.domain.interfaces.repository_interface',

        # Domain - Services
        'src.domain.services',
        'src.domain.services.__init__',
        'src.domain.services.link_detection_service',
        'src.domain.services.todo_sort_service',
        'src.domain.services.todo_search_service',

        # Domain - Value Objects
        'src.domain.value_objects',
        'src.domain.value_objects.__init__',
        'src.domain.value_objects.content',
        'src.domain.value_objects.due_date',
        'src.domain.value_objects.todo_id',

        # Application Layer
        'src.application',
        'src.application.__init__',

        # Application - Interfaces
        'src.application.interfaces',
        'src.application.interfaces.__init__',
        'src.application.interfaces.service_interface',

        # Application - Services
        'src.application.services',
        'src.application.services.__init__',
        'src.application.services.data_preservation_service',
        'src.application.services.todo_service',

        # Application - Use Cases
        'src.application.use_cases',
        'src.application.use_cases.__init__',
        'src.application.use_cases.change_sort_order',
        'src.application.use_cases.reorder_todo',
        'src.application.use_cases.sort_todos',

        # Infrastructure Layer
        'src.infrastructure',
        'src.infrastructure.__init__',

        # Infrastructure - File System
        'src.infrastructure.file_system',
        'src.infrastructure.file_system.__init__',
        'src.infrastructure.file_system.backup_service',
        'src.infrastructure.file_system.migration_service',

        # Infrastructure - Repositories
        'src.infrastructure.repositories',
        'src.infrastructure.repositories.__init__',
        'src.infrastructure.repositories.todo_repository_impl',

        # Infrastructure - System
        'src.infrastructure.system',
        'src.infrastructure.system.__init__',

        # Infrastructure - Utils
        'src.infrastructure.utils.debounce_manager',

        # Presentation Layer
        'src.presentation',
        'src.presentation.__init__',

        # Presentation - Dialogs
        'src.presentation.dialogs',
        'src.presentation.dialogs.__init__',
        'src.presentation.dialogs.edit_dialog',
        'src.presentation.dialogs.backup_manager_dialog',

        # Presentation - System
        'src.presentation.system',
        'src.presentation.system.__init__',
        'src.presentation.system.single_instance',
        'src.presentation.system.tray_manager',
        'src.presentation.system.window_manager',

        # Presentation - UI
        'src.presentation.ui',
        'src.presentation.ui.__init__',
        'src.presentation.ui.main_window',

        # Presentation - UI Event Handlers
        'src.presentation.ui.event_handlers',
        'src.presentation.ui.event_handlers.__init__',
        'src.presentation.ui.event_handlers.main_window_event_handler',

        # Presentation - Utils
        'src.presentation.utils',
        'src.presentation.utils.__init__',
        'src.presentation.utils.link_parser',

        # Presentation - Widgets
        'src.presentation.widgets',
        'src.presentation.widgets.__init__',
        'src.presentation.widgets.custom_splitter',
        'src.presentation.widgets.custom_splitter_handle',
        'src.presentation.widgets.footer_widget',
        'src.presentation.widgets.header_widget',
        'src.presentation.widgets.rich_text_widget',
        'src.presentation.widgets.section_widget',
        'src.presentation.widgets.todo_item_widget',

        # Presentation - Widgets Mixins
        'src.presentation.widgets.mixins',
        'src.presentation.widgets.mixins.__init__',
        'src.presentation.widgets.mixins.draggable_mixin',
    ],

    # 훅 디렉토리
    hookspath=[],

    # 런타임 훅
    hooksconfig={},

    # 런타임 옵션
    runtime_tmpdir=None,

    # 제외할 모듈들 (테스트 파일들과 개발용 스크립트)
    excludes=[
        'debug_main',
        'test',
        'tests',
        'pytest',
        'unittest',
    ],

    # Win32 특정 옵션
    win_no_prefer_redirects=False,
    win_private_assemblies=False,

    # 암호화 키 (필요시)
    cipher=None,

    # 분석 시 노이즈 제거
    noarchive=False,
)

# PYZ 아카이브 생성
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# 실행 파일 생성 (단일 파일 모드)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],

    # 출력 파일명
    name='SimpleTodo',

    # 디버그 정보
    debug=False,
    bootloader_ignore_signals=False,

    # 스트립 심볼
    strip=False,

    # UPX 압축 (사용 가능한 경우)
    upx=False,  # UPX를 찾을 수 없으므로 비활성화
    upx_exclude=[],

    # 런타임 임시 디렉토리
    runtime_tmpdir=None,

    # 콘솔 창 숨기기
    console=False,

    # Windows 전용 GUI 모드
    disable_windowed_traceback=False,

    # 아이콘 설정
    icon=icon_file if os.path.exists(icon_file) else None,

    # 버전 정보
    version=version_file if os.path.exists(version_file) else None,

    # Windows 매니페스트 (관리자 권한 등)
    uac_admin=False,
    uac_uiaccess=False,

    # 대상 아키텍처
    target_arch=None,

    # 단일 파일 모드의 압축 수준
    codesign_identity=None,
    entitlements_file=None,
)
