"""
TODO 정렬 시스템 관리 모듈 (DRY+CLEAN+Simple)
"""

from typing import List, Dict, Any, Callable, Optional
from enum import Enum
from .date_utils import DateUtils


class SortDirection(Enum):
    """정렬 방향"""
    ASCENDING = "asc"
    DESCENDING = "desc"


class SortCriteria(Enum):
    """정렬 기준"""
    DUE_DATE = "due_date"
    CREATED_DATE = "created_date"
    MANUAL = "manual"  # 수동 순서 (사용자가 드래그로 변경)


class SortManager:
    """TODO 항목 정렬 관리 클래스 (DRY+CLEAN+Simple)"""

    def __init__(self):
        self.current_criteria = SortCriteria.DUE_DATE
        self.current_direction = SortDirection.ASCENDING

        # 4개 정렬 옵션만 유지 (DEFAULT 제거)
        self._sort_options = [
            {'key': 'due_date_asc', 'criteria': SortCriteria.DUE_DATE, 'direction': SortDirection.ASCENDING, 'icon': '📅↑', 'display_name': '납기일 빠른순'},
            {'key': 'due_date_desc', 'criteria': SortCriteria.DUE_DATE, 'direction': SortDirection.DESCENDING, 'icon': '📅↓', 'display_name': '납기일 늦은순'},
            {'key': 'created_asc', 'criteria': SortCriteria.CREATED_DATE, 'direction': SortDirection.ASCENDING, 'icon': '📝↑', 'display_name': '생성일 오래된순'},
            {'key': 'created_desc', 'criteria': SortCriteria.CREATED_DATE, 'direction': SortDirection.DESCENDING, 'icon': '📝↓', 'display_name': '생성일 최신순'}
        ]
        self._current_option_index = 0

    def get_sort_options(self) -> List[Dict[str, Any]]:
        """사용 가능한 정렬 옵션 목록 반환"""
        return self._sort_options.copy()

    def set_sort_option(self, option_key: str) -> bool:
        """정렬 옵션 직접 설정"""
        for i, option in enumerate(self._sort_options):
            if option['key'] == option_key:
                self.current_criteria = option['criteria']
                self.current_direction = option['direction']
                self._current_option_index = i
                return True
        return False

    def get_current_sort_info(self) -> dict:
        """현재 정렬 상태 정보 반환"""
        if self.current_criteria == SortCriteria.MANUAL:
            return {
                'criteria': self.current_criteria,
                'direction': self.current_direction,
                'description': '수동 순서',
                'icon': '🔧',
                'tooltip': '수동으로 정렬된 순서'
            }

        # 현재 옵션 찾기
        current_option = self._sort_options[self._current_option_index]
        for option in self._sort_options:
            if option['criteria'] == self.current_criteria and option['direction'] == self.current_direction:
                current_option = option
                break

        return {
            'criteria': self.current_criteria,
            'direction': self.current_direction,
            'description': current_option['display_name'],
            'icon': current_option['icon'],
            'tooltip': f"현재: {current_option['display_name']}"
        }

    def sort_todos(self, todos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """TODO 목록을 현재 정렬 기준에 따라 정렬 (통합 정렬 함수)"""
        if not todos:
            return todos

        if self.current_criteria == SortCriteria.MANUAL:
            # 수동 순서: position 기준
            return self._sort_by_key(todos, lambda x: x.get('position', 0))
        elif self.current_criteria == SortCriteria.DUE_DATE:
            return self._sort_by_key(todos, self._get_due_date_key, self.current_direction == SortDirection.DESCENDING)
        elif self.current_criteria == SortCriteria.CREATED_DATE:
            return self._sort_by_key(todos, self._get_created_date_key, self.current_direction == SortDirection.DESCENDING)
        else:
            # 폴백: position 기준
            return self._sort_by_key(todos, lambda x: x.get('position', 0))

    def _sort_by_key(self, todos: List[Dict[str, Any]], key_func: Callable, reverse: bool = False) -> List[Dict[str, Any]]:
        """통합 정렬 함수 - DRY 원칙 적용"""
        return sorted(todos, key=key_func, reverse=reverse)

    def _get_due_date_key(self, todo: Dict[str, Any]) -> tuple:
        """납기일 정렬 키 생성"""
        due_date = todo.get('due_date')
        if not due_date:
            # 납기일이 없는 항목은 맨 뒤로
            return ('9999-12-31', todo.get('position', 0))

        parsed_date = DateUtils.parse_date(due_date)
        if not parsed_date:
            return ('9999-12-31', todo.get('position', 0))

        return (due_date, todo.get('position', 0))

    def _get_created_date_key(self, todo: Dict[str, Any]) -> tuple:
        """생성일 정렬 키 생성"""
        created_at = todo.get('created_at')
        if not created_at:
            # 생성일이 없는 항목은 기본값 사용
            return (DateUtils.DEFAULT_CREATED_DATE, todo.get('position', 0))

        # ISO datetime에서 날짜 부분만 추출
        if 'T' in created_at:
            date_part = created_at.split('T')[0]
        else:
            date_part = created_at[:10]

        return (date_part, todo.get('position', 0))

    def set_manual_mode(self):
        """수동 정렬 모드로 전환 (사용자가 순서를 변경했을 때)"""
        self.current_criteria = SortCriteria.MANUAL
        self.current_direction = SortDirection.ASCENDING

    def set_sort_criteria(self, criteria: SortCriteria, direction: SortDirection = SortDirection.ASCENDING):
        """정렬 기준 직접 설정"""
        self.current_criteria = criteria
        self.current_direction = direction

        # 옵션 인덱스 업데이트
        for i, option in enumerate(self._sort_options):
            if option['criteria'] == criteria and option['direction'] == direction:
                self._current_option_index = i
                break


    def separate_by_completion(self, todos: List[Dict[str, Any]]) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """TODO를 완료/미완료로 분리하고 각각 정렬"""
        pending_todos = [todo for todo in todos if not todo.get('completed', False)]
        completed_todos = [todo for todo in todos if todo.get('completed', False)]

        # 각각 현재 정렬 기준으로 정렬
        sorted_pending = self.sort_todos(pending_todos)
        sorted_completed = self.sort_todos(completed_todos)

        return sorted_pending, sorted_completed

    def is_manual_mode(self) -> bool:
        """현재 수동 정렬 모드인지 확인"""
        return self.current_criteria == SortCriteria.MANUAL