"""
Integration tests for Preferences Merging

Tests that updating user preferences doesn't delete existing preference data,
particularly the parsed_cv data.
"""
import pytest
from app.models.user import User


@pytest.fixture
def user_with_parsed_cv(db_session, test_user):
    """Create a user with parsed CV data in preferences"""
    test_user.preferences = {
        "parsed_cv": {
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "+1-555-0100",
            "summary": "Experienced developer",
            "skills": ["Python", "JavaScript", "SQL"],
            "experience": [],
            "education": [],
            "years_of_experience": 5
        },
        "job_preferences": {
            "min_salary": 100000,
            "preferred_locations": ["San Francisco", "Remote"]
        }
    }
    db_session.commit()
    db_session.refresh(test_user)
    return test_user


class TestPreferencesMerging:
    """Test that preferences are properly merged instead of overwritten"""

    def test_update_preferences_merges_not_overwrites(self, authenticated_client, user_with_parsed_cv, db_session):
        """Test that updating preferences merges with existing data"""
        # Update job preferences
        response = authenticated_client.put(
            "/api/profile",
            json={
                "preferences": {
                    "job_preferences": {
                        "min_salary": 120000,
                        "work_type": "remote"
                    }
                }
            }
        )

        assert response.status_code == 200

        # Refresh user from database
        db_session.refresh(user_with_parsed_cv)

        # parsed_cv should still exist
        assert "parsed_cv" in user_with_parsed_cv.preferences
        assert user_with_parsed_cv.preferences["parsed_cv"]["name"] == "John Doe"
        assert user_with_parsed_cv.preferences["parsed_cv"]["skills"] == ["Python", "JavaScript", "SQL"]

        # job_preferences should be updated
        assert "job_preferences" in user_with_parsed_cv.preferences
        assert user_with_parsed_cv.preferences["job_preferences"]["min_salary"] == 120000
        assert user_with_parsed_cv.preferences["job_preferences"]["work_type"] == "remote"

    def test_update_new_preference_preserves_existing(self, authenticated_client, user_with_parsed_cv, db_session):
        """Test adding a new preference key preserves existing data"""
        response = authenticated_client.put(
            "/api/profile",
            json={
                "preferences": {
                    "notification_settings": {
                        "email_enabled": True,
                        "frequency": "daily"
                    }
                }
            }
        )

        assert response.status_code == 200

        db_session.refresh(user_with_parsed_cv)

        # All existing preferences should still exist
        assert "parsed_cv" in user_with_parsed_cv.preferences
        assert "job_preferences" in user_with_parsed_cv.preferences

        # New preference should be added
        assert "notification_settings" in user_with_parsed_cv.preferences
        assert user_with_parsed_cv.preferences["notification_settings"]["email_enabled"] is True

    def test_update_profile_without_preferences(self, authenticated_client, user_with_parsed_cv, db_session):
        """Test updating other profile fields doesn't affect preferences"""
        response = authenticated_client.put(
            "/api/profile",
            json={
                "full_name": "John Doe Updated",
                "bio": "Software engineer with 5 years of experience"
            }
        )

        assert response.status_code == 200

        db_session.refresh(user_with_parsed_cv)

        # Preferences should remain unchanged
        assert "parsed_cv" in user_with_parsed_cv.preferences
        assert user_with_parsed_cv.preferences["parsed_cv"]["name"] == "John Doe"

        # Other fields should be updated
        assert user_with_parsed_cv.full_name == "John Doe Updated"
        assert user_with_parsed_cv.bio == "Software engineer with 5 years of experience"

    def test_update_skills_preserves_parsed_cv(self, authenticated_client, user_with_parsed_cv, db_session):
        """Test updating skills doesn't delete parsed_cv"""
        response = authenticated_client.put(
            "/api/profile",
            json={
                "skills": ["Python", "TypeScript", "React"]
            }
        )

        assert response.status_code == 200

        db_session.refresh(user_with_parsed_cv)

        # parsed_cv should still exist
        assert "parsed_cv" in user_with_parsed_cv.preferences

        # Skills should be updated
        assert user_with_parsed_cv.skills == ["Python", "TypeScript", "React"]

    def test_multiple_preference_updates(self, authenticated_client, user_with_parsed_cv, db_session):
        """Test multiple consecutive preference updates preserve data"""
        # First update
        response = authenticated_client.put(
            "/api/profile",
            json={
                "preferences": {
                    "job_preferences": {
                        "min_salary": 120000
                    }
                }
            }
        )
        assert response.status_code == 200

        # Second update
        response = authenticated_client.put(
            "/api/profile",
            json={
                "preferences": {
                    "notification_settings": {
                        "email_enabled": True
                    }
                }
            }
        )
        assert response.status_code == 200

        db_session.refresh(user_with_parsed_cv)

        # All preferences should exist
        assert "parsed_cv" in user_with_parsed_cv.preferences
        assert "job_preferences" in user_with_parsed_cv.preferences
        assert "notification_settings" in user_with_parsed_cv.preferences

    def test_update_parsed_cv_via_endpoint(self, authenticated_client, user_with_parsed_cv, db_session):
        """Test updating parsed CV via dedicated endpoint"""
        response = authenticated_client.put(
            "/api/profile/cv/parsed",
            json={
                "name": "John Doe Updated",
                "skills": ["Python", "Go", "Rust"]
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Response should have updated data
        assert data["name"] == "John Doe Updated"
        assert "Go" in data["skills"]
        assert "Rust" in data["skills"]

        db_session.refresh(user_with_parsed_cv)

        # parsed_cv should be updated
        assert user_with_parsed_cv.preferences["parsed_cv"]["name"] == "John Doe Updated"
        assert "Go" in user_with_parsed_cv.preferences["parsed_cv"]["skills"]

        # Main profile should be synced
        assert user_with_parsed_cv.full_name == "John Doe Updated"
        assert "Go" in user_with_parsed_cv.skills

    def test_update_parsed_cv_syncs_to_profile(self, authenticated_client, user_with_parsed_cv, db_session):
        """Test that updating parsed CV syncs key fields to main profile"""
        response = authenticated_client.put(
            "/api/profile/cv/parsed",
            json={
                "name": "Jane Smith",
                "skills": ["Java", "Spring"],
                "years_of_experience": 8
            }
        )

        assert response.status_code == 200

        db_session.refresh(user_with_parsed_cv)

        # Main profile fields should be synced
        assert user_with_parsed_cv.full_name == "Jane Smith"
        assert user_with_parsed_cv.skills == ["Java", "Spring"]
        assert user_with_parsed_cv.experience_years == 8

    def test_preferences_with_null_value(self, authenticated_client, user_with_parsed_cv, db_session):
        """Test that explicitly setting preferences to null clears them"""
        response = authenticated_client.put(
            "/api/profile",
            json={
                "preferences": None
            }
        )

        assert response.status_code == 200

        db_session.refresh(user_with_parsed_cv)

        # Explicitly sending None clears preferences
        assert user_with_parsed_cv.preferences is None

    def test_empty_preferences_dict(self, authenticated_client, user_with_parsed_cv, db_session):
        """Test updating with empty preferences dict"""
        response = authenticated_client.put(
            "/api/profile",
            json={
                "preferences": {}
            }
        )

        assert response.status_code == 200

        db_session.refresh(user_with_parsed_cv)

        # Existing preferences should be preserved
        assert "parsed_cv" in user_with_parsed_cv.preferences

    def test_nested_preference_update(self, authenticated_client, user_with_parsed_cv, db_session):
        """Test updating nested preference values"""
        response = authenticated_client.put(
            "/api/profile",
            json={
                "preferences": {
                    "job_preferences": {
                        "min_salary": 150000,
                        "preferred_locations": ["New York", "Boston"]
                    }
                }
            }
        )

        assert response.status_code == 200

        db_session.refresh(user_with_parsed_cv)

        # Nested update should merge
        assert user_with_parsed_cv.preferences["job_preferences"]["min_salary"] == 150000
        assert "New York" in user_with_parsed_cv.preferences["job_preferences"]["preferred_locations"]

        # parsed_cv should still exist
        assert "parsed_cv" in user_with_parsed_cv.preferences

    def test_user_without_preferences(self, authenticated_client, test_user, db_session):
        """Test updating preferences for user with no existing preferences"""
        # Ensure user has no preferences
        test_user.preferences = None
        db_session.commit()

        response = authenticated_client.put(
            "/api/profile",
            json={
                "preferences": {
                    "job_preferences": {
                        "min_salary": 100000
                    }
                }
            }
        )

        assert response.status_code == 200

        db_session.refresh(test_user)

        # Preferences should be created
        assert test_user.preferences is not None
        assert "job_preferences" in test_user.preferences
        assert test_user.preferences["job_preferences"]["min_salary"] == 100000
