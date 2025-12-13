# -*- coding: utf-8 -*-
"""DataPreservationService - 데이터 무결성 보장 서비스"""

import logging
import json
import os
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path
from ...domain.entities.todo import Todo


logger = logging.getLogger(__name__)


class DataPreservationService:
    """데이터 무결성을 보장하는 서비스

    저장 전 데이터를 검증하고 필요시 수정합니다.
    업데이트 시 데이터 손실을 방지하기 위한 강화된 기능을 제공합니다.
    """

    @staticmethod
    def validate_and_fix(todos: List[Todo]) -> List[Todo]:
        """TODO 리스트를 검증하고 수정합니다.

        Args:
            todos: 검증할 TODO 리스트

        Returns:
            List[Todo]: 검증 및 수정된 TODO 리스트

        검증 규칙:
        1. 모든 TODO는 유효한 ID 보유 (TodoId Value Object가 보장)
        2. order는 중복 없이 연속적 (섹션별)
        3. completed 상태와 섹션 일치
        4. createdAt 필드 보존 (누락 시 현재 시간)

        수정 사항:
        - order 중복 시 재계산
        - createdAt 누락 시 현재 시간으로 설정

        Raises:
            ValueError: 중복 ID가 있는 경우
        """
        # 1. ID 중복 검증 (예외 발생)
        DataPreservationService.validate_unique_ids(todos)

        # 2. createdAt 보장
        todos = DataPreservationService.ensure_created_at(todos)

        # 3. order 일관성 보장
        todos = DataPreservationService.ensure_order_consistency(todos)

        return todos

    @staticmethod
    def ensure_order_consistency(todos: List[Todo]) -> List[Todo]:
        """order 필드의 일관성을 보장합니다.

        Args:
            todos: TODO 리스트

        Returns:
            List[Todo]: order가 재계산된 TODO 리스트

        로직:
        - 진행중/완료 섹션별로 order를 0부터 순차적으로 설정
        - 중복 방지
        """
        # 1. 진행중(completed=False)과 완료(completed=True) 분리
        in_progress = [todo for todo in todos if not todo.completed]
        completed = [todo for todo in todos if todo.completed]

        # 2. 각 섹션의 order를 0부터 순차적으로 재설정
        for index, todo in enumerate(in_progress):
            todo.change_order(index)

        for index, todo in enumerate(completed):
            todo.change_order(index)

        # 3. 합쳐서 반환
        return in_progress + completed

    @staticmethod
    def ensure_created_at(todos: List[Todo]) -> List[Todo]:
        """createdAt 필드를 보장합니다.

        Args:
            todos: TODO 리스트

        Returns:
            List[Todo]: createdAt이 보장된 TODO 리스트

        로직:
        - createdAt이 None이거나 유효하지 않으면 현재 시간으로 설정
        """
        current_time = datetime.now()

        for todo in todos:
            # createdAt이 None이면 현재 시간으로 설정
            if todo.created_at is None:
                todo.created_at = current_time

        return todos

    @staticmethod
    def validate_unique_ids(todos: List[Todo]) -> bool:
        """ID 중복을 검사합니다.

        Args:
            todos: TODO 리스트

        Returns:
            bool: 중복이 없으면 True

        Raises:
            ValueError: 중복 ID가 있는 경우
        """
        # 1. 모든 TODO의 ID 추출
        ids = [str(todo.id) for todo in todos]

        # 2. set으로 중복 검사
        unique_ids = set(ids)

        # 3. 중복 시 ValueError 발생
        if len(ids) != len(unique_ids):
            # 중복된 ID 찾기
            seen = set()
            duplicates = set()
            for todo_id in ids:
                if todo_id in seen:
                    duplicates.add(todo_id)
                seen.add(todo_id)

            raise ValueError(f"Duplicate IDs found: {duplicates}")

        return True

    @staticmethod
    def create_data_backup(data: List[Todo], backup_dir: Optional[Path] = None) -> Optional[Path]:
        """TODO 데이터 백업을 생성합니다.

        Args:
            data: 백업할 TODO 데이터 리스트
            backup_dir: 백업 디렉터리 (None이면 기본 위치 사용)

        Returns:
            Optional[Path]: 백업 파일 경로 (실패 시 None)
        """
        try:
            if backup_dir is None:
                # 사용자 문서 디렉터리의 SimpleTodo 백업 폴더
                import os
                documents_dir = Path(os.path.expanduser("~/Documents"))
                backup_dir = documents_dir / "SimpleTodo" / "backups"

            # 백업 디렉터리 생성
            backup_dir.mkdir(parents=True, exist_ok=True)

            # 백업 파일명 생성 (타임스탬프 포함)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = backup_dir / f"todo_backup_{timestamp}.json"

            # 데이터를 JSON으로 직렬화
            backup_data = {
                "version": "1.0",
                "timestamp": timestamp,
                "count": len(data),
                "todos": [todo.to_dict() for todo in data]
            }

            # 백업 파일 저장
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2)

            logger.info(f"데이터 백업 생성 완료: {backup_file}")
            return backup_file

        except Exception as e:
            logger.error(f"데이터 백업 실패: {e}")
            return None

    @staticmethod
    def load_data_backup(backup_file: Path) -> Optional[List[Todo]]:
        """백업 파일에서 TODO 데이터를 로드합니다.

        Args:
            backup_file: 백업 파일 경로

        Returns:
            Optional[List[Todo]]: 복원된 TODO 리스트 (실패 시 None)
        """
        try:
            backup_file = Path(backup_file)
            if not backup_file.exists():
                logger.error(f"백업 파일이 존재하지 않습니다: {backup_file}")
                return None

            # 백업 파일 로드
            with open(backup_file, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)

            # 데이터 검증
            if not isinstance(backup_data, dict) or 'todos' not in backup_data:
                logger.error("유효하지 않은 백업 파일 형식")
                return None

            # TODO 객체 복원
            todos = []
            for todo_data in backup_data['todos']:
                # Todo 객체 생성 (도메인 엔티티의 from_dict 메서드 사용)
                todo = Todo.from_dict(todo_data)
                todos.append(todo)

            logger.info(f"백업 데이터 복원 완료: {len(todos)}개 항목")
            return todos

        except Exception as e:
            logger.error(f"백업 데이터 로드 실패: {e}")
            return None

    @staticmethod
    def cleanup_old_backups(backup_dir: Path, keep_count: int = 10) -> None:
        """오래된 백업 파일을 정리합니다.

        Args:
            backup_dir: 백업 파일이 있는 디렉터리
            keep_count: 유지할 최신 백업 파일 개수
        """
        try:
            backup_dir = Path(backup_dir)
            if not backup_dir.exists():
                return

            # 백업 파일 목록 가져오기 (수정시간 기준 정렬)
            backup_files = list(backup_dir.glob("todo_backup_*.json"))
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

            # keep_count만큼 최신 파일 제외하고 삭제
            for old_backup in backup_files[keep_count:]:
                try:
                    old_backup.unlink()
                    logger.info(f"오래된 백업 파일 삭제: {old_backup}")
                except Exception as e:
                    logger.warning(f"백업 파일 삭제 실패: {old_backup} - {e}")

        except Exception as e:
            logger.error(f"백업 정리 중 오류: {e}")

    @staticmethod
    def verify_data_integrity(original: List[Todo], restored: List[Todo]) -> bool:
        """데이터 무결성을 검증합니다.

        Args:
            original: 원본 데이터
            restored: 복원된 데이터

        Returns:
            bool: 무결성 검증 결과
        """
        try:
            # 개수 비교
            if len(original) != len(restored):
                logger.error(f"데이터 개수 불일치: 원본={len(original)}, 복원={len(restored)}")
                return False

            # 각 항목 비교
            for orig, resto in zip(original, restored):
                if str(orig.id) != str(resto.id):
                    logger.error(f"ID 불일치: {orig.id} vs {resto.id}")
                    return False

                if orig.content != resto.content:
                    logger.error(f"내용 불일치: {orig.id}")
                    return False

                if orig.completed != resto.completed:
                    logger.error(f"완료 상태 불일치: {orig.id}")
                    return False

            logger.info("데이터 무결성 검증 성공")
            return True

        except Exception as e:
            logger.error(f"데이터 무결성 검증 중 오류: {e}")
            return False

    @staticmethod
    def ensure_data_saved(data: List[Todo], file_path: Path) -> bool:
        """데이터가 성공적으로 저장되었는지 확인합니다.

        Args:
            data: 저장할 데이터
            file_path: 저장 파일 경로

        Returns:
            bool: 저장 성공 여부
        """
        try:
            file_path = Path(file_path)

            # 데이터를 파일에 저장
            save_data = [todo.to_dict() for todo in data]
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)

            # 저장 확인
            if not file_path.exists():
                logger.error("파일이 생성되지 않음")
                return False

            # 파일 크기 확인
            if file_path.stat().st_size == 0:
                logger.error("파일이 비어있음")
                return False

            # 다시 읽어서 검증
            with open(file_path, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)

            if len(loaded_data) != len(data):
                logger.error("저장된 데이터 개수 불일치")
                return False

            logger.info(f"데이터 저장 확인 완료: {file_path}")
            return True

        except Exception as e:
            logger.error(f"데이터 저장 확인 중 오류: {e}")
            return False

    @staticmethod
    def get_backup_info(backup_file: Path) -> Optional[Dict[str, Any]]:
        """백업 파일의 정보를 반환합니다.

        Args:
            backup_file: 백업 파일 경로

        Returns:
            Optional[Dict[str, Any]]: 백업 정보 (실패 시 None)
        """
        try:
            backup_file = Path(backup_file)
            if not backup_file.exists():
                return None

            # 파일 정보
            stat = backup_file.stat()

            # 백업 파일 로드
            with open(backup_file, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)

            info = {
                "file_path": str(backup_file),
                "file_size": stat.st_size,
                "created_time": datetime.fromtimestamp(stat.st_ctime),
                "modified_time": datetime.fromtimestamp(stat.st_mtime),
                "version": backup_data.get("version", "unknown"),
                "timestamp": backup_data.get("timestamp"),
                "count": backup_data.get("count", 0)
            }

            return info

        except Exception as e:
            logger.error(f"백업 정보 조회 실패: {e}")
            return None
