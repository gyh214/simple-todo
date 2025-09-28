"""
표준화된 로깅 설정 모듈 (Phase 4B)

Windows 환경에 최적화된 로깅 시스템을 제공합니다.
DRY+CLEAN+Simple 원칙을 적용하여 일관된 로깅 경험을 제공합니다.
"""

import logging
import logging.handlers
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


class TodoPanelLogFormatter(logging.Formatter):
    """TODO Panel 전용 로그 포맷터

    컬러 출력과 상세한 정보를 제공하는 커스텀 포맷터입니다.
    """

    # 로그 레벨별 색상 코드 (ANSI)
    COLORS = {
        "DEBUG": "\033[36m",  # 청록색
        "INFO": "\033[32m",  # 녹색
        "WARNING": "\033[33m",  # 노란색
        "ERROR": "\033[31m",  # 빨간색
        "CRITICAL": "\033[35m",  # 마젠타
    }
    RESET = "\033[0m"

    def __init__(self, use_colors: bool = True, include_func: bool = False) -> None:
        """
        Args:
            use_colors: 컬러 출력 사용 여부
            include_func: 함수명 포함 여부
        """
        self.use_colors = use_colors and sys.stdout.isatty()
        self.include_func = include_func

        # 기본 포맷 정의
        if include_func:
            fmt = "%(asctime)s | %(name)-20s | %(levelname)-8s | %(funcName)s:%(lineno)d | %(message)s"
        else:
            fmt = "%(asctime)s | %(name)-20s | %(levelname)-8s | %(message)s"

        super().__init__(fmt, datefmt="%Y-%m-%d %H:%M:%S")

    def format(self, record: logging.LogRecord) -> str:
        """로그 레코드를 포맷팅"""
        # 기본 포맷 적용
        formatted = super().format(record)

        # 컬러 적용 (콘솔 출력용)
        if self.use_colors:
            color = self.COLORS.get(record.levelname, "")
            if color:
                formatted = f"{color}{formatted}{self.RESET}"

        return formatted


def get_log_directory() -> Path:
    """로그 파일 저장 디렉토리 반환

    Windows AppData 또는 실행 파일 기준 경로에 로그 디렉토리를 생성합니다.

    Returns:
        로그 디렉토리 Path 객체
    """
    try:
        # 실행 파일의 경로 가져오기 (PyInstaller 대응)
        if getattr(sys, "frozen", False):
            # PyInstaller로 빌드된 경우
            app_dir = Path(sys.executable).parent
            log_dir = app_dir / "logs"
        else:
            # 개발 환경: Windows AppData 사용
            import os

            appdata = os.getenv("LOCALAPPDATA")
            if appdata:
                log_dir = Path(appdata) / "TodoPanel" / "logs"
            else:
                # 폴백: 프로젝트 디렉토리
                log_dir = Path(__file__).parent.parent.parent / "logs"

        # 디렉토리 생성
        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir

    except Exception as e:
        # 최후 폴백: 현재 디렉토리
        fallback_dir = Path.cwd() / "logs"
        fallback_dir.mkdir(exist_ok=True)
        print(f"[WARNING] 로그 디렉토리 설정 실패, 폴백 사용: {fallback_dir} (원인: {e})")
        return fallback_dir


def setup_logging(
    level: str = "INFO",
    log_to_file: bool = True,
    log_to_console: bool = True,
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    include_func: bool = False,
) -> logging.Logger:
    """표준화된 로깅 설정

    Args:
        level: 로그 레벨 ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
        log_to_file: 파일 로그 활성화 여부
        log_to_console: 콘솔 로그 활성화 여부
        max_file_size: 로그 파일 최대 크기 (바이트)
        backup_count: 로그 파일 백업 개수
        include_func: 함수명 포함 여부

    Returns:
        설정된 루트 로거
    """
    # 기존 핸들러 제거 (중복 방지)
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # 로그 레벨 설정
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    root_logger.setLevel(numeric_level)

    # 포맷터 생성
    console_formatter = TodoPanelLogFormatter(use_colors=True, include_func=include_func)
    file_formatter = TodoPanelLogFormatter(
        use_colors=False, include_func=True
    )  # 파일에는 항상 함수명 포함

    # 콘솔 핸들러 설정
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

    # 파일 핸들러 설정
    if log_to_file:
        try:
            log_dir = get_log_directory()

            # 메인 로그 파일 (회전 로그)
            main_log_file = log_dir / "todo_panel.log"
            file_handler = logging.handlers.RotatingFileHandler(
                main_log_file, maxBytes=max_file_size, backupCount=backup_count, encoding="utf-8"
            )
            file_handler.setLevel(numeric_level)
            file_handler.setFormatter(file_formatter)
            root_logger.addHandler(file_handler)

            # 에러 전용 로그 파일
            error_log_file = log_dir / "errors.log"
            error_handler = logging.handlers.RotatingFileHandler(
                error_log_file, maxBytes=max_file_size, backupCount=backup_count, encoding="utf-8"
            )
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(file_formatter)
            root_logger.addHandler(error_handler)

            # 시작 로그 기록
            root_logger.info(f"로깅 시스템 초기화 완료 - 로그 디렉토리: {log_dir}")

        except Exception as e:
            print(f"[ERROR] 파일 로깅 설정 실패: {e}")
            # 파일 로깅 실패해도 콘솔 로깅은 유지

    return root_logger


def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """모듈별 로거 생성

    Args:
        name: 로거 이름 (일반적으로 __name__ 사용)
        level: 개별 로그 레벨 (None이면 루트 로거 레벨 사용)

    Returns:
        설정된 로거 인스턴스
    """
    logger = logging.getLogger(name)

    if level:
        numeric_level = getattr(logging, level.upper(), None)
        if numeric_level:
            logger.setLevel(numeric_level)

    return logger


def log_system_info() -> None:
    """시스템 정보를 로그에 기록"""
    logger = get_logger(__name__)

    try:
        import platform
        import sys
        from pathlib import Path

        logger.info("=== 시스템 정보 ===")
        logger.info(f"OS: {platform.system()} {platform.release()} ({platform.architecture()[0]})")
        logger.info(f"Python: {sys.version}")
        logger.info(f"실행 경로: {Path.cwd()}")
        logger.info(f"실행 파일: {sys.executable}")

        if getattr(sys, "frozen", False):
            logger.info("실행 모드: PyInstaller 빌드")
        else:
            logger.info("실행 모드: 개발 환경")

        logger.info("==================")

    except Exception as e:
        logger.warning(f"시스템 정보 수집 실패: {e}")


def setup_development_logging() -> logging.Logger:
    """개발 환경용 로깅 설정

    디버그 레벨, 상세한 출력, 함수명 포함 등 개발에 최적화된 설정입니다.

    Returns:
        설정된 루트 로거
    """
    logger = setup_logging(level="DEBUG", log_to_file=True, log_to_console=True, include_func=True)

    log_system_info()
    logger.debug("개발 환경 로깅 설정 완료")

    return logger


def setup_production_logging() -> logging.Logger:
    """운영 환경용 로깅 설정

    INFO 레벨, 효율적인 로그 회전, 에러 중심의 설정입니다.

    Returns:
        설정된 루트 로거
    """
    logger = setup_logging(
        level="INFO",
        log_to_file=True,
        log_to_console=False,  # 운영 환경에서는 파일만
        max_file_size=50 * 1024 * 1024,  # 50MB
        backup_count=10,
        include_func=False,
    )

    log_system_info()
    logger.info("운영 환경 로깅 설정 완료")

    return logger


def log_performance(func_name: str, execution_time: float, **kwargs: Any) -> None:
    """성능 로깅 유틸리티

    Args:
        func_name: 함수명
        execution_time: 실행 시간 (초)
        **kwargs: 추가 정보
    """
    logger = get_logger("performance")

    extra_info = ""
    if kwargs:
        extra_info = " | " + " | ".join(f"{k}={v}" for k, v in kwargs.items())

    if execution_time > 1.0:
        logger.warning(f"성능 주의: {func_name} - {execution_time:.3f}초{extra_info}")
    elif execution_time > 0.1:
        logger.info(f"성능: {func_name} - {execution_time:.3f}초{extra_info}")
    else:
        logger.debug(f"성능: {func_name} - {execution_time:.3f}초{extra_info}")


# 로깅 레벨별 편의 함수들
def debug(message: str, logger_name: str = None) -> None:
    """디버그 로그 출력"""
    logger = get_logger(logger_name or __name__)
    logger.debug(message)


def info(message: str, logger_name: str = None) -> None:
    """정보 로그 출력"""
    logger = get_logger(logger_name or __name__)
    logger.info(message)


def warning(message: str, logger_name: str = None) -> None:
    """경고 로그 출력"""
    logger = get_logger(logger_name or __name__)
    logger.warning(message)


def error(message: str, logger_name: str = None, exc_info: bool = True) -> None:
    """에러 로그 출력"""
    logger = get_logger(logger_name or __name__)
    logger.error(message, exc_info=exc_info)


def critical(message: str, logger_name: str = None, exc_info: bool = True) -> None:
    """크리티컬 로그 출력"""
    logger = get_logger(logger_name or __name__)
    logger.critical(message, exc_info=exc_info)


# 모듈 로드 시 기본 설정
if __name__ != "__main__":
    # 모듈이 import될 때 기본 로깅 설정 (개발용)
    _default_logger = get_logger(__name__)
    _default_logger.debug("logging_config 모듈 로드됨")
