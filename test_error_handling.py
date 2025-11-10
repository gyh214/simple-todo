# -*- coding: utf-8 -*-
"""
자동 업데이트 기능 에러 처리 시나리오 테스트

Test 7: 에러 처리 검증
- Domain Layer: 값 검증, 타입 검증
- Infrastructure Layer: 네트워크, 파일 시스템, API 에러
- Application Layer: UseCase 에러 전파 및 처리
- 종합 에러 체인 테스트
"""

import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
sys.path.insert(0, str(Path(__file__).parent))

import unittest
from unittest.mock import Mock, patch, MagicMock, mock_open
from datetime import datetime, timedelta
import tempfile
import json

# requests 모킹을 위한 import
try:
    import requests
except ImportError:
    requests = None

# 테스트 대상 imports
from src.domain.value_objects.app_version import AppVersion
from src.domain.entities.release import Release
from src.infrastructure.repositories.github_release_repository import GitHubReleaseRepository
from src.infrastructure.repositories.update_settings_repository import UpdateSettingsRepository
from src.infrastructure.services.update_downloader_service import UpdateDownloaderService
from src.infrastructure.services.update_installer_service import UpdateInstallerService
from src.application.use_cases.check_for_updates import CheckForUpdatesUseCase
from src.domain.services.version_comparison_service import VersionComparisonService


class TestDomainLayerErrorHandling(unittest.TestCase):
    """Domain Layer 에러 처리 테스트"""

    def test_app_version_invalid_strings(self):
        """Test 7-1-1: AppVersion 파싱 에러 - 잘못된 버전 문자열"""
        print("\n[Test 7-1-1] AppVersion 파싱 에러 - 잘못된 버전 문자열")

        invalid_versions = [
            ("abc", "숫자가 아닌 문자"),
            ("1.2.3.4.5", "너무 많은 버전 파트"),
            ("", "빈 문자열"),
            ("v", "v만 있는 경우"),
            ("1.", "불완전한 버전"),
            ("1.a", "문자 포함"),
            (".1.2", "점으로 시작"),
            ("1..2", "연속된 점"),
        ]

        for invalid, description in invalid_versions:
            with self.assertRaises(ValueError, msg=f"'{invalid}' ({description})"):
                AppVersion.from_string(invalid)
            print(f"  [OK] '{invalid}' ({description}) -> ValueError 발생")

    def test_app_version_none_input(self):
        """Test 7-1-2: AppVersion 파싱 에러 - None 입력"""
        print("\n[Test 7-1-2] AppVersion 파싱 에러 - None 입력")

        with self.assertRaises(ValueError):
            AppVersion.from_string(None)
        print("  [OK] None 입력 -> ValueError 발생")

    def test_app_version_negative_numbers(self):
        """Test 7-1-3: AppVersion 생성 에러 - 음수 버전"""
        print("\n[Test 7-1-3] AppVersion 생성 에러 - 음수 버전")

        with self.assertRaises(ValueError):
            AppVersion(major=-1, minor=0, patch=0)
        print("  [OK] 음수 major -> ValueError 발생")

        with self.assertRaises(ValueError):
            AppVersion(major=1, minor=-1, patch=0)
        print("  [OK] 음수 minor -> ValueError 발생")

        with self.assertRaises(ValueError):
            AppVersion(major=1, minor=0, patch=-1)
        print("  [OK] 음수 patch -> ValueError 발생")

    def test_release_invalid_download_url(self):
        """Test 7-1-4: Release 검증 에러 - 빈 download_url"""
        print("\n[Test 7-1-4] Release 검증 에러 - 빈 download_url")

        # 빈 URL
        with self.assertRaises(ValueError):
            Release(
                version=AppVersion(2, 4, 0),
                download_url="",
                release_notes="test",
                published_at=datetime.now(),
                asset_name="test.exe",
                asset_size=1000
            )
        print("  [OK] 빈 download_url -> ValueError 발생")

        # None URL
        with self.assertRaises(ValueError):
            Release(
                version=AppVersion(2, 4, 0),
                download_url=None,
                release_notes="test",
                published_at=datetime.now(),
                asset_name="test.exe",
                asset_size=1000
            )
        print("  [OK] None download_url -> ValueError 발생")

        # 잘못된 프로토콜
        with self.assertRaises(ValueError):
            Release(
                version=AppVersion(2, 4, 0),
                download_url="ftp://example.com/file.exe",
                release_notes="test",
                published_at=datetime.now(),
                asset_name="test.exe",
                asset_size=1000
            )
        print("  [OK] 잘못된 프로토콜 (ftp://) -> ValueError 발생")

    def test_release_negative_asset_size(self):
        """Test 7-1-5: Release 검증 에러 - 음수 asset_size"""
        print("\n[Test 7-1-5] Release 검증 에러 - 음수 asset_size")

        with self.assertRaises(ValueError):
            Release(
                version=AppVersion(2, 4, 0),
                download_url="https://example.com/file.exe",
                release_notes="test",
                published_at=datetime.now(),
                asset_name="test.exe",
                asset_size=-1
            )
        print("  [OK] 음수 asset_size -> ValueError 발생")

    def test_release_invalid_published_at(self):
        """Test 7-1-6: Release 검증 에러 - 잘못된 published_at"""
        print("\n[Test 7-1-6] Release 검증 에러 - 잘못된 published_at")

        # 문자열 대신 datetime이 아닌 값
        with self.assertRaises(ValueError):
            Release(
                version=AppVersion(2, 4, 0),
                download_url="https://example.com/file.exe",
                release_notes="test",
                published_at="2025-01-01",  # 문자열
                asset_name="test.exe",
                asset_size=1000
            )
        print("  [OK] 문자열 published_at -> ValueError 발생")


class TestInfrastructureLayerErrorHandling(unittest.TestCase):
    """Infrastructure Layer 에러 처리 테스트"""

    def test_github_repo_invalid_init_params(self):
        """Test 7-2-1: GitHubReleaseRepository 초기화 에러"""
        print("\n[Test 7-2-1] GitHubReleaseRepository 초기화 에러")

        # 빈 repo_owner
        with self.assertRaises(ValueError):
            GitHubReleaseRepository(repo_owner="", repo_name="simple-todo")
        print("  [OK] 빈 repo_owner -> ValueError 발생")

        # 빈 repo_name
        with self.assertRaises(ValueError):
            GitHubReleaseRepository(repo_owner="gyh214", repo_name="")
        print("  [OK] 빈 repo_name -> ValueError 발생")

    @patch('requests.get')
    def test_github_repo_network_error(self, mock_get):
        """Test 7-2-2: GitHub API 네트워크 에러"""
        print("\n[Test 7-2-2] GitHub API 네트워크 에러")

        # ConnectionError 시뮬레이션
        mock_get.side_effect = requests.exceptions.ConnectionError("Network unreachable")

        repo = GitHubReleaseRepository(
            repo_owner="gyh214",
            repo_name="simple-todo"
        )

        result = repo.get_latest_release()
        self.assertIsNone(result)
        print("  [OK] ConnectionError 발생 -> None 반환")

    @patch('requests.get')
    def test_github_repo_timeout(self, mock_get):
        """Test 7-2-3: GitHub API 타임아웃"""
        print("\n[Test 7-2-3] GitHub API 타임아웃")

        mock_get.side_effect = requests.exceptions.Timeout("Request timed out")

        repo = GitHubReleaseRepository(
            repo_owner="gyh214",
            repo_name="simple-todo"
        )

        result = repo.get_latest_release()
        self.assertIsNone(result)
        print("  [OK] Timeout 발생 -> None 반환")

    @patch('requests.get')
    def test_github_repo_http_errors(self, mock_get):
        """Test 7-2-4: GitHub API HTTP 에러"""
        print("\n[Test 7-2-4] GitHub API HTTP 에러")

        # 404 Not Found
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        repo = GitHubReleaseRepository("gyh214", "simple-todo")
        result = repo.get_latest_release()
        self.assertIsNone(result)
        print("  [OK] HTTP 404 -> None 반환")

        # 403 Rate Limit
        mock_response.status_code = 403
        result = repo.get_latest_release()
        self.assertIsNone(result)
        print("  [OK] HTTP 403 (Rate Limit) -> None 반환")

        # 500 Server Error
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        result = repo.get_latest_release()
        self.assertIsNone(result)
        print("  [OK] HTTP 500 -> None 반환")

    @patch('requests.get')
    def test_github_repo_json_error(self, mock_get):
        """Test 7-2-5: GitHub API JSON 파싱 에러"""
        print("\n[Test 7-2-5] GitHub API JSON 파싱 에러")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_get.return_value = mock_response

        repo = GitHubReleaseRepository("gyh214", "simple-todo")
        result = repo.get_latest_release()
        self.assertIsNone(result)
        print("  [OK] JSON 파싱 에러 -> None 반환")

    @patch('requests.get')
    def test_github_repo_missing_fields(self, mock_get):
        """Test 7-2-6: GitHub API 응답에 필수 필드 누락"""
        print("\n[Test 7-2-6] GitHub API 응답에 필수 필드 누락")

        mock_response = Mock()
        mock_response.status_code = 200

        # tag_name 없음
        mock_response.json.return_value = {
            "published_at": "2025-01-01T00:00:00Z",
            "assets": []
        }
        mock_get.return_value = mock_response

        repo = GitHubReleaseRepository("gyh214", "simple-todo")
        result = repo.get_latest_release()
        self.assertIsNone(result)
        print("  [OK] tag_name 누락 -> None 반환")

        # published_at 없음
        mock_response.json.return_value = {
            "tag_name": "v2.4.0",
            "assets": []
        }
        result = repo.get_latest_release()
        self.assertIsNone(result)
        print("  [OK] published_at 누락 -> None 반환")

    @patch('requests.get')
    def test_downloader_invalid_url(self, mock_get):
        """Test 7-2-7: UpdateDownloader 잘못된 URL"""
        print("\n[Test 7-2-7] UpdateDownloader 잘못된 URL")

        # ConnectionError 시뮬레이션
        mock_get.side_effect = requests.exceptions.ConnectionError("Invalid domain")

        downloader = UpdateDownloaderService()

        result = downloader.download(
            url="https://invalid-domain-12345.com/file.exe",
            filename="test.exe"
        )

        self.assertIsNone(result)
        print("  [OK] 잘못된 URL -> None 반환")

    @patch('requests.get')
    def test_downloader_http_error(self, mock_get):
        """Test 7-2-8: UpdateDownloader HTTP 에러"""
        print("\n[Test 7-2-8] UpdateDownloader HTTP 에러")

        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        downloader = UpdateDownloaderService()
        result = downloader.download(
            url="https://example.com/notfound.exe",
            filename="test.exe"
        )

        self.assertIsNone(result)
        print("  [OK] HTTP 404 -> None 반환")

    @patch('requests.get')
    def test_downloader_timeout(self, mock_get):
        """Test 7-2-9: UpdateDownloader 타임아웃"""
        print("\n[Test 7-2-9] UpdateDownloader 타임아웃")

        mock_get.side_effect = requests.exceptions.Timeout("Download timed out")

        downloader = UpdateDownloaderService()
        result = downloader.download(
            url="https://example.com/slow.exe",
            filename="test.exe"
        )

        self.assertIsNone(result)
        print("  [OK] Timeout 발생 -> None 반환")

    def test_downloader_invalid_params(self):
        """Test 7-2-10: UpdateDownloader 잘못된 파라미터"""
        print("\n[Test 7-2-10] UpdateDownloader 잘못된 파라미터")

        downloader = UpdateDownloaderService()

        # 빈 URL
        result = downloader.download(url="", filename="test.exe")
        self.assertIsNone(result)
        print("  [OK] 빈 URL -> None 반환")

        # None URL
        result = downloader.download(url=None, filename="test.exe")
        self.assertIsNone(result)
        print("  [OK] None URL -> None 반환")

        # 빈 filename
        result = downloader.download(url="https://example.com/file.exe", filename="")
        self.assertIsNone(result)
        print("  [OK] 빈 filename -> None 반환")

    def test_installer_nonexistent_file(self):
        """Test 7-2-11: UpdateInstaller 존재하지 않는 파일"""
        print("\n[Test 7-2-11] UpdateInstaller 존재하지 않는 파일")

        installer = UpdateInstallerService()

        new_exe = Path("nonexistent_file_12345.exe")
        current_exe = Path("current.exe")

        # 파일이 없으면 None 반환
        result = installer.create_update_script(new_exe, current_exe)

        self.assertIsNone(result)
        print("  [OK] 존재하지 않는 파일 -> None 반환")

    def test_installer_invalid_params(self):
        """Test 7-2-12: UpdateInstaller 잘못된 파라미터"""
        print("\n[Test 7-2-12] UpdateInstaller 잘못된 파라미터")

        installer = UpdateInstallerService()

        # None 파라미터
        with self.assertRaises(ValueError):
            installer.create_update_script(None, Path("current.exe"))
        print("  [OK] None new_exe_path -> ValueError 발생")

        with self.assertRaises(ValueError):
            installer.create_update_script(Path("new.exe"), None)
        print("  [OK] None current_exe_path -> ValueError 발생")

    def test_update_settings_repo_invalid_init(self):
        """Test 7-2-13: UpdateSettingsRepository 초기화 에러"""
        print("\n[Test 7-2-13] UpdateSettingsRepository 초기화 에러")

        # None 경로
        with self.assertRaises(ValueError):
            UpdateSettingsRepository(None)
        print("  [OK] None data_file_path -> ValueError 발생")

    def test_update_settings_repo_corrupted_file(self):
        """Test 7-2-14: UpdateSettingsRepository 손상된 파일 처리"""
        print("\n[Test 7-2-14] UpdateSettingsRepository 손상된 파일 처리")

        # 임시 파일 생성
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json', encoding='utf-8') as f:
            # 잘못된 JSON 작성
            f.write("{invalid json content")
            temp_path = Path(f.name)

        try:
            repo = UpdateSettingsRepository(temp_path)

            # 손상된 파일이어도 안전하게 처리
            last_check = repo.get_last_check_time()
            self.assertIsNone(last_check)
            print("  [OK] 손상된 JSON -> 안전하게 None 반환")

            # 쓰기는 정상 작동
            success = repo.save_last_check_time(datetime.now())
            self.assertTrue(success)
            print("  [OK] 손상된 파일 복구 -> 정상 저장 가능")
        finally:
            temp_path.unlink(missing_ok=True)

    def test_update_settings_repo_invalid_data_types(self):
        """Test 7-2-15: UpdateSettingsRepository 잘못된 데이터 타입"""
        print("\n[Test 7-2-15] UpdateSettingsRepository 잘못된 데이터 타입")

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json', encoding='utf-8') as f:
            temp_path = Path(f.name)

        try:
            repo = UpdateSettingsRepository(temp_path)

            # 잘못된 타입으로 저장 시도
            with self.assertRaises(TypeError):
                repo.save_last_check_time("2025-01-01")  # 문자열 (datetime이 아님)
            print("  [OK] 문자열 check_time -> TypeError 발생")

            with self.assertRaises(TypeError):
                repo.set_skipped_version("2.4.0")  # 문자열 (AppVersion이 아님)
            print("  [OK] 문자열 version -> TypeError 발생")

            with self.assertRaises(TypeError):
                repo.set_auto_check_enabled("true")  # 문자열 (bool이 아님)
            print("  [OK] 문자열 enabled -> TypeError 발생")
        finally:
            temp_path.unlink(missing_ok=True)


class TestApplicationLayerErrorHandling(unittest.TestCase):
    """Application Layer 에러 처리 테스트"""

    @patch.object(GitHubReleaseRepository, 'get_latest_release')
    def test_check_updates_github_failure(self, mock_get_latest):
        """Test 7-3-1: CheckForUpdates GitHub API 실패"""
        print("\n[Test 7-3-1] CheckForUpdates GitHub API 실패")

        mock_get_latest.return_value = None  # API 실패 시뮬레이션

        github_repo = GitHubReleaseRepository("gyh214", "simple-todo")

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json', encoding='utf-8') as f:
            temp_path = Path(f.name)

        try:
            settings_repo = UpdateSettingsRepository(temp_path)
            version_service = VersionComparisonService()

            use_case = CheckForUpdatesUseCase(
                github_repo=github_repo,
                settings_repo=settings_repo,
                version_service=version_service,
                current_version=AppVersion.from_string("2.4"),
                check_interval_hours=24
            )

            result = use_case.force_check()  # 강제 체크
            self.assertIsNone(result)
            print("  [OK] GitHub API 실패 -> None 반환")
        finally:
            temp_path.unlink(missing_ok=True)

    def test_check_updates_invalid_init_params(self):
        """Test 7-3-2: CheckForUpdates 초기화 에러"""
        print("\n[Test 7-3-2] CheckForUpdates 초기화 에러")

        github_repo = GitHubReleaseRepository("gyh214", "simple-todo")

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json', encoding='utf-8') as f:
            temp_path = Path(f.name)

        try:
            settings_repo = UpdateSettingsRepository(temp_path)
            version_service = VersionComparisonService()

            # 잘못된 타입
            with self.assertRaises(TypeError):
                CheckForUpdatesUseCase(
                    github_repo="not a repo",  # 문자열
                    settings_repo=settings_repo,
                    version_service=version_service,
                    current_version=AppVersion.from_string("2.4")
                )
            print("  [OK] 잘못된 github_repo 타입 -> TypeError 발생")

            # 잘못된 check_interval
            with self.assertRaises(ValueError):
                CheckForUpdatesUseCase(
                    github_repo=github_repo,
                    settings_repo=settings_repo,
                    version_service=version_service,
                    current_version=AppVersion.from_string("2.4"),
                    check_interval_hours=0  # 0 이하
                )
            print("  [OK] check_interval_hours=0 -> ValueError 발생")
        finally:
            temp_path.unlink(missing_ok=True)


class TestComprehensiveErrorChain(unittest.TestCase):
    """종합 에러 체인 테스트"""

    @patch('requests.get')
    def test_full_error_chain(self, mock_get):
        """Test 7-4-1: 전체 에러 체인 안전성 검증"""
        print("\n[Test 7-4-1] 전체 에러 체인 안전성 검증")

        # 1. GitHub API 실패
        mock_get.side_effect = requests.exceptions.ConnectionError("Network error")

        repo = GitHubReleaseRepository("gyh214", "simple-todo")
        release = repo.get_latest_release()
        self.assertIsNone(release)
        print("  [OK] Step 1: GitHub API 실패 -> None")

        # 2. 다운로드 실패
        mock_get.side_effect = requests.exceptions.Timeout("Timeout")

        downloader = UpdateDownloaderService()
        file_path = downloader.download(
            "https://example.com/file.exe",
            "test.exe"
        )
        self.assertIsNone(file_path)
        print("  [OK] Step 2: 다운로드 실패 -> None")

        # 3. 설치 스크립트 생성 실패
        installer = UpdateInstallerService()
        script_path = installer.create_update_script(
            Path("nonexistent.exe"),
            Path("current.exe")
        )
        self.assertIsNone(script_path)
        print("  [OK] Step 3: 스크립트 생성 실패 -> None")

        print("  [OK] 전체 에러 체인 안전하게 처리됨")

    @patch('requests.get')
    def test_recovery_after_errors(self, mock_get):
        """Test 7-4-2: 에러 후 복구 테스트"""
        print("\n[Test 7-4-2] 에러 후 복구 테스트")

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json', encoding='utf-8') as f:
            temp_path = Path(f.name)

        try:
            settings_repo = UpdateSettingsRepository(temp_path)

            # 1. 첫 번째 체크 실패
            mock_get.side_effect = requests.exceptions.ConnectionError("Network error")

            github_repo = GitHubReleaseRepository("gyh214", "simple-todo")
            version_service = VersionComparisonService()

            use_case = CheckForUpdatesUseCase(
                github_repo=github_repo,
                settings_repo=settings_repo,
                version_service=version_service,
                current_version=AppVersion.from_string("2.4"),
                check_interval_hours=24
            )

            result = use_case.force_check()
            self.assertIsNone(result)
            print("  [OK] Step 1: 네트워크 에러 -> None 반환")

            # 2. 체크 시간이 저장되었는지 확인
            last_check = settings_repo.get_last_check_time()
            self.assertIsNotNone(last_check)
            print("  [OK] Step 2: 실패 후에도 체크 시간 저장됨")

            # 3. 설정 저장/로드가 정상 작동하는지 확인
            success = settings_repo.set_skipped_version(AppVersion.from_string("2.5"))
            self.assertTrue(success)

            skipped = settings_repo.get_skipped_version()
            self.assertEqual(str(skipped), "2.5.0")
            print("  [OK] Step 3: 에러 후에도 설정 저장/로드 정상 작동")

        finally:
            temp_path.unlink(missing_ok=True)

    def test_concurrent_errors(self):
        """Test 7-4-3: 동시 에러 발생 시나리오"""
        print("\n[Test 7-4-3] 동시 에러 발생 시나리오")

        # 여러 에러가 동시에 발생해도 안전하게 처리
        errors = []

        # Domain 에러
        try:
            AppVersion.from_string("invalid")
        except ValueError as e:
            errors.append(("Domain", str(e)))

        # Infrastructure 에러
        try:
            GitHubReleaseRepository("", "")
        except ValueError as e:
            errors.append(("Infrastructure", str(e)))

        # Application 에러
        try:
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json', encoding='utf-8') as f:
                temp_path = Path(f.name)

            settings_repo = UpdateSettingsRepository(temp_path)
            settings_repo.save_last_check_time("not a datetime")
            temp_path.unlink(missing_ok=True)
        except TypeError as e:
            errors.append(("Application", str(e)))

        self.assertEqual(len(errors), 3)
        print(f"  [OK] {len(errors)}개 레이어에서 에러 안전하게 처리됨")

        for layer, msg in errors:
            print(f"    - {layer}: {msg[:60]}...")


def run_tests():
    """테스트 실행"""
    print("=" * 70)
    print("자동 업데이트 기능 에러 처리 시나리오 테스트 (Test 7)")
    print("=" * 70)
    print()

    # 테스트 스위트 생성
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Domain Layer 테스트
    print("=" * 70)
    print("Part 1: Domain Layer 에러 처리 테스트")
    print("=" * 70)
    suite.addTests(loader.loadTestsFromTestCase(TestDomainLayerErrorHandling))

    # Infrastructure Layer 테스트
    print("\n" + "=" * 70)
    print("Part 2: Infrastructure Layer 에러 처리 테스트")
    print("=" * 70)
    suite.addTests(loader.loadTestsFromTestCase(TestInfrastructureLayerErrorHandling))

    # Application Layer 테스트
    print("\n" + "=" * 70)
    print("Part 3: Application Layer 에러 처리 테스트")
    print("=" * 70)
    suite.addTests(loader.loadTestsFromTestCase(TestApplicationLayerErrorHandling))

    # 종합 테스트
    print("\n" + "=" * 70)
    print("Part 4: 종합 에러 체인 테스트")
    print("=" * 70)
    suite.addTests(loader.loadTestsFromTestCase(TestComprehensiveErrorChain))

    # 테스트 실행
    runner = unittest.TextTestRunner(verbosity=1)
    result = runner.run(suite)

    # 결과 요약
    print("\n" + "=" * 70)
    print("테스트 결과 요약")
    print("=" * 70)
    print(f"총 테스트: {result.testsRun}")
    print(f"성공: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"실패: {len(result.failures)}")
    print(f"에러: {len(result.errors)}")

    if result.wasSuccessful():
        print("\n[결론] 모든 에러 처리 시나리오가 안전하게 작동합니다!")
    else:
        print("\n[경고] 일부 에러 처리에 문제가 있습니다.")

        if result.failures:
            print("\n실패한 테스트:")
            for test, traceback in result.failures:
                print(f"  - {test}: {traceback[:200]}...")

        if result.errors:
            print("\n에러 발생 테스트:")
            for test, traceback in result.errors:
                print(f"  - {test}: {traceback[:200]}...")

    print("=" * 70)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
