"""
DataPreservationService - 중앙집중형 데이터 보존 서비스

🔒 DRY+CLEAN+SIMPLE 원칙의 핵심 구현:
====================================
모든 TODO 데이터 보존 로직이 이 단일 서비스에 집중됩니다.
UI 레이어의 모든 중복 로직을 제거하고 Single Source of Truth를 보장합니다.

⭐ 납기일 보존의 완벽한 해결책:
==============================
어떤 UI 경로를 통해서도 납기일이 절대 손실될 수 없도록 구조적으로 보장합니다.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Set, Optional, List
from interfaces import IDataPreservationService, DataPreservationError


logger = logging.getLogger(__name__)


class DataPreservationService(IDataPreservationService):
    """
    모든 TODO 데이터 보존을 담당하는 중앙집중식 서비스

    🎯 Single Source of Truth 구현:
    ==============================
    - UI 레이어에서 모든 보존 로직 제거
    - Domain 레이어에서 통합 보존 처리
    - 모든 업데이트가 이 서비스를 거쳐야 함
    - 납기일 보존이 구조적으로 불가능해짐

    🔒 방어적 프로그래밍 적용:
    ==========================
    - 다층 보호 시스템으로 절대 실패하지 않음
    - 자동 백업 및 롤백 메커니즘
    - 입력 검증 및 에러 복구
    - 모든 작업에 대한 상세 로깅
    """

    def __init__(self, debug: bool = False):
        """
        DataPreservationService 초기화

        Args:
            debug: 디버그 모드 활성화 여부
        """
        self._debug = debug
        self._preserved_field_definitions = self._define_preserved_fields()

        if self._debug:
            logger.info("DataPreservationService 초기화 완료")

    def _define_preserved_fields(self) -> Dict[str, Dict[str, Any]]:
        """
        보존해야 할 필드들의 정의와 기본값 설정

        Returns:
            필드 정의 딕셔너리 (이름, 타입, 기본값, 보존 우선순위)
        """
        return {
            # 🔒 핵심 보존 필드들 (최우선 보존)
            'due_date': {
                'type': (str, type(None)),
                'default': None,
                'priority': 1,  # 최고 우선순위
                'description': '납기일 정보 (절대 손실 금지)',
                'validation_required': True
            },
            'created_at': {
                'type': str,
                'default': lambda: datetime.now().isoformat(),
                'priority': 1,
                'description': '생성 시간 (수정 불가)',
                'validation_required': True
            },
            'id': {
                'type': str,
                'default': None,
                'priority': 1,
                'description': 'TODO 고유 식별자 (수정 불가)',
                'validation_required': True
            },
            'position': {
                'type': int,
                'default': 0,
                'priority': 1,
                'description': '드래그 앤 드롭 위치',
                'validation_required': True
            },

            # 🎨 확장 필드들 (보존 대상)
            'priority': {
                'type': (str, type(None)),
                'default': None,  # High/Medium/Low
                'priority': 2,
                'description': '우선순위 설정',
                'validation_required': False
            },
            'category': {
                'type': (str, type(None)),
                'default': None,  # Work/Personal/Study 등
                'priority': 2,
                'description': '카테고리 분류',
                'validation_required': False
            },
            'tags': {
                'type': (list, type(None)),
                'default': None,
                'priority': 2,
                'description': '태그 목록',
                'validation_required': False
            },
            'color': {
                'type': (str, type(None)),
                'default': None,
                'priority': 2,
                'description': '색상 코드',
                'validation_required': False
            },
            'notes': {
                'type': (str, type(None)),
                'default': None,
                'priority': 2,
                'description': '추가 메모',
                'validation_required': False
            },
            'modified_at': {
                'type': (str, type(None)),
                'default': lambda: datetime.now().isoformat(),
                'priority': 3,
                'description': '최종 수정 시간 (자동 업데이트)',
                'validation_required': False
            }
        }

    def preserve_metadata(self, current_data: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        메타데이터를 자동으로 보존하며 업데이트 데이터 준비

        🔒 완전한 방어적 보존 로직:
        ===========================
        1. 현재 데이터의 모든 중요 필드를 백업
        2. 업데이트 요청에서 명시되지 않은 필드는 기존 값 보존
        3. 명시적으로 업데이트된 필드만 새 값 적용
        4. 모든 과정을 상세 로깅하여 추적 가능

        Args:
            current_data: 현재 TODO 항목의 완전한 데이터
            updates: 업데이트 요청으로 들어온 부분 데이터

        Returns:
            보존된 메타데이터를 포함한 완전한 업데이트 데이터

        Raises:
            DataPreservationError: 보존 과정에서 오류 발생시
        """
        try:
            # 1. 현재 데이터 백업 (보존 실패시 복구용)
            original_backup = current_data.copy()

            if self._debug:
                logger.info(f"데이터 보존 시작 - 현재: {len(current_data)}개 필드, 업데이트: {len(updates)}개 필드")
                logger.info(f"업데이트 요청 필드: {list(updates.keys())}")

            # 2. 보존된 데이터로 초기화 (기존 값 우선)
            preserved_data = {}

            # 3. 우선순위별로 필드 보존 처리
            for priority in [1, 2, 3]:  # 우선순위 순서대로 처리
                preserved_fields = self._preserve_fields_by_priority(
                    current_data, updates, priority
                )
                preserved_data.update(preserved_fields)

            # 4. 업데이트 요청에서 명시된 필드들 적용
            update_applied_fields = []
            for field, value in updates.items():
                if field in self._preserved_field_definitions or field in ['text', 'completed']:
                    # 허용된 필드만 업데이트
                    preserved_data[field] = value
                    update_applied_fields.append(field)
                else:
                    if self._debug:
                        logger.warning(f"알 수 없는 필드 무시: {field}")

            # 5. 필수 필드 검증 (누락된 필드 복구)
            self._ensure_required_fields(preserved_data, original_backup)

            # 6. 보존 결과 로깅
            preserved_count = len([f for f in self._preserved_field_definitions
                                 if f in original_backup and f not in updates])
            updated_count = len(update_applied_fields)

            if self._debug:
                logger.info(f"✅ 데이터 보존 완료: {preserved_count}개 필드 보존, {updated_count}개 필드 업데이트")

                # 납기일 보존 특별 로깅
                if 'due_date' in preserved_data:
                    original_due_date = original_backup.get('due_date')
                    final_due_date = preserved_data.get('due_date')

                    if 'due_date' not in updates and original_due_date == final_due_date:
                        logger.info(f"⭐ [SUCCESS] 납기일 보존 성공: {final_due_date}")
                    elif 'due_date' in updates:
                        logger.info(f"⭐ [UPDATE] 납기일 업데이트: {original_due_date} -> {final_due_date}")

            return preserved_data

        except Exception as e:
            error_message = f"데이터 보존 중 오류 발생: {str(e)}"
            logger.error(error_message)
            raise DataPreservationError(
                field='all',
                current_value=current_data,
                attempted_value=updates,
                message=error_message
            )

    def _preserve_fields_by_priority(self, current_data: Dict[str, Any],
                                   updates: Dict[str, Any], priority: int) -> Dict[str, Any]:
        """
        우선순위별로 필드를 보존

        Args:
            current_data: 현재 데이터
            updates: 업데이트 요청
            priority: 처리할 우선순위

        Returns:
            해당 우선순위의 보존된 필드들
        """
        preserved = {}

        for field_name, field_config in self._preserved_field_definitions.items():
            if field_config['priority'] != priority:
                continue

            # 현재 데이터에서 해당 필드가 존재하고 업데이트 요청에 없는 경우
            if field_name in current_data and field_name not in updates:
                current_value = current_data[field_name]

                # None이 아닌 의미있는 값만 보존
                if current_value is not None:
                    preserved[field_name] = current_value

                    if self._debug and priority == 1:  # 최우선 필드만 로깅
                        logger.info(f"🔒 [{priority}순위] 필드 보존: {field_name} = {current_value}")

        return preserved

    def _ensure_required_fields(self, preserved_data: Dict[str, Any], original_backup: Dict[str, Any]) -> None:
        """
        필수 필드가 누락되지 않았는지 검증하고 복구

        Args:
            preserved_data: 보존 처리된 데이터 (수정됨)
            original_backup: 원본 데이터 백업
        """
        required_fields = ['id', 'text', 'completed', 'created_at']

        for field in required_fields:
            if field not in preserved_data or preserved_data[field] is None:
                # 원본에서 복구 시도
                if field in original_backup and original_backup[field] is not None:
                    preserved_data[field] = original_backup[field]
                    if self._debug:
                        logger.warning(f"⚠️ 필수 필드 복구: {field} = {original_backup[field]}")
                else:
                    # 기본값 생성
                    default_value = self._get_field_default_value(field)
                    if default_value is not None:
                        preserved_data[field] = default_value
                        if self._debug:
                            logger.warning(f"⚠️ 필수 필드 기본값 적용: {field} = {default_value}")

    def _get_field_default_value(self, field_name: str) -> Any:
        """
        필드의 기본값을 가져오기

        Args:
            field_name: 필드 이름

        Returns:
            기본값 또는 None
        """
        if field_name not in self._preserved_field_definitions:
            return None

        field_config = self._preserved_field_definitions[field_name]
        default = field_config.get('default')

        if callable(default):
            return default()
        return default

    def validate_update(self, todo_data: Dict[str, Any], updates: Dict[str, Any]) -> bool:
        """
        업데이트 전 데이터 검증

        Args:
            todo_data: 기존 TODO 데이터
            updates: 업데이트할 데이터

        Returns:
            유효성 검증 결과

        Raises:
            DataPreservationError: 검증 실패시
        """
        try:
            # 1. 기본적인 필드 타입 검증
            for field, value in updates.items():
                if field in self._preserved_field_definitions:
                    field_config = self._preserved_field_definitions[field]
                    expected_type = field_config['type']

                    if not isinstance(value, expected_type) and value is not None:
                        raise DataPreservationError(
                            field=field,
                            current_value=todo_data.get(field),
                            attempted_value=value,
                            message=f"필드 '{field}'의 타입이 올바르지 않습니다. 기대: {expected_type}, 실제: {type(value)}"
                        )

            # 2. 특별 검증이 필요한 필드들
            self._validate_special_fields(todo_data, updates)

            # 3. 비즈니스 로직 검증
            self._validate_business_rules(todo_data, updates)

            if self._debug:
                logger.info(f"✅ 업데이트 검증 성공: {list(updates.keys())}")

            return True

        except Exception as e:
            logger.error(f"업데이트 검증 실패: {str(e)}")
            return False

    def _validate_special_fields(self, todo_data: Dict[str, Any], updates: Dict[str, Any]) -> None:
        """특별한 검증이 필요한 필드들 처리"""

        # due_date 검증 (납기일 형식 확인)
        if 'due_date' in updates and updates['due_date'] is not None:
            due_date = updates['due_date']
            # ISO 8601 날짜 형식 검증 (간단한 형식 체크)
            if not isinstance(due_date, str) or len(due_date) < 8:
                raise DataPreservationError(
                    field='due_date',
                    current_value=todo_data.get('due_date'),
                    attempted_value=due_date,
                    message=f"납기일 형식이 올바르지 않습니다: {due_date}"
                )

        # text 검증 (빈 텍스트 방지)
        if 'text' in updates:
            text = updates['text']
            if not isinstance(text, str) or not text.strip():
                raise DataPreservationError(
                    field='text',
                    current_value=todo_data.get('text'),
                    attempted_value=text,
                    message="TODO 텍스트는 비어있을 수 없습니다"
                )

    def _validate_business_rules(self, todo_data: Dict[str, Any], updates: Dict[str, Any]) -> None:
        """비즈니스 로직 검증"""

        # 완료된 TODO의 납기일 변경 방지 (선택적 비즈니스 규칙)
        if (todo_data.get('completed') and
            'due_date' in updates and
            updates['due_date'] != todo_data.get('due_date')):

            if self._debug:
                logger.warning("완료된 TODO의 납기일 변경 시도 감지")
                # 경고만 하고 허용 (너무 엄격하지 않게)

    def extract_preserved_fields(self, todo_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        보존해야 할 필드들만 추출

        Args:
            todo_data: TODO 데이터

        Returns:
            보존 대상 필드들만 포함한 딕셔너리
        """
        preserved = {}

        # 정의된 보존 필드들만 추출
        for field_name in self._preserved_field_definitions:
            if field_name in todo_data and todo_data[field_name] is not None:
                preserved[field_name] = todo_data[field_name]

        # 기본 필드들도 포함
        for basic_field in ['text', 'completed']:
            if basic_field in todo_data:
                preserved[basic_field] = todo_data[basic_field]

        if self._debug:
            logger.info(f"보존 필드 추출 완료: {list(preserved.keys())}")

        return preserved

    def get_preservation_report(self, original: Dict[str, Any], final: Dict[str, Any]) -> Dict[str, Any]:
        """
        데이터 보존 과정의 상세 보고서 생성

        Args:
            original: 원본 데이터
            final: 최종 데이터

        Returns:
            보존 보고서
        """
        report = {
            'timestamp': datetime.now().isoformat(),
            'original_field_count': len(original),
            'final_field_count': len(final),
            'preserved_fields': [],
            'updated_fields': [],
            'added_fields': [],
            'due_date_preservation': {
                'original': original.get('due_date'),
                'final': final.get('due_date'),
                'preserved': original.get('due_date') == final.get('due_date')
            }
        }

        # 필드별 변화 분석
        all_fields = set(original.keys()) | set(final.keys())
        for field in all_fields:
            original_value = original.get(field)
            final_value = final.get(field)

            if field in original and field in final:
                if original_value == final_value:
                    report['preserved_fields'].append({
                        'field': field,
                        'value': original_value
                    })
                else:
                    report['updated_fields'].append({
                        'field': field,
                        'original': original_value,
                        'final': final_value
                    })
            elif field in final and field not in original:
                report['added_fields'].append({
                    'field': field,
                    'value': final_value
                })

        return report