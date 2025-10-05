# -*- coding: utf-8 -*-
"""DataMigrationService - 레거시 데이터 포맷 변환"""

import logging
from typing import Union, Dict, List, Any
from datetime import datetime

# 로깅 설정
logger = logging.getLogger(__name__)


class DataMigrationService:
    """레거시 데이터 포맷을 신규 포맷으로 변환하는 서비스

    manualOrder 필드 추가 및 제거 지원
    """

    @staticmethod
    def detect_legacy_format(data: Union[Dict, List]) -> bool:
        """레거시 형식인지 감지합니다.

        Args:
            data: 로드된 JSON 데이터

        Returns:
            bool: 레거시 형식이면 True, 신규 형식이면 False
        """
        # 배열이면 레거시 형식
        if isinstance(data, list):
            logger.info("Legacy format detected: data is a list")
            return True

        # 딕셔너리인데 version 필드가 없으면 레거시
        if isinstance(data, dict) and "version" not in data:
            logger.info("Legacy format detected: missing version field")
            return True

        logger.info("New format detected")
        return False

    @staticmethod
    def needs_manual_order_migration(data: Dict[str, Any]) -> bool:
        """manualOrder 필드가 없는 신규 포맷 데이터인지 확인합니다.

        Args:
            data: 신규 형식 데이터

        Returns:
            bool: manualOrder 마이그레이션 필요 여부
        """
        if not isinstance(data, dict) or "todos" not in data:
            return False

        todos = data.get("todos", [])
        if not todos:
            return False

        # 첫 번째 todo에 manualOrder가 없으면 마이그레이션 필요
        first_todo = todos[0]
        return "manualOrder" not in first_todo

    @staticmethod
    def migrate_legacy_data(legacy_data: Union[Dict, List]) -> Dict[str, Any]:
        """레거시 포맷을 신규 포맷으로 변환합니다.

        Args:
            legacy_data: 레거시 형식 데이터

        Returns:
            Dict: 신규 형식 데이터

        Raises:
            ValueError: 변환 실패 시
        """
        try:
            # 레거시 배열을 todos로 변환
            if isinstance(legacy_data, list):
                todos = legacy_data
            elif isinstance(legacy_data, dict):
                todos = legacy_data.get("todos", [])
            else:
                raise ValueError(f"Unsupported data type: {type(legacy_data)}")

            # 각 TODO 항목 변환
            migrated_todos = []
            for i, todo in enumerate(todos):
                try:
                    migrated_todo = DataMigrationService._migrate_todo_item(todo)
                    migrated_todos.append(migrated_todo)
                except Exception as e:
                    logger.warning(f"Failed to migrate todo item {i}: {e}")
                    # 기본값으로 채워서 계속 진행
                    migrated_todo = DataMigrationService._create_fallback_todo(todo, i)
                    migrated_todos.append(migrated_todo)

            # 신규 형식으로 구성
            migrated_data = {
                "version": "1.0",
                "settings": {
                    "sortOrder": "dueDate_asc",
                    "splitRatio": [9, 1],  # 진행중 섹션 최대화
                    "alwaysOnTop": False
                },
                "todos": migrated_todos
            }

            logger.info(f"Successfully migrated {len(migrated_todos)} todos")
            return migrated_data

        except Exception as e:
            logger.error(f"Migration failed: {e}")
            raise ValueError(f"Failed to migrate legacy data: {e}") from e

    @staticmethod
    def add_manual_order_field(data: Dict[str, Any]) -> Dict[str, Any]:
        """기존 신규 포맷 데이터에 manualOrder 필드를 추가합니다.

        Args:
            data: 신규 형식 데이터 (manualOrder 없음)

        Returns:
            Dict: manualOrder가 추가된 데이터
        """
        if not isinstance(data, dict) or "todos" not in data:
            logger.warning("Invalid data format for manual order migration")
            return data

        todos = data.get("todos", [])
        for todo in todos:
            if "manualOrder" not in todo:
                # order 값을 복사하여 manualOrder로 설정
                todo["manualOrder"] = todo.get("order", 0)
                todo_id = todo.get("id", "unknown")[:8]
                logger.debug(f"Added manualOrder to todo {todo_id}...")

        logger.info(f"Added manualOrder field to {len(todos)} todos")
        return data

    @staticmethod
    def needs_manual_order_removal_migration(data: Dict[str, Any]) -> bool:
        """manualOrder 필드 제거가 필요한지 확인합니다.

        Args:
            data: 검사할 데이터

        Returns:
            bool: manualOrder 필드가 존재하면 True
        """
        if not isinstance(data, dict) or "todos" not in data:
            return False

        todos = data.get("todos", [])
        # 하나라도 manualOrder 필드가 있으면 제거 필요
        return any("manualOrder" in todo for todo in todos if isinstance(todo, dict))

    @staticmethod
    def remove_manual_order_field(data: Dict[str, Any]) -> Dict[str, Any]:
        """manualOrder 필드를 제거하고 order로 통합합니다.

        Args:
            data: 마이그레이션할 데이터

        Returns:
            Dict[str, Any]: 마이그레이션된 데이터
        """
        migrated_data = data.copy()
        migrated_data["todos"] = []

        for todo in data.get("todos", []):
            migrated_todo = todo.copy()

            # manualOrder가 있으면 order로 복사 (manualOrder 우선)
            if "manualOrder" in migrated_todo:
                manual_order = migrated_todo["manualOrder"]
                migrated_todo["order"] = manual_order
                del migrated_todo["manualOrder"]
                logger.debug(
                    f"Removed manualOrder from {migrated_todo.get('id', 'unknown')[:8]}..., "
                    f"set order={manual_order}"
                )

            migrated_data["todos"].append(migrated_todo)

        logger.info(f"Removed manualOrder field from {len(migrated_data['todos'])} todos")
        return migrated_data

    @staticmethod
    def _migrate_todo_item(todo: Dict[str, Any]) -> Dict[str, Any]:
        """개별 TODO 항목을 변환합니다."""
        migrated = {}

        # ID (필수)
        migrated["id"] = todo.get("id", "")
        if not migrated["id"]:
            raise ValueError("Missing required field: id")

        # Content (text -> content)
        migrated["content"] = todo.get("text", todo.get("content", ""))
        if not migrated["content"]:
            raise ValueError("Missing required field: content")

        # Completed (필수)
        migrated["completed"] = todo.get("completed", False)

        # Created At (created_at -> createdAt)
        created_at = todo.get("created_at", todo.get("createdAt"))
        if not created_at:
            created_at = datetime.now().isoformat()
        migrated["createdAt"] = created_at

        # Due Date (due_date -> dueDate, optional)
        due_date = todo.get("due_date", todo.get("dueDate"))
        if due_date:
            migrated["dueDate"] = due_date

        # Order (position -> order)
        order_value = todo.get("position", todo.get("order", 0))
        migrated["order"] = order_value

        # ManualOrder (position -> manualOrder)
        # NOTE: 레거시 마이그레이션 시에만 생성, 신규 데이터는 제거 예정
        if "manualOrder" in todo:
            migrated["manualOrder"] = todo["manualOrder"]
        elif "position" in todo:
            migrated["manualOrder"] = todo["position"]
        else:
            migrated["manualOrder"] = order_value

        return migrated

    @staticmethod
    def _create_fallback_todo(todo: Dict[str, Any], index: int) -> Dict[str, Any]:
        """마이그레이션 실패 시 기본값으로 채운 TODO를 생성합니다."""
        from uuid import uuid4

        order_value = todo.get("position", todo.get("order", index))

        return {
            "id": todo.get("id", str(uuid4())),
            "content": todo.get("text", todo.get("content", f"Migrated TODO {index}")),
            "completed": todo.get("completed", False),
            "createdAt": todo.get("created_at", todo.get("createdAt", datetime.now().isoformat())),
            "order": order_value,
            "manualOrder": order_value
        }

    @staticmethod
    def needs_migration(data: Union[Dict, List]) -> bool:
        """마이그레이션이 필요한지 확인합니다."""
        return DataMigrationService.detect_legacy_format(data)

    @staticmethod
    def validate_migrated_data(data: Dict[str, Any]) -> bool:
        """마이그레이션된 데이터의 유효성을 검증합니다."""
        try:
            if not isinstance(data, dict):
                return False

            if "version" not in data:
                return False

            if "settings" not in data:
                return False

            if "todos" not in data or not isinstance(data["todos"], list):
                return False

            settings = data["settings"]
            required_settings = ["sortOrder", "splitRatio", "alwaysOnTop"]
            for field in required_settings:
                if field not in settings:
                    return False

            for todo in data["todos"]:
                if not isinstance(todo, dict):
                    return False

                required_fields = ["id", "content", "completed", "createdAt", "order"]
                for field in required_fields:
                    if field not in todo:
                        return False

            return True

        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return False
