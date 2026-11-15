import pytest
from app.core.database import init_db


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Ensure database tables exist before any tests run."""
    init_db()
