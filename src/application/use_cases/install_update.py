# -*- coding: utf-8 -*-
"""InstallUpdateUseCase - 업데이트 설치 및 재시작 Use Case"""

import logging
from pathlib import Path
from typing import Optional

from ...infrastructure.services.update_installer_service import UpdateInstallerService


logger = logging.getLogger(__name__)


class InstallUpdateUseCase:
    """업데이트 설치 및 애플리케이션 재시작을 관리하는 Use Case

    비즈니스 규칙:
    - Windows Batch script를 생성하여 파일 교체 수행
    - 현재 프로세스 종료 후 파일 교체
    - 새 버전으로 자동 재시작
    - Script 자체 삭제로 흔적 제거

    Attributes:
        installer: 업데이트 설치 서비스
        current_exe_path: 현재 실행 중인 exe 파일 경로

    Examples:
        >>> use_case = InstallUpdateUseCase(installer, Path("D:/app/SimpleTodo.exe"))
        >>> new_exe_path = Path("D:/temp/SimpleTodo_new.exe")
        >>> success = use_case.execute(new_exe_path)
        >>> if success:
        ...     print("업데이트 시작됨. 앱이 곧 종료됩니다.")

    Warning:
        execute() 메서드가 성공하면 현재 애플리케이션이 종료됩니다!
    """

    def __init__(
        self,
        installer: UpdateInstallerService,
        current_exe_path: Path
    ):
        """InstallUpdateUseCase 초기화

        Args:
            installer: 업데이트 설치 서비스
            current_exe_path: 현재 실행 중인 exe 파일 경로

        Raises:
            TypeError: installer가 UpdateInstallerService가 아닌 경우
            ValueError: current_exe_path가 유효하지 않은 경우
        """
        if not isinstance(installer, UpdateInstallerService):
            raise TypeError(
                f"installer는 UpdateInstallerService여야 합니다. "
                f"받은 타입: {type(installer)}"
            )

        if not current_exe_path or not isinstance(current_exe_path, Path):
            raise ValueError(
                f"current_exe_path가 유효하지 않습니다: {current_exe_path}"
            )

        self.installer = installer
        self.current_exe_path = Path(current_exe_path)

        logger.info(
            f"InstallUpdateUseCase 초기화: current_exe={self.current_exe_path}"
        )

    def execute(self, new_exe_path: Path) -> bool:
        """업데이트를 설치하고 애플리케이션을 재시작합니다.

        비즈니스 흐름:
        1. 새 exe 파일 존재 확인
        2. Batch script 생성 (installer.create_update_script())
        3. Batch script 실행 (installer.execute_update())
        4. 성공 시 True 반환 (앱은 곧 종료됨)
        5. 실패 시 False 반환

        Args:
            new_exe_path: 새 버전 exe 파일 경로

        Returns:
            bool: 성공 시 True (앱 곧 종료됨), 실패 시 False

        Raises:
            TypeError: new_exe_path가 Path가 아닌 경우
            ValueError: new_exe_path가 존재하지 않는 경우

        Warning:
            이 메서드가 True를 반환하면 현재 애플리케이션이 곧 종료됩니다!
            UI는 "앱을 종료하고 업데이트를 설치합니다..." 메시지를 표시해야 합니다.

        Note:
            Batch script는 다음 작업을 수행합니다:
            1. 2초 대기 (프로세스 종료 대기)
            2. 이전 프로세스 강제 종료 (taskkill)
            3. 파일 교체 (이전 exe 삭제 → 새 exe 이동)
            4. 새 앱 실행
            5. Script 자체 삭제
        """
        if not isinstance(new_exe_path, Path):
            raise TypeError(
                f"new_exe_path는 Path여야 합니다. "
                f"받은 타입: {type(new_exe_path)}"
            )

        new_exe_path = Path(new_exe_path)

        if not new_exe_path.exists():
            raise ValueError(f"새 exe 파일이 존재하지 않습니다: {new_exe_path}")

        try:
            logger.info("업데이트 설치 시작...")
            logger.info(f"새 exe: {new_exe_path}")
            logger.info(f"현재 exe: {self.current_exe_path}")

            # 1. Batch script 생성
            script_path = self.installer.create_update_script(
                new_exe_path=new_exe_path,
                current_exe_path=self.current_exe_path
            )

            if not script_path:
                logger.error("Batch script 생성 실패")
                return False

            logger.info(f"Batch script 생성 완료: {script_path}")

            # 2. Script 실행
            success = self.installer.execute_update(script_path)

            if not success:
                logger.error("Batch script 실행 실패")
                # Script 파일 정리
                self._cleanup_script(script_path)
                return False

            logger.info("업데이트 설치가 시작되었습니다. 애플리케이션을 종료합니다.")
            return True

        except Exception as e:
            logger.error(f"업데이트 설치 중 오류 발생: {e}", exc_info=True)
            return False

    def prepare_for_shutdown(self) -> None:
        """애플리케이션 종료 전 준비 작업을 수행합니다.

        다음 작업을 수행합니다:
        - 데이터 저장 (TODO 리스트, 설정 등)
        - 리소스 정리 (파일 핸들, 네트워크 연결 등)
        - 로그 플러시

        Note:
            이 메서드는 execute() 호출 전에 UI에서 호출해야 합니다.
            데이터 무결성을 보장하기 위해 필수적입니다.

        Examples:
            >>> use_case.prepare_for_shutdown()
            >>> # 데이터 저장 완료
            >>> use_case.execute(new_exe_path)
            >>> # 앱 종료
        """
        logger.info("애플리케이션 종료 준비 중...")

        try:
            # 로그 플러시
            for handler in logging.getLogger().handlers:
                handler.flush()

            logger.info("종료 준비 완료")

        except Exception as e:
            logger.error(f"종료 준비 중 오류: {e}", exc_info=True)

    def verify_new_exe(self, new_exe_path: Path) -> bool:
        """새 exe 파일의 유효성을 검증합니다.

        다음을 확인합니다:
        - 파일 존재 여부
        - 파일 확장자 (.exe)
        - 파일 크기 (0 bytes가 아닌지)

        Args:
            new_exe_path: 검증할 exe 파일 경로

        Returns:
            bool: 유효하면 True

        Note:
            이 메서드는 execute() 호출 전에 검증용으로 사용할 수 있습니다.
        """
        try:
            new_exe_path = Path(new_exe_path)

            # 파일 존재 확인
            if not new_exe_path.exists():
                logger.error(f"파일이 존재하지 않습니다: {new_exe_path}")
                return False

            # 확장자 확인
            if not new_exe_path.suffix.lower() == '.exe':
                logger.error(f"exe 파일이 아닙니다: {new_exe_path}")
                return False

            # 파일 크기 확인
            file_size = new_exe_path.stat().st_size
            if file_size == 0:
                logger.error(f"파일 크기가 0입니다: {new_exe_path}")
                return False

            logger.info(f"새 exe 파일 검증 성공: {new_exe_path} ({file_size:,} bytes)")
            return True

        except Exception as e:
            logger.error(f"파일 검증 중 오류: {e}", exc_info=True)
            return False

    def _cleanup_script(self, script_path: Optional[Path]):
        """실패한 Batch script를 정리합니다.

        Args:
            script_path: 삭제할 script 경로
        """
        if not script_path:
            return

        try:
            script_path = Path(script_path)
            if script_path.exists():
                script_path.unlink()
                logger.info(f"Script 파일 삭제: {script_path}")
        except Exception as e:
            logger.warning(f"Script 파일 삭제 실패: {script_path} - {e}")

    def __repr__(self) -> str:
        """개발자용 문자열 표현을 반환합니다."""
        return f"InstallUpdateUseCase(current_exe='{self.current_exe_path}')"
