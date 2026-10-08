from datetime import date
import pytest
from fastapi.testclient import TestClient
from app import database, filters
from app.main import app
from scripts.seed import seed_database

# Fixed "today" so seed dates and filter cutoffs never depend on the wall clock.
# Aug 31 also exercises month-end clamping (6 months back -> Feb 28).
FROZEN_TODAY = date(2026, 8, 31)


class FrozenDate(date):
    @classmethod
    def today(cls):
        return FROZEN_TODAY


@pytest.fixture(scope="session", autouse=True)
def isolated_database(tmp_path_factory):
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(database, "DB_PATH", tmp_path_factory.mktemp("db") / "test_bookstore.db")
        patch.setattr(filters, "date", FrozenDate)
        seed_database(FROZEN_TODAY)
        yield


@pytest.fixture(scope="session")
def frozen_today():
    return FROZEN_TODAY


@pytest.fixture(scope="session")
def client(isolated_database):
    return TestClient(app)
