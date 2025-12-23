"""
Unit tests for database models
"""
import pytest
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.user import User
from app.models.match import Match
from app.models.job import Job


class TestUserModel:
    """Test User model"""

    def test_create_user(self, db_session: Session):
        """Test creating a user with required fields"""
        user = User(
            email="test@example.com",
            hashed_password="hashed_password_123",
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.hashed_password == "hashed_password_123"
        assert user.is_active is True  # default value
        assert user.created_at is not None
        assert user.updated_at is not None

    def test_create_user_with_profile_data(self, db_session: Session):
        """Test creating a user with profile information"""
        user = User(
            email="profile@example.com",
            hashed_password="hashed_pwd",
            full_name="John Doe",
            bio="Experienced software developer",
            skills=["Python", "Django", "PostgreSQL"],
            experience_years=5,
            preferences={"remote_only": True, "min_salary": 100000},
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        assert user.full_name == "John Doe"
        assert user.bio == "Experienced software developer"
        assert user.skills == ["Python", "Django", "PostgreSQL"]
        assert user.experience_years == 5
        assert user.preferences == {"remote_only": True, "min_salary": 100000}

    def test_user_email_must_be_unique(self, db_session: Session):
        """Test that email must be unique"""
        user1 = User(email="unique@example.com", hashed_password="pwd1")
        db_session.add(user1)
        db_session.commit()

        # Try to create another user with same email
        user2 = User(email="unique@example.com", hashed_password="pwd2")
        db_session.add(user2)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_user_email_required(self, db_session: Session):
        """Test that email is required"""
        user = User(hashed_password="pwd")

        db_session.add(user)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_user_hashed_password_required(self, db_session: Session):
        """Test that hashed_password is required"""
        user = User(email="test@example.com")

        db_session.add(user)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_user_cv_fields(self, db_session: Session):
        """Test CV-related fields"""
        cv_time = datetime.now(timezone.utc)
        user = User(
            email="cv@example.com",
            hashed_password="pwd",
            cv_text="CV content extracted text",
            cv_filename="john_doe_cv.pdf",
            cv_uploaded_at=cv_time,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        assert user.cv_text == "CV content extracted text"
        assert user.cv_filename == "john_doe_cv.pdf"
        # Compare without timezone (SQLite strips timezone info)
        assert user.cv_uploaded_at.replace(tzinfo=None) == cv_time.replace(tzinfo=None)

    def test_user_default_values(self, db_session: Session):
        """Test default values for optional fields"""
        user = User(email="defaults@example.com", hashed_password="pwd")
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        assert user.is_active is True
        assert user.skills == []
        assert user.preferences == {}
        assert user.full_name is None
        assert user.bio is None
        assert user.experience_years is None

    def test_user_repr(self, db_session: Session):
        """Test User __repr__ method"""
        user = User(email="repr@example.com", hashed_password="pwd")
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        repr_str = repr(user)
        assert "User" in repr_str
        assert str(user.id) in repr_str
        assert "repr@example.com" in repr_str


class TestMatchModel:
    """Test Match model"""

    @pytest.fixture
    def sample_user(self, db_session: Session):
        """Create a sample user"""
        user = User(email="matcher@example.com", hashed_password="pwd")
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user

    @pytest.fixture
    def sample_job(self, db_session: Session):
        """Create a sample job"""
        job = Job(
            source="test",
            source_id="match_test_job",
            url="https://example.com/job",
            title="Test Job",
            company="Test Company",
            description="Test description",
        )
        db_session.add(job)
        db_session.commit()
        db_session.refresh(job)
        return job

    def test_create_match(self, db_session: Session, sample_user, sample_job):
        """Test creating a match with required fields"""
        match = Match(
            user_id=sample_user.id,
            job_id=sample_job.id,
            score=85.5,
        )
        db_session.add(match)
        db_session.commit()
        db_session.refresh(match)

        assert match.id is not None
        assert match.user_id == sample_user.id
        assert match.job_id == sample_job.id
        assert match.score == 85.5
        assert match.status == "matched"  # default
        assert match.created_at is not None
        assert match.updated_at is not None

    def test_create_match_with_analysis(self, db_session: Session, sample_user, sample_job):
        """Test creating a match with AI analysis"""
        match = Match(
            user_id=sample_user.id,
            job_id=sample_job.id,
            score=92.0,
            analysis="This is a great match because skills align perfectly",
            reasoning={
                "skills_match": 95,
                "experience_match": 90,
                "preferences_match": 91,
            },
        )
        db_session.add(match)
        db_session.commit()
        db_session.refresh(match)

        assert match.analysis == "This is a great match because skills align perfectly"
        assert match.reasoning == {
            "skills_match": 95,
            "experience_match": 90,
            "preferences_match": 91,
        }

    def test_match_with_application_tracking(self, db_session: Session, sample_user, sample_job):
        """Test match with application tracking fields"""
        applied_time = datetime.now(timezone.utc)
        match = Match(
            user_id=sample_user.id,
            job_id=sample_job.id,
            score=88.0,
            status="applied",
            applied_at=applied_time,
        )
        db_session.add(match)
        db_session.commit()
        db_session.refresh(match)

        assert match.status == "applied"
        # Compare without timezone (SQLite strips timezone info)
        assert match.applied_at.replace(tzinfo=None) == applied_time.replace(tzinfo=None)

    def test_match_with_generated_content(self, db_session: Session, sample_user, sample_job):
        """Test match with AI-generated content"""
        match = Match(
            user_id=sample_user.id,
            job_id=sample_job.id,
            score=87.0,
            cover_letter="Dear Hiring Manager, I am excited to apply...",
            cv_highlights="Key highlights: Python expert, 5 years experience...",
        )
        db_session.add(match)
        db_session.commit()
        db_session.refresh(match)

        assert "Dear Hiring Manager" in match.cover_letter
        assert "Python expert" in match.cv_highlights

    def test_match_score_range(self, db_session: Session, sample_user):
        """Test that match score can be 0-100"""
        from app.models import Job

        # Create two different jobs for testing different scores (unique constraint on user_id, job_id)
        job_min = Job(
            source="test",
            source_id="test-score-min",
            url="https://example.com/min",
            title="Test Job Min",
            company="Test Co",
            description="Test",
        )
        job_max = Job(
            source="test",
            source_id="test-score-max",
            url="https://example.com/max",
            title="Test Job Max",
            company="Test Co",
            description="Test",
        )
        db_session.add_all([job_min, job_max])
        db_session.flush()

        # Test minimum score
        match_min = Match(user_id=sample_user.id, job_id=job_min.id, score=0.0)
        db_session.add(match_min)

        # Test maximum score
        match_max = Match(user_id=sample_user.id, job_id=job_max.id, score=100.0)
        db_session.add(match_max)
        db_session.commit()

        assert match_min.score == 0.0
        assert match_max.score == 100.0

    def test_match_user_id_required(self, db_session: Session, sample_job):
        """Test that user_id is required"""
        match = Match(job_id=sample_job.id, score=85.0)
        db_session.add(match)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_match_job_id_required(self, db_session: Session, sample_user):
        """Test that job_id is required"""
        match = Match(user_id=sample_user.id, score=85.0)
        db_session.add(match)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_match_score_required(self, db_session: Session, sample_user, sample_job):
        """Test that score is required"""
        match = Match(user_id=sample_user.id, job_id=sample_job.id)
        db_session.add(match)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_match_default_status(self, db_session: Session, sample_user, sample_job):
        """Test default status is 'matched'"""
        match = Match(user_id=sample_user.id, job_id=sample_job.id, score=80.0)
        db_session.add(match)
        db_session.commit()
        db_session.refresh(match)

        assert match.status == "matched"

    def test_match_status_transitions(self, db_session: Session, sample_user, sample_job):
        """Test different status values by updating a single match"""
        statuses = ["matched", "interested", "applied", "rejected"]

        # Create a single match and update its status (unique constraint on user_id, job_id)
        match = Match(
            user_id=sample_user.id,
            job_id=sample_job.id,
            score=85.0,
            status="matched",
        )
        db_session.add(match)
        db_session.commit()
        db_session.refresh(match)

        for status in statuses:
            match.status = status
            db_session.commit()
            db_session.refresh(match)

            assert match.status == status

    def test_match_repr(self, db_session: Session, sample_user, sample_job):
        """Test Match __repr__ method"""
        match = Match(user_id=sample_user.id, job_id=sample_job.id, score=85.0)
        db_session.add(match)
        db_session.commit()
        db_session.refresh(match)

        repr_str = repr(match)
        assert "Match" in repr_str
        assert str(match.id) in repr_str
        assert str(match.user_id) in repr_str
        assert str(match.job_id) in repr_str
        assert "85.0" in repr_str


class TestJobModel:
    """Test Job model (additional tests beyond schema validation)"""

    def test_create_job_with_all_fields(self, db_session: Session):
        """Test creating a job with all fields"""
        job = Job(
            source="remoteok",
            source_id="full_job_test",
            url="https://remoteok.com/job/123",
            title="Full Stack Developer",
            company="TechCorp",
            description="Looking for an experienced full stack developer",
            salary_min=100000,
            salary_max=150000,
            salary_currency="USD",
            location="Remote",
            remote_type="full",
            job_type="permanent",
            tags=["python", "react", "aws"],
            posted_at=datetime.now(timezone.utc),
            raw_data={"original_data": "value"},
        )
        db_session.add(job)
        db_session.commit()
        db_session.refresh(job)

        assert job.id is not None
        assert job.source == "remoteok"
        assert job.title == "Full Stack Developer"
        assert job.tags == ["python", "react", "aws"]

    def test_job_default_values(self, db_session: Session):
        """Test default values for job fields"""
        job = Job(
            source="test",
            source_id="defaults_test",
            url="https://example.com/job",
            title="Test Job",
            company="Test Company",
            description="Test description",
        )
        db_session.add(job)
        db_session.commit()
        db_session.refresh(job)

        assert job.salary_currency == "USD"
        assert job.location == "Remote"
        assert job.remote_type == "full"
        assert job.job_type == "permanent"
        assert job.tags == []

    def test_job_timestamps_set_automatically(self, db_session: Session):
        """Test that timestamps are set automatically"""
        job = Job(
            source="test",
            source_id="timestamp_test",
            url="https://example.com/job",
            title="Test Job",
            company="Test Company",
            description="Test description",
        )
        db_session.add(job)
        db_session.commit()
        db_session.refresh(job)

        assert job.created_at is not None
        assert job.updated_at is not None
        assert job.scraped_at is not None
