import os
import pytest
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

@pytest.fixture(scope="session")
def pg_engine():
    engine = create_engine(
        f"postgresql+psycopg2://{os.environ['PG_USER']}:{os.environ['PG_PASSWORD']}"
        f"@{os.environ['PG_HOST']}:{os.environ['PG_PORT']}/{os.environ['PG_DATABASE']}"
    )
    yield engine
    engine.dispose()
