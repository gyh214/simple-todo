# -*- coding: utf-8 -*-
"""
Phase 4: Application Layer 사용 예제

이 파일은 자동 업데이트 기능의 Application Layer 사용 방법을 보여줍니다.
Presentation Layer에서 참고할 수 있도록 작성되었습니다.
"""

import sys
from pathlib import Path
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import (
    APP_VERSION,
    GITHUB_REPO_OWNER,
    GITHUB_REPO_NAME,
    UPDATE_CHECK_INTERVAL_HOURS,
    DATA_FILE
)

# Domain Layer
from src.domain.value_objects.app_version import AppVersion
from src.domain.services.version_comparison_service import VersionComparisonService

# Infrastructure Layer
from src.infrastructure.repositories.github_release_repository import GitHubReleaseRepository
from src.infrastructure.repositories.update_settings_repository import UpdateSettingsRepository
from src.infrastructure.services.update_downloader_service import UpdateDownloaderService
from src.infrastructure.services.update_installer_service import UpdateInstallerService

# Application Layer
from src.application.use_cases.check_for_updates import CheckForUpdatesUseCase
from src.application.use_cases.download_update import DownloadUpdateUseCase
from src.application.use_cases.install_update import InstallUpdateUseCase
from src.application.services.update_scheduler_service import UpdateSchedulerService


def example_1_app_startup_check():
    """예제 1: 앱 시작 시 자동 업데이트 체크

    Presentation Layer (main_window.py)에서 앱 시작 시 호출됩니다.
    """
    print("=" * 60)
    print("예제 1: 앱 시작 시 자동 업데이트 체크")
    print("=" * 60)

    # 1. 의존성 주입 (DI Container에서 생성)
    current_version = AppVersion.from_string(APP_VERSION)

    github_repo = GitHubReleaseRepository(
        repo_owner=GITHUB_REPO_OWNER,
        repo_name=GITHUB_REPO_NAME
    )

    settings_repo = UpdateSettingsRepository(DATA_FILE)
    version_service = VersionComparisonService()

    check_use_case = CheckForUpdatesUseCase(
        github_repo=github_repo,
        settings_repo=settings_repo,
        version_service=version_service,
        current_version=current_version,
        check_interval_hours=UPDATE_CHECK_INTERVAL_HOURS
    )

    scheduler = UpdateSchedulerService(
        check_use_case=check_use_case,
        settings_repo=settings_repo
    )

    # 2. 앱 시작 시 체크 여부 확인
    if scheduler.should_check_on_startup():
        print("자동 업데이트 체크 활성화됨")

        # 3. 업데이트 확인
        release = scheduler.check_and_notify()

        if release:
            print(f"\n업데이트 가능!")
            print(f"  현재 버전: {current_version}")
            print(f"  최신 버전: {release.version}")
            print(f"  파일 크기: {release.format_file_size()}")
            print(f"  공개 날짜: {release.format_published_date()}")
            print(f"\n릴리스 노트:\n{release.get_short_release_notes()}")

            # UI에서 업데이트 다이얼로그 표시
            # show_update_dialog(release)
        else:
            print("업데이트 없음")
    else:
        print("자동 업데이트 체크 비활성화됨")


def example_2_manual_check():
    """예제 2: 사용자가 수동으로 업데이트 확인

    메뉴에서 "업데이트 확인" 버튼 클릭 시 호출됩니다.
    """
    print("\n" + "=" * 60)
    print("예제 2: 수동 업데이트 확인")
    print("=" * 60)

    # 1. 의존성 주입
    current_version = AppVersion.from_string(APP_VERSION)
    github_repo = GitHubReleaseRepository(GITHUB_REPO_OWNER, GITHUB_REPO_NAME)
    settings_repo = UpdateSettingsRepository(DATA_FILE)
    version_service = VersionComparisonService()

    check_use_case = CheckForUpdatesUseCase(
        github_repo=github_repo,
        settings_repo=settings_repo,
        version_service=version_service,
        current_version=current_version,
        check_interval_hours=UPDATE_CHECK_INTERVAL_HOURS
    )

    scheduler = UpdateSchedulerService(check_use_case, settings_repo)

    # 2. 건너뛴 버전 초기화 (수동 체크이므로)
    scheduler.reset_skipped_version()

    # 3. 강제 체크 (24시간 무시)
    print("업데이트 확인 중...")
    release = check_use_case.force_check()

    if release:
        print(f"\n업데이트 발견: {release.version}")
        print("업데이트 다이얼로그 표시")
        # show_update_dialog(release)
    else:
        print("\n최신 버전입니다!")
        # show_message("이미 최신 버전입니다.")


def example_3_download_and_install():
    """예제 3: 업데이트 다운로드 및 설치

    사용자가 업데이트 다이얼로그에서 "업데이트" 버튼 클릭 시 호출됩니다.
    """
    print("\n" + "=" * 60)
    print("예제 3: 업데이트 다운로드 및 설치")
    print("=" * 60)

    # 1. 업데이트 확인 (예제 1,2에서 받은 release 객체 사용)
    # 여기서는 임시로 release를 조회
    current_version = AppVersion.from_string(APP_VERSION)
    github_repo = GitHubReleaseRepository(GITHUB_REPO_OWNER, GITHUB_REPO_NAME)

    release = github_repo.get_latest_release()

    if not release:
        print("최신 릴리스를 찾을 수 없습니다")
        return

    if not release.is_newer_than(current_version):
        print("이미 최신 버전입니다")
        return

    # 2. 다운로드
    print(f"\n다운로드 시작: {release.asset_name} ({release.format_file_size()})")

    downloader = UpdateDownloaderService()
    download_use_case = DownloadUpdateUseCase(
        downloader=downloader,
        filename="SimpleTodo_new.exe"
    )

    # 진행률 콜백
    def on_progress(downloaded: int, total: int):
        if total > 0:
            percent = (downloaded / total) * 100
            print(f"  진행률: {percent:.1f}% ({downloaded:,} / {total:,} bytes)")
        else:
            print(f"  다운로드 중: {downloaded:,} bytes")

    # 다운로드 수행
    new_exe_path = download_use_case.execute(
        release=release,
        progress_callback=on_progress
    )

    if not new_exe_path:
        print("\n다운로드 실패!")
        # show_error("다운로드에 실패했습니다.")
        return

    print(f"\n다운로드 완료: {new_exe_path}")

    # 3. 설치
    print("\n설치 시작...")

    current_exe_path = Path(sys.executable)
    installer = UpdateInstallerService()
    install_use_case = InstallUpdateUseCase(
        installer=installer,
        current_exe_path=current_exe_path
    )

    # 설치 전 검증
    if not install_use_case.verify_new_exe(new_exe_path):
        print("파일 검증 실패!")
        return

    # 종료 준비
    install_use_case.prepare_for_shutdown()

    # 설치 및 재시작
    success = install_use_case.execute(new_exe_path)

    if success:
        print("\n업데이트가 시작되었습니다.")
        print("애플리케이션이 곧 종료되고 새 버전으로 재시작됩니다.")
        # QApplication.quit()
    else:
        print("\n설치 실패!")
        # show_error("설치에 실패했습니다.")


def example_4_skip_version():
    """예제 4: 버전 건너뛰기

    사용자가 업데이트 다이얼로그에서 "건너뛰기" 버튼 클릭 시 호출됩니다.
    """
    print("\n" + "=" * 60)
    print("예제 4: 버전 건너뛰기")
    print("=" * 60)

    # 1. 최신 릴리스 조회
    github_repo = GitHubReleaseRepository(GITHUB_REPO_OWNER, GITHUB_REPO_NAME)
    release = github_repo.get_latest_release()

    if not release:
        print("최신 릴리스를 찾을 수 없습니다")
        return

    # 2. 스케줄러에서 버전 건너뛰기
    settings_repo = UpdateSettingsRepository(DATA_FILE)
    check_use_case = CheckForUpdatesUseCase(
        github_repo=github_repo,
        settings_repo=settings_repo,
        version_service=VersionComparisonService(),
        current_version=AppVersion.from_string(APP_VERSION),
        check_interval_hours=UPDATE_CHECK_INTERVAL_HOURS
    )

    scheduler = UpdateSchedulerService(check_use_case, settings_repo)

    success = scheduler.skip_version(release.version)

    if success:
        print(f"버전 {release.version}을(를) 건너뛰기로 설정했습니다")
        print("다음에 업데이트 확인 시 이 버전은 알림 표시되지 않습니다")
    else:
        print("건너뛰기 설정 실패")


def example_5_settings():
    """예제 5: 자동 업데이트 설정 관리

    설정 다이얼로그에서 자동 업데이트 옵션 변경 시 호출됩니다.
    """
    print("\n" + "=" * 60)
    print("예제 5: 자동 업데이트 설정 관리")
    print("=" * 60)

    settings_repo = UpdateSettingsRepository(DATA_FILE)
    github_repo = GitHubReleaseRepository(GITHUB_REPO_OWNER, GITHUB_REPO_NAME)
    check_use_case = CheckForUpdatesUseCase(
        github_repo=github_repo,
        settings_repo=settings_repo,
        version_service=VersionComparisonService(),
        current_version=AppVersion.from_string(APP_VERSION),
        check_interval_hours=UPDATE_CHECK_INTERVAL_HOURS
    )

    scheduler = UpdateSchedulerService(check_use_case, settings_repo)

    # 1. 현재 상태 조회
    is_enabled = scheduler.get_auto_check_status()
    skipped_version = scheduler.get_skipped_version()

    print(f"자동 체크: {'활성화' if is_enabled else '비활성화'}")
    print(f"건너뛴 버전: {skipped_version if skipped_version else '없음'}")

    # 2. 자동 체크 비활성화
    print("\n자동 체크 비활성화...")
    scheduler.enable_auto_check(False)
    print(f"자동 체크: {'활성화' if scheduler.get_auto_check_status() else '비활성화'}")

    # 3. 다시 활성화
    print("\n자동 체크 활성화...")
    scheduler.enable_auto_check(True)
    print(f"자동 체크: {'활성화' if scheduler.get_auto_check_status() else '비활성화'}")


def main():
    """모든 예제 실행"""
    print("\n" + "=" * 60)
    print("Phase 4: Application Layer 사용 예제")
    print("=" * 60)
    print(f"현재 버전: {APP_VERSION}")
    print(f"GitHub: {GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}")
    print(f"체크 간격: {UPDATE_CHECK_INTERVAL_HOURS}시간")
    print("=" * 60)

    try:
        # 예제 1: 앱 시작 시 자동 체크
        example_1_app_startup_check()

        # 예제 2: 수동 체크
        # example_2_manual_check()

        # 예제 3: 다운로드 및 설치 (실제 다운로드 수행, 주의!)
        # example_3_download_and_install()

        # 예제 4: 버전 건너뛰기
        # example_4_skip_version()

        # 예제 5: 설정 관리
        # example_5_settings()

    except KeyboardInterrupt:
        print("\n\n중단됨")
    except Exception as e:
        print(f"\n\n오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
