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

# 로그 디렉토리 생성
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


def main():
    """애플리케이션 진입점"""
    from PyQt6.QtWidgets import QMessageBox
    from src.presentation.system.single_instance import SingleInstanceManager

    app = QApplication(sys.argv)

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

    # DI Container 초기화 (Infrastructure → Application → Presentation)
    repository = initialize_infrastructure_layer()
    initialize_application_layer()
    initialize_presentation_layer()

    # 메인 윈도우 생성 (Repository 주입)
    window = MainWindow(repository=repository)

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
