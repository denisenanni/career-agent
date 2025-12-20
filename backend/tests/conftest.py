"""
Pytest configuration and fixtures for all tests
"""
import pytest
import os

# Disable rate limiting FIRST before any app imports
os.environ["RATE_LIMIT_ENABLED"] = "false"

from sqlalchemy import create_engine, event, text
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
    Create a fresh test database for each test with transaction-based isolation.
    Uses the TEST_DATABASE_URL environment variable if set, otherwise uses in-memory SQLite.

    Each test runs in a nested transaction (SAVEPOINT) that is rolled back after the test
    completes, ensuring complete isolation between tests even when tests call commit().

    Note: Integration tests require PostgreSQL. Set TEST_DATABASE_URL to use real database.
    """
    test_db_url = os.getenv("TEST_DATABASE_URL")

    if test_db_url:
        # Use real PostgreSQL for integration tests with transaction-based isolation
        engine = create_engine(test_db_url)

        # Create all tables (only once per test session)
        Base.metadata.create_all(bind=engine)

        # Create a connection and begin a transaction
        connection = engine.connect()
        transaction = connection.begin()

        # Create session bound to this connection
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=connection)
        session = TestingSessionLocal()

        # Begin a nested transaction (SAVEPOINT)
        # This allows tests to call commit() without affecting the outer transaction
        session.begin_nested()

        # Patch commit to use the savepoint
        @event.listens_for(session, "after_transaction_end")
        def restart_savepoint(session, transaction):
            if transaction.nested and not transaction._parent.nested:
                # Restart the savepoint after commit
                session.begin_nested()

        try:
            yield session
        finally:
            # Remove all objects from session to avoid detached instance errors
            session.expunge_all()

            # Close session
            session.close()

            # Rollback the outer transaction - this undoes ALL changes made during the test
            # Only rollback if transaction is still active
            if transaction.is_active:
                transaction.rollback()

            # Close connection
            connection.close()
    else:
        # Use in-memory SQLite for unit tests
        engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )

        # Create all tables
        Base.metadata.create_all(bind=engine)

        # For SQLite, use similar transaction-based approach
        connection = engine.connect()
        transaction = connection.begin()

        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=connection)
        session = TestingSessionLocal()

        # Begin a nested transaction (SAVEPOINT)
        session.begin_nested()

        @event.listens_for(session, "after_transaction_end")
        def restart_savepoint_sqlite(session, transaction):
            if transaction.nested and not transaction._parent.nested:
                session.begin_nested()

        try:
            yield session
        finally:
            # Remove all objects from session to avoid detached instance errors
            session.expunge_all()

            # Close session
            session.close()

            # Rollback transaction only if still active
            if transaction.is_active:
                transaction.rollback()

            # Close connection
            connection.close()

            # Clean up for SQLite
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
    """Create a test user in the database (non-admin)"""
    # Ensure admin user exists first (id=1) so test_user gets id > 1
    # This is needed for admin permission tests
    admin_exists = db_session.query(User).filter(User.id == 1).first()
    if not admin_exists:
        admin = User(
            id=1,
            email="admin@example.com",
            hashed_password=get_password_hash("adminpass123"),
            is_admin=True
        )
        db_session.add(admin)
        db_session.commit()

    # Now create the test user (will get id > 1)
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


@pytest.fixture
def client(db_session: Session):
    """FastAPI test client with database override"""
    from fastapi.testclient import TestClient
    from app.database import get_db
    from app.main import app
    import app.dependencies.auth as auth_module

    # Clear user cache before test to avoid stale data
    # Access the module's cache directly to ensure we're clearing the right one
    auth_module._user_cache.clear()

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    # Clear any existing overrides before setting new ones
    app.dependency_overrides.clear()
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    # Clean up
    app.dependency_overrides.clear()
    auth_module._user_cache.clear()


@pytest.fixture
def authenticated_client(client, test_user):
    """Client with authentication token"""
    # Login to get token
    response = client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "testpassword123"}
    )
    token = response.json()["access_token"]

    # Add token to client headers
    client.headers = {"Authorization": f"Bearer {token}"}
    return client


@pytest.fixture
def admin_client(client, db_session: Session):
    """Client authenticated as admin user"""
    # Ensure admin user exists
    admin = db_session.query(User).filter(User.id == 1).first()
    if not admin:
        admin = User(
            id=1,
            email="admin@example.com",
            hashed_password=get_password_hash("adminpass123"),
            is_admin=True
        )
        db_session.add(admin)
        db_session.commit()
    elif not admin.is_admin:
        admin.is_admin = True
        db_session.commit()

    # Login as admin
    response = client.post(
        "/auth/login",
        json={"email": "admin@example.com", "password": "adminpass123"}
    )
    token = response.json()["access_token"]

    # Add token to client headers
    client.headers = {"Authorization": f"Bearer {token}"}
    return client
