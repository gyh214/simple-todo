# -*- coding: utf-8 -*-
"""Infrastructure Layer 구현 검증 테스트"""

import sys
from pathlib import Path

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_imports():
    """Import 테스트"""
    print("=" * 60)
    print("1. Import Test")
    print("=" * 60)

    try:
        # Domain Layer
        from src.domain.value_objects.app_version import AppVersion
        from src.domain.entities.release import Release
        print("[OK] Domain Layer import")

        # Infrastructure Repositories
        from src.infrastructure.repositories.github_release_repository import GitHubReleaseRepository
        from src.infrastructure.repositories.update_settings_repository import UpdateSettingsRepository
        print("[OK] Infrastructure Repositories import")

        # Infrastructure Services
        from src.infrastructure.services.update_downloader_service import UpdateDownloaderService
        from src.infrastructure.services.update_installer_service import UpdateInstallerService
        print("[OK] Infrastructure Services import")

        print("\n[SUCCESS] All imports passed!\n")
        return True

    except Exception as e:
        print(f"\n[FAILED] Import error: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_app_version():
    """AppVersion 테스트"""
    print("=" * 60)
    print("2. AppVersion Test")
    print("=" * 60)

    try:
        from src.domain.value_objects.app_version import AppVersion

        # 버전 생성
        v1 = AppVersion.from_string("2.4")
        v2 = AppVersion.from_string("v2.5.1")
        v3 = AppVersion.from_string("2.4.0")

        print(f"v1 = {v1}")
        print(f"v2 = {v2}")
        print(f"v3 = {v3}")

        # 비교
        assert v1 < v2, "v1 < v2"
        assert v1 == v3, "v1 == v3"
        assert v2 > v1, "v2 > v1"

        print("\n[SUCCESS] AppVersion test passed!\n")
        return True

    except Exception as e:
        print(f"\n[FAILED] AppVersion test error: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_github_release_repository():
    """GitHubReleaseRepository 테스트"""
    print("=" * 60)
    print("3. GitHubReleaseRepository Test")
    print("=" * 60)

    try:
        from src.infrastructure.repositories.github_release_repository import GitHubReleaseRepository

        # Repository 생성
        repo = GitHubReleaseRepository("gyh214", "simple-todo", timeout=10)
        print(f"Repository created: {repo}")

        print("\nFetching latest release... (requires network)")
        release = repo.get_latest_release()

        if release:
            print(f"\n[OK] Latest release found:")
            print(f"  - Version: {release.version}")
            print(f"  - Filename: {release.asset_name}")
            print(f"  - Size: {release.format_file_size()}")
            print(f"  - Published: {release.format_published_date()}")
            print(f"  - URL: {release.download_url[:50]}...")
        else:
            print("\n[WARNING] Release not found or network error")

        print("\n[SUCCESS] GitHubReleaseRepository test completed!\n")
        return True

    except Exception as e:
        print(f"\n[FAILED] GitHubReleaseRepository test error: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_update_settings_repository():
    """UpdateSettingsRepository 테스트"""
    print("=" * 60)
    print("4. UpdateSettingsRepository Test")
    print("=" * 60)

    try:
        from src.infrastructure.repositories.update_settings_repository import UpdateSettingsRepository
        from src.domain.value_objects.app_version import AppVersion
        from datetime import datetime
        import config

        # Repository 생성
        repo = UpdateSettingsRepository(config.DATA_FILE)
        print(f"Repository created: {repo}")

        # 자동 체크 활성화 확인
        auto_check = repo.is_auto_check_enabled()
        print(f"\nAuto check enabled: {auto_check}")

        # 마지막 체크 시간 확인
        last_check = repo.get_last_check_time()
        print(f"Last check time: {last_check}")

        # 건너뛴 버전 확인
        skipped = repo.get_skipped_version()
        print(f"Skipped version: {skipped}")

        # 테스트 데이터 저장
        print("\nSaving test data...")
        now = datetime.now()
        success = repo.save_last_check_time(now)
        print(f"  - Check time saved: {'OK' if success else 'FAILED'}")

        version = AppVersion.from_string("2.5.0")
        success = repo.set_skipped_version(version)
        print(f"  - Skipped version saved: {'OK' if success else 'FAILED'}")

        # 저장 확인
        saved_check = repo.get_last_check_time()
        saved_version = repo.get_skipped_version()

        assert saved_check is not None, "Check time verification"
        assert saved_version == version, "Version verification"

        print(f"\nVerification:")
        print(f"  - Check time: {saved_check}")
        print(f"  - Skipped version: {saved_version}")

        print("\n[SUCCESS] UpdateSettingsRepository test passed!\n")
        return True

    except Exception as e:
        print(f"\n[FAILED] UpdateSettingsRepository test error: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_update_downloader_service():
    """UpdateDownloaderService 테스트"""
    print("=" * 60)
    print("5. UpdateDownloaderService Test")
    print("=" * 60)

    try:
        from src.infrastructure.services.update_downloader_service import UpdateDownloaderService

        # Service 생성
        service = UpdateDownloaderService()
        print(f"Service created: {service}")
        print(f"Download dir: {service.download_dir}")

        # 임시 파일 정리 테스트
        print("\nCleaning up temp files...")
        service.cleanup_temp_files()

        print("\n[SUCCESS] UpdateDownloaderService test passed!\n")
        return True

    except Exception as e:
        print(f"\n[FAILED] UpdateDownloaderService test error: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_update_installer_service():
    """UpdateInstallerService 테스트"""
    print("=" * 60)
    print("6. UpdateInstallerService Test")
    print("=" * 60)

    try:
        from src.infrastructure.services.update_installer_service import UpdateInstallerService

        # Service 생성
        service = UpdateInstallerService()
        print(f"Service created: {service}")

        # Batch script 생성 테스트
        print("\nTesting batch script generation...")
        new_exe = Path("D:/temp/SimpleTodo_new.exe")
        current_exe = Path("D:/app/SimpleTodo.exe")

        # 실제로 파일을 생성하지 않고 script 내용만 확인
        script_content = service._generate_batch_script(new_exe, current_exe)

        print(f"\nScript content preview:")
        print("-" * 40)
        print(script_content[:300] + "...")
        print("-" * 40)

        assert "timeout /t 2" in script_content, "Wait command check"
        assert "taskkill" in script_content, "Kill process command check"
        assert "move /Y" in script_content, "Move file command check"
        assert "start" in script_content, "Start app command check"

        print("\n[SUCCESS] UpdateInstallerService test passed!\n")
        return True

    except Exception as e:
        print(f"\n[FAILED] UpdateInstallerService test error: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def main():
    """메인 테스트 실행"""
    print("\n" + "=" * 60)
    print("Infrastructure Layer Implementation Verification Test")
    print("=" * 60 + "\n")

    results = []

    # 1. Import 테스트
    results.append(("Import", test_imports()))

    # 2. AppVersion 테스트
    results.append(("AppVersion", test_app_version()))

    # 3. GitHubReleaseRepository 테스트
    results.append(("GitHubReleaseRepository", test_github_release_repository()))

    # 4. UpdateSettingsRepository 테스트
    results.append(("UpdateSettingsRepository", test_update_settings_repository()))

    # 5. UpdateDownloaderService 테스트
    results.append(("UpdateDownloaderService", test_update_downloader_service()))

    # 6. UpdateInstallerService 테스트
    results.append(("UpdateInstallerService", test_update_installer_service()))

    # 결과 요약
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)

    for name, success in results:
        status = "[PASS]" if success else "[FAIL]"
        print(f"{status} {name}")

    total = len(results)
    passed = sum(1 for _, success in results if success)

    print("\n" + "=" * 60)
    print(f"Total: {total}, Passed: {passed}, Failed: {total - passed}")
    print("=" * 60 + "\n")

    if passed == total:
        print("All tests passed!")
        return 0
    else:
        print("Some tests failed")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
