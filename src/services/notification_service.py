"""
NotificationService - CLEAN 아키텍처 알림 전담 서비스

🔔 크로스 커팅 관심사:
====================
모든 레이어에서 사용할 수 있는 알림 서비스입니다.
UI 프레임워크에 의존하지 않는 추상화된 알림 인터페이스를 제공합니다.

📱 지원 알림 유형:
==================
- 정보 알림 (성공 메시지, 일반 정보)
- 경고 알림 (주의사항, 검증 실패)
- 오류 알림 (예외 상황, 시스템 오류)
- 확인 대화상자 (사용자 의사 결정)

🎨 테마 지원:
============
- Dark/Light 테마 자동 적응
- 시스템 알림과의 일관성 유지
- 사용자 정의 스타일 지원
"""

import tkinter as tk
from tkinter import messagebox
import logging
from typing import Optional

from interfaces import INotificationService

logger = logging.getLogger(__name__)


class TkinterNotificationService(INotificationService):
    """
    Tkinter 기반 알림 서비스 구현체

    🎯 UI 프레임워크 추상화:
    ======================
    비즈니스 로직은 Tkinter에 직접 의존하지 않고
    이 서비스를 통해서만 사용자와 상호작용합니다.

    🔄 테스트 가능성:
    ================
    Mock 객체로 완전히 교체 가능하여
    자동화된 테스트에서 사용자 상호작용을 시뮬레이션할 수 있습니다.
    """

    def __init__(self, parent_window: Optional[tk.Tk] = None):
        """
        알림 서비스 초기화

        Args:
            parent_window: 부모 윈도우 (모달 대화상자용)
        """
        self._parent_window = parent_window
        self._notification_count = 0
        logger.info("TkinterNotificationService 초기화 완료")

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
            # 알림 표시 실패 시에도 시스템이 중단되지 않도록
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

    def ask_yes_no_cancel(self, message: str, title: str = "선택") -> Optional[bool]:
        """
        3-way 선택 대화상자

        🔀 사용 사례:
        =============
        - 저장하지 않은 변경사항 처리
        - 파일 충돌 해결 옵션
        - 복잡한 의사결정

        Args:
            message: 선택 메시지
            title: 대화상자 제목

        Returns:
            사용자 선택 (True: 예, False: 아니오, None: 취소)
        """
        try:
            result = messagebox.askyesnocancel(
                title=title,
                message=message,
                parent=self._parent_window
            )
            self._notification_count += 1
            logger.debug(f"3-way 선택 요청: {title} - 결과: {result}")
            return result

        except Exception as e:
            logger.error(f"3-way 대화상자 표시 실패: {str(e)}")
            return None

    def show_custom_dialog(self, message: str, title: str = "알림",
                          buttons: list = None, default_button: int = 0) -> str:
        """
        사용자 정의 대화상자 표시

        🎛️ 고급 기능:
        =============
        - 사용자 정의 버튼
        - 기본 버튼 선택
        - 복잡한 사용자 인터랙션

        Args:
            message: 표시할 메시지
            title: 대화상자 제목
            buttons: 버튼 목록
            default_button: 기본 선택 버튼 인덱스

        Returns:
            선택된 버튼 텍스트
        """
        if buttons is None:
            buttons = ["확인"]

        try:
            # 간단한 구현 (tkinter 기본 기능 사용)
            if len(buttons) == 1:
                messagebox.showinfo(title, message, parent=self._parent_window)
                return buttons[0]
            elif len(buttons) == 2:
                result = messagebox.askyesno(title, message, parent=self._parent_window)
                return buttons[0] if result else buttons[1]
            else:
                # 3개 이상의 버튼이 필요한 경우 커스텀 다이얼로그 구현
                return self._show_multi_button_dialog(message, title, buttons, default_button)

        except Exception as e:
            logger.error(f"사용자 정의 대화상자 실패: {str(e)}")
            return buttons[0] if buttons else "확인"

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

    def _show_multi_button_dialog(self, message: str, title: str,
                                buttons: list, default_button: int) -> str:
        """
        다중 버튼 커스텀 대화상자

        Args:
            message: 메시지
            title: 제목
            buttons: 버튼 목록
            default_button: 기본 버튼

        Returns:
            선택된 버튼 텍스트
        """
        try:
            # 간단한 커스텀 대화상자 구현
            dialog = tk.Toplevel(self._parent_window)
            dialog.title(title)
            dialog.transient(self._parent_window)
            dialog.grab_set()

            # 메시지 레이블
            msg_label = tk.Label(dialog, text=message, wraplength=300, justify='left')
            msg_label.pack(pady=20, padx=20)

            # 버튼 프레임
            button_frame = tk.Frame(dialog)
            button_frame.pack(pady=10)

            result = [None]  # 결과 저장용 (클로저에서 접근)

            def on_button_click(button_text):
                result[0] = button_text
                dialog.destroy()

            # 버튼 생성
            for i, button_text in enumerate(buttons):
                btn = tk.Button(
                    button_frame,
                    text=button_text,
                    command=lambda bt=button_text: on_button_click(bt),
                    width=10
                )
                btn.pack(side='left', padx=5)

                # 기본 버튼 설정
                if i == default_button:
                    btn.focus_set()
                    dialog.bind('<Return>', lambda e, bt=button_text: on_button_click(bt))

            # ESC로 취소
            dialog.bind('<Escape>', lambda e: dialog.destroy())

            # 대화상자 크기 조정 및 중앙 배치
            dialog.update_idletasks()
            width = dialog.winfo_reqwidth()
            height = dialog.winfo_reqheight()
            x = (dialog.winfo_screenwidth() // 2) - (width // 2)
            y = (dialog.winfo_screenheight() // 2) - (height // 2)
            dialog.geometry(f"{width}x{height}+{x}+{y}")

            # 모달 대기
            dialog.wait_window(dialog)

            return result[0] if result[0] else buttons[0]

        except Exception as e:
            logger.error(f"커스텀 다중 버튼 대화상자 실패: {str(e)}")
            return buttons[0] if buttons else "확인"