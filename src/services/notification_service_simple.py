"""
NotificationService - CLEAN 아키텍처 알림 전담 서비스 (간소화 버전)

🔔 크로스 커팅 관심사:
====================
모든 레이어에서 사용할 수 있는 알림 서비스입니다.
UI 프레임워크에 의존하지 않는 추상화된 알림 인터페이스를 제공합니다.

🎯 DI Container 호환성:
======================
의존성 주입 컨테이너에서 쉽게 사용할 수 있도록 단순화된 생성자를 제공합니다.
"""

import tkinter as tk
from tkinter import messagebox
import logging
from typing import Optional

from interfaces import INotificationService

logger = logging.getLogger(__name__)


class TkinterNotificationService(INotificationService):
    """
    Tkinter 기반 알림 서비스 구현체 (DI Container 호환 버전)

    🎯 UI 프레임워크 추상화:
    ======================
    비즈니스 로직은 Tkinter에 직접 의존하지 않고
    이 서비스를 통해서만 사용자와 상호작용합니다.

    🔄 DI Container 호환성:
    ======================
    기본 생성자만 제공하여 의존성 주입이 쉽도록 설계되었습니다.
    """

    def __init__(self):
        """
        알림 서비스 초기화 (DI Container 호환용)

        parent_window는 나중에 set_parent_window()로 설정
        """
        self._parent_window = None
        self._notification_count = 0
        logger.info("TkinterNotificationService 초기화 완료")

    def set_parent_window(self, parent_window: Optional[tk.Tk]):
        """부모 윈도우 설정"""
        self._parent_window = parent_window

    def show_info(self, message: str, title: str = "정보") -> None:
        """
        정보 알림 표시

        ℹ️ 사용 사례:
        =============
        - TODO 생성/수정 성공
        - 작업 완료 알림
        - 일반적인 시스템 상태

        Args:
            message: 표시할 메시지
            title: 대화상자 제목
        """
        try:
            messagebox.showinfo(
                title=title,
                message=message,
                parent=self._parent_window
            )
            self._notification_count += 1
            logger.debug(f"정보 알림 표시: {title} - {message[:50]}...")

        except Exception as e:
            logger.error(f"정보 알림 표시 실패: {str(e)}")
            self._fallback_notification("INFO", title, message)

    def show_warning(self, message: str, title: str = "경고") -> None:
        """
        경고 알림 표시

        ⚠️ 사용 사례:
        =============
        - 입력 검증 실패
        - 권장하지 않는 작업
        - 주의가 필요한 상황

        Args:
            message: 경고 메시지
            title: 대화상자 제목
        """
        try:
            messagebox.showwarning(
                title=title,
                message=message,
                parent=self._parent_window
            )
            self._notification_count += 1
            logger.debug(f"경고 알림 표시: {title} - {message[:50]}...")

        except Exception as e:
            logger.error(f"경고 알림 표시 실패: {str(e)}")
            self._fallback_notification("WARNING", title, message)

    def show_error(self, message: str, title: str = "오류") -> None:
        """
        오류 알림 표시

        ❌ 사용 사례:
        =============
        - 시스템 오류
        - 작업 실패
        - 예상치 못한 예외

        Args:
            message: 오류 메시지
            title: 대화상자 제목
        """
        try:
            messagebox.showerror(
                title=title,
                message=message,
                parent=self._parent_window
            )
            self._notification_count += 1
            logger.warning(f"오류 알림 표시: {title} - {message[:50]}...")

        except Exception as e:
            logger.error(f"오류 알림 표시 실패: {str(e)}")
            self._fallback_notification("ERROR", title, message)

    def ask_confirmation(self, message: str, title: str = "확인") -> bool:
        """
        사용자 확인 요청

        ❓ 사용 사례:
        =============
        - TODO 삭제 확인
        - 일괄 작업 확인
        - 되돌릴 수 없는 작업 확인

        Args:
            message: 확인 메시지
            title: 대화상자 제목

        Returns:
            사용자 선택 (True: 확인, False: 취소)
        """
        try:
            result = messagebox.askyesno(
                title=title,
                message=message,
                parent=self._parent_window
            )
            self._notification_count += 1
            logger.debug(f"확인 요청: {title} - 결과: {result}")
            return result

        except Exception as e:
            logger.error(f"확인 대화상자 표시 실패: {str(e)}")
            # 실패 시 안전한 기본값 (취소)
            return False

    def get_notification_stats(self) -> dict:
        """
        알림 통계 정보 조회

        📊 디버그 정보:
        ==============
        - 총 알림 개수
        - 알림 유형별 통계
        - 성능 모니터링

        Returns:
            통계 정보 딕셔너리
        """
        return {
            'total_notifications': self._notification_count,
            'service_type': 'TkinterNotificationService',
            'parent_window': self._parent_window is not None
        }

    def _fallback_notification(self, level: str, title: str, message: str) -> None:
        """
        대화상자 실패 시 폴백 알림

        🚨 비상 알림:
        ============
        GUI 대화상자가 실패할 경우 콘솔 로그로 폴백합니다.

        Args:
            level: 알림 수준
            title: 제목
            message: 메시지
        """
        try:
            # 콘솔 출력으로 폴백
            print(f"[{level}] {title}: {message}")

            # Windows 시스템 알림 시도 (선택사항)
            if hasattr(tk, '_default_root') and tk._default_root:
                tk._default_root.bell()  # 시스템 beep 소리

        except Exception as e:
            # 최후의 수단 - 로그만 남김
            logger.critical(f"모든 알림 방법 실패 - {level}: {title} - {message}")


# 편의를 위한 별칭
NotificationService = TkinterNotificationService