# -*- coding: utf-8 -*-
"""
GitHub API 통신 테스트 스크립트

Simple ToDo 애플리케이션의 GitHubReleaseRepository가 실제 GitHub API와
정상적으로 통신하여 릴리스 정보를 가져올 수 있는지 검증합니다.
"""

import sys
import io
from pathlib import Path

# Windows 콘솔 UTF-8 인코딩 설정
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 프로젝트 루트를 sys.path에 추가
sys.path.insert(0, str(Path(__file__).parent))

import requests
import config
from datetime import datetime
from src.infrastructure.repositories.github_release_repository import GitHubReleaseRepository
from src.domain.entities.release import Release
from src.domain.value_objects.app_version import AppVersion


def safe_print(text):
    """안전하게 텍스트를 출력합니다 (이모지 등 특수문자 처리)"""
    try:
        print(text)
    except UnicodeEncodeError:
        # 출력 불가능한 문자는 ?로 대체
        print(text.encode('ascii', errors='replace').decode('ascii'))


def test_github_api_connection():
    """GitHub API 직접 연결 테스트"""
    print("=== Test 6-1: GitHub API 직접 연결 ===\n")

    url = f"https://api.github.com/repos/{config.GITHUB_REPO_OWNER}/{config.GITHUB_REPO_NAME}/releases/latest"

    print(f"Testing URL: {url}")

    try:
        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'SimpleTodo-Test/1.0'
        }
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            print("[OK] API 연결 성공 - 릴리스 존재")
            data = response.json()
            print(f"    - Tag: {data.get('tag_name', 'N/A')}")
            safe_print(f"    - Name: {data.get('name', 'N/A')}")
            print(f"    - Published: {data.get('published_at', 'N/A')}")
            print(f"    - Assets: {len(data.get('assets', []))}")
            if data.get('assets'):
                for asset in data.get('assets', []):
                    print(f"      * {asset.get('name')} ({asset.get('size', 0):,} bytes)")
            return True
        elif response.status_code == 404:
            print("[WARN] 릴리스가 아직 존재하지 않음 (404)")
            print("       -> 정상적인 상황입니다. 첫 릴리스를 만들어주세요.")
            return False
        elif response.status_code == 403:
            print("[ERROR] GitHub API rate limit 초과 (403)")
            print("        -> 잠시 후 다시 시도하세요.")
            return False
        else:
            print(f"[WARN] Unexpected status code: {response.status_code}")
            print(f"       Response: {response.text[:200]}")
            return False

    except requests.exceptions.Timeout:
        print("[ERROR] Timeout - GitHub API 응답 시간 초과")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"[ERROR] Connection Error - 네트워크 연결 실패: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_github_release_repository():
    """GitHubReleaseRepository.get_latest_release() 테스트"""
    print("\n=== Test 6-2: GitHubReleaseRepository.get_latest_release() ===\n")

    repo = GitHubReleaseRepository(
        repo_owner=config.GITHUB_REPO_OWNER,
        repo_name=config.GITHUB_REPO_NAME
    )

    print(f"Repository: {repo}")

    try:
        release = repo.get_latest_release()

        if release is None:
            print("[WARN] No release found (None returned)")
            print("       -> GitHubReleaseRepository가 올바르게 None을 반환했습니다.")
            print("       -> 첫 GitHub Release를 만들어주세요.")
            return False

        print("[OK] Release 객체 생성 성공\n")

        # Release 엔티티 검증
        assert isinstance(release, Release), "release should be Release instance"
        print(f"[OK] Release 인스턴스 확인")

        assert isinstance(release.version, AppVersion), "version should be AppVersion instance"
        print(f"[OK] Version: {release.version}")

        assert isinstance(release.download_url, str), "download_url should be string"
        assert release.download_url.startswith("http"), "download_url should be URL"
        print(f"[OK] Download URL: {release.download_url}")

        assert isinstance(release.release_notes, str), "release_notes should be string"
        print(f"[OK] Release Notes: {len(release.release_notes)} characters")
        if release.release_notes:
            # 릴리스 노트 미리보기 (이모지 제거)
            preview = release.get_short_release_notes(100)
            # ASCII로 변환 가능한 부분만 출력
            safe_preview = preview.encode('ascii', errors='replace').decode('ascii')
            print(f"     Preview: {safe_preview}")

        assert isinstance(release.published_at, datetime), "published_at should be datetime"
        print(f"[OK] Published At: {release.published_at}")

        assert isinstance(release.asset_name, str), "asset_name should be string"
        print(f"[OK] Asset Name: {release.asset_name}")

        assert isinstance(release.asset_size, int), "asset_size should be int"
        assert release.asset_size > 0, "asset_size should be positive"
        print(f"[OK] Asset Size: {release.asset_size:,} bytes ({release.asset_size / 1024 / 1024:.2f} MB)")

        print(f"\n[SUCCESS] Release 엔티티 검증 완료")
        print(f"\nRelease 정보:")
        print(f"  {release}")

        # 현재 버전과 비교
        current_version = AppVersion.from_string(config.APP_VERSION)
        print(f"\n현재 설치된 버전: {current_version}")
        print(f"최신 릴리스 버전: {release.version}")

        if release.is_newer_than(current_version):
            print(f"[INFO] 새로운 버전이 있습니다! ({current_version} -> {release.version})")
        elif release.version == current_version:
            print(f"[INFO] 최신 버전을 사용 중입니다.")
        else:
            print(f"[INFO] 개발 버전을 사용 중입니다. (릴리스 버전보다 높음)")

        return True

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False


def test_error_handling():
    """에러 처리 검증"""
    print("\n=== Test 6-3: 에러 처리 검증 ===\n")

    # 1. 존재하지 않는 repo_name
    print("Test 6-3-1: 존재하지 않는 repo_name")
    repo = GitHubReleaseRepository(
        repo_owner=config.GITHUB_REPO_OWNER,
        repo_name="nonexistent-repo-12345-xyz"
    )

    try:
        release = repo.get_latest_release()
        assert release is None, "Should return None for non-existent repo"
        print("[OK] 존재하지 않는 repo에 대해 None 반환")
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")

    # 2. 잘못된 repo_owner
    print("\nTest 6-3-2: 존재하지 않는 repo_owner")
    repo = GitHubReleaseRepository(
        repo_owner="nonexistent-user-12345-xyz",
        repo_name=config.GITHUB_REPO_NAME
    )

    try:
        release = repo.get_latest_release()
        assert release is None, "Should return None for non-existent owner"
        print("[OK] 존재하지 않는 owner에 대해 None 반환")
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")

    # 3. ValueError 검증 (빈 문자열)
    print("\nTest 6-3-3: ValueError 검증 (빈 repo_owner)")
    try:
        repo = GitHubReleaseRepository(
            repo_owner="",
            repo_name=config.GITHUB_REPO_NAME
        )
        print("[ERROR] ValueError가 발생해야 합니다")
    except ValueError as e:
        print(f"[OK] ValueError 발생: {e}")

    print("\nTest 6-3-4: ValueError 검증 (빈 repo_name)")
    try:
        repo = GitHubReleaseRepository(
            repo_owner=config.GITHUB_REPO_OWNER,
            repo_name=""
        )
        print("[ERROR] ValueError가 발생해야 합니다")
    except ValueError as e:
        print(f"[OK] ValueError 발생: {e}")

    print("\n[SUCCESS] 에러 처리 검증 완료")


def test_app_version_parsing():
    """AppVersion 파싱 테스트"""
    print("\n=== Test 6-4: AppVersion 파싱 테스트 ===\n")

    test_cases = [
        ("2.4", "2.4.0"),
        ("v2.4", "2.4.0"),
        ("2.4.1", "2.4.1"),
        ("v2.4.1", "2.4.1"),
        ("3.0", "3.0.0"),
        ("10.15.3", "10.15.3"),
    ]

    for input_str, expected_str in test_cases:
        try:
            version = AppVersion.from_string(input_str)
            assert str(version) == expected_str, f"Expected {expected_str}, got {version}"
            print(f"[OK] '{input_str}' -> {version}")
        except Exception as e:
            print(f"[ERROR] '{input_str}' 파싱 실패: {e}")

    # 버전 비교 테스트
    print("\n버전 비교 테스트:")
    v1 = AppVersion.from_string("2.4")
    v2 = AppVersion.from_string("2.5")
    v3 = AppVersion.from_string("2.4.1")
    v4 = AppVersion.from_string("3.0")

    assert v1 < v2, "2.4 < 2.5"
    print(f"[OK] {v1} < {v2}")

    assert v1 < v3, "2.4 < 2.4.1"
    print(f"[OK] {v1} < {v3}")

    assert v2 < v4, "2.5 < 3.0"
    print(f"[OK] {v2} < {v4}")

    assert v1 == AppVersion.from_string("2.4.0"), "2.4 == 2.4.0"
    print(f"[OK] {v1} == 2.4.0")

    print("\n[SUCCESS] AppVersion 파싱 및 비교 테스트 완료")


if __name__ == "__main__":
    print("="*70)
    print("  GitHub API 통신 테스트")
    print("="*70)
    print(f"\nRepository: {config.GITHUB_REPO_OWNER}/{config.GITHUB_REPO_NAME}")
    print(f"현재 버전: {config.APP_VERSION}")
    print()

    # Test 6-1: GitHub API 직접 연결
    has_release = test_github_api_connection()

    # Test 6-2: GitHubReleaseRepository 테스트
    test_github_release_repository()

    # Test 6-3: 에러 처리 검증
    test_error_handling()

    # Test 6-4: AppVersion 파싱 테스트
    test_app_version_parsing()

    print("\n" + "="*70)
    print("테스트 완료")
    print("="*70)

    if not has_release:
        print("\n⚠️  중요: GitHub Release가 아직 생성되지 않았습니다.")
        print("   다음 명령으로 첫 릴리스를 만들어주세요:")
        print(f"   1. 빌드: python build.py")
        print(f"   2. GitHub에서 새 릴리스 생성:")
        print(f"      - URL: https://github.com/{config.GITHUB_REPO_OWNER}/{config.GITHUB_REPO_NAME}/releases/new")
        print(f"      - Tag: v{config.APP_VERSION}")
        print(f"      - Title: v{config.APP_VERSION}")
        print(f"      - 파일 업로드: dist/SimpleTodo.exe")
