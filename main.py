# -*- coding: utf-8 -*-
"""
Simple ToDo 애플리케이션 진입점
"""
import sys
import logging
from pathlib import Path
from datetime import datetime
from PyQt6.QtWidgets import QApplication

import config
from src.core.container import Container, ServiceNames
from src.presentation.ui.main_window import MainWindow
from src.infrastructure.repositories.todo_repository_impl import TodoRepositoryImpl

# PyInstaller 환경에서도 안전한 로그 디렉토리 설정
# PyInstaller: sys.executable는 exe 위치를 나타냄
# 일반 Python: sys.executable는 python.exe 위치를 나타냄 (사용 안 함)
if getattr(sys, 'frozen', False):
    # PyInstaller로 빌드된 실행 파일인 경우
    LOG_DIR = Path(sys.executable).parent / "logs"
else:
    # 일반 Python 스크립트로 실행된 경우 (개발 환경)
    LOG_DIR = Path(__file__).parent / "logs"

LOG_DIR.mkdir(exist_ok=True)

# 로그 파일명 (타임스탬프 포함)
LOG_FILE = LOG_DIR / f"app_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

# 로깅 설정 (파일 + 콘솔)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        # 파일 핸들러 (모든 로그를 파일에 저장)
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        # 콘솔 핸들러 (INFO 이상만 콘솔에 출력)
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)
logger.info(f"=== {config.APP_NAME} 시작 ===")
logger.info(f"로그 파일: {LOG_FILE}")
logger.info(f"PyInstaller 환경: {getattr(sys, 'frozen', False)}")


def setup_global_exception_handler():
    """
    전역 예외 핸들러 설정

    처리되지 않은 예외를 로그에 기록하고 사용자에게 알림.
    프로그램 크래시 시에도 로그 파일에 스택 트레이스가 남아 디버깅 용이.
    """
    def handle_exception(exc_type, exc_value, exc_traceback):
        """처리되지 않은 예외를 처리하는 핸들러"""
        if issubclass(exc_type, KeyboardInterrupt):
            # Ctrl+C는 정상 종료이므로 로그하지 않음
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        # 예외를 로그에 기록 (전체 스택 트레이스 포함)
        logger.critical(
            "처리되지 않은 예외 발생",
            exc_info=(exc_type, exc_value, exc_traceback)
        )

    sys.excepthook = handle_exception


def initialize_infrastructure_layer():
    """
    Infrastructure Layer 초기화

    리포지토리, 백업 서비스, 마이그레이션 서비스 등을 생성하고 DI Container에 등록
    """
    try:
        # TodoRepository 생성
        repository = TodoRepositoryImpl(
            data_file=config.DATA_FILE,
            backup_dir=config.BACKUP_DIR,
            max_backups=config.MAX_BACKUP_COUNT
        )

        # DI Container에 등록
        Container.register(ServiceNames.TODO_REPOSITORY, repository)
        logger.info("Infrastructure layer initialized successfully")

        return repository

    except Exception as e:
        logger.error(f"Failed to initialize infrastructure layer: {e}")
        raise


def initialize_application_layer():
    """
    Application Layer 초기화

    서비스, 유스케이스 등을 생성하고 DI Container에 등록
    Infrastructure Layer의 의존성 주입
    """
    from src.application.services.todo_service import TodoService
    from src.application.use_cases.sort_todos import TodoSortUseCase
    from src.application.use_cases.reorder_todo import ReorderTodoUseCase
    from src.application.use_cases.change_sort_order import ChangeSortOrderUseCase

    try:
        # Repository 조회
        repository = Container.resolve(ServiceNames.TODO_REPOSITORY)

        # TodoService 생성 및 등록
        todo_service = TodoService(repository=repository)
        Container.register(ServiceNames.TODO_SERVICE, todo_service)

        # TodoSortUseCase 생성 및 등록
        sort_use_case = TodoSortUseCase(repository=repository)
        Container.register(ServiceNames.TODO_SORT_USE_CASE, sort_use_case)

        # ReorderTodoUseCase 생성 및 등록
        reorder_use_case = ReorderTodoUseCase(repository=repository)
        Container.register(ServiceNames.REORDER_TODO_USE_CASE, reorder_use_case)

        # ChangeSortOrderUseCase 생성 및 등록
        change_sort_order_use_case = ChangeSortOrderUseCase(repository=repository)
        Container.register(ServiceNames.CHANGE_SORT_ORDER_USE_CASE, change_sort_order_use_case)

        # DataPreservationService는 static 메서드만 있으므로 등록 불필요

        logger.info("Application layer initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize application layer: {e}")
        raise


def initialize_update_services():
    """
    Phase 6: Update 관련 서비스 초기화

    자동 업데이트 기능을 위한 모든 레이어의 서비스를 생성하고 DI Container에 등록
    """
    try:
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

        # Infrastructure Layer 등록
        github_repo = GitHubReleaseRepository(
            repo_owner=config.GITHUB_REPO_OWNER,
            repo_name=config.GITHUB_REPO_NAME
        )
        Container.register(ServiceNames.GITHUB_RELEASE_REPOSITORY, github_repo)

        settings_repo = UpdateSettingsRepository(config.DATA_FILE)
        Container.register(ServiceNames.UPDATE_SETTINGS_REPOSITORY, settings_repo)

        downloader = UpdateDownloaderService()
        Container.register(ServiceNames.UPDATE_DOWNLOADER_SERVICE, downloader)

        installer = UpdateInstallerService()
        Container.register(ServiceNames.UPDATE_INSTALLER_SERVICE, installer)

        # Application Layer 등록
        current_version = AppVersion.from_string(config.APP_VERSION)
        version_service = VersionComparisonService()

        check_use_case = CheckForUpdatesUseCase(
            github_repo=github_repo,
            settings_repo=settings_repo,
            version_service=version_service,
            current_version=current_version,
            check_interval_hours=config.UPDATE_CHECK_INTERVAL_HOURS
        )
        Container.register(ServiceNames.CHECK_FOR_UPDATES_USE_CASE, check_use_case)

        download_use_case = DownloadUpdateUseCase(
            downloader=downloader,
            filename="SimpleTodo_new.exe"
        )
        Container.register(ServiceNames.DOWNLOAD_UPDATE_USE_CASE, download_use_case)

        install_use_case = InstallUpdateUseCase(
            installer=installer,
            current_exe_path=Path(sys.executable)
        )
        Container.register(ServiceNames.INSTALL_UPDATE_USE_CASE, install_use_case)

        scheduler = UpdateSchedulerService(
            check_use_case=check_use_case,
            settings_repo=settings_repo
        )
        Container.register(ServiceNames.UPDATE_SCHEDULER_SERVICE, scheduler)

        logger.info("Update services initialized successfully")
        return True

    except Exception as e:
        logger.error(f"Failed to initialize update services: {e}")
        # 업데이트 기능은 선택 사항이므로 앱 시작을 중단하지 않음
        logger.warning("App will continue without auto-update feature")
        return False


def initialize_presentation_layer():
    """
    Presentation Layer 초기화

    UI 컴포넌트, 시스템 매니저 등을 생성하고 DI Container에 등록
    Application Layer의 의존성 주입
    """
    # SystemTrayManager는 MainWindow에서 생성됨
    # SingleInstanceManager는 main()에서 직접 처리됨
    # WindowManager는 MainWindow 내부에서 생성됨
    logger.info("Presentation layer initialized successfully")


def setup_global_palette(app):
    """
    전역 QPalette 설정 (다크 모드 강제 적용)

    Windows 시스템 테마와 무관하게 config.COLORS 기반 다크 모드 적용
    """
    from PyQt6.QtGui import QPalette, QColor

    palette = QPalette()

    # Helper: rgba 문자열을 QColor로 변환
    def parse_color(color_str):
        if color_str.startswith('rgba'):
            # rgba(255, 255, 255, 0.92) -> QColor
            parts = color_str.replace('rgba(', '').replace(')', '').split(',')
            r, g, b = int(parts[0]), int(parts[1]), int(parts[2])
            a = int(float(parts[3]) * 255)
            return QColor(r, g, b, a)
        else:
            # #RRGGBB -> QColor
            return QColor(color_str)

    # 배경 색상
    palette.setColor(QPalette.ColorRole.Window, parse_color(config.COLORS['primary_bg']))
    palette.setColor(QPalette.ColorRole.Base, parse_color(config.COLORS['secondary_bg']))
    palette.setColor(QPalette.ColorRole.AlternateBase, parse_color(config.COLORS['card']))

    # 텍스트 색상
    palette.setColor(QPalette.ColorRole.WindowText, parse_color(config.COLORS['text_primary']))
    palette.setColor(QPalette.ColorRole.Text, parse_color(config.COLORS['text_primary']))
    palette.setColor(QPalette.ColorRole.ButtonText, parse_color(config.COLORS['text_primary']))
    palette.setColor(QPalette.ColorRole.BrightText, parse_color(config.COLORS['text_primary']))

    # 버튼 배경
    palette.setColor(QPalette.ColorRole.Button, parse_color(config.COLORS['secondary_bg']))

    # 하이라이트 (선택 영역)
    palette.setColor(QPalette.ColorRole.Highlight, parse_color(config.COLORS['accent']))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor('#FFFFFF'))

    # 링크
    palette.setColor(QPalette.ColorRole.Link, parse_color(config.COLORS['accent']))
    palette.setColor(QPalette.ColorRole.LinkVisited, parse_color(config.COLORS['accent_hover']))

    # 비활성화 상태 (Disabled 그룹)
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText,
                     parse_color(config.COLORS['text_disabled']))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text,
                     parse_color(config.COLORS['text_disabled']))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText,
                     parse_color(config.COLORS['text_disabled']))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Button,
                     parse_color(config.COLORS['card']))

    # 툴팁 색상
    palette.setColor(QPalette.ColorRole.ToolTipBase, parse_color(config.COLORS['secondary_bg']))
    palette.setColor(QPalette.ColorRole.ToolTipText, parse_color(config.COLORS['text_primary']))

    # 플레이스홀더 색상 (QLineEdit, QTextEdit)
    palette.setColor(QPalette.ColorRole.PlaceholderText, parse_color(config.COLORS['text_disabled']))

    # 전역 팔레트 적용
    app.setPalette(palette)

    # Fusion 스타일 적용 (플랫폼 독립적 일관성)
    app.setStyle('Fusion')

    logger.info("Global QPalette applied (Dark Mode enforced)")


def main():
    """애플리케이션 진입점"""
    from PyQt6.QtWidgets import QMessageBox
    from src.presentation.system.single_instance import SingleInstanceManager

    # 전역 예외 핸들러 설정 (프로그램 크래시 시 로그 기록)
    setup_global_exception_handler()

    app = QApplication(sys.argv)

    # 전역 다크 모드 팔레트 적용 (Windows 시스템 테마 무시)
    setup_global_palette(app)

    # 애플리케이션 설정
    app.setApplicationName(config.APP_NAME)
    app.setApplicationVersion(config.APP_VERSION)

    # 애플리케이션 아이콘 설정 (작업관리자 아이콘)
    from PyQt6.QtGui import QIcon
    icon_path = config.get_resource_path(config.ICON_FILE)
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
        logger.info(f"Application icon set: {icon_path}")
    else:
        logger.warning(f"Icon file not found: {icon_path}")

    # 단일 인스턴스 체크
    single_instance = SingleInstanceManager()

    if single_instance.is_already_running():
        # 이미 실행 중인 경우
        logger.info("Application is already running. Activating existing instance.")

        # 기존 인스턴스 활성화 시도
        if single_instance.activate_existing_instance():
            logger.info("Existing instance activated successfully")
        else:
            logger.warning("Failed to activate existing instance")

        # 메시지 박스 표시
        QMessageBox.information(
            None,
            config.APP_NAME,
            "Simple ToDo가 이미 실행 중입니다.\n기존 창이 활성화됩니다."
        )

        # 현재 인스턴스 종료
        sys.exit(0)

    # 첫 실행 - 활성화 요청 수신 리스너 시작
    single_instance.start_listener()

    # DI Container 초기화 (Infrastructure → Application → Update → Presentation)
    repository = initialize_infrastructure_layer()
    initialize_application_layer()
    initialize_update_services()  # Phase 6: 업데이트 서비스 초기화
    initialize_presentation_layer()

    # 메인 윈도우 생성 (Repository 주입)
    window = MainWindow(repository=repository)

    # Phase 6: UpdateManager 생성 및 주입 (선택적)
    try:
        from src.presentation.system.update_manager import UpdateManager
        from src.domain.value_objects.app_version import AppVersion

        update_manager = UpdateManager(
            parent_window=window,
            scheduler=Container.resolve(ServiceNames.UPDATE_SCHEDULER_SERVICE),
            check_use_case=Container.resolve(ServiceNames.CHECK_FOR_UPDATES_USE_CASE),
            download_use_case=Container.resolve(ServiceNames.DOWNLOAD_UPDATE_USE_CASE),
            install_use_case=Container.resolve(ServiceNames.INSTALL_UPDATE_USE_CASE),
            current_version=AppVersion.from_string(config.APP_VERSION)
        )

        # UpdateManager를 MainWindow에 설정
        window.set_update_manager(update_manager)
        logger.info("UpdateManager integrated successfully")

    except Exception as e:
        logger.error(f"Failed to integrate UpdateManager: {e}")
        logger.warning("App will continue without auto-update UI integration")

    # 활성화 요청 시 창 표시
    single_instance.activate_requested.connect(lambda: (window.show(), window.activateWindow(), window.raise_()))

    window.show()

    logger.info(f"{config.APP_NAME} started successfully")
    logger.info(f"로그는 {LOG_FILE}에 저장됩니다")

    # 이벤트 루프 실행
    exit_code = app.exec()

    # 정리
    single_instance.cleanup()

    logger.info(f"=== {config.APP_NAME} 종료 (exit_code: {exit_code}) ===")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
