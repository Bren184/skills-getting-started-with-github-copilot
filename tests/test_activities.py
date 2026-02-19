"""
Tests for the Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path to import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app, activities

# Create test client
client = TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to initial state before each test"""
    # Store original state
    original_state = {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        }
    }
    
    # Clear and reset activities
    activities.clear()
    activities.update(original_state)
    
    yield
    
    # Reset after test
    activities.clear()
    activities.update(original_state)


class TestRootEndpoint:
    """Test the root endpoint"""
    
    def test_root_redirect(self):
        """Test that root redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestActivitiesEndpoint:
    """Test the activities endpoint"""
    
    def test_get_activities(self, reset_activities):
        """Test getting all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        
        data = response.json()
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
        
        # Verify structure
        assert data["Chess Club"]["description"]
        assert data["Chess Club"]["schedule"]
        assert data["Chess Club"]["max_participants"]
        assert data["Chess Club"]["participants"]
    
    def test_get_activities_has_participants(self, reset_activities):
        """Test that activities have correct initial participants"""
        response = client.get("/activities")
        data = response.json()
        
        assert "michael@mergington.edu" in data["Chess Club"]["participants"]
        assert "daniel@mergington.edu" in data["Chess Club"]["participants"]


class TestSignupEndpoint:
    """Test the signup endpoint"""
    
    def test_signup_success(self, reset_activities):
        """Test successful signup"""
        response = client.post(
            "/activities/Chess Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
    
    def test_signup_adds_participant(self, reset_activities):
        """Test that signup actually adds the participant"""
        client.post("/activities/Chess Club/signup?email=newstudent@mergington.edu")
        
        response = client.get("/activities")
        data = response.json()
        
        assert "newstudent@mergington.edu" in data["Chess Club"]["participants"]
        assert len(data["Chess Club"]["participants"]) == 3
    
    def test_signup_invalid_activity(self, reset_activities):
        """Test signup for non-existent activity"""
        response = client.post(
            "/activities/NonExistent Club/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_signup_duplicate_student(self, reset_activities):
        """Test signup when student already registered"""
        response = client.post(
            "/activities/Chess Club/signup?email=michael@mergington.edu"
        )
        assert response.status_code == 400
        
        data = response.json()
        assert "already signed up" in data["detail"]
    
    def test_signup_multiple_students(self, reset_activities):
        """Test multiple students can sign up"""
        emails = [
            "student1@mergington.edu",
            "student2@mergington.edu",
            "student3@mergington.edu"
        ]
        
        for email in emails:
            response = client.post(
                f"/activities/Programming Class/signup?email={email}"
            )
            assert response.status_code == 200
        
        response = client.get("/activities")
        data = response.json()
        
        for email in emails:
            assert email in data["Programming Class"]["participants"]


class TestUnregisterEndpoint:
    """Test the unregister endpoint"""
    
    def test_unregister_success(self, reset_activities):
        """Test successful unregistration"""
        response = client.delete(
            "/activities/Chess Club/signup/michael@mergington.edu"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "Unregistered" in data["message"]
    
    def test_unregister_removes_participant(self, reset_activities):
        """Test that unregister actually removes the participant"""
        client.delete("/activities/Chess Club/signup/michael@mergington.edu")
        
        response = client.get("/activities")
        data = response.json()
        
        assert "michael@mergington.edu" not in data["Chess Club"]["participants"]
        assert len(data["Chess Club"]["participants"]) == 1
    
    def test_unregister_invalid_activity(self, reset_activities):
        """Test unregister from non-existent activity"""
        response = client.delete(
            "/activities/NonExistent Club/signup/student@mergington.edu"
        )
        assert response.status_code == 404
        
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_unregister_not_registered_student(self, reset_activities):
        """Test unregister when student not registered"""
        response = client.delete(
            "/activities/Chess Club/signup/notstudent@mergington.edu"
        )
        assert response.status_code == 404
        
        data = response.json()
        assert "not registered" in data["detail"]


class TestIntegration:
    """Integration tests for signup and unregister workflow"""
    
    def test_signup_and_unregister_flow(self, reset_activities):
        """Test complete flow: signup then unregister"""
        email = "testuser@mergington.edu"
        activity = "Programming Class"
        
        # Verify not registered
        response = client.get("/activities")
        assert email not in response.json()[activity]["participants"]
        
        # Sign up
        response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        assert response.status_code == 200
        
        # Verify registered
        response = client.get("/activities")
        assert email in response.json()[activity]["participants"]
        
        # Unregister
        response = client.delete(
            f"/activities/{activity}/signup/{email}"
        )
        assert response.status_code == 200
        
        # Verify unregistered
        response = client.get("/activities")
        assert email not in response.json()[activity]["participants"]
    
    def test_full_activity_lifecycle(self, reset_activities):
        """Test complete activity lifecycle with multiple users"""
        activity = "Gym Class"
        initial_count = len(activities[activity]["participants"])
        
        users = [f"user{i}@mergington.edu" for i in range(3)]
        
        # Sign up multiple users
        for user in users:
            response = client.post(
                f"/activities/{activity}/signup?email={user}"
            )
            assert response.status_code == 200
        
        # Verify all signed up
        response = client.get("/activities")
        data = response.json()
        assert len(data[activity]["participants"]) == initial_count + 3
        
        # Unregister one user
        response = client.delete(
            f"/activities/{activity}/signup/{users[0]}"
        )
        assert response.status_code == 200
        
        # Verify correct count
        response = client.get("/activities")
        data = response.json()
        assert len(data[activity]["participants"]) == initial_count + 2
        assert users[0] not in data[activity]["participants"]
        assert users[1] in data[activity]["participants"]
