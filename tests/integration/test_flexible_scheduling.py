"""Flexible task scheduling integration tests."""
import pytest
from fastapi.testclient import TestClient
from uuid import UUID
from app.main import app


@pytest.fixture
def client():
    """FastAPI test client"""
    return TestClient(app)


def test_create_schedule_without_name(client: TestClient):
    """Test creating schedule without name (auto-generation)."""
    response = client.post(
        "/api/v1/schedules",
        json={
            "task_name": "fetch_listed_info_task_asyncpg",
            "cron_expression": "0 9 * * *",
            "enabled": True,
            "task_params": {"period_type": "yesterday"},
            "description": "昨日の上場情報を取得",
            "category": "data_fetch",
            "tags": ["jquants", "daily"],
            "execution_policy": "skip"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["auto_generated_name"] is True
    assert "fetch_listed_info_task_asyncpg" in data["name"]
    assert data["category"] == "data_fetch"
    assert data["tags"] == ["jquants", "daily"]
    assert data["execution_policy"] == "skip"


def test_create_multiple_schedules_same_task(client: TestClient):
    """Test creating multiple schedules for the same task."""
    # Create first schedule
    response1 = client.post(
        "/api/v1/schedules",
        json={
            "name": "fetch_listed_info_yesterday",
            "task_name": "fetch_listed_info_task_asyncpg",
            "cron_expression": "0 9 * * *",
            "enabled": True,
            "task_params": {"period_type": "yesterday"},
            "category": "data_fetch",
            "tags": ["jquants", "daily"]
        }
    )
    assert response1.status_code == 201
    
    # Create second schedule with same task but different params
    response2 = client.post(
        "/api/v1/schedules",
        json={
            "name": "fetch_listed_info_7days",
            "task_name": "fetch_listed_info_task_asyncpg",
            "cron_expression": "0 10 * * 1",
            "enabled": True,
            "task_params": {"period_type": "7days"},
            "category": "data_fetch",
            "tags": ["jquants", "weekly"]
        }
    )
    assert response2.status_code == 201
    
    # Verify both schedules exist
    response_list = client.get("/api/v1/schedules")
    assert response_list.status_code == 200
    schedules = response_list.json()["items"]
    task_names = [s["task_name"] for s in schedules]
    assert task_names.count("fetch_listed_info_task_asyncpg") >= 2


def test_filter_schedules_by_category(client: TestClient):
    """Test filtering schedules by category."""
    # Create schedules with different categories
    client.post(
        "/api/v1/schedules",
        json={
            "name": "analysis_task_1",
            "task_name": "run_analysis",
            "cron_expression": "0 12 * * *",
            "category": "analysis"
        }
    )
    
    client.post(
        "/api/v1/schedules",
        json={
            "name": "maintenance_task_1",
            "task_name": "cleanup_old_data",
            "cron_expression": "0 3 * * *",
            "category": "maintenance"
        }
    )
    
    # Filter by category
    response = client.get("/api/v1/schedules?category=analysis")
    assert response.status_code == 200
    schedules = response.json()["items"]
    assert all(s["category"] == "analysis" for s in schedules)


def test_filter_schedules_by_tags(client: TestClient):
    """Test filtering schedules by tags."""
    # Create schedule with tags
    client.post(
        "/api/v1/schedules",
        json={
            "name": "critical_task",
            "task_name": "critical_process",
            "cron_expression": "*/5 * * * *",
            "tags": ["critical", "monitoring"]
        }
    )
    
    # Filter by tag
    response = client.get("/api/v1/schedules?tags=critical")
    assert response.status_code == 200
    schedules = response.json()["items"]
    assert all("critical" in s["tags"] for s in schedules)


def test_execution_policy_validation(client: TestClient):
    """Test execution policy validation."""
    # Valid execution policy
    response = client.post(
        "/api/v1/schedules",
        json={
            "name": "test_policy_valid",
            "task_name": "test_task",
            "cron_expression": "0 0 * * *",
            "execution_policy": "queue"
        }
    )
    assert response.status_code == 201
    
    # Invalid execution policy
    response = client.post(
        "/api/v1/schedules",
        json={
            "name": "test_policy_invalid",
            "task_name": "test_task",
            "cron_expression": "0 0 * * *",
            "execution_policy": "invalid_policy"
        }
    )
    assert response.status_code == 422