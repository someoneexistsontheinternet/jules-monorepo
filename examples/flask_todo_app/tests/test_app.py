import pytest
import json
from examples.flask_todo_app.app import app as flask_app # Import the Flask app instance

@pytest.fixture
def app():
    yield flask_app

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

# Utility to clear todos for isolated tests
def clear_todos_for_testing():
    from examples.flask_todo_app.app import todos, next_id
    todos.clear()
    globals()['next_id'] = 1 # Reset next_id, careful with direct global modification in real apps

def test_get_todos_initially_empty(client):
    """Test GET /todos returns an empty list initially."""
    clear_todos_for_testing()
    response = client.get('/todos')
    assert response.status_code == 200
    assert response.json == []

def test_post_todo_missing_task(client):
    """Test POST /todos with missing 'task' in payload."""
    clear_todos_for_testing()
    response = client.post('/todos', json={})
    assert response.status_code == 400
    assert 'error' in response.json
    assert response.json['error'] == 'Missing task'

# This test is expected to fail due to partial POST implementation
def test_post_add_todo_partially_implemented(client):
    """
    Test basic successful addition. 
    This test is expected to fail or behave unexpectedly due to 
    the partial implementation of POST /todos (e.g., fixed response, no actual addition).
    """
    clear_todos_for_testing()
    response = client.post('/todos', json={'task': 'Test task 1'})
    assert response.status_code == 201 
    # The following assertions will likely fail with the current partial implementation
    assert response.json['id'] == 1 
    assert response.json['task'] == 'Test task 1'
    assert response.json['completed'] == False

    # Verify it's "added" (or not, depending on how partial the POST is)
    # get_response = client.get('/todos')
    # assert len(get_response.json) == 1 # This will fail if POST doesn't add to 'todos' list

def test_get_added_todos(client):
    """Test GET /todos returns added todos correctly (assuming POST works)."""
    clear_todos_for_testing()
    # Manually add items for now, as POST is partially implemented
    from examples.flask_todo_app.app import todos, next_id
    todos.append({"id": next_id, "task": "Manual Task 1", "completed": False})
    globals()['next_id'] +=1
    todos.append({"id": next_id, "task": "Manual Task 2", "completed": True})
    globals()['next_id'] +=1
    
    response = client.get('/todos')
    assert response.status_code == 200
    assert len(response.json) == 2
    assert response.json[0]['task'] == 'Manual Task 1'
    assert response.json[1]['task'] == 'Manual Task 2'

def test_get_specific_todo(client):
    """Test GET /todos/<id> for an existing todo."""
    clear_todos_for_testing()
    from examples.flask_todo_app.app import todos, next_id
    todos.append({"id": next_id, "task": "Specific Task", "completed": False})
    task_id = next_id
    globals()['next_id'] +=1

    response = client.get(f'/todos/{task_id}')
    assert response.status_code == 200
    assert response.json['id'] == task_id
    assert response.json['task'] == 'Specific Task'

def test_get_specific_todo_not_found(client):
    """Test GET /todos/<id> for a non-existent todo."""
    clear_todos_for_testing()
    response = client.get('/todos/999')
    assert response.status_code == 404
    assert 'error' in response.json
    assert response.json['error'] == 'Todo not found'

# This test is expected to fail or partially pass due to partial PUT implementation
def test_put_update_todo_task_partially_implemented(client):
    """
    Test updating an existing todo's task.
    This test is expected to fail or partially pass as PUT /todos/<id> is partially implemented.
    """
    clear_todos_for_testing()
    from examples.flask_todo_app.app import todos, next_id
    todos.append({"id": next_id, "task": "Original Task", "completed": False})
    task_id = next_id
    globals()['next_id'] +=1

    response = client.put(f'/todos/{task_id}', json={'task': 'Updated Task'})
    assert response.status_code == 200
    # The following assertions might fail if 'task' is not updated or if other fields are missing
    assert response.json['task'] == 'Updated Task' 
    # assert response.json['id'] == task_id # Check if ID is preserved
    # assert response.json['completed'] == False # Check if 'completed' status is preserved

# This test is expected to fail due to partial PUT implementation (completed status)
def test_put_update_todo_completion_partially_implemented(client):
    """
    Test updating an existing todo's completion status.
    This test is expected to fail as the 'completed' field update is not implemented in PUT.
    """
    clear_todos_for_testing()
    from examples.flask_todo_app.app import todos, next_id
    todos.append({"id": next_id, "task": "Task for completion", "completed": False})
    task_id = next_id
    globals()['next_id'] +=1

    response = client.put(f'/todos/{task_id}', json={'completed': True})
    assert response.status_code == 200
    # This assertion will fail as 'completed' update is not implemented
    assert response.json['completed'] == True 
    # assert response.json['task'] == "Task for completion" # Check if task is preserved

def test_put_update_non_existent_todo(client):
    """Test PUT /todos/<id> for a non-existent todo."""
    clear_todos_for_testing()
    response = client.put('/todos/999', json={'task': 'Try to update non-existent'})
    assert response.status_code == 404
    assert 'error' in response.json
    assert response.json['error'] == 'Todo not found'

def test_delete_todo(client):
    """Test DELETE /todos/<id> for an existing todo."""
    clear_todos_for_testing()
    from examples.flask_todo_app.app import todos, next_id
    todos.append({"id": next_id, "task": "Task to delete", "completed": False})
    task_id_to_delete = next_id
    globals()['next_id'] +=1
    
    # Add another task to ensure only the specified one is deleted
    todos.append({"id": next_id, "task": "Another task", "completed": False})
    globals()['next_id'] +=1

    response = client.delete(f'/todos/{task_id_to_delete}')
    assert response.status_code == 204

    # Verify it's actually deleted
    # get_response = client.get(f'/todos/{task_id_to_delete}')
    # assert get_response.status_code == 404 # This should be 404 after deletion

    # Verify other tasks remain
    # list_response = client.get('/todos')
    # assert len(list_response.json) == 1
    # assert list_response.json[0]['task'] == "Another task"


def test_delete_non_existent_todo(client):
    """Test DELETE /todos/<id> for a non-existent todo."""
    clear_todos_for_testing()
    response = client.delete('/todos/999')
    assert response.status_code == 404
    assert 'error' in response.json
    assert response.json['error'] == 'Todo not found'
