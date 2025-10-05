"""
표준화된 에러 처리 시스템 (Phase 4B)

DRY+CLEAN+Simple 원칙을 적용한 통합 에러 처리 및 로깅 시스템입니다.
모든 Manager 클래스에서 일관된 에러 처리를 제공하며, 디버깅과 유지보수를 용이하게 합니다.
"""

import logging
import traceback
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Optional, TypeVar, Union

# 타입 변수 정의
F = TypeVar("F", bound=Callable[..., Any])


class TodoPanelError(Exception):
    """TODO Panel 애플리케이션 기본 예외 클래스

    모든 애플리케이션 특화 예외의 기본 클래스입니다.
    """

    def __init__(self, message: str, original_error: Optional[Exception] = None) -> None:
        super().__init__(message)
        self.message = message
        self.original_error = original_error

    def __str__(self) -> str:
        if self.original_error:
            return f"{self.message} (원인: {str(self.original_error)})"
        return self.message


class UIManagerError(TodoPanelError):
    """UI Manager 관련 예외 클래스

    UI 구성, 레이아웃, 위젯 생성 등 UI 관련 작업에서 발생하는 예외입니다.
    """

    pass


class SettingsError(TodoPanelError):
    """설정 관리 관련 예외 클래스

    설정 파일 읽기/쓰기, 설정 값 검증 등에서 발생하는 예외입니다.
    """

    pass


class EventHandlerError(TodoPanelError):
    """이벤트 처리 관련 예외 클래스

    사용자 이벤트 처리, 콜백 실행 등에서 발생하는 예외입니다.
    """

    pass


class DisplayManagerError(TodoPanelError):
    """디스플레이 관리 관련 예외 클래스

    TODO 아이템 표시, 섹션 관리 등에서 발생하는 예외입니다.
    """

    pass


def safe_execute(error_msg: str = "작업 실행 중 오류 발생") -> Callable[[F], F]:
    """안전한 메서드 실행을 위한 데코레이터

    메서드 실행 중 발생하는 예외를 캐치하고 로깅한 후 TodoPanelError로 변환합니다.
    중요한 비즈니스 로직에서 사용하며, 예외 발생 시 상위로 전파됩니다.

    Args:
        error_msg: 에러 발생 시 표시할 기본 메시지

    Returns:
        데코레이터 함수

    Example:
        @safe_execute("TODO 생성 중 오류 발생")
        def create_todo(self, text: str) -> Dict[str, Any]:
            # 구현 코드
            pass
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except TodoPanelError:
                # 이미 우리 예외인 경우 재전파
                raise
            except Exception as e:
                # 로깅
                logger = logging.getLogger(func.__module__)
                logger.error(f"{error_msg}: {func.__name__} - {str(e)}")
                logger.debug(f"상세 스택 트레이스:\n{traceback.format_exc()}")

                # TodoPanelError로 변환하여 전파
                raise TodoPanelError(f"{error_msg}: {str(e)}", original_error=e) from e

        return wrapper  # type: ignore

    return decorator


def safe_ui_operation(default_return: Any = None, log_level: str = "warning") -> Callable[[F], F]:
    """UI 작업용 안전 실행 데코레이터

    UI 관련 작업에서 예외가 발생해도 애플리케이션이 크래시되지 않도록 합니다.
    예외 발생 시 기본값을 반환하고 경고 로그만 출력합니다.

    Args:
        default_return: 예외 발생 시 반환할 기본값
        log_level: 로그 레벨 ("debug", "info", "warning", "error")

    Returns:
        데코레이터 함수

    Example:
        @safe_ui_operation(default_return=False)
        def update_ui_element(self) -> bool:
            # UI 업데이트 코드
            return True
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # 로깅
                logger = logging.getLogger(func.__module__)
                log_method = getattr(logger, log_level.lower(), logger.warning)
                log_method(f"UI 작업 실패: {func.__name__} - {str(e)}")

                # 디버그 모드에서만 상세 스택 트레이스 출력
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(f"UI 작업 실패 상세:\n{traceback.format_exc()}")

                return default_return

        return wrapper  # type: ignore

    return decorator


def log_method_call(include_args: bool = False, include_result: bool = False) -> Callable[[F], F]:
    """메서드 호출을 로깅하는 데코레이터

    개발 및 디버깅 목적으로 메서드 호출을 추적합니다.

    Args:
        include_args: 메서드 인자를 로그에 포함할지 여부
        include_result: 메서드 반환값을 로그에 포함할지 여부

    Returns:
        데코레이터 함수
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            logger = logging.getLogger(func.__module__)

            # 메서드 호출 시작 로그
            if include_args and logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"메서드 호출: {func.__name__}(args={args[1:]}, kwargs={kwargs})")
            elif logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"메서드 호출: {func.__name__}")

            try:
                result = func(*args, **kwargs)

                # 메서드 완료 로그
                if include_result and logger.isEnabledFor(logging.DEBUG):
                    logger.debug(f"메서드 완료: {func.__name__} -> {result}")

                return result
            except Exception as e:
                logger.error(f"메서드 실행 실패: {func.__name__} - {str(e)}")
                raise

        return wrapper  # type: ignore

    return decorator


def validate_type(
    param_name: str, value: Any, expected_type: Union[type, tuple], allow_none: bool = False
) -> None:
    """타입 검증 유틸리티 함수

    런타임에서 매개변수 타입을 검증합니다.

    Args:
        param_name: 매개변수 이름
        value: 검증할 값
        expected_type: 예상 타입 (단일 타입 또는 타입 튜플)
        allow_none: None 값 허용 여부

    Raises:
        TodoPanelError: 타입이 일치하지 않을 경우
    """
    if allow_none and value is None:
        return

    if not isinstance(value, expected_type):
        expected_str = getattr(expected_type, "__name__", str(expected_type))
        actual_str = type(value).__name__
        raise TodoPanelError(
            f"매개변수 '{param_name}'의 타입이 올바르지 않습니다. "
            f"예상: {expected_str}, 실제: {actual_str}"
        )


def ensure_file_path(file_path: Union[str, Path]) -> Path:
    """파일 경로를 Path 객체로 변환하고 검증

    Windows 환경에서 안전한 파일 경로 처리를 제공합니다.

    Args:
        file_path: 파일 경로 (문자열 또는 Path 객체)

    Returns:
        검증된 Path 객체

    Raises:
        SettingsError: 경로가 유효하지 않을 경우
    """
    try:
        path = Path(file_path)

        # 부모 디렉토리 존재 확인 및 생성
        if not path.parent.exists():
            path.parent.mkdir(parents=True, exist_ok=True)

        return path
    except Exception as e:
        raise SettingsError(f"파일 경로 처리 실패: {file_path}", original_error=e) from e


# 에러 복구 전략을 위한 헬퍼 함수들


def retry_on_failure(max_attempts: int = 3, delay_seconds: float = 0.1) -> Callable[[F], F]:
    """실패 시 재시도하는 데코레이터

    일시적인 오류에 대해 자동으로 재시도를 수행합니다.

    Args:
        max_attempts: 최대 시도 횟수
        delay_seconds: 재시도 간 대기 시간 (초)

    Returns:
        데코레이터 함수
    """
    import time

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    logger = logging.getLogger(func.__module__)

                    if attempt < max_attempts - 1:
                        logger.warning(
                            f"재시도 {attempt + 1}/{max_attempts}: {func.__name__} - {str(e)}"
                        )
                        time.sleep(delay_seconds)
                    else:
                        logger.error(f"최대 재시도 횟수 초과: {func.__name__} - {str(e)}")

            # 모든 시도 실패 시 마지막 예외 전파
            raise last_exception

        return wrapper  # type: ignore

    return decorator


def format_error_message(
    error: Exception, context: str = "", include_traceback: bool = False
) -> str:
    """에러 메시지를 사용자 친화적으로 포맷팅

    Args:
        error: 예외 객체
        context: 에러 발생 맥락
        include_traceback: 스택 트레이스 포함 여부

    Returns:
        포맷팅된 에러 메시지
    """
    base_msg = f"{context}: {str(error)}" if context else str(error)

    if include_traceback and hasattr(error, "__traceback__"):
        return f"{base_msg}\n\n상세 정보:\n{traceback.format_exc()}"

    return base_msg


# 로깅 설정을 위한 상수들
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


# 개발용 로깅 설정
def setup_development_logging(level: int = logging.DEBUG) -> None:
    """개발 환경용 로깅 설정"""
    logging.basicConfig(level=level, format=LOG_FORMAT, datefmt=LOG_DATE_FORMAT)


# 모듈 레벨에서 기본 로거 설정
logger = logging.getLogger(__name__)
