import pytest
from werkzeug.security import generate_password_hash
from app import create_app
from db import get_db


@pytest.fixture
def app(tmp_path):
    app = create_app({
        "TESTING": True,
        "SECRET_KEY": "test-key-only",
        "DATABASE": str(tmp_path / "test.sqlite3"),
    })
    with app.app_context():
        get_db().execute(
            "INSERT INTO usuarios(nome, login, senha_hash) VALUES (?, ?, ?)",
            ("Funcionário Teste", "funcionario", generate_password_hash("senha-segura-123")),
        )
        get_db().commit()
    return app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def logged_client(client):
    with client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["csrf_token"] = "test-csrf-token"
    return client
