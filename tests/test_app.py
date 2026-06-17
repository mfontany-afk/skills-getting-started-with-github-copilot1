import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Provide a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to initial state before each test"""
    original_activities = {
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
        },
    }
    
    # Clear and repopulate activities
    activities.clear()
    activities.update(original_activities)
    
    yield
    
    # Cleanup after test
    activities.clear()
    activities.update(original_activities)


# ========== GET /activities Tests ==========

class TestGetActivities:
    """Tests for the GET /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self, client, reset_activities):
        """Test that GET /activities returns all activities"""
        # Arrange
        # (state is set up by reset_activities fixture)
        
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
    
    def test_get_activities_includes_activity_details(self, client, reset_activities):
        """Test that activities include required fields"""
        # Arrange
        # (state is set up by reset_activities fixture)
        expected_description = "Learn strategies and compete in chess tournaments"
        expected_schedule = "Fridays, 3:30 PM - 5:00 PM"
        
        # Act
        response = client.get("/activities")
        data = response.json()
        chess_club = data["Chess Club"]
        
        # Assert
        assert chess_club["description"] == expected_description
        assert chess_club["schedule"] == expected_schedule
        assert chess_club["max_participants"] == 12
        assert chess_club["participants"] == ["michael@mergington.edu", "daniel@mergington.edu"]
    
    def test_get_activities_returns_participant_list(self, client, reset_activities):
        """Test that activities include participants list"""
        # Arrange
        expected_participant_count = 2
        expected_participant = "john@mergington.edu"
        
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        assert len(data["Gym Class"]["participants"]) == expected_participant_count
        assert expected_participant in data["Gym Class"]["participants"]


# ========== POST /activities/{activity_name}/signup Tests ==========

class TestSignupForActivity:
    """Tests for the POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_new_participant_success(self, client, reset_activities):
        """Test successful signup of a new participant"""
        # Arrange
        activity_name = "Chess Club"
        new_email = "newstudent@mergington.edu"
        
        # Act
        response = client.post(
            "/activities/Chess%20Club/signup",
            params={"email": new_email}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == f"Signed up {new_email} for {activity_name}"
        assert new_email in activities["Chess Club"]["participants"]
    
    def test_signup_multiple_different_students(self, client, reset_activities):
        """Test multiple different students can sign up"""
        # Arrange
        activity_name = "Chess Club"
        student1_email = "student1@mergington.edu"
        student2_email = "student2@mergington.edu"
        
        # Act
        response1 = client.post(
            "/activities/Chess%20Club/signup",
            params={"email": student1_email}
        )
        response2 = client.post(
            "/activities/Chess%20Club/signup",
            params={"email": student2_email}
        )
        
        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert student1_email in activities[activity_name]["participants"]
        assert student2_email in activities[activity_name]["participants"]
    
    def test_signup_duplicate_student_fails(self, client, reset_activities):
        """Test that a student cannot sign up twice for the same activity"""
        # Arrange
        activity_name = "Chess Club"
        existing_email = "michael@mergington.edu"  # Already registered
        expected_error = "Student is already signed up for this activity"
        
        # Act
        response = client.post(
            "/activities/Chess%20Club/signup",
            params={"email": existing_email}
        )
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert data["detail"] == expected_error
    
    def test_signup_nonexistent_activity_fails(self, client, reset_activities):
        """Test that signing up for a nonexistent activity returns 404"""
        # Arrange
        nonexistent_activity = "Nonexistent Club"
        new_email = "student@mergington.edu"
        expected_error = "Activity not found"
        
        # Act
        response = client.post(
            "/activities/Nonexistent%20Club/signup",
            params={"email": new_email}
        )
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == expected_error
    
    def test_signup_adds_participant_to_list(self, client, reset_activities):
        """Test that signup correctly adds participant to the participants list"""
        # Arrange
        activity_name = "Programming Class"
        new_email = "newprogrammer@mergington.edu"
        initial_count = len(activities[activity_name]["participants"])
        expected_new_count = initial_count + 1
        
        # Act
        client.post(
            "/activities/Programming%20Class/signup",
            params={"email": new_email}
        )
        
        # Assert
        assert len(activities[activity_name]["participants"]) == expected_new_count


# ========== POST /activities/{activity_name}/remove Tests ==========

class TestRemoveParticipant:
    """Tests for the POST /activities/{activity_name}/remove endpoint"""
    
    def test_remove_participant_success(self, client, reset_activities):
        """Test successful removal of a participant"""
        # Arrange
        activity_name = "Chess Club"
        email_to_remove = "michael@mergington.edu"
        
        # Act
        response = client.post(
            "/activities/Chess%20Club/remove",
            params={"email": email_to_remove}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == f"Removed {email_to_remove} from {activity_name}"
        assert email_to_remove not in activities[activity_name]["participants"]
    
    def test_remove_participant_updates_list(self, client, reset_activities):
        """Test that removal correctly updates participant list"""
        # Arrange
        activity_name = "Gym Class"
        email_to_remove = "john@mergington.edu"
        initial_count = len(activities[activity_name]["participants"])
        expected_new_count = initial_count - 1
        
        # Act
        client.post(
            "/activities/Gym%20Class/remove",
            params={"email": email_to_remove}
        )
        
        # Assert
        assert len(activities[activity_name]["participants"]) == expected_new_count
    
    def test_remove_nonexistent_participant_fails(self, client, reset_activities):
        """Test that removing a non-participant returns 400"""
        # Arrange
        activity_name = "Chess Club"
        unregistered_email = "notregistered@mergington.edu"
        expected_error = "Student is not signed up for this activity"
        
        # Act
        response = client.post(
            "/activities/Chess%20Club/remove",
            params={"email": unregistered_email}
        )
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert data["detail"] == expected_error
    
    def test_remove_from_nonexistent_activity_fails(self, client, reset_activities):
        """Test that removing from a nonexistent activity returns 404"""
        # Arrange
        nonexistent_activity = "Nonexistent Club"
        email = "student@mergington.edu"
        expected_error = "Activity not found"
        
        # Act
        response = client.post(
            "/activities/Nonexistent%20Club/remove",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == expected_error
    
    def test_remove_can_signup_again(self, client, reset_activities):
        """Test that a student can sign up again after being removed"""
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"
        
        # Act - Remove
        client.post(
            f"/activities/{activity_name.replace(' ', '%20')}/remove",
            params={"email": email}
        )
        
        # Act - Sign up again
        response = client.post(
            f"/activities/{activity_name.replace(' ', '%20')}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        assert email in activities[activity_name]["participants"]


# ========== Integration Tests ==========

class TestIntegration:
    """Integration tests combining multiple operations"""
    
    def test_signup_and_remove_flow(self, client, reset_activities):
        """Test complete signup and removal flow"""
        # Arrange
        activity_name = "Programming Class"
        email = "testuser@mergington.edu"
        activity_encoded = "Programming%20Class"
        
        # Act - Sign up
        signup_response = client.post(
            f"/activities/{activity_encoded}/signup",
            params={"email": email}
        )
        
        # Assert - Signup successful
        assert signup_response.status_code == 200
        
        # Act - Verify in list
        get_response = client.get("/activities")
        
        # Assert - Email in participants
        assert email in get_response.json()[activity_name]["participants"]
        
        # Act - Remove
        remove_response = client.post(
            f"/activities/{activity_encoded}/remove",
            params={"email": email}
        )
        
        # Assert - Removal successful
        assert remove_response.status_code == 200
        
        # Act - Verify removed from list
        get_response = client.get("/activities")
        
        # Assert - Email not in participants
        assert email not in get_response.json()[activity_name]["participants"]
    
    def test_multiple_participants_across_activities(self, client, reset_activities):
        """Test multiple participants in different activities"""
        # Arrange
        student_email = "versatile@mergington.edu"
        activities_to_join = [
            ("Chess%20Club", "Chess Club"),
            ("Programming%20Class", "Programming Class")
        ]
        
        # Act - Sign up for multiple activities
        responses = []
        for encoded_name, _ in activities_to_join:
            response = client.post(
                f"/activities/{encoded_name}/signup",
                params={"email": student_email}
            )
            responses.append(response)
        
        # Assert - All signups successful
        for response in responses:
            assert response.status_code == 200
        
        # Assert - Student in all activities
        for _, activity_name in activities_to_join:
            assert student_email in activities[activity_name]["participants"]
