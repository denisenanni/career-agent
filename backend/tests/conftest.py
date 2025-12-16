"""
Pytest configuration and fixtures for all tests
"""
import pytest
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.models import Base
from app.models.job import Job
from app.models.scrape_log import ScrapeLog
from app.models.user import User
from app.utils.auth import get_password_hash


@pytest.fixture(scope="function")
def db_session() -> Session:
    """
    Create a fresh test database for each test.
    Uses the TEST_DATABASE_URL environment variable if set, otherwise uses in-memory SQLite.

    Note: Integration tests require PostgreSQL. Set TEST_DATABASE_URL to use real database.
    """
    test_db_url = os.getenv("TEST_DATABASE_URL")

    if test_db_url:
        # Use real PostgreSQL for integration tests
        engine = create_engine(test_db_url)

        # Create all tables
        Base.metadata.create_all(bind=engine)

        # Create session
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = TestingSessionLocal()

        try:
            yield session
        finally:
            # Close session
            session.close()

            # Drop all data - truncate only tables that exist
            with engine.begin() as conn:
                conn.execute(text("TRUNCATE TABLE jobs, scrape_logs, users, matches RESTART IDENTITY CASCADE"))
    else:
        # Use in-memory SQLite for unit tests
        engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )

        # Create all tables
        Base.metadata.create_all(bind=engine)

        # Create session
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = TestingSessionLocal()

        try:
            yield session
        finally:
            session.close()
            Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_job_data():
    """Sample valid job data for testing"""
    return {
        "source_id": "test_job_123",
        "url": "https://example.com/job/123",
        "title": "Senior Python Developer",
        "company": "Tech Corp",
        "description": "Looking for an experienced Python developer to join our team.",
        "salary_min": 120000,
        "salary_max": 180000,
        "salary_currency": "USD",
        "location": "Remote",
        "remote_type": "full",
        "job_type": "permanent",
        "tags": ["python", "django", "postgresql", "aws"],
        "raw_data": {
            "original_id": "123",
            "source_url": "https://example.com/job/123",
        },
    }


@pytest.fixture
def sample_jobs_batch():
    """Sample batch of job data for bulk insert testing"""
    return [
        {
            "source_id": f"job_{i}",
            "url": f"https://example.com/job/{i}",
            "title": f"Developer Position {i}",
            "company": f"Company {i}",
            "description": f"Description for job {i}",
            "salary_min": 100000 + (i * 10000),
            "salary_max": 150000 + (i * 10000),
            "tags": ["python", "remote"],
        }
        for i in range(1, 6)
    ]


@pytest.fixture
def existing_job(db_session: Session, sample_job_data):
    """Create an existing job in the database"""
    job = Job(
        source="test_source",
        **sample_job_data
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)
    return job


@pytest.fixture
def sample_user_data():
    """Sample user data for testing"""
    return {
        "email": "test@example.com",
        "password": "testpassword123"
    }


@pytest.fixture
def test_user(db_session: Session):
    """Create a test user in the database"""
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("testpassword123")
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def sample_cv_text():
    """Sample CV text for testing"""
    return """
John Doe
Email: john.doe@example.com
Phone: +1-555-0100

PROFESSIONAL SUMMARY
Experienced Software Engineer with 5 years of expertise in Python and web development.

SKILLS
- Programming: Python, JavaScript, SQL
- Frameworks: Django, FastAPI, React
- Databases: PostgreSQL, Redis
- Cloud: AWS, Docker

WORK EXPERIENCE

Senior Software Engineer
Tech Company Inc. | San Francisco, CA
2020-01 - present
- Led development of microservices architecture
- Implemented CI/CD pipelines
- Mentored junior developers

Software Engineer
Startup LLC | New York, NY
2018-06 - 2019-12
- Developed RESTful APIs
- Built React-based dashboards

EDUCATION

Bachelor of Science in Computer Science
University of Technology | 2018
"""
