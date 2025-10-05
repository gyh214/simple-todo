# -*- coding: utf-8 -*-
"""
단일 인스턴스 보장 매니저

포트 기반 소켓 락을 사용하여 애플리케이션의 중복 실행을 방지하고,
중복 실행 시도 시 기존 창을 활성화합니다.
"""
import socket
import sys
import threading
from typing import Optional
from PyQt6.QtCore import QObject, pyqtSignal


class SingleInstanceManager(QObject):
    """
    단일 인스턴스 보장 관리자

    Attributes:
        PORT (int): 락으로 사용할 포트 번호 (65432)
        ACTIVATION_MESSAGE (bytes): 활성화 요청 메시지
        activate_requested (pyqtSignal): 활성화 요청 시그널
    """

    PORT = 65432
    ACTIVATION_MESSAGE = b"ACTIVATE"
    BUFFER_SIZE = 1024
    TIMEOUT = 2.0  # 소켓 타임아웃 (초)

    # PyQt6 시그널: 활성화 요청이 들어왔을 때 발생
    activate_requested = pyqtSignal()

    def __init__(self):
        """SingleInstanceManager 초기화"""
        super().__init__()
        self._server_socket: Optional[socket.socket] = None
        self._listener_thread: Optional[threading.Thread] = None
        self._is_listening = False

    def is_already_running(self) -> bool:
        """
        이미 실행 중인 인스턴스가 있는지 확인

        Returns:
            bool: 이미 실행 중이면 True, 첫 실행이면 False
        """
        try:
            # 서버 소켓 생성 시도
            self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            # Windows에서 단일 인스턴스 보장을 위해 SO_EXCLUSIVEADDRUSE 사용
            # Linux/Mac에서는 기본 동작이 배타적이므로 옵션 불필요
            if sys.platform == 'win32':
                # Windows 전용: SO_EXCLUSIVEADDRUSE (값: -5)
                # 이 옵션은 포트를 배타적으로 점유하여 다른 소켓이 바인딩 불가
                try:
                    self._server_socket.setsockopt(
                        socket.SOL_SOCKET,
                        socket.SO_EXCLUSIVEADDRUSE,
                        1
                    )
                except (AttributeError, OSError):
                    # SO_EXCLUSIVEADDRUSE가 없으면 그냥 진행
                    # (기본적으로 Windows는 배타적 바인딩)
                    pass

            self._server_socket.bind(('127.0.0.1', self.PORT))
            self._server_socket.listen(1)

            # 바인딩 성공 = 첫 실행
            return False

        except OSError as e:
            # 바인딩 실패 = 이미 실행 중
            if self._server_socket:
                try:
                    self._server_socket.close()
                except Exception:
                    pass
                self._server_socket = None
            return True

    def start_listener(self):
        """
        활성화 요청 수신 리스너 시작

        백그라운드 스레드에서 소켓 연결을 수신하고,
        활성화 메시지를 받으면 activate_requested 시그널을 발생시킵니다.
        """
        if self._is_listening or not self._server_socket:
            return

        self._is_listening = True
        self._listener_thread = threading.Thread(
            target=self._listen_for_activation,
            daemon=True,
            name="SingleInstanceListener"
        )
        self._listener_thread.start()

    def _listen_for_activation(self):
        """
        활성화 요청 수신 루프 (백그라운드 스레드)

        클라이언트 연결을 수신하고 ACTIVATE 메시지를 받으면
        PyQt6 시그널을 발생시킵니다.
        """
        if not self._server_socket:
            return

        # 소켓 타임아웃 설정 (종료 시 빠른 응답을 위해)
        self._server_socket.settimeout(1.0)

        while self._is_listening:
            try:
                # 클라이언트 연결 대기
                client_socket, address = self._server_socket.accept()

                try:
                    # 메시지 수신
                    client_socket.settimeout(self.TIMEOUT)
                    data = client_socket.recv(self.BUFFER_SIZE)

                    # ACTIVATE 메시지 확인
                    if data == self.ACTIVATION_MESSAGE:
                        # PyQt6 시그널 발생 (메인 스레드에서 처리됨)
                        self.activate_requested.emit()

                    # 응답 전송 (확인용)
                    client_socket.sendall(b"OK")

                except socket.timeout:
                    # 타임아웃 발생 시 무시
                    pass

                finally:
                    # 클라이언트 소켓 닫기
                    try:
                        client_socket.close()
                    except Exception:
                        pass

            except socket.timeout:
                # accept() 타임아웃은 정상 (루프 계속)
                continue

            except Exception as e:
                # 리스닝 중이면 에러 로깅, 아니면 종료
                if self._is_listening:
                    print(f"SingleInstanceManager 리스너 에러: {e}")
                break

    def activate_existing_instance(self) -> bool:
        """
        기존 실행 중인 인스턴스로 활성화 요청 전송

        Returns:
            bool: 활성화 요청 성공 여부
        """
        try:
            # 클라이언트 소켓 생성
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(self.TIMEOUT)

            try:
                # 기존 인스턴스에 연결
                client_socket.connect(('127.0.0.1', self.PORT))

                # ACTIVATE 메시지 전송
                client_socket.sendall(self.ACTIVATION_MESSAGE)

                # 응답 대기 (옵션)
                response = client_socket.recv(self.BUFFER_SIZE)

                return response == b"OK"

            finally:
                # 클라이언트 소켓 닫기
                try:
                    client_socket.close()
                except Exception:
                    pass

        except (socket.timeout, ConnectionRefusedError, OSError) as e:
            # 연결 실패 (기존 인스턴스가 응답하지 않음)
            print(f"기존 인스턴스 활성화 실패: {e}")
            return False

    def cleanup(self):
        """
        리소스 정리

        리스너 스레드를 중지하고 서버 소켓을 닫습니다.
        """
        # 리스너 중지
        self._is_listening = False

        # 리스너 스레드 종료 대기 (최대 2초)
        if self._listener_thread and self._listener_thread.is_alive():
            self._listener_thread.join(timeout=2.0)

        # 서버 소켓 닫기
        if self._server_socket:
            try:
                self._server_socket.close()
            except Exception as e:
                print(f"서버 소켓 닫기 실패: {e}")
            finally:
                self._server_socket = None

    def __del__(self):
        """소멸자: 리소스 정리"""
        self.cleanup()
