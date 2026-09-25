from fastapi.testclient import TestClient
from unittest.mock import patch
from src.api.routes import app

client = TestClient(app)

def test_read_docs():
    """Verify that the API documentation loads properly."""
    response = client.get("/docs")
    assert response.status_code == 200

def test_trigger_research_task_invalid_payload():
    """Verify validation handling when an empty or bad payload is sent."""
    response = client.post("/research", json={})
    assert response.status_code == 422

@patch("src.api.routes.run_research_task.delay")
def test_trigger_research_task_success(mock_celery_delay):
    """Verify that a valid research question successfully enqueues and returns a task ID."""
    # Mock the Celery task return object to have a fake task ID
    mock_task_instance = mock_celery_delay.return_value
    mock_task_instance.id = "mock-task-id-123"

    payload = {
        "question": "How do transformer attention mechanisms work?"
    }
    
    response = client.post("/research", json=payload)
    
    assert response.status_code in [200, 202]
    data = response.json()
    
    # Assert that Celery was called with the correct argument
    mock_celery_delay.assert_called_once_with(payload["question"])