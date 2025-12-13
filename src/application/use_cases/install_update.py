# -*- coding: utf-8 -*-
"""InstallUpdateUseCase - 업데이트 설치 및 재시작 Use Case"""

import logging
import os
import sys
import ctypes
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

    def is_admin(self) -> bool:
        """현재 프로세스가 관리자 권한으로 실행 중인지 확인합니다.

        Returns:
            bool: 관리자 권한이면 True
        """
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False

    def check_write_permissions(self, path: Path) -> tuple[bool, str]:
        """지정된 경로의 쓰기 권한을 확인합니다.

        Args:
            path: 권한을 확인할 경로

        Returns:
            tuple[bool, str]: (권한 있음, 메시지)
        """
        try:
            path = Path(path)

            # 디렉터리가 없으면 생성 시도
            if not path.exists():
                if path.is_file():
                    path = path.parent
                try:
                    path.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    return False, f"디렉터리 생성 실패: {e}\n원인: 권한 부족 또는 읽기 전용 폴더"

            # 임시 파일 생성으로 쓰기 권한 테스트
            test_file = path / ".write_test_temp"
            try:
                test_file.write_text("test")
                test_file.unlink()
                return True, "쓰기 권한 확인됨"
            except PermissionError:
                return False, "쓰기 권한이 없습니다\n해결책: 관리자 권한으로 실행 또는 폴더 권한 확인"
            except Exception as e:
                return False, f"권한 확인 중 오류 발생: {e}"

        except Exception as e:
            return False, f"경로 확인 중 오류: {e}"

    def request_admin_privileges(self) -> bool:
        """관리자 권한을 요청합니다 (UAC 승격).

        Returns:
            bool: 권한 획득 성공 시 True (프로세스 재시작 필요)

        Note:
            Windows에서만 동작합니다.
            성공 시 현재 프로세스는 종료되고 관리자 권한으로 재시작됩니다.
        """
        if os.name != 'nt':
            logger.warning("UAC 승격은 Windows에서만 지원됩니다.")
            return False

        if self.is_admin():
            logger.info("이미 관리자 권한을 가지고 있습니다.")
            return True

        try:
            # 현재 스크립트/실행파일 경로
            executable = sys.executable if hasattr(sys, 'frozen') else __file__

            # ShellExecuteW를 사용하여 UAC 승격 요청
            rc = ctypes.windll.shell32.ShellExecuteW(
                None,           # 부모 창
                "runas",        # 동사 (관리자 권한 요청)
                executable,     # 실행 파일
                " ".join(sys.argv),  # 인자
                None,           # 작업 디렉터리
                1               # 보이기 모드 (SW_SHOWNORMAL)
            )

            # 성공 여부 확인 (32보다 크면 성공)
            if rc > 32:
                logger.info("관리자 권한 요청 성공. 프로세스를 재시작합니다.")
                return True
            else:
                logger.error(f"관리자 권한 요청 실패. Error code: {rc}")
                return False

        except Exception as e:
            logger.error(f"UAC 승격 중 오류: {e}")
            return False

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
        1. 권한 사전 확인 (쓰기 권한, 관리자 권한 필요 시)
        2. 새 exe 파일 존재 확인
        3. 현재 exe 백업 생성
        4. Batch script 생성 (installer.create_update_script())
        5. Batch script 실행 (installer.execute_update())
        6. 성공 시 True 반환 (앱은 곧 종료됨)
        7. 실패 시 롤백 시도

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

        # 백업 경로 저장용 변수
        backup_path = None

        try:
            logger.info("업데이트 설치 시작...")
            logger.info(f"새 exe: {new_exe_path}")
            logger.info(f"현재 exe: {self.current_exe_path}")

            # 0. 권한 사전 확인
            logger.info("권한 사전 확인 중...")

            # 현재 exe 디렉터리의 쓰기 권한 확인
            can_write, write_msg = self.check_write_permissions(self.current_exe_path.parent)
            if not can_write:
                logger.error(f"쓰기 권한 확인 실패: {write_msg}")
                # 관리자 권한 요청 시도
                if not self.is_admin():
                    logger.info("관리자 권한을 요청합니다...")
                    if self.request_admin_privileges():
                        # 권한 획득 성공 시 프로세스가 재시작되므로 여기서 종료
                        return True
                    else:
                        logger.error("관리자 권한 획득 실패")
                        return False
                else:
                    logger.error("이미 관리자 권한을 가지고 있지만 쓰기 권한이 없습니다")
                    return False

            logger.info("권한 확인 완료")

            # 1. 현재 exe 백업 생성
            logger.info("현재 exe 백업 생성 중...")
            backup_path = self.create_backup(self.current_exe_path)
            if not backup_path:
                logger.error("백업 생성 실패")
                return False

            # 2. Batch script 생성
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

                # 롤백 시도
                if backup_path:
                    logger.info("업데이트 실패로 롤백 시도 중...")
                    if self.rollback_update(backup_path, self.current_exe_path):
                        # 롤백 검증
                        if self.verify_rollback(backup_path, self.current_exe_path):
                            logger.info("롤백 성공 및 검증 완료")
                        else:
                            logger.error("롤백 검증 실패")
                    else:
                        logger.error("롤백 실패")

                return False

            logger.info("업데이트 설치가 시작되었습니다. 애플리케이션을 종료합니다.")

            # 성공 시 오래된 백업 파일 정리
            self.cleanup_old_backups(self.current_exe_path.parent)

            return True

        except Exception as e:
            logger.error(f"업데이트 설치 중 오류 발생: {e}", exc_info=True)

            # 예외 발생 시 롤백 시도
            if backup_path:
                logger.info("예외 발생으로 롤백 시도 중...")
                if self.rollback_update(backup_path, self.current_exe_path):
                    logger.info("예외 처리 중 롤백 성공")
                else:
                    logger.error("예외 처리 중 롤백 실패")

            return False

    def prepare_for_shutdown(self, data=None, data_file_path: Optional[Path] = None) -> bool:
        """애플리케이션 종료 전 준비 작업을 수행합니다.

        다음 작업을 수행합니다:
        - 데이터 저장 (TODO 리스트, 설정 등)
        - 데이터 백업 생성
        - 리소스 정리 (파일 핸들, 네트워크 연결 등)
        - 로그 플러시

        Args:
            data: 저장할 데이터 (TODO 리스트 등)
            data_file_path: 데이터 파일 경로

        Returns:
            bool: 준비 성공 여부

        Note:
            이 메서드는 execute() 호출 전에 UI에서 호출해야 합니다.
            데이터 무결성을 보장하기 위해 필수적입니다.

        Examples:
            >>> use_case.prepare_for_shutdown(todo_list, Path("data.json"))
            >>> # 데이터 저장 및 백업 완료
            >>> use_case.execute(new_exe_path)
            >>> # 앱 종료
        """
        logger.info("애플리케이션 종료 준비 중...")
        backup_path = None

        try:
            # 1. 데이터 저장 및 백업
            if data is not None and data_file_path is not None:
                logger.info("데이터 저장 및 백업 생성 중...")

                # DataPreservationService import
                from ...application.services.data_preservation_service import DataPreservationService

                # 데이터 유효성 검사 및 수정
                validated_data = DataPreservationService.validate_and_fix(data)

                # 데이터 저장 확인
                if not DataPreservationService.ensure_data_saved(validated_data, data_file_path):
                    logger.error("데이터 저장 실패")
                    return False

                # 데이터 백업 생성
                backup_path = DataPreservationService.create_data_backup(validated_data)
                if backup_path:
                    logger.info(f"데이터 백업 생성 성공: {backup_path}")
                else:
                    logger.warning("데이터 백업 생성 실패 (계속 진행)")

            # 2. 로그 핸들러 안전 종료
            logger.info("로그 핸들러 종료 중...")
            root_logger = logging.getLogger()

            # 모든 핸들러 플러시 및 종료
            for handler in root_logger.handlers[:]:  # 복사본으로 순회
                try:
                    handler.flush()
                    if hasattr(handler, 'close'):
                        handler.close()
                except Exception as e:
                    logger.warning(f"로그 핸들러 종료 중 오류: {e}")

            # 임시 파일 정리
            self._cleanup_temp_files()

            logger.info("종료 준비 완료")
            return True

        except Exception as e:
            logger.error(f"종료 준비 중 오류: {e}", exc_info=True)
            return False

    def _cleanup_temp_files(self) -> None:
        """임시 파일을 정리합니다."""
        try:
            import tempfile
            import glob

            # tempfile 모듈의 임시 디렉터리 가져오기
            temp_dir = tempfile.gettempdir()

            # SimpleTodo 관련 임시 파일 검색 및 삭제
            temp_patterns = [
                os.path.join(temp_dir, "SimpleTodo_*"),
                os.path.join(temp_dir, "*_SimpleTodo_*"),
                os.path.join(temp_dir, "tmp_*_todo*")
            ]

            for pattern in temp_patterns:
                for temp_file in glob.glob(pattern):
                    try:
                        if os.path.isfile(temp_file):
                            os.unlink(temp_file)
                            logger.debug(f"임시 파일 삭제: {temp_file}")
                        elif os.path.isdir(temp_file):
                            import shutil
                            shutil.rmtree(temp_file, ignore_errors=True)
                            logger.debug(f"임시 디렉터리 삭제: {temp_file}")
                    except Exception as e:
                        logger.warning(f"임시 파일 정리 실패: {temp_file} - {e}")

        except Exception as e:
            logger.warning(f"임시 파일 정리 중 오류: {e}")

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

    def create_backup(self, file_path: Path) -> Optional[Path]:
        """파일 백업을 생성합니다.

        Args:
            file_path: 백업할 파일 경로

        Returns:
            Optional[Path]: 백업 파일 경로 (실패 시 None)
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                logger.warning(f"백업할 파일이 존재하지 않습니다: {file_path}")
                return None

            # 백업 파일명 생성 (타임스탬프 포함)
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{file_path.stem}_backup_{timestamp}{file_path.suffix}"
            backup_path = file_path.parent / backup_name

            # 파일 복사
            import shutil
            shutil.copy2(file_path, backup_path)

            logger.info(f"백업 파일 생성: {backup_path}")
            return backup_path

        except Exception as e:
            logger.error(f"백업 생성 실패: {file_path} - {e}")
            return None

    def rollback_update(self, backup_path: Path, target_path: Path) -> bool:
        """업데이트를 롤백합니다.

        Args:
            backup_path: 백업 파일 경로
            target_path: 복원할 대상 경로

        Returns:
            bool: 롤백 성공 여부
        """
        try:
            backup_path = Path(backup_path)
            target_path = Path(target_path)

            if not backup_path.exists():
                logger.error(f"백업 파일이 존재하지 않습니다: {backup_path}")
                return False

            # 현재 파일 백업 (롤백 실패 대비)
            current_backup = target_path.with_suffix('.rollback_failed')
            if target_path.exists():
                import shutil
                shutil.move(str(target_path), str(current_backup))
                logger.info(f"현재 파일 백업: {current_backup}")

            # 백업 파일로 복원
            import shutil
            shutil.copy2(backup_path, target_path)

            logger.info(f"롤백 완료: {backup_path} -> {target_path}")

            # 롤백 성공 시 현재 파일 백업 삭제
            if current_backup.exists():
                current_backup.unlink()
                logger.info(f"임시 백업 파일 삭제: {current_backup}")

            return True

        except Exception as e:
            logger.error(f"롤백 실패: {backup_path} -> {target_path} - {e}")
            return False

    def cleanup_old_backups(self, directory: Path, keep_days: int = 7) -> None:
        """오래된 백업 파일을 정리합니다.

        Args:
            directory: 백업 파일이 있는 디렉터리
            keep_days: 유지할 일수
        """
        try:
            directory = Path(directory)
            if not directory.exists():
                return

            import datetime
            cutoff_time = datetime.datetime.now() - datetime.timedelta(days=keep_days)

            # 백업 파일 검색 및 삭제
            for backup_file in directory.glob("*_backup_*.exe"):
                try:
                    # 파일 생성 시간 확인
                    file_time = datetime.datetime.fromtimestamp(backup_file.stat().st_mtime)

                    if file_time < cutoff_time:
                        backup_file.unlink()
                        logger.info(f"오래된 백업 파일 삭제: {backup_file}")
                except Exception as e:
                    logger.warning(f"백업 파일 삭제 실패: {backup_file} - {e}")

        except Exception as e:
            logger.error(f"백업 정리 중 오류: {e}")

    def verify_rollback(self, original_path: Path, rollback_path: Path) -> bool:
        """롤백이 성공적으로 완료되었는지 검증합니다.

        Args:
            original_path: 원본 파일 경로 (백업)
            rollback_path: 롤백된 파일 경로

        Returns:
            bool: 검증 성공 여부
        """
        try:
            original_path = Path(original_path)
            rollback_path = Path(rollback_path)

            if not original_path.exists() or not rollback_path.exists():
                logger.error("파일이 존재하지 않아 검증 실패")
                return False

            # 파일 크기 비교
            original_size = original_path.stat().st_size
            rollback_size = rollback_path.stat().st_size

            if original_size != rollback_size:
                logger.error(f"파일 크기 불일치: 원본={original_size}, 롤백={rollback_size}")
                return False

            logger.info("롤백 검증 성공")
            return True

        except Exception as e:
            logger.error(f"롤백 검증 중 오류: {e}")
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
