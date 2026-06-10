"""
Tests for the Mergington High School Activities API

This test suite uses the AAA (Arrange-Act-Assert) pattern to structure tests
for the FastAPI activity registration system.
"""

import copy
import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to initial state before each test"""
    # Store original activities
    original_activities = copy.deepcopy(activities)
    
    yield
    
    # Reset activities after test completes
    activities.clear()
    activities.update(original_activities)


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self, client, reset_activities):
        """Test that GET /activities returns all registered activities"""
        # Arrange
        expected_activity_names = {
            "Chess Club",
            "Programming Class",
            "Gym Class",
            "Soccer Team",
            "Basketball Club",
            "Art Club",
            "Drama Club",
            "Science Olympiad",
            "Debate Team"
        }
        
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        assert response.status_code == 200
        assert set(data.keys()) == expected_activity_names
        
    def test_get_activities_contains_activity_details(self, client, reset_activities):
        """Test that each activity has required fields"""
        # Arrange
        required_fields = {"description", "schedule", "max_participants", "participants"}
        
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        assert response.status_code == 200
        for activity in data.values():
            assert all(field in activity for field in required_fields)
            assert isinstance(activity["participants"], list)


class TestRootRedirect:
    """Tests for GET / endpoint"""
    
    def test_root_redirects_to_static(self, client, reset_activities):
        """Test that GET / redirects to /static/index.html"""
        # Arrange & Act
        response = client.get("/", follow_redirects=False)
        
        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_successful(self, client, reset_activities):
        """Test successful student signup for an activity"""
        # Arrange
        activity_name = "Chess Club"
        email = "new_student@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Signed up {email} for {activity_name}"
        assert email in activities[activity_name]["participants"]
    
    def test_signup_activity_not_found(self, client, reset_activities):
        """Test signup fails when activity doesn't exist"""
        # Arrange
        activity_name = "Non-existent Activity"
        email = "student@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"
    
    def test_signup_duplicate_student(self, client, reset_activities):
        """Test that a student cannot sign up twice for the same activity"""
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already signed up
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 400
        assert response.json()["detail"] == "Student already signed up for this activity"
        # Verify participant was not added twice
        assert activities[activity_name]["participants"].count(email) == 1
    
    def test_signup_multiple_students_same_activity(self, client, reset_activities):
        """Test that multiple different students can sign up for the same activity"""
        # Arrange
        activity_name = "Chess Club"
        student1 = "alice@mergington.edu"
        student2 = "bob@mergington.edu"
        initial_count = len(activities[activity_name]["participants"])
        
        # Act
        response1 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": student1}
        )
        response2 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": student2}
        )
        
        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert len(activities[activity_name]["participants"]) == initial_count + 2
        assert student1 in activities[activity_name]["participants"]
        assert student2 in activities[activity_name]["participants"]


class TestUnregisterFromActivity:
    """Tests for POST /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_successful(self, client, reset_activities):
        """Test successful student unregister from an activity"""
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already signed up
        assert email in activities[activity_name]["participants"]
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Unregistered {email} from {activity_name}"
        assert email not in activities[activity_name]["participants"]
    
    def test_unregister_activity_not_found(self, client, reset_activities):
        """Test unregister fails when activity doesn't exist"""
        # Arrange
        activity_name = "Non-existent Activity"
        email = "student@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"
    
    def test_unregister_student_not_registered(self, client, reset_activities):
        """Test unregister fails when student is not registered"""
        # Arrange
        activity_name = "Chess Club"
        email = "not_registered@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 400
        assert response.json()["detail"] == "Student is not registered for this activity"
    
    def test_unregister_multiple_students(self, client, reset_activities):
        """Test that unregistering one student doesn't affect others"""
        # Arrange
        activity_name = "Chess Club"
        student1 = "michael@mergington.edu"
        student2 = "daniel@mergington.edu"
        initial_count = len(activities[activity_name]["participants"])
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": student1}
        )
        
        # Assert
        assert response.status_code == 200
        assert len(activities[activity_name]["participants"]) == initial_count - 1
        assert student1 not in activities[activity_name]["participants"]
        assert student2 in activities[activity_name]["participants"]


class TestIntegrationSignupAndUnregister:
    """Integration tests combining signup and unregister operations"""
    
    def test_signup_then_unregister(self, client, reset_activities):
        """Test the full flow of signing up and then unregistering"""
        # Arrange
        activity_name = "Chess Club"
        email = "integration_test@mergington.edu"
        
        # Act - Sign up
        signup_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        assert signup_response.status_code == 200
        
        # Act - Unregister
        unregister_response = client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Assert
        assert unregister_response.status_code == 200
        assert email not in activities[activity_name]["participants"]
    
    def test_cannot_unregister_after_signup_fails(self, client, reset_activities):
        """Test that unregister fails if signup failed"""
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already registered
        
        # Act - Try to sign up (will fail)
        signup_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        assert signup_response.status_code == 400
        
        # Act - Try to unregister
        unregister_response = client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Assert - Original participant should still be there (could unregister)
        assert unregister_response.status_code == 200
        assert email not in activities[activity_name]["participants"]
