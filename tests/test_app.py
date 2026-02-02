"""Comprehensive tests for Mergington High School API."""

import pytest
from fastapi.testclient import TestClient


class TestRootEndpoint:
    """Tests for the root endpoint."""
    
    def test_root_redirect(self, client):
        """Test that root endpoint redirects to static HTML."""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Tests for the GET /activities endpoint."""
    
    def test_get_activities_returns_dict(self, client, reset_activities):
        """Test that get_activities returns a dictionary of all activities."""
        response = client.get("/activities")
        assert response.status_code == 200
        activities = response.json()
        
        # Verify it's a dict
        assert isinstance(activities, dict)
        
    def test_get_activities_has_all_activities(self, client, reset_activities):
        """Test that all expected activities are present."""
        response = client.get("/activities")
        activities = response.json()
        
        expected_activities = [
            "Chess Club",
            "Programming Class",
            "Gym Class",
            "Basketball Team",
            "Soccer Club",
            "Debate Club",
            "Drama Club",
            "Science Club",
            "Art Club"
        ]
        
        for activity_name in expected_activities:
            assert activity_name in activities
    
    def test_get_activities_has_required_fields(self, client, reset_activities):
        """Test that each activity has the required fields."""
        response = client.get("/activities")
        activities = response.json()
        
        required_fields = ["description", "schedule", "max_participants", "participants"]
        
        for activity_name, activity_data in activities.items():
            for field in required_fields:
                assert field in activity_data, f"Missing field '{field}' in {activity_name}"
    
    def test_get_activities_participants_is_list(self, client, reset_activities):
        """Test that participants field is a list."""
        response = client.get("/activities")
        activities = response.json()
        
        for activity_name, activity_data in activities.items():
            assert isinstance(activity_data["participants"], list), \
                f"participants for {activity_name} is not a list"


class TestSignupForActivity:
    """Tests for the POST /activities/{activity_name}/signup endpoint."""
    
    def test_signup_valid_activity_success(self, client, reset_activities):
        """Test successful signup for a valid activity."""
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
    
    def test_signup_adds_participant(self, client, reset_activities):
        """Test that signup actually adds participant to activity."""
        email = "newstudent@mergington.edu"
        
        # Signup
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        assert response.status_code == 200
        
        # Verify participant was added
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email in activities["Chess Club"]["participants"]
    
    def test_signup_nonexistent_activity_returns_404(self, client, reset_activities):
        """Test that signup for non-existent activity returns 404."""
        response = client.post(
            "/activities/Nonexistent Club/signup",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_signup_duplicate_returns_400(self, client, reset_activities):
        """Test that duplicate signup returns 400 error."""
        email = "michael@mergington.edu"  # Already in Chess Club
        
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]
    
    def test_signup_different_activities_allowed(self, client, reset_activities):
        """Test that same student can signup for different activities."""
        email = "newstudent@mergington.edu"
        
        # Signup for first activity
        response1 = client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        # Signup for second activity
        response2 = client.post(
            "/activities/Programming Class/signup",
            params={"email": email}
        )
        assert response2.status_code == 200
        
        # Verify student is in both activities
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email in activities["Chess Club"]["participants"]
        assert email in activities["Programming Class"]["participants"]
    
    def test_signup_multiple_students_same_activity(self, client, reset_activities):
        """Test that multiple different students can signup for same activity."""
        activity = "Drama Club"
        
        emails = [
            "student1@mergington.edu",
            "student2@mergington.edu",
            "student3@mergington.edu"
        ]
        
        for email in emails:
            response = client.post(
                f"/activities/{activity}/signup",
                params={"email": email}
            )
            assert response.status_code == 200
        
        # Verify all were added
        activities_response = client.get("/activities")
        activities = activities_response.json()
        for email in emails:
            assert email in activities[activity]["participants"]
    
    def test_signup_various_activities(self, client, reset_activities):
        """Test signup for various different activities."""
        test_cases = [
            ("Chess Club", "test1@mergington.edu"),
            ("Basketball Team", "test2@mergington.edu"),
            ("Science Club", "test3@mergington.edu"),
            ("Art Club", "test4@mergington.edu"),
            ("Debate Club", "test5@mergington.edu"),
        ]
        
        for activity_name, email in test_cases:
            response = client.post(
                f"/activities/{activity_name}/signup",
                params={"email": email}
            )
            assert response.status_code == 200, \
                f"Failed to signup for {activity_name}"
    
    def test_signup_case_sensitive_email(self, client, reset_activities):
        """Test signup with different email cases."""
        # Signup with lowercase
        response1 = client.post(
            "/activities/Chess Club/signup",
            params={"email": "student@mergington.edu"}
        )
        assert response1.status_code == 200
        
        # Try to signup with same email but different case
        response2 = client.post(
            "/activities/Chess Club/signup",
            params={"email": "student@mergington.edu"}
        )
        assert response2.status_code == 400


class TestEdgeCases:
    """Tests for edge cases and error handling."""
    
    def test_signup_missing_email_parameter(self, client, reset_activities):
        """Test signup without email parameter."""
        response = client.post("/activities/Chess Club/signup")
        # Should return 422 (validation error) because email is required
        assert response.status_code == 422
    
    def test_activity_names_with_special_characters(self, client, reset_activities):
        """Test that activity names with spaces are handled correctly."""
        response = client.get("/activities")
        activities = response.json()
        
        # These activities have spaces - verify they're accessible
        assert "Chess Club" in activities
        assert "Programming Class" in activities
        assert "Basketball Team" in activities
    
    def test_get_activities_response_structure(self, client, reset_activities):
        """Test the complete response structure of get_activities."""
        response = client.get("/activities")
        assert response.status_code == 200
        
        activities = response.json()
        
        # Verify Chess Club structure as example
        chess_club = activities["Chess Club"]
        assert isinstance(chess_club["description"], str)
        assert isinstance(chess_club["schedule"], str)
        assert isinstance(chess_club["max_participants"], int)
        assert isinstance(chess_club["participants"], list)
        assert chess_club["max_participants"] > 0


class TestDataIntegrity:
    """Tests to verify data integrity and consistency."""
    
    def test_activities_not_empty(self, client, reset_activities):
        """Test that activities list is not empty."""
        response = client.get("/activities")
        activities = response.json()
        assert len(activities) > 0
    
    def test_activity_descriptions_are_strings(self, client, reset_activities):
        """Test that all activities have valid descriptions."""
        response = client.get("/activities")
        activities = response.json()
        
        for activity_name, activity_data in activities.items():
            assert isinstance(activity_data["description"], str)
            assert len(activity_data["description"]) > 0
    
    def test_activity_schedules_are_strings(self, client, reset_activities):
        """Test that all activities have valid schedules."""
        response = client.get("/activities")
        activities = response.json()
        
        for activity_name, activity_data in activities.items():
            assert isinstance(activity_data["schedule"], str)
            assert len(activity_data["schedule"]) > 0
    
    def test_max_participants_is_positive(self, client, reset_activities):
        """Test that max_participants is positive for all activities."""
        response = client.get("/activities")
        activities = response.json()
        
        for activity_name, activity_data in activities.items():
            assert activity_data["max_participants"] > 0, \
                f"{activity_name} has non-positive max_participants"
    
    def test_participants_count_valid(self, client, reset_activities):
        """Test that participant count doesn't exceed max."""
        response = client.get("/activities")
        activities = response.json()
        
        for activity_name, activity_data in activities.items():
            participant_count = len(activity_data["participants"])
            assert participant_count <= activity_data["max_participants"], \
                f"{activity_name} has more participants than max allowed"
