# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Windows TODO Panel

이 파일은 PyInstaller가 TODO Panel 애플리케이션을 빌드할 때 사용하는 
설정 파일입니다.

사용법:
pyinstaller todo_panel.spec
"""

import sys
import os
from pathlib import Path

# 현재 디렉토리와 소스 디렉토리 설정
spec_dir = Path(SPECPATH)
src_dir = spec_dir / 'src'

# 메인 스크립트 파일
main_script = str(src_dir / 'main.py')

# 아이콘 파일 경로
icon_file = str(spec_dir / 'TodoPanel.ico')

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
    
    # 데이터 파일들
    datas=[],
    
    # 숨겨진 imports (자동 감지되지 않는 모듈들)
    hiddenimports=[
        'pystray',
        'PIL',
        'PIL.Image',
        'PIL.ImageDraw',
        'psutil',
        'tkinter',
        'tkinter.ttk',
        'tkinter.messagebox',
        'uuid',
        'json',
        'logging',
        'threading',
        'datetime',
        # UI 패키지 및 모듈들 (모든 새로운 기능 포함)
        'ui',
        'ui.widgets',
        'ui.date_utils',
        'ui.sort_manager',
        'ui.main_app',
        # 추가 UI 관련 모듈들
        'ui_components',
        'todo_manager',
        # 새로 추가된 아키텍처 모듈들
        'interfaces',
        'di_container',
        'app_bootstrap',
        'data_preservation_service',
        # 서비스 패키지
        'services',
        'services.todo_app_service',
        'services.validation_service',
        'services.notification_service',
        'services.notification_service_simple',
        # 인프라스트럭처 패키지
        'infrastructure',
        'infrastructure.system_service',
        'infrastructure.file_service',
        # 유틸리티 모듈들
        'tooltip',
        'run_todo_panel'
    ],
    
    # 훅 디렉토리 
    hookspath=[],
    
    # 런타임 훅
    hooksconfig={},
    
    # 런타임 옵션
    runtime_tmpdir=None,
    
    # 제외할 모듈들 (필요시)
    excludes=[
        'test_todo_manager',
        'test_main',
        'simple_test',
        'test_integration',
        'test_data_preservation',
        'test_unified_manager',
        'todo_manager_legacy_backup'
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
    name='TodoPanel',
    
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