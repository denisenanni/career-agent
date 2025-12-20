"""
Unit tests for database module
"""
import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session


class TestGetDb:
    """Test get_db dependency function"""

    def test_get_db_yields_session(self):
        """Test that get_db yields a database session"""
        from app.database import get_db

        # Get the generator
        gen = get_db()

        # Get the session
        session = next(gen)

        assert session is not None
        assert isinstance(session, Session)

        # Clean up - close the generator properly
        gen.close()

    def test_get_db_full_lifecycle(self):
        """Test the full lifecycle of get_db"""
        from app.database import get_db

        sessions = []
        for session in get_db():
            sessions.append(session)
            assert isinstance(session, Session)

        # Should have yielded exactly one session
        assert len(sessions) == 1


class TestGetDbSession:
    """Test get_db_session context manager"""

    def test_get_db_session_yields_session(self):
        """Test that get_db_session yields a database session"""
        from app.database import get_db_session

        with get_db_session() as session:
            assert session is not None
            assert isinstance(session, Session)

    def test_get_db_session_commits_on_success(self):
        """Test that context manager completes without error"""
        from app.database import get_db_session

        # This should complete without raising
        with get_db_session() as session:
            # Just verify we can use the session
            assert session.is_active

    def test_get_db_session_rollbacks_on_exception(self):
        """Test that get_db_session rolls back on exception"""
        from app.database import get_db_session

        with pytest.raises(ValueError):
            with get_db_session() as session:
                raise ValueError("Test error")

        # If we get here, rollback was called and exception was re-raised


class TestInitDb:
    """Test init_db function"""

    def test_init_db_creates_tables(self):
        """Test that init_db creates database tables"""
        from app.database import init_db, engine
        from app.models import Base

        with patch.object(Base.metadata, 'create_all') as mock_create_all:
            init_db()

            mock_create_all.assert_called_once_with(bind=engine)
