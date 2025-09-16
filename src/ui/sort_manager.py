"""
범용 정렬 시스템 관리 모듈
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
    DEFAULT = "default"
    DUE_DATE = "due_date"
    CREATED_DATE = "created_date"
    ALPHABETICAL = "alphabetical"
    COMPLETION_STATUS = "completion"


class SortManager:
    """TODO 항목 정렬 관리 클래스"""

    def __init__(self):
        self.current_criteria = SortCriteria.DEFAULT
        self.current_direction = SortDirection.ASCENDING
        self._sort_cycle = [
            (SortCriteria.DUE_DATE, SortDirection.ASCENDING),
            (SortCriteria.DUE_DATE, SortDirection.DESCENDING),
            (SortCriteria.CREATED_DATE, SortDirection.ASCENDING),
            (SortCriteria.CREATED_DATE, SortDirection.DESCENDING),
            (SortCriteria.DEFAULT, SortDirection.ASCENDING)
        ]
        self._current_cycle_index = 0

    def get_next_sort_state(self) -> tuple[SortCriteria, SortDirection]:
        """다음 정렬 상태 반환 (토글용)"""
        self._current_cycle_index = (self._current_cycle_index + 1) % len(self._sort_cycle)
        criteria, direction = self._sort_cycle[self._current_cycle_index]
        self.current_criteria = criteria
        self.current_direction = direction
        return criteria, direction

    def get_current_sort_info(self) -> dict:
        """현재 정렬 상태 정보 반환"""
        if self.current_criteria == SortCriteria.DEFAULT:
            description = "기본 순서"
            icon = "🔄"
        elif self.current_criteria == SortCriteria.DUE_DATE:
            direction_text = "↑" if self.current_direction == SortDirection.ASCENDING else "↓"
            description = f"납기일 {direction_text}"
            icon = "📅"
        elif self.current_criteria == SortCriteria.CREATED_DATE:
            direction_text = "↑" if self.current_direction == SortDirection.ASCENDING else "↓"
            description = f"생성일 {direction_text}"
            icon = "📝"
        else:
            description = "정렬"
            icon = "🔄"

        return {
            'criteria': self.current_criteria,
            'direction': self.current_direction,
            'description': description,
            'icon': icon,
            'tooltip': f"현재: {description} (클릭하여 변경)"
        }

    def sort_todos(self, todos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """TODO 목록을 현재 정렬 기준에 따라 정렬"""
        if not todos:
            return todos

        if self.current_criteria == SortCriteria.DEFAULT:
            # 기본 정렬: position 기준
            return sorted(todos, key=lambda x: x.get('position', 0))

        elif self.current_criteria == SortCriteria.DUE_DATE:
            return self._sort_by_due_date(todos)

        elif self.current_criteria == SortCriteria.CREATED_DATE:
            return self._sort_by_created_date(todos)

        elif self.current_criteria == SortCriteria.ALPHABETICAL:
            return self._sort_by_alphabetical(todos)

        elif self.current_criteria == SortCriteria.COMPLETION_STATUS:
            return self._sort_by_completion_status(todos)

        else:
            # 기본값으로 폴백
            return sorted(todos, key=lambda x: x.get('position', 0))

    def _sort_by_due_date(self, todos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """납기일 기준 정렬"""
        def get_sort_key(todo):
            due_date = todo.get('due_date')
            if not due_date:
                # 납기일이 없는 항목은 맨 뒤로
                return ('9999-12-31', todo.get('position', 0))

            parsed_date = DateUtils.parse_date(due_date)
            if not parsed_date:
                return ('9999-12-31', todo.get('position', 0))

            return (due_date, todo.get('position', 0))

        reverse_order = (self.current_direction == SortDirection.DESCENDING)
        return sorted(todos, key=get_sort_key, reverse=reverse_order)

    def _sort_by_created_date(self, todos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """생성일 기준 정렬"""
        def get_sort_key(todo):
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

        reverse_order = (self.current_direction == SortDirection.DESCENDING)
        return sorted(todos, key=get_sort_key, reverse=reverse_order)

    def _sort_by_alphabetical(self, todos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """알파벳(가나다) 순 정렬"""
        def get_sort_key(todo):
            text = todo.get('text', '').lower().strip()
            return (text, todo.get('position', 0))

        reverse_order = (self.current_direction == SortDirection.DESCENDING)
        return sorted(todos, key=get_sort_key, reverse=reverse_order)

    def _sort_by_completion_status(self, todos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """완료 상태 기준 정렬"""
        def get_sort_key(todo):
            completed = todo.get('completed', False)
            # False(미완료)가 먼저 오도록
            return (completed, todo.get('position', 0))

        reverse_order = (self.current_direction == SortDirection.DESCENDING)
        return sorted(todos, key=get_sort_key, reverse=reverse_order)

    def reset_to_default(self):
        """정렬을 기본 상태로 리셋"""
        self.current_criteria = SortCriteria.DEFAULT
        self.current_direction = SortDirection.ASCENDING
        self._current_cycle_index = len(self._sort_cycle) - 1  # DEFAULT 위치

    def set_sort_criteria(self, criteria: SortCriteria, direction: SortDirection = SortDirection.ASCENDING):
        """정렬 기준 직접 설정"""
        self.current_criteria = criteria
        self.current_direction = direction

        # 사이클 인덱스도 맞춰서 설정
        try:
            self._current_cycle_index = self._sort_cycle.index((criteria, direction))
        except ValueError:
            # 사이클에 없는 조합이면 기본값으로
            self.reset_to_default()

    def get_sort_options(self) -> List[Dict[str, Any]]:
        """사용 가능한 정렬 옵션 목록 반환"""
        return [
            {
                'criteria': SortCriteria.DEFAULT,
                'direction': SortDirection.ASCENDING,
                'display_name': '기본 순서',
                'icon': '🔄'
            },
            {
                'criteria': SortCriteria.DUE_DATE,
                'direction': SortDirection.ASCENDING,
                'display_name': '납기일 빠른순',
                'icon': '📅↑'
            },
            {
                'criteria': SortCriteria.DUE_DATE,
                'direction': SortDirection.DESCENDING,
                'display_name': '납기일 늦은순',
                'icon': '📅↓'
            },
            {
                'criteria': SortCriteria.CREATED_DATE,
                'direction': SortDirection.ASCENDING,
                'display_name': '생성일 오래된순',
                'icon': '📝↑'
            },
            {
                'criteria': SortCriteria.CREATED_DATE,
                'direction': SortDirection.DESCENDING,
                'display_name': '생성일 최신순',
                'icon': '📝↓'
            },
            {
                'criteria': SortCriteria.ALPHABETICAL,
                'direction': SortDirection.ASCENDING,
                'display_name': '가나다순',
                'icon': '🔤↑'
            },
            {
                'criteria': SortCriteria.ALPHABETICAL,
                'direction': SortDirection.DESCENDING,
                'display_name': '가나다 역순',
                'icon': '🔤↓'
            }
        ]

    def separate_by_completion(self, todos: List[Dict[str, Any]]) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """TODO를 완료/미완료로 분리하고 각각 정렬"""
        pending_todos = [todo for todo in todos if not todo.get('completed', False)]
        completed_todos = [todo for todo in todos if todo.get('completed', False)]

        # 각각 현재 정렬 기준으로 정렬
        sorted_pending = self.sort_todos(pending_todos)
        sorted_completed = self.sort_todos(completed_todos)

        return sorted_pending, sorted_completed

    def get_priority_sorted_todos(self, todos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """우선순위를 고려한 정렬 (만료된 항목이 맨 위로)"""
        if self.current_criteria == SortCriteria.DEFAULT:
            # 기본 정렬에서만 우선순위 적용
            expired_todos = []
            normal_todos = []

            for todo in todos:
                if DateUtils.is_date_expired(todo.get('due_date')):
                    expired_todos.append(todo)
                else:
                    normal_todos.append(todo)

            # 만료된 항목을 먼저, 그 다음 일반 항목
            sorted_expired = sorted(expired_todos, key=lambda x: x.get('position', 0))
            sorted_normal = sorted(normal_todos, key=lambda x: x.get('position', 0))

            return sorted_expired + sorted_normal
        else:
            # 다른 정렬에서는 일반 정렬 적용
            return self.sort_todos(todos)