# -*- coding: utf-8 -*-
"""Update Installer Service - Windows Batch script 생성 및 실행"""

import logging
import subprocess
import tempfile
import os
import psutil
from pathlib import Path
from typing import Optional
import sys


logger = logging.getLogger(__name__)


class UpdateInstallerService:
    """Windows Batch script를 생성하고 실행하여 업데이트를 설치하는 서비스

    현재 실행 중인 exe를 새 버전으로 교체하는 Batch script를 생성합니다.
    Script는 다음 작업을 수행합니다:
    1. 프로세스 종료 대기 (2초)
    2. 이전 프로세스 강제 종료 (혹시 남아있을 경우)
    3. 파일 교체
    4. 새 앱 실행
    5. Batch script 자체 삭제

    Examples:
        >>> service = UpdateInstallerService()
        >>> new_exe = Path("D:/temp/SimpleTodo_new.exe")
        >>> current_exe = Path("D:/app/SimpleTodo.exe")
        >>> script_path = service.create_update_script(new_exe, current_exe)
        >>> if script_path:
        ...     service.execute_update(script_path)
    """

    def __init__(self):
        """UpdateInstallerService 초기화"""
        self.current_pid = os.getpid()
        self.process_name = Path(sys.argv[0] if sys.argv else "SimpleTodo.exe").stem
        logger.info(f"UpdateInstallerService 초기화 - PID: {self.current_pid}, Process: {self.process_name}")

    def create_update_script(
        self,
        new_exe_path: Path,
        current_exe_path: Path
    ) -> Optional[Path]:
        """업데이트 Batch script를 생성합니다.

        Args:
            new_exe_path: 새 버전 exe 파일 경로
            current_exe_path: 현재 실행 중인 exe 파일 경로

        Returns:
            Optional[Path]: 생성된 script 경로 (실패 시 None)

        Raises:
            ValueError: 경로가 유효하지 않은 경우
        """
        # 경로 검증
        if not new_exe_path or not isinstance(new_exe_path, Path):
            raise ValueError(f"유효하지 않은 new_exe_path: {new_exe_path}")

        if not current_exe_path or not isinstance(current_exe_path, Path):
            raise ValueError(f"유효하지 않은 current_exe_path: {current_exe_path}")

        new_exe_path = Path(new_exe_path)
        current_exe_path = Path(current_exe_path)

        # 새 exe 파일 존재 확인
        if not new_exe_path.exists():
            logger.error(f"새 exe 파일이 존재하지 않습니다: {new_exe_path}")
            return None

        try:
            # Batch script 생성
            script_content = self._generate_batch_script(new_exe_path, current_exe_path)

            # 임시 파일로 저장
            with tempfile.NamedTemporaryFile(
                mode='w',
                encoding='utf-8',
                delete=False,
                suffix='.bat',
                prefix='SimpleTodo_Update_'
            ) as script_file:
                script_file.write(script_content)
                script_path = Path(script_file.name)

            logger.info(f"업데이트 script 생성 완료: {script_path}")
            return script_path

        except Exception as e:
            logger.error(f"Script 생성 중 오류: {e}", exc_info=True)
            return None

    def wait_for_process_termination(self, pid: int, timeout: int = 10) -> bool:
        """프로세스가 완전히 종료될 때까지 대기합니다.

        Args:
            pid: 종료를 기다릴 프로세스 ID
            timeout: 최대 대기 시간 (초)

        Returns:
            bool: 프로세스가 종료되면 True, 타임아웃 시 False
        """
        try:
            process = psutil.Process(pid)

            # 프로세스가 이미 종료된 경우
            if not process.is_running():
                logger.info(f"프로세스 {pid}가 이미 종료되었습니다.")
                return True

            logger.info(f"프로세스 {pid} 종료 대기 시작 (최대 {timeout}초)...")

            # 프로세스 종료 대기
            try:
                process.wait(timeout=timeout)
                logger.info(f"프로세스 {pid}가 성공적으로 종료되었습니다.")
                return True
            except psutil.TimeoutExpired:
                logger.warning(f"프로세스 {pid}가 {timeout}초 후에도 종료되지 않았습니다.")

                # 강제 종료 시도
                try:
                    process.kill()
                    process.wait(timeout=3)
                    logger.info(f"프로세스 {pid}를 강제 종료했습니다.")
                    return True
                except (psutil.NoSuchProcess, psutil.TimeoutExpired):
                    logger.error(f"프로세스 {pid} 강제 종료 실패")
                    return False

        except psutil.NoSuchProcess:
            logger.info(f"프로세스 {pid}가 존재하지 않습니다.")
            return True
        except Exception as e:
            logger.error(f"프로세스 종료 확인 중 오류: {e}")
            return False

    def execute_update(self, script_path: Path) -> bool:
        """업데이트 Batch script를 실행하고 현재 앱을 종료합니다.

        Args:
            script_path: Batch script 경로

        Returns:
            bool: 성공 여부

        Note:
            이 메서드가 성공하면 현재 애플리케이션이 종료됩니다!
        """
        if not script_path or not isinstance(script_path, Path):
            logger.error(f"유효하지 않은 script_path: {script_path}")
            return False

        script_path = Path(script_path)

        if not script_path.exists():
            logger.error(f"Script 파일이 존재하지 않습니다: {script_path}")
            return False

        try:
            logger.info(f"업데이트 script 실행: {script_path}")
            logger.info(f"현재 프로세스 정보 - PID: {self.current_pid}, Name: {self.process_name}")

            # Batch script를 백그라운드에서 실행
            # CREATE_NO_WINDOW 플래그로 콘솔 창 숨김
            subprocess.Popen(
                [str(script_path)],
                shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )

            logger.info("업데이트 script가 시작되었습니다. 애플리케이션을 종료합니다.")
            return True

        except Exception as e:
            logger.error(f"Script 실행 중 오류: {e}", exc_info=True)
            return False

    def _generate_batch_script(self, new_exe: Path, current_exe: Path) -> str:
        """Batch script 내용을 생성합니다.

        Args:
            new_exe: 새 버전 exe 파일 경로
            current_exe: 현재 exe 파일 경로

        Returns:
            str: Batch script 내용

        개선사항:
        1. 백업 후 교체 방식: 이전 exe를 먼저 백업하여 실패 시 복구 가능
        2. 프로세스 종료 확인 루프: taskkill 후 프로세스가 완전히 종료될 때까지 대기
        3. _MEI 임시 폴더 정리: PyInstaller 임시 폴더 명시적 삭제로 DLL 에러 방지
        """
        # Windows 경로로 변환 (백슬래시)
        new_exe_win = str(new_exe.absolute()).replace('/', '\\')
        current_exe_win = str(current_exe.absolute()).replace('/', '\\')
        backup_exe_win = current_exe_win.replace('.exe', '_old.exe')

        script = f'''@echo off
REM ============================================================
REM SimpleTodo 자동 업데이트 스크립트 (v2.7.0+)
REM UpdateInstallerService에서 생성
REM
REM 개선사항:
REM 1. 백업 방식으로 안전한 파일 교체
REM 2. 프로세스 종료 대기 루프 추가
REM 3. PyInstaller _MEI 임시 폴더 정리
REM 4. 사용자 친화적인 한국어 메시지
REM ============================================================

setlocal enabledelayedexpansion
chcp 65001 > nul

echo [SimpleTodo 업데이트] 업데이트를 시작합니다 (v2.7.0+)...

REM ============================================================
REM 1단계: 이전 exe 백업
REM ============================================================
echo [SimpleTodo 업데이트] 현재 프로그램을 백업합니다...
if exist "{current_exe_win}" (
    ren "{current_exe_win}" "{Path(current_exe).name.replace('.exe', '_old.exe')}"
    if errorlevel 1 (
        echo [SimpleTodo 오류] 백업 생성에 실패했습니다
        echo [SimpleTodo 정보] 관리자 권한으로 실행하거나 바이러스 백신을 확인해주세요
        echo.
        echo 아무 키나 누르면 창을 닫습니다...
        pause > nul
        exit /b 1
    )
    echo [SimpleTodo 정보] 백업이 완료되었습니다
) else (
    echo [SimpleTodo 경고] 백업할 파일이 없습니다
)

REM ============================================================
REM 2단계: 프로세스 안전 종료
REM ============================================================
echo [SimpleTodo 업데이트] 프로그램을 안전하게 종료합니다...
echo [SimpleTodo 정보] PID: {self.current_pid}

REM 1. 정상 종료 요청
taskkill /PID {self.current_pid} /T 2>nul
timeout /t 2 /nobreak > nul

REM 2. 프로세스 상태 확인 루프 (최대 5초 대기)
set PROCESS_CHECK=0
:CHECK_PROCESS_BY_PID
tasklist | find " {self.current_pid} " >nul
if %ERRORLEVEL% EQU 0 (
    REM 프로세스가 아직 살아있음
    if %PROCESS_CHECK% LSS 5 (
        echo [SimpleTodo 정보] 프로그램이 종료되기를 기다립니다... (!PROCESS_CHECK!/5)
        timeout /t 1 /nobreak > nul
        set /a PROCESS_CHECK=!PROCESS_CHECK!+1
        goto CHECK_PROCESS_BY_PID
    ) else (
        REM 강제 종료 시도
        echo [SimpleTodo 정보] 프로그램을 강제 종료합니다...
        taskkill /F /PID {self.current_pid} /T 2>nul
        timeout /t 1 /nobreak > nul
    )
)

REM 3. 프로세스 이름으로도 확인 (안전장치)
echo [SimpleTodo 업데이트] 남은 프로세스를 확인합니다...
taskkill /F /IM {self.process_name}.exe 2>nul
timeout /t 1 /nobreak > nul

REM 4. 최종 확인 (프로세스 이름으로)
set FINAL_CHECK=0
:FINAL_PROCESS_CHECK
tasklist | find /I "{self.process_name}.exe" >nul
if %ERRORLEVEL% EQU 0 (
    if %FINAL_CHECK% LSS 3 (
        echo [SimpleTodo 정보] 프로세스가 남아있습니다. 잠시만 기다려주세요... (!FINAL_CHECK!/3)
        timeout /t 1 /nobreak > nul
        set /a FINAL_CHECK=!FINAL_CHECK!+1
        goto FINAL_PROCESS_CHECK
    ) else (
        echo [SimpleTodo 경고] 일부 프로세스가 남아있을 수 있습니다
        echo [SimpleTodo 정보] 재부팅 후 남은 프로세스가 정리됩니다
    )
)

echo [SimpleTodo 정보] 프로그램 종료가 완료되었습니다

REM ============================================================
REM 3단계: 임시 파일 정리
REM ============================================================
echo [SimpleTodo 업데이트] 임시 파일을 정리합니다...
for /d %%i in ("%TEMP%\_MEI*") do (
    echo [SimpleTodo 정보] 임시 폴더 정리: %%~nxi
    rmdir /S /Q "%%i" 2>nul
)

REM ============================================================
REM 4단계: 새 파일 설치
REM ============================================================
echo [SimpleTodo 업데이트] 새 버전을 설치합니다...
move /Y "{new_exe_win}" "{current_exe_win}"
if errorlevel 1 (
    echo [SimpleTodo 오류] 파일 이동에 실패했습니다
    echo [SimpleTodo 원인] 1) 바이러스 백신 차단 2) 파일 사용 중 3) 디스크 공간 부족
    echo.
    echo 해결 방법:
    echo 1. 바이러스 백신에서 SimpleTodo를 예외 목록에 추가
    echo 2. 모든 SimpleTodo 창을 닫고 다시 시도
    echo 3. 디스크 공간을 확인
    echo.
    echo [SimpleTodo 업데이트] 백업에서 복원합니다...
    if exist "{backup_exe_win}" (
        ren "{backup_exe_win}" "{Path(current_exe).name}"
        echo [SimpleTodo 정보] 복원 완료
    )
    echo.
    echo 아무 키나 누르면 창을 닫습니다...
    pause > nul
    exit /b 1
)

echo [SimpleTodo 정보] 파일 설치가 완료되었습니다

REM ============================================================
REM 5단계: 프로그램 시작
REM ============================================================
echo [SimpleTodo 업데이트] 새 버전을 시작합니다...
timeout /t 1 /nobreak > nul
start "" "{current_exe_win}"

REM ============================================================
REM 6단계: 정리
REM ============================================================
echo [SimpleTodo 업데이트] 백업 파일을 정리합니다...
timeout /t 2 /nobreak > nul
if exist "{backup_exe_win}" (
    del /F /Q "{backup_exe_win}" 2>nul
    if errorlevel 1 (
        echo [SimpleTodo 경고] 백업 파일 삭제에 실패했습니다
        echo [SimpleTodo 정보] 수동 삭제해도 됩니다: {backup_exe_win}
    )
)

REM 스크립트 자체 삭제
echo [SimpleTodo 정보] 업데이트가 완료되었습니다!
(goto) 2>nul & del "%~f0"
endlocal
'''

        return script

    def __repr__(self) -> str:
        """개발자용 문자열 표현을 반환합니다."""
        return "UpdateInstallerService()"
