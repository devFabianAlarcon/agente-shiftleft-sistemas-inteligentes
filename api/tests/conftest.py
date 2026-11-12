import pytest

from banco import create_app
from banco.db import init_db


@pytest.fixture
def app(tmp_path):
    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "test.db")})
    with app.app_context():
        init_db()
    yield app


@pytest.fixture
def client(app):
    return app.test_client()


ANA = {"Authorization": "Bearer token-prueba-ana"}
BETO = {"Authorization": "Bearer token-prueba-beto"}
