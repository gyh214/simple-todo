import pytest
from unittest.mock import Mock, MagicMock
from src.application.services.todo_service import TodoService, _UNDEFINED
from src.domain.entities.todo import Todo
from src.domain.entities.subtask import SubTask
from src.domain.value_objects.todo_id import TodoId
from src.domain.value_objects.content import Content
from src.domain.value_objects.due_date import DueDate

@pytest.fixture
def mock_repository():
    return Mock()

@pytest.fixture
def todo_service(mock_repository):
    return TodoService(mock_repository)

@pytest.fixture
def sample_todo():
    todo = Mock(spec=Todo)
    todo.id = TodoId.generate()
    return todo

@pytest.fixture
def sample_subtask():
    subtask = Mock(spec=SubTask)
    subtask.id = TodoId.generate()
    return subtask

def test_update_subtask_removes_due_date_when_none_passed(todo_service, mock_repository, sample_todo, sample_subtask):
    """due_date=None을 전달하면 납기일이 제거되어야 한다."""
    # Given
    parent_id = sample_todo.id
    subtask_id = sample_subtask.id
    
    mock_repository.find_by_id.return_value = sample_todo
    sample_todo.get_subtask.return_value = sample_subtask
    
    # When
    todo_service.update_subtask(
        parent_todo_id=parent_id,
        subtask_id=subtask_id,
        due_date=None # 명시적 제거 요청
    )
    
    # Then
    sample_subtask.set_due_date.assert_called_once_with(None)
    mock_repository.save.assert_called_once_with(sample_todo)

def test_update_subtask_keeps_due_date_when_sentinel_passed(todo_service, mock_repository, sample_todo, sample_subtask):
    """due_date가 _UNDEFINED(생략)이면 납기일이 변경되지 않아야 한다."""
    # Given
    parent_id = sample_todo.id
    subtask_id = sample_subtask.id
    
    mock_repository.find_by_id.return_value = sample_todo
    sample_todo.get_subtask.return_value = sample_subtask
    
    # When
    todo_service.update_subtask(
        parent_todo_id=parent_id,
        subtask_id=subtask_id,
        content_str="New Content"
        # due_date 생략 -> _UNDEFINED
    )
    
    # Then
    sample_subtask.set_due_date.assert_not_called() # 호출되지 않아야 함
    sample_subtask.update_content.assert_called_once()
    mock_repository.save.assert_called_once_with(sample_todo)

def test_update_subtask_updates_due_date_when_value_passed(todo_service, mock_repository, sample_todo, sample_subtask):
    """due_date에 값이 전달되면 납기일이 업데이트되어야 한다."""
    # Given
    parent_id = sample_todo.id
    subtask_id = sample_subtask.id
    new_due_date = DueDate.from_string("2025-12-31")
    
    mock_repository.find_by_id.return_value = sample_todo
    sample_todo.get_subtask.return_value = sample_subtask
    
    # When
    todo_service.update_subtask(
        parent_todo_id=parent_id,
        subtask_id=subtask_id,
        due_date=new_due_date
    )
    
    # Then
    sample_subtask.set_due_date.assert_called_once_with(new_due_date)
    mock_repository.save.assert_called_once_with(sample_todo)
