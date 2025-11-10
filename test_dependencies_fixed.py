"""
자동 업데이트 기능 의존성 및 Import 검증 테스트 스크립트
"""
import sys
import importlib.util

def check_python_version():
    """Python 버전 확인"""
    version = sys.version.split()[0]
    major, minor = sys.version_info.major, sys.version_info.minor

    print(f"Python version: {version}", end=" ")
    if major >= 3 and minor >= 7:
        print("[OK]")
        return True
    else:
        print(f"[FAIL] - Python 3.7+ required")
        return False

def check_library(library_name):
    """라이브러리 설치 및 import 가능 여부 확인"""
    try:
        __import__(library_name)
        print(f"{library_name}: [OK]")
        return True
    except ImportError as e:
        print(f"{library_name}: [FAIL] - {str(e)}")
        return False

def check_import(import_path, class_name):
    """특정 클래스 import 검증"""
    try:
        module_path = import_path.replace('.', '/')

        # Import 시도
        parts = import_path.split('.')
        module = __import__(import_path, fromlist=[class_name])
        getattr(module, class_name)

        print(f"{class_name}: [OK]")
        return True
    except ImportError as e:
        print(f"{class_name}: [FAIL - Import Error] - {str(e)}")
        return False
    except AttributeError as e:
        print(f"{class_name}: [FAIL - Attribute Error] - {str(e)}")
        return False
    except Exception as e:
        print(f"{class_name}: [FAIL - {type(e).__name__}] - {str(e)}")
        return False

def check_config_value(config_module, attr_name):
    """Config 값 확인"""
    try:
        value = getattr(config_module, attr_name)
        if value:
            print(f"{attr_name}: [OK] (value: {value})")
            return True
        else:
            print(f"{attr_name}: [FAIL] - Empty value")
            return False
    except AttributeError:
        print(f"{attr_name}: [FAIL] - Not defined")
        return False

def main():
    """메인 테스트 함수"""
    print("="*60)
    print("Auto Update Feature - Dependency & Import Verification Test")
    print("="*60)
    print()

    all_success = True

    # 1. Python 버전 확인
    print("=== Python Version ===")
    if not check_python_version():
        all_success = False
    print()

    # 2. 필수 라이브러리 확인
    print("=== Required Libraries ===")
    libraries = ['PyQt6', 'requests', 'dateutil']
    for lib in libraries:
        if not check_library(lib):
            all_success = False
    print()

    # 3. Domain Layer Import 검증
    print("=== Domain Layer (3 classes) ===")
    domain_imports = [
        ('src.domain.value_objects.app_version', 'AppVersion'),
        ('src.domain.entities.release', 'Release'),
        ('src.domain.services.version_comparison_service', 'VersionComparisonService'),
    ]
    for module_path, class_name in domain_imports:
        if not check_import(module_path, class_name):
            all_success = False
    print()

    # 4. Infrastructure Layer Import 검증
    print("=== Infrastructure Layer (4 classes) ===")
    infra_imports = [
        ('src.infrastructure.repositories.github_release_repository', 'GitHubReleaseRepository'),
        ('src.infrastructure.repositories.update_settings_repository', 'UpdateSettingsRepository'),
        ('src.infrastructure.services.update_downloader_service', 'UpdateDownloaderService'),
        ('src.infrastructure.services.update_installer_service', 'UpdateInstallerService'),
    ]
    for module_path, class_name in infra_imports:
        if not check_import(module_path, class_name):
            all_success = False
    print()

    # 5. Application Layer Import 검증
    print("=== Application Layer (4 classes) ===")
    app_imports = [
        ('src.application.use_cases.check_for_updates', 'CheckForUpdatesUseCase'),
        ('src.application.use_cases.download_update', 'DownloadUpdateUseCase'),
        ('src.application.use_cases.install_update', 'InstallUpdateUseCase'),
        ('src.application.services.update_scheduler_service', 'UpdateSchedulerService'),
    ]
    for module_path, class_name in app_imports:
        if not check_import(module_path, class_name):
            all_success = False
    print()

    # 6. Presentation Layer Import 검증
    print("=== Presentation Layer (5 classes) ===")
    presentation_imports = [
        ('src.presentation.workers.update_check_worker', 'UpdateCheckWorker'),
        ('src.presentation.workers.update_download_worker', 'UpdateDownloadWorker'),
        ('src.presentation.dialogs.update_available_dialog', 'UpdateAvailableDialog'),
        ('src.presentation.dialogs.update_progress_dialog', 'UpdateProgressDialog'),
        ('src.presentation.system.update_manager', 'UpdateManager'),
    ]
    for module_path, class_name in presentation_imports:
        if not check_import(module_path, class_name):
            all_success = False
    print()

    # 7. Config 파일 확인
    print("=== Config Verification ===")
    try:
        import config
        config_attrs = [
            'GITHUB_REPO_OWNER',
            'GITHUB_REPO_NAME',
            'GITHUB_API_URL',
            'APP_VERSION'
        ]
        for attr in config_attrs:
            if not check_config_value(config, attr):
                all_success = False
    except ImportError as e:
        print(f"config.py: [FAIL] - {str(e)}")
        all_success = False
    print()

    # 최종 결과
    print("="*60)
    print("SUMMARY:")
    print("  - Total classes tested: 16")
    print("  - Domain Layer: 3 classes")
    print("  - Infrastructure Layer: 4 classes")
    print("  - Application Layer: 4 classes")
    print("  - Presentation Layer: 5 classes")
    print()
    if all_success:
        print("RESULT: All imports successful! [PASS]")
        return 0
    else:
        print("RESULT: Some imports failed! [FAIL]")
        return 1

if __name__ == "__main__":
    sys.exit(main())
