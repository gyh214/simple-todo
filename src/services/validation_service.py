"""
ValidationService - CLEAN 아키텍처 검증 전담 서비스

📐 Interface Segregation Principle 적용:
=========================================
검증 책임만을 분리하여 단일 책임 원칙(SRP)을 준수합니다.
다른 서비스들은 복잡한 검증 로직을 알 필요가 없습니다.

🔒 검증 종류:
=============
- 필수 필드 검증 (텍스트 존재, 길이 제한)
- 형식 검증 (날짜 형식, URL 형식)
- 비즈니스 룰 검증 (중복 방지, 일관성 검사)
- 크로스 필드 검증 (필드간 의존성 검사)

⚡ 성능 최적화:
===============
- 빠른 실패 (Fast Fail) 패턴 적용
- 정규표현식 캐싱으로 성능 향상
- 검증 결과 캐싱으로 중복 검증 방지
"""

import re
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from interfaces import IValidationService

logger = logging.getLogger(__name__)


class ValidationService(IValidationService):
    """
    검증 전담 서비스 구현체

    🎯 단일 책임:
    ============
    오직 데이터 검증만을 담당합니다.
    UI나 비즈니스 로직에는 전혀 의존하지 않습니다.
    """

    # 성능 최적화를 위한 정규표현식 캐싱
    _URL_PATTERN = re.compile(r'https?://[^\s]+|www\.[^\s]+')
    _EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    _DATE_PATTERNS = [
        re.compile(r'^\d{4}-\d{2}-\d{2}$'),  # YYYY-MM-DD
        re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}'),  # ISO datetime
        re.compile(r'^\d{2}/\d{2}/\d{4}$')  # MM/DD/YYYY
    ]

    def __init__(self):
        """검증 서비스 초기화"""
        self._validation_cache = {}
        logger.info("ValidationService 초기화 완료")

    def validate_todo_text(self, text: str) -> bool:
        """
        TODO 텍스트 유효성 검증

        🔍 검증 항목:
        ============
        - 존재성 검증 (None, 빈 문자열 불허)
        - 길이 제한 (1~500자)
        - 금지된 문자 검사 (특수 제어 문자)
        - 공백 전용 문자열 불허

        Args:
            text: 검증할 텍스트

        Returns:
            유효성 검증 결과
        """
        if not text:
            logger.debug("TODO 텍스트 검증 실패: 빈 텍스트")
            return False

        # 문자열 변환 및 공백 제거 후 검사
        text_str = str(text).strip()

        # 1. 길이 검증
        if len(text_str) == 0:
            logger.debug("TODO 텍스트 검증 실패: 공백 전용 텍스트")
            return False

        if len(text_str) > 500:
            logger.debug(f"TODO 텍스트 검증 실패: 길이 초과 ({len(text_str)}자)")
            return False

        # 2. 금지된 문자 검사 (제어 문자 제외)
        forbidden_chars = ['\x00', '\x01', '\x02', '\x03', '\x04', '\x05']
        if any(char in text_str for char in forbidden_chars):
            logger.debug("TODO 텍스트 검증 실패: 금지된 제어 문자 포함")
            return False

        # 3. SQL Injection 기본 방어 (간단한 패턴)
        dangerous_patterns = ['--', ';DELETE', ';DROP', 'UNION SELECT', '<script>']
        text_upper = text_str.upper()
        for pattern in dangerous_patterns:
            if pattern in text_upper:
                logger.warning(f"TODO 텍스트 검증 실패: 위험한 패턴 감지 - {pattern}")
                return False

        logger.debug("TODO 텍스트 검증 성공")
        return True

    def validate_due_date(self, date_str: str) -> bool:
        """
        납기일 형식 유효성 검증

        🗓️ 지원 형식:
        =============
        - YYYY-MM-DD (ISO 날짜)
        - YYYY-MM-DDTHH:MM:SS (ISO datetime)
        - MM/DD/YYYY (미국식)

        🔍 추가 검증:
        ============
        - 실제 존재하는 날짜인지 검증
        - 과거 날짜 허용 여부 (설정 가능)
        - 너무 먼 미래 날짜 제한

        Args:
            date_str: 날짜 문자열

        Returns:
            날짜 형식 유효성
        """
        if not date_str:
            return True  # 납기일은 선택사항

        # 캐시 확인 (성능 최적화)
        cache_key = f"date:{date_str}"
        if cache_key in self._validation_cache:
            return self._validation_cache[cache_key]

        date_str = str(date_str).strip()

        # 1. 형식 검증
        format_valid = False
        for pattern in self._DATE_PATTERNS:
            if pattern.match(date_str):
                format_valid = True
                break

        if not format_valid:
            logger.debug(f"납기일 검증 실패: 지원하지 않는 형식 - {date_str}")
            self._validation_cache[cache_key] = False
            return False

        # 2. 실제 날짜 유효성 검증
        try:
            # 다양한 형식 파싱 시도
            date_obj = None

            # ISO 형식 시도
            if 'T' in date_str:
                date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            elif '/' in date_str:
                date_obj = datetime.strptime(date_str, '%m/%d/%Y')
            else:
                date_obj = datetime.fromisoformat(date_str)

            if date_obj is None:
                raise ValueError("파싱 실패")

            # 3. 비즈니스 룰 검증
            # 너무 먼 미래 제한 (100년 후)
            max_future = datetime.now().replace(year=datetime.now().year + 100)
            if date_obj > max_future:
                logger.debug(f"납기일 검증 실패: 너무 먼 미래 - {date_str}")
                self._validation_cache[cache_key] = False
                return False

            # 성공
            logger.debug(f"납기일 검증 성공: {date_str}")
            self._validation_cache[cache_key] = True
            return True

        except Exception as e:
            logger.debug(f"납기일 검증 실패: 파싱 오류 - {date_str}, {str(e)}")
            self._validation_cache[cache_key] = False
            return False

    def validate_todo_data(self, todo_data: Dict[str, Any]) -> List[str]:
        """
        TODO 데이터 전체 검증

        🔍 종합 검증:
        ============
        - 모든 필드의 개별 검증
        - 필드간 상호 의존성 검사
        - 비즈니스 룰 검증
        - 데이터 일관성 검사

        Args:
            todo_data: 검증할 TODO 데이터

        Returns:
            오류 메시지 목록 (빈 목록이면 검증 성공)
        """
        errors = []

        if not isinstance(todo_data, dict):
            errors.append("TODO 데이터는 딕셔너리 형태여야 합니다.")
            return errors

        # 1. 필수 필드 검증
        text = todo_data.get('text', '')
        if not self.validate_todo_text(text):
            errors.append("유효하지 않은 TODO 텍스트입니다.")

        # 2. 선택 필드 검증
        due_date = todo_data.get('due_date')
        if due_date is not None and not self.validate_due_date(due_date):
            errors.append("유효하지 않은 납기일 형식입니다.")

        # 3. 완료 상태 검증
        completed = todo_data.get('completed')
        if completed is not None and not isinstance(completed, bool):
            errors.append("완료 상태는 true/false 값이어야 합니다.")

        # 4. 위치 정보 검증
        position = todo_data.get('position')
        if position is not None:
            if not isinstance(position, int) or position < 0:
                errors.append("위치 정보는 0 이상의 정수여야 합니다.")

        # 5. ID 검증 (업데이트 시)
        todo_id = todo_data.get('id')
        if todo_id is not None:
            if not isinstance(todo_id, str) or len(todo_id.strip()) == 0:
                errors.append("ID는 비어있지 않은 문자열이어야 합니다.")

        # 6. 생성/수정 시간 검증
        for time_field in ['created_at', 'updated_at']:
            time_value = todo_data.get(time_field)
            if time_value is not None:
                if not self._validate_timestamp(time_value):
                    errors.append(f"{time_field}는 유효한 시간 형식이어야 합니다.")

        # 7. 우선순위 검증 (확장 기능)
        priority = todo_data.get('priority')
        if priority is not None:
            valid_priorities = ['low', 'medium', 'high']
            if priority not in valid_priorities:
                errors.append(f"우선순위는 {', '.join(valid_priorities)} 중 하나여야 합니다.")

        # 8. 카테고리 검증 (확장 기능)
        category = todo_data.get('category')
        if category is not None:
            if not isinstance(category, str) or len(category.strip()) > 50:
                errors.append("카테고리는 50자 이하의 문자열이어야 합니다.")

        # 9. 태그 검증 (확장 기능)
        tags = todo_data.get('tags')
        if tags is not None:
            if not isinstance(tags, list):
                errors.append("태그는 리스트 형태여야 합니다.")
            elif len(tags) > 10:
                errors.append("태그는 최대 10개까지 허용됩니다.")
            else:
                for tag in tags:
                    if not isinstance(tag, str) or len(tag.strip()) > 20:
                        errors.append("각 태그는 20자 이하의 문자열이어야 합니다.")
                        break

        # 10. 크로스 필드 검증
        # 완료된 TODO의 납기일 일관성 검사
        if completed is True and due_date:
            try:
                due_date_obj = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
                created_at = todo_data.get('created_at')
                if created_at:
                    created_at_obj = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    if due_date_obj < created_at_obj:
                        errors.append("납기일이 생성일보다 이전일 수 없습니다.")
            except:
                pass  # 이미 개별 필드 검증에서 처리됨

        if errors:
            logger.debug(f"TODO 데이터 검증 실패: {len(errors)}개 오류")
        else:
            logger.debug("TODO 데이터 검증 성공")

        return errors

    def validate_batch_operation(self, todos: List[Dict[str, Any]]) -> List[str]:
        """
        일괄 작업 데이터 검증

        📦 배치 검증:
        ============
        - 개별 TODO 검증
        - 중복 ID 검사
        - 위치 충돌 검사
        - 배치 크기 제한

        Args:
            todos: TODO 목록

        Returns:
            오류 메시지 목록
        """
        errors = []

        if not isinstance(todos, list):
            errors.append("TODO 목록은 리스트 형태여야 합니다.")
            return errors

        # 1. 배치 크기 제한
        if len(todos) > 1000:
            errors.append("한 번에 처리할 수 있는 TODO는 최대 1000개입니다.")
            return errors

        # 2. 개별 TODO 검증
        seen_ids = set()
        seen_positions = set()

        for i, todo in enumerate(todos):
            # 개별 검증
            todo_errors = self.validate_todo_data(todo)
            for error in todo_errors:
                errors.append(f"TODO {i+1}: {error}")

            # ID 중복 검사
            todo_id = todo.get('id')
            if todo_id:
                if todo_id in seen_ids:
                    errors.append(f"중복된 ID 발견: {todo_id}")
                else:
                    seen_ids.add(todo_id)

            # 위치 중복 검사
            position = todo.get('position')
            if position is not None:
                if position in seen_positions:
                    errors.append(f"중복된 위치 발견: {position}")
                else:
                    seen_positions.add(position)

        return errors

    def _validate_timestamp(self, timestamp: Any) -> bool:
        """
        타임스탬프 유효성 검증

        Args:
            timestamp: 검증할 타임스탬프

        Returns:
            유효성 여부
        """
        if timestamp is None:
            return True

        try:
            if isinstance(timestamp, str):
                datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                return True
            elif isinstance(timestamp, (int, float)):
                datetime.fromtimestamp(timestamp)
                return True
            else:
                return False
        except:
            return False

    def clear_cache(self):
        """검증 캐시 초기화 (메모리 관리)"""
        self._validation_cache.clear()
        logger.debug("검증 캐시 초기화 완료")