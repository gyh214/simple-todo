"""Debounce/Throttle 패턴 구현을 위한 유틸리티 모듈

QTimer 기반으로 연속적인 호출을 지연시키고 마지막 호출만 실행하는
Debounce 패턴을 제공합니다.

Usage:
    # Debounce 예시 (300ms 지연)
    def on_save(data):
        print(f"Saving: {data}")

    debouncer = DebounceManager(delay_ms=300, callback=on_save)

    # 연속 호출 - 마지막 호출만 실행됨
    debouncer.schedule({"id": 1})
    debouncer.schedule({"id": 2})
    debouncer.schedule({"id": 3})  # 300ms 후 이것만 실행

    # Throttle 예시 (100ms 간격)
    throttler = DebounceManager(delay_ms=100, callback=on_update)

    for i in range(100):
        throttler.schedule(i)  # 100ms마다 한 번씩만 실행
"""

from PyQt6.QtCore import QTimer
from typing import Callable, Any, Optional
import logging

logger = logging.getLogger(__name__)


class DebounceManager:
    """QTimer 기반 Debounce/Throttle 패턴 구현

    연속적인 호출을 지연시키고 마지막 호출만 실행하는 패턴입니다.

    **Debounce vs Throttle:**
    - Debounce: 마지막 호출 후 delay_ms가 지나면 실행
      → 연속 호출이 멈출 때까지 대기 (예: 타이핑 완료 후 검색)
    - Throttle: 첫 호출 즉시 실행, 이후 delay_ms 동안 무시
      → 일정 간격으로 실행 (예: 스크롤 이벤트)

    이 클래스는 Debounce 패턴을 기본 제공하며,
    Throttle 패턴은 호출 측에서 isActive() 체크로 구현 가능합니다.

    Attributes:
        _delay_ms: 지연 시간 (밀리초)
        _callback: 실행할 콜백 함수
        _timer: QTimer 인스턴스
        _pending_data: 대기 중인 데이터

    Example:
        >>> def save_data(data):
        ...     print(f"Saved: {data}")
        >>>
        >>> debouncer = DebounceManager(delay_ms=300, callback=save_data)
        >>> debouncer.schedule({"id": 1})  # 타이머 시작
        >>> debouncer.schedule({"id": 2})  # 타이머 재시작 (1은 무시됨)
        >>> debouncer.schedule({"id": 3})  # 타이머 재시작 (2는 무시됨)
        >>> # 300ms 후: "Saved: {'id': 3}" 출력 (마지막 값만 실행)
    """

    def __init__(self, delay_ms: int, callback: Callable[[Any], None]):
        """DebounceManager 초기화

        Args:
            delay_ms: 지연 시간 (밀리초). 마지막 호출 후 이 시간이 지나면 콜백 실행
            callback: 실행할 콜백 함수. data를 인자로 받음

        Raises:
            ValueError: delay_ms가 0 이하인 경우
            TypeError: callback이 callable이 아닌 경우

        Example:
            >>> debouncer = DebounceManager(delay_ms=300, callback=lambda x: print(x))
        """
        if delay_ms <= 0:
            raise ValueError(f"delay_ms must be positive, got {delay_ms}")

        if not callable(callback):
            raise TypeError(f"callback must be callable, got {type(callback)}")

        self._delay_ms: int = delay_ms
        self._callback: Callable[[Any], None] = callback
        self._timer: Optional[QTimer] = None
        self._pending_data: Any = None

        logger.debug(f"DebounceManager initialized: delay={delay_ms}ms, callback={callback.__name__}")

    def schedule(self, data: Any = None) -> None:
        """Debounce 실행 예약

        마지막 호출 후 delay_ms가 지나면 콜백이 실행됩니다.
        연속적으로 호출되면 타이머가 재시작되며, 마지막 data만 콜백에 전달됩니다.

        Args:
            data: 콜백에 전달할 데이터 (optional). None도 유효한 값

        Example:
            >>> debouncer.schedule({"action": "save", "id": 123})
            >>> debouncer.schedule(None)  # None도 전달 가능

        Implementation Details:
            1. pending_data 업데이트 (마지막 값 유지)
            2. 기존 타이머가 active면 중지
            3. 새 타이머 생성 및 시작 (delay_ms)
            4. delay_ms 후 _execute_callback() 호출
        """
        # pending 데이터 업데이트 (마지막 값만 유지)
        self._pending_data = data

        # 기존 타이머가 있으면 중지 (타이머 재시작)
        if self._timer and self._timer.isActive():
            self._timer.stop()
            logger.debug(f"Debounce timer restarted: delay={self._delay_ms}ms")
        else:
            logger.debug(f"Debounce timer started: delay={self._delay_ms}ms")

        # 새 타이머 생성 및 시작
        self._timer = QTimer()
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._execute_callback)
        self._timer.start(self._delay_ms)

    def cancel(self) -> None:
        """예약된 실행 취소

        타이머를 중지하고 pending 데이터를 제거합니다.
        이미 실행된 경우나 예약이 없는 경우 아무 동작도 하지 않습니다.

        Example:
            >>> debouncer.schedule({"id": 1})
            >>> debouncer.cancel()  # 실행 취소됨
            >>> # 콜백이 호출되지 않음
        """
        if self._timer and self._timer.isActive():
            self._timer.stop()
            self._pending_data = None
            logger.debug("Debounce timer cancelled")
        else:
            logger.debug("No active debounce timer to cancel")

    def is_active(self) -> bool:
        """타이머가 활성화되어 있는지 확인

        Returns:
            bool: 타이머가 대기 중이면 True, 그렇지 않으면 False

        Example:
            >>> debouncer.schedule({"id": 1})
            >>> debouncer.is_active()
            True
            >>> debouncer.cancel()
            >>> debouncer.is_active()
            False

        Note:
            Throttle 패턴 구현 시 이 메서드를 사용하여
            타이머가 active일 때 schedule() 호출을 무시할 수 있습니다.

            예시 (Throttle):
            ```python
            if not throttler.is_active():
                throttler.schedule(data)
            ```
        """
        return self._timer is not None and self._timer.isActive()

    def _execute_callback(self) -> None:
        """타이머 완료 시 실제 콜백을 실행합니다 (내부 메서드)

        pending_data를 콜백에 전달하고 초기화합니다.

        Note:
            이 메서드는 QTimer.timeout 시그널에서 호출되므로
            외부에서 직접 호출하면 안 됩니다.
        """
        if self._pending_data is not None or self._callback.__code__.co_argcount > 0:
            # pending_data가 있거나 콜백이 인자를 받는 경우
            data = self._pending_data
            self._pending_data = None

            logger.debug(f"Executing debounced callback with data: {data}")

            try:
                self._callback(data)
            except Exception as e:
                logger.error(f"Error in debounced callback: {e}", exc_info=True)
        else:
            # pending_data가 None이고 콜백이 인자 없는 경우
            logger.debug("Executing debounced callback without data")

            try:
                self._callback()
            except Exception as e:
                logger.error(f"Error in debounced callback: {e}", exc_info=True)
