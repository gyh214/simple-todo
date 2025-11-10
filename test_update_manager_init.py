# -*- coding: utf-8 -*-
"""
UpdateManager 초기화 및 DI Container 통합 테스트

UpdateManager가 DI Container에 올바르게 등록되고,
모든 업데이트 서비스가 정상적으로 초기화되는지 검증합니다.
"""
import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
PROJECT_ROOT = Path(__file__).parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

import config
from src.core.container import Container, ServiceNames


def test_initialize_update_services():
    """UpdateManager 초기화 테스트"""
    print("=" * 70)
    print("=== UpdateManager 초기화 및 DI Container 통합 테스트 ===")
    print("=" * 70)
    print()

    # Container 초기화 (기존 서비스 제거)
    Container.clear()
    print("[SETUP] DI Container 초기화 완료")
    print()

    # ========================================================================
    # 1. initialize_update_services() 함수 실행
    # ========================================================================
    print("[TEST 1] initialize_update_services() 함수 실행")
    print("-" * 70)

    from main import initialize_update_services

    try:
        result = initialize_update_services()
        print(f"[OK] 함수 실행 완료 (반환값: {result})")

        if not result:
            print("[ERROR] initialize_update_services() 가 False를 반환했습니다.")
            return False

    except Exception as e:
        print(f"[FAIL] 함수 실행 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

    print()

    # ========================================================================
    # 2. DI Container 서비스 등록 검증
    # ========================================================================
    print("[TEST 2] DI Container 서비스 등록 검증")
    print("-" * 70)

    services_to_check = [
        ServiceNames.GITHUB_RELEASE_REPOSITORY,
        ServiceNames.UPDATE_SETTINGS_REPOSITORY,
        ServiceNames.UPDATE_DOWNLOADER_SERVICE,
        ServiceNames.UPDATE_INSTALLER_SERVICE,
        ServiceNames.CHECK_FOR_UPDATES_USE_CASE,
        ServiceNames.DOWNLOAD_UPDATE_USE_CASE,
        ServiceNames.INSTALL_UPDATE_USE_CASE,
        ServiceNames.UPDATE_SCHEDULER_SERVICE,
    ]

    all_registered = True
    for service_name in services_to_check:
        try:
            service = Container.resolve(service_name)
            if service is not None:
                print(f"[OK] {service_name:40s} : 등록됨")
            else:
                print(f"[FAIL] {service_name:40s} : None 반환")
                all_registered = False
        except KeyError as e:
            print(f"[FAIL] {service_name:40s} : 미등록 ({e})")
            all_registered = False

    if not all_registered:
        print()
        print("[ERROR] 일부 서비스가 등록되지 않았습니다.")
        return False

    print()

    # ========================================================================
    # 3. 각 서비스의 인스턴스 타입 검증
    # ========================================================================
    print("[TEST 3] 서비스 인스턴스 타입 검증")
    print("-" * 70)

    from src.infrastructure.repositories.github_release_repository import GitHubReleaseRepository
    from src.infrastructure.repositories.update_settings_repository import UpdateSettingsRepository
    from src.infrastructure.services.update_downloader_service import UpdateDownloaderService
    from src.infrastructure.services.update_installer_service import UpdateInstallerService
    from src.application.use_cases.check_for_updates import CheckForUpdatesUseCase
    from src.application.use_cases.download_update import DownloadUpdateUseCase
    from src.application.use_cases.install_update import InstallUpdateUseCase
    from src.application.services.update_scheduler_service import UpdateSchedulerService

    type_checks = [
        (ServiceNames.GITHUB_RELEASE_REPOSITORY, GitHubReleaseRepository),
        (ServiceNames.UPDATE_SETTINGS_REPOSITORY, UpdateSettingsRepository),
        (ServiceNames.UPDATE_DOWNLOADER_SERVICE, UpdateDownloaderService),
        (ServiceNames.UPDATE_INSTALLER_SERVICE, UpdateInstallerService),
        (ServiceNames.CHECK_FOR_UPDATES_USE_CASE, CheckForUpdatesUseCase),
        (ServiceNames.DOWNLOAD_UPDATE_USE_CASE, DownloadUpdateUseCase),
        (ServiceNames.INSTALL_UPDATE_USE_CASE, InstallUpdateUseCase),
        (ServiceNames.UPDATE_SCHEDULER_SERVICE, UpdateSchedulerService),
    ]

    all_types_correct = True
    for service_name, expected_type in type_checks:
        service = Container.resolve(service_name)
        if isinstance(service, expected_type):
            print(f"[OK] {service_name:40s} : {expected_type.__name__}")
        else:
            print(f"[FAIL] {service_name:40s} : 타입 불일치 (기대: {expected_type.__name__}, 실제: {type(service).__name__})")
            all_types_correct = False

    if not all_types_correct:
        print()
        print("[ERROR] 일부 서비스의 타입이 올바르지 않습니다.")
        return False

    print()

    # ========================================================================
    # 4. GitHubReleaseRepository 설정 검증
    # ========================================================================
    print("[TEST 4] GitHubReleaseRepository 설정 검증")
    print("-" * 70)

    github_repo = Container.resolve(ServiceNames.GITHUB_RELEASE_REPOSITORY)

    checks = [
        ("repo_owner", config.GITHUB_REPO_OWNER, "gyh214"),
        ("repo_name", config.GITHUB_REPO_NAME, "simple-todo"),
    ]

    config_correct = True
    for attr_name, config_value, expected_value in checks:
        actual_value = getattr(github_repo, attr_name, None)

        # config 값 검증
        if config_value != expected_value:
            print(f"[WARN] config.{attr_name.upper()} = '{config_value}' (기대값: '{expected_value}')")

        # 인스턴스 값 검증
        if actual_value == expected_value:
            print(f"[OK] github_repo.{attr_name:15s} = '{actual_value}'")
        else:
            print(f"[FAIL] github_repo.{attr_name:15s} = '{actual_value}' (기대값: '{expected_value}')")
            config_correct = False

    if not config_correct:
        print()
        print("[ERROR] GitHubReleaseRepository 설정이 올바르지 않습니다.")
        return False

    print()

    # ========================================================================
    # 5. UseCase 의존성 주입 검증
    # ========================================================================
    print("[TEST 5] UseCase 의존성 주입 검증")
    print("-" * 70)

    check_use_case = Container.resolve(ServiceNames.CHECK_FOR_UPDATES_USE_CASE)
    download_use_case = Container.resolve(ServiceNames.DOWNLOAD_UPDATE_USE_CASE)
    install_use_case = Container.resolve(ServiceNames.INSTALL_UPDATE_USE_CASE)
    scheduler = Container.resolve(ServiceNames.UPDATE_SCHEDULER_SERVICE)

    dependency_checks = [
        ("CheckForUpdatesUseCase.github_repo", check_use_case, "github_repo", GitHubReleaseRepository),
        ("CheckForUpdatesUseCase.settings_repo", check_use_case, "settings_repo", UpdateSettingsRepository),
        ("CheckForUpdatesUseCase.version_service", check_use_case, "version_service", object),
        ("DownloadUpdateUseCase.downloader", download_use_case, "downloader", UpdateDownloaderService),
        ("InstallUpdateUseCase.installer", install_use_case, "installer", UpdateInstallerService),
        ("UpdateSchedulerService.check_use_case", scheduler, "check_use_case", CheckForUpdatesUseCase),
        ("UpdateSchedulerService.settings_repo", scheduler, "settings_repo", UpdateSettingsRepository),
    ]

    dependencies_correct = True
    for check_name, obj, attr_name, expected_type in dependency_checks:
        if hasattr(obj, attr_name):
            attr_value = getattr(obj, attr_name)
            if attr_value is not None:
                if expected_type == object or isinstance(attr_value, expected_type):
                    print(f"[OK] {check_name:45s} : {type(attr_value).__name__}")
                else:
                    print(f"[FAIL] {check_name:45s} : 타입 불일치 (기대: {expected_type.__name__})")
                    dependencies_correct = False
            else:
                print(f"[FAIL] {check_name:45s} : None")
                dependencies_correct = False
        else:
            print(f"[FAIL] {check_name:45s} : 속성 없음")
            dependencies_correct = False

    if not dependencies_correct:
        print()
        print("[ERROR] 일부 UseCase의 의존성이 올바르게 주입되지 않았습니다.")
        return False

    print()

    # ========================================================================
    # 6. UpdateManager 인스턴스 생성 검증 (main.py 로직 시뮬레이션)
    # ========================================================================
    print("[TEST 6] UpdateManager 인스턴스 생성 검증")
    print("-" * 70)

    # PyQt6 없이 테스트하기 위해 parent_window=None으로 생성
    try:
        from src.presentation.system.update_manager import UpdateManager

        update_manager = UpdateManager(
            parent_window=None,  # QWidget 없이 테스트
            scheduler=Container.resolve(ServiceNames.UPDATE_SCHEDULER_SERVICE),
            check_use_case=Container.resolve(ServiceNames.CHECK_FOR_UPDATES_USE_CASE),
            download_use_case=Container.resolve(ServiceNames.DOWNLOAD_UPDATE_USE_CASE),
            install_use_case=Container.resolve(ServiceNames.INSTALL_UPDATE_USE_CASE),
            current_version=config.APP_VERSION
        )

        print(f"[OK] UpdateManager 인스턴스 생성 완료")
        print(f"     - current_version: {update_manager.current_version}")

        # UpdateManager 속성 검증
        required_attrs = [
            "check_use_case",
            "download_use_case",
            "install_use_case",
            "scheduler",
            "current_version",
        ]

        attrs_correct = True
        for attr in required_attrs:
            if hasattr(update_manager, attr):
                attr_value = getattr(update_manager, attr)
                if attr_value is not None:
                    print(f"[OK] UpdateManager.{attr:25s} : {type(attr_value).__name__ if not isinstance(attr_value, str) else repr(attr_value)}")
                else:
                    print(f"[FAIL] UpdateManager.{attr:25s} : None")
                    attrs_correct = False
            else:
                print(f"[FAIL] UpdateManager.{attr:25s} : 속성 없음")
                attrs_correct = False

        if not attrs_correct:
            print()
            print("[ERROR] UpdateManager의 일부 속성이 올바르게 초기화되지 않았습니다.")
            return False

        # Container에 UpdateManager 등록 (선택 사항이지만 테스트)
        Container.register(ServiceNames.UPDATE_MANAGER, update_manager)
        print(f"[OK] UpdateManager를 DI Container에 등록 완료")

    except Exception as e:
        print(f"[FAIL] UpdateManager 생성 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

    print()

    # ========================================================================
    # 7. 전체 서비스 목록 출력
    # ========================================================================
    print("[INFO] 등록된 전체 서비스 목록")
    print("-" * 70)

    all_services = Container.get_all()
    for idx, (name, service) in enumerate(sorted(all_services.items()), 1):
        print(f"{idx:2d}. {name:45s} : {type(service).__name__}")

    print()

    # ========================================================================
    # 최종 결과
    # ========================================================================
    print("=" * 70)
    print("=== 모든 테스트 통과 ===")
    print("=" * 70)
    print()
    print("검증 완료:")
    print("  1. initialize_update_services() 정상 실행")
    print("  2. 8개 업데이트 서비스 DI Container 등록 확인")
    print("  3. 서비스 인스턴스 타입 검증")
    print("  4. GitHubReleaseRepository 설정 검증 (gyh214/simple-todo)")
    print("  5. UseCase 의존성 주입 체인 검증")
    print("  6. UpdateManager 인스턴스 생성 및 속성 검증")
    print()

    return True


if __name__ == "__main__":
    try:
        success = test_initialize_update_services()
        if success:
            print("[SUCCESS] 모든 테스트가 성공적으로 완료되었습니다.")
            sys.exit(0)
        else:
            print("[FAILURE] 일부 테스트가 실패했습니다.")
            sys.exit(1)
    except AssertionError as e:
        print(f"[FAIL] Assertion failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
