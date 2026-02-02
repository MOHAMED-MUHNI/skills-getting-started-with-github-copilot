"""Pytest configuration and fixtures for FastAPI tests."""

import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def client():
    """Fixture providing a FastAPI TestClient."""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """Fixture to reset the activities database before each test."""
    from src.app import activities
    
    # Store original state
    original_activities = {
        name: {
            "description": data["description"],
            "schedule": data["schedule"],
            "max_participants": data["max_participants"],
            "participants": data["participants"].copy()
        }
        for name, data in activities.items()
    }
    
    yield
    
    # Reset to original state after test
    activities.clear()
    for name, data in original_activities.items():
        activities[name] = data
