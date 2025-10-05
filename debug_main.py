# -*- coding: utf-8 -*-
"""
Simple ToDo 애플리케이션 진입점 (디버그 모드)

디버그 로그를 파일과 콘솔에 모두 출력합니다.
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
LOG_FILE = LOG_DIR / f"debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

# 디버그 로깅 설정
logging.basicConfig(
    level=logging.DEBUG,  # DEBUG 레벨로 설정
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        # 파일 핸들러 (모든 로그를 파일에 저장)
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        # 콘솔 핸들러 (INFO 이상만 콘솔에 출력)
        logging.StreamHandler(sys.stdout)
    ]
)

# 콘솔 핸들러는 INFO 레벨로 설정 (너무 많은 출력 방지)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

logger = logging.getLogger(__name__)
logger.info(f"=== Simple ToDo 디버그 모드 시작 ===")
logger.info(f"로그 파일: {LOG_FILE}")


def initialize_infrastructure_layer():
    """
    Infrastructure Layer 초기화

    리포지토리, 백업 서비스, 마이그레이션 서비스 등을 생성하고 DI Container에 등록
    """
    try:
        logger.debug("Infrastructure layer 초기화 시작")

        # TodoRepository 생성
        repository = TodoRepositoryImpl(
            data_file=config.DATA_FILE,
            backup_dir=config.BACKUP_DIR,
            max_backups=config.MAX_BACKUP_COUNT
        )

        # DI Container에 등록
        Container.register(ServiceNames.TODO_REPOSITORY, repository)
        logger.info("Infrastructure layer initialized successfully")
        logger.debug(f"Repository 등록: {ServiceNames.TODO_REPOSITORY}")

        return repository

    except Exception as e:
        logger.error(f"Failed to initialize infrastructure layer: {e}", exc_info=True)
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
        logger.debug("Application layer 초기화 시작")

        # Repository 조회
        repository = Container.resolve(ServiceNames.TODO_REPOSITORY)
        logger.debug(f"Repository 조회 성공: {ServiceNames.TODO_REPOSITORY}")

        # TodoService 생성 및 등록
        todo_service = TodoService(repository=repository)
        Container.register(ServiceNames.TODO_SERVICE, todo_service)
        logger.debug(f"TodoService 등록: {ServiceNames.TODO_SERVICE}")

        # TodoSortUseCase 생성 및 등록
        sort_use_case = TodoSortUseCase(repository=repository)
        Container.register(ServiceNames.TODO_SORT_USE_CASE, sort_use_case)
        logger.debug(f"TodoSortUseCase 등록: {ServiceNames.TODO_SORT_USE_CASE}")

        # ReorderTodoUseCase 생성 및 등록
        reorder_use_case = ReorderTodoUseCase(repository=repository)
        Container.register(ServiceNames.REORDER_TODO_USE_CASE, reorder_use_case)
        logger.debug(f"ReorderTodoUseCase 등록: {ServiceNames.REORDER_TODO_USE_CASE}")

        # ChangeSortOrderUseCase 생성 및 등록
        change_sort_order_use_case = ChangeSortOrderUseCase(repository=repository)
        Container.register(ServiceNames.CHANGE_SORT_ORDER_USE_CASE, change_sort_order_use_case)
        logger.debug(f"ChangeSortOrderUseCase 등록: {ServiceNames.CHANGE_SORT_ORDER_USE_CASE}")

        # DataPreservationService는 static 메서드만 있으므로 등록 불필요

        logger.info("Application layer initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize application layer: {e}", exc_info=True)
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
    logger.debug("Presentation layer 초기화 시작")
    logger.info("Presentation layer initialized successfully")


def main():
    """애플리케이션 진입점 (디버그 모드)"""
    from PyQt6.QtWidgets import QMessageBox
    from src.presentation.system.single_instance import SingleInstanceManager

    logger.debug("QApplication 생성 시작")
    app = QApplication(sys.argv)

    # 애플리케이션 설정
    app.setApplicationName(config.APP_NAME)
    app.setApplicationVersion(config.APP_VERSION)
    logger.debug(f"Application name: {config.APP_NAME}, version: {config.APP_VERSION}")

    # 단일 인스턴스 체크
    logger.debug("단일 인스턴스 매니저 생성")
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
        logger.debug("Exiting current instance (duplicate)")
        sys.exit(0)

    # 첫 실행 - 활성화 요청 수신 리스너 시작
    logger.debug("활성화 요청 리스너 시작")
    single_instance.start_listener()

    # DI Container 초기화 (Infrastructure → Application → Presentation)
    logger.info("DI Container 초기화 시작")
    repository = initialize_infrastructure_layer()
    initialize_application_layer()
    initialize_presentation_layer()
    logger.info("DI Container 초기화 완료")

    # 메인 윈도우 생성 (Repository 주입)
    logger.debug("MainWindow 생성 시작")
    window = MainWindow(repository=repository)

    # 활성화 요청 시 창 표시
    single_instance.activate_requested.connect(
        lambda: (
            logger.debug("활성화 요청 수신"),
            window.show(),
            window.activateWindow(),
            window.raise_()
        )
    )

    logger.debug("MainWindow 표시")
    window.show()

    logger.info(f"{config.APP_NAME} started successfully")
    logger.info(f"로그는 {LOG_FILE}에 저장됩니다")

    # 이벤트 루프 실행
    logger.debug("이벤트 루프 시작")
    exit_code = app.exec()
    logger.debug(f"이벤트 루프 종료, exit_code: {exit_code}")

    # 정리
    logger.debug("SingleInstanceManager cleanup")
    single_instance.cleanup()

    logger.info(f"=== Simple ToDo 종료 (exit_code: {exit_code}) ===")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
