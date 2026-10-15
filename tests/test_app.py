"""
Unit and integration tests for the Mergington High School Activities API.
Uses the AAA (Arrange-Act-Assert) pattern.
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Fixture providing a test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activity participants between tests to avoid side-effects."""
    original_participants = {
        name: list(details["participants"])
        for name, details in activities.items()
    }
    yield
    for name, participants in original_participants.items():
        activities[name]["participants"] = list(participants)


def test_root_redirect(client):
    """Test that root endpoint redirects to static index.html."""
    # Arrange: client is ready

    # Act: request the root path without following redirects
    response = client.get("/", follow_redirects=False)

    # Assert: response should be a redirect to static index
    assert response.status_code in (302, 307)
    assert response.headers["location"] == "/static/index.html"


def test_get_activities(client):
    """Test retrieving all activities."""
    # Arrange: activities in database

    # Act: call the GET /activities endpoint
    response = client.get("/activities")

    # Assert: response contains expected status and activities
    assert response.status_code == 200
    data = response.json()
    assert "Chess Club" in data
    assert "Programming Class" in data
    assert "Gym Class" in data


def test_signup_for_activity_success(client):
    """Test signing up for an activity successfully (AAA pattern)."""
    # Arrange: prepare activity name and new student email
    activity_name = "Basketball Team"
    email = "new_student@mergington.edu"

    # Act: sign up the student
    response = client.post(f"/activities/{activity_name}/signup?email={email}")

    # Assert: signup succeeds and participant is recorded
    assert response.status_code == 200
    assert response.json()["message"] == f"Signed up {email} for {activity_name}"
    assert email in activities[activity_name]["participants"]


def test_signup_duplicate_prevented(client):
    """Test that registering twice for the same activity is rejected."""
    # Arrange: student is already signed up for Chess Club
    activity_name = "Chess Club"
    email = "michael@mergington.edu"

    # Act: try signing up the student again
    response = client.post(f"/activities/{activity_name}/signup?email={email}")

    # Assert: request is rejected with 400 Bad Request
    assert response.status_code == 400
    assert "Student is already signed up" in response.json()["detail"]


def test_signup_nonexistent_activity(client):
    """Test signing up for an activity that does not exist."""
    # Arrange: invalid activity name
    activity_name = "Nonexistent Activity"
    email = "student@mergington.edu"

    # Act: attempt to sign up
    response = client.post(f"/activities/{activity_name}/signup?email={email}")

    # Assert: returns 404 Not Found
    assert response.status_code == 404
    assert "Activity not found" in response.json()["detail"]


def test_unregister_from_activity_success(client):
    """Test unregistering a student from an activity."""
    # Arrange: michael is already in Chess Club
    activity_name = "Chess Club"
    email = "michael@mergington.edu"

    # Act: unregister the student
    response = client.post(f"/activities/{activity_name}/unregister?email={email}")

    # Assert: unregister succeeds and student is removed
    assert response.status_code == 200
    assert response.json()["message"] == f"Unregistered {email} from {activity_name}"
    assert email not in activities[activity_name]["participants"]


def test_unregister_not_signed_up(client):
    """Test unregistering a student who is not registered."""
    # Arrange: email that is not in Chess Club
    activity_name = "Chess Club"
    email = "stranger@mergington.edu"

    # Act: attempt to unregister
    response = client.post(f"/activities/{activity_name}/unregister?email={email}")

    # Assert: request is rejected with 400 Bad Request
    assert response.status_code == 400
    assert "Student is not signed up" in response.json()["detail"]


def test_unregister_nonexistent_activity(client):
    """Test unregistering from an activity that does not exist."""
    # Arrange: non-existent activity name
    activity_name = "Flying Club"
    email = "pilot@mergington.edu"

    # Act: attempt to unregister
    response = client.post(f"/activities/{activity_name}/unregister?email={email}")

    # Assert: returns 404 Not Found
    assert response.status_code == 404
    assert "Activity not found" in response.json()["detail"]
