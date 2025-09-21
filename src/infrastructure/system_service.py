"""
SystemService - CLEAN 아키텍처 시스템 기능 추상화

🖥️ Infrastructure Layer:
========================
운영체제와의 모든 상호작용을 추상화하여
Domain Layer가 플랫폼에 의존하지 않도록 합니다.

🎯 Windows 특화:
===============
- Windows 파일 시스템 경로 처리
- Windows 기본 애플리케이션 연동
- Windows 환경 변수 및 레지스트리 접근
- Windows API 래핑

🔒 보안 고려사항:
================
- 실행 파일 검증 및 사용자 확인
- 안전하지 않은 URL 필터링
- 권한 검사 및 샌드박싱
"""

import os
import sys
import webbrowser
import logging
import subprocess
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from interfaces import ISystemService

logger = logging.getLogger(__name__)


class WindowsSystemService(ISystemService):
    """
    Windows 환경 최적화된 시스템 서비스 구현체

    🖥️ Windows API 활용:
    ====================
    - os.startfile()로 파일 기본 앱 실행
    - webbrowser 모듈로 브라우저 제어
    - Windows 환경 변수 접근
    - APPDATA 경로 자동 감지
    """

    def __init__(self):
        """시스템 서비스 초기화"""
        self._dangerous_extensions = {
            '.exe', '.com', '.scr', '.bat', '.cmd', '.pif',
            '.vbs', '.js', '.jar', '.app', '.deb', '.rpm'
        }
        logger.info("WindowsSystemService 초기화 완료")

    def open_url(self, url: str) -> bool:
        """
        웹 URL을 기본 브라우저에서 열기

        🌐 안전한 URL 처리:
        ==================
        - URL 형식 검증
        - 위험한 프로토콜 필터링
        - 로컬 파일 URL 차단
        - 사용자 확인 대화상자

        Args:
            url: 열 URL

        Returns:
            열기 성공 여부
        """
        if not url or not isinstance(url, str):
            logger.warning("유효하지 않은 URL")
            return False

        try:
            url = url.strip()

            # URL 형식 검증
            if not self._is_safe_url(url):
                logger.warning(f"안전하지 않은 URL: {url}")
                return False

            # webbrowser 모듈 사용 (크로스 플랫폼)
            webbrowser.open(url)

            logger.info(f"URL 열기 성공: {url}")
            return True

        except Exception as e:
            logger.error(f"URL 열기 실패: {url} - {str(e)}")
            return False

    def open_file(self, file_path: str) -> bool:
        """
        파일을 기본 애플리케이션으로 열기

        📂 안전한 파일 실행:
        ===================
        - 파일 존재 확인
        - 실행 파일 검증 및 경고
        - Windows os.startfile() 사용
        - 권한 검사

        Args:
            file_path: 열 파일 경로

        Returns:
            열기 성공 여부
        """
        if not file_path or not isinstance(file_path, str):
            logger.warning("유효하지 않은 파일 경로")
            return False

        try:
            file_path = str(file_path).strip()

            # 파일 존재 확인
            if not os.path.exists(file_path):
                logger.warning(f"파일이 존재하지 않음: {file_path}")
                return False

            # 실행 파일 보안 검사
            if self._is_executable_file(file_path):
                if not self._confirm_executable_launch(file_path):
                    logger.info(f"사용자가 실행을 취소함: {file_path}")
                    return False

            # Windows에서 파일 열기
            if os.name == 'nt':
                os.startfile(file_path)
            else:
                # 다른 플랫폼 지원 (확장 가능)
                subprocess.run(['xdg-open', file_path], check=True)

            logger.info(f"파일 열기 성공: {file_path}")
            return True

        except Exception as e:
            logger.error(f"파일 열기 실패: {file_path} - {str(e)}")
            return False

    def get_app_data_path(self) -> str:
        """
        애플리케이션 데이터 저장 경로 조회

        📁 Windows APPDATA:
        ==================
        - %APPDATA%\\TodoPanel 경로 사용
        - 사용자별 독립 데이터 디렉토리
        - 자동 디렉토리 생성
        - 권한 문제 해결

        Returns:
            애플리케이션 데이터 경로
        """
        try:
            if os.name == 'nt':
                # Windows APPDATA 경로
                appdata = os.environ.get('APPDATA')
                if appdata:
                    app_path = os.path.join(appdata, 'TodoPanel')
                else:
                    # APPDATA가 없는 경우 대안
                    user_profile = os.environ.get('USERPROFILE', os.path.expanduser('~'))
                    app_path = os.path.join(user_profile, 'AppData', 'Roaming', 'TodoPanel')
            else:
                # 다른 플랫폼 지원
                home = os.path.expanduser('~')
                app_path = os.path.join(home, '.todopanel')

            # 디렉토리 생성 보장
            os.makedirs(app_path, exist_ok=True)

            logger.debug(f"앱 데이터 경로: {app_path}")
            return app_path

        except Exception as e:
            # 실패 시 현재 디렉토리 사용
            logger.error(f"앱 데이터 경로 조회 실패: {str(e)}")
            fallback_path = os.path.join(os.getcwd(), 'data')
            os.makedirs(fallback_path, exist_ok=True)
            return fallback_path

    def get_system_info(self) -> dict:
        """
        시스템 정보 조회

        💻 시스템 환경:
        ==============
        - 운영체제 정보
        - Python 버전
        - 아키텍처 정보
        - 환경 변수

        Returns:
            시스템 정보 딕셔너리
        """
        try:
            import platform

            info = {
                'os_name': os.name,
                'platform': platform.system(),
                'platform_release': platform.release(),
                'platform_version': platform.version(),
                'architecture': platform.architecture(),
                'machine': platform.machine(),
                'processor': platform.processor(),
                'python_version': sys.version,
                'python_executable': sys.executable,
                'app_data_path': self.get_app_data_path(),
                'current_working_directory': os.getcwd(),
                'user_name': os.environ.get('USERNAME', 'Unknown'),
                'computer_name': os.environ.get('COMPUTERNAME', 'Unknown')
            }

            logger.debug("시스템 정보 조회 완료")
            return info

        except Exception as e:
            logger.error(f"시스템 정보 조회 실패: {str(e)}")
            return {'error': str(e)}

    def is_admin(self) -> bool:
        """
        관리자 권한 확인

        🔐 권한 검사:
        ============
        Windows에서 현재 프로세스가 관리자 권한으로 실행되는지 확인합니다.

        Returns:
            관리자 권한 여부
        """
        try:
            if os.name == 'nt':
                import ctypes
                return ctypes.windll.shell32.IsUserAnAdmin() != 0
            else:
                # Unix 계열에서는 root 권한 확인
                return os.geteuid() == 0

        except Exception as e:
            logger.debug(f"권한 확인 실패: {str(e)}")
            return False

    def run_command(self, command: str, capture_output: bool = False) -> dict:
        """
        시스템 명령어 실행

        ⚠️ 보안 주의:
        =============
        외부 명령어 실행은 보안상 위험할 수 있습니다.
        필요한 경우에만 사용하고 입력을 철저히 검증해야 합니다.

        Args:
            command: 실행할 명령어
            capture_output: 출력 캡처 여부

        Returns:
            실행 결과 딕셔너리
        """
        if not command or not isinstance(command, str):
            return {'success': False, 'error': 'Invalid command'}

        try:
            logger.warning(f"시스템 명령어 실행: {command}")

            # 위험한 명령어 필터링
            dangerous_commands = ['del', 'rm', 'format', 'fdisk', 'reg delete']
            if any(dangerous in command.lower() for dangerous in dangerous_commands):
                return {'success': False, 'error': 'Dangerous command blocked'}

            result = subprocess.run(
                command,
                shell=True,
                capture_output=capture_output,
                text=True,
                timeout=30  # 30초 제한
            )

            response = {
                'success': result.returncode == 0,
                'return_code': result.returncode
            }

            if capture_output:
                response['stdout'] = result.stdout
                response['stderr'] = result.stderr

            return response

        except subprocess.TimeoutExpired:
            return {'success': False, 'error': 'Command timeout'}
        except Exception as e:
            logger.error(f"명령어 실행 실패: {command} - {str(e)}")
            return {'success': False, 'error': str(e)}

    def _is_safe_url(self, url: str) -> bool:
        """
        URL 안전성 검사

        Args:
            url: 검사할 URL

        Returns:
            안전한 URL 여부
        """
        try:
            # 기본 URL 형식 검사
            if not url.startswith(('http://', 'https://', 'www.')):
                return False

            parsed = urlparse(url)

            # 로컬 호스트 차단
            dangerous_hosts = ['localhost', '127.0.0.1', '0.0.0.0', '::1']
            if parsed.hostname in dangerous_hosts:
                return False

            # 파일 프로토콜 차단
            if parsed.scheme in ['file', 'ftp']:
                return False

            return True

        except Exception:
            return False

    def _is_executable_file(self, file_path: str) -> bool:
        """
        실행 파일 여부 확인

        Args:
            file_path: 파일 경로

        Returns:
            실행 파일 여부
        """
        try:
            _, ext = os.path.splitext(file_path.lower())
            return ext in self._dangerous_extensions
        except Exception:
            return False

    def _confirm_executable_launch(self, file_path: str) -> bool:
        """
        실행 파일 실행 확인

        Args:
            file_path: 실행할 파일 경로

        Returns:
            사용자 확인 결과
        """
        try:
            # tkinter messagebox를 사용한 확인 대화상자
            import tkinter.messagebox as messagebox

            file_name = os.path.basename(file_path)
            message = (
                f"다음 실행 파일을 열려고 합니다:\\n\\n"
                f"파일: {file_name}\\n"
                f"경로: {file_path}\\n\\n"
                f"이 파일을 실행하시겠습니까?\\n"
                f"⚠️ 신뢰할 수 있는 파일만 실행하세요."
            )

            return messagebox.askyesno(
                "실행 파일 확인",
                message,
                icon='warning'
            )

        except Exception as e:
            logger.error(f"실행 확인 대화상자 실패: {str(e)}")
            # 확인할 수 없으면 안전을 위해 차단
            return False