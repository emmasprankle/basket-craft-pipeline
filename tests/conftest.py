import pytest
from db import get_pg_engine

@pytest.fixture(scope="session")
def pg_engine():
    engine = get_pg_engine()
    yield engine
    engine.dispose()
