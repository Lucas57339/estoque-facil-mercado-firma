"""Estoque Fácil: aplicação web de controle de estoque (MVP acadêmico)."""
import os
import secrets
from pathlib import Path
import click
from flask import Flask, g
from werkzeug.security import generate_password_hash


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    secret_path = Path(app.instance_path) / ".secret_key"
    secret = os.environ.get("SECRET_KEY")
    if not secret:
        if secret_path.exists():
            secret = secret_path.read_text(encoding="utf-8")
        else:
            secret = secrets.token_hex(32)
            secret_path.write_text(secret, encoding="utf-8")
    app.config.update(
        SECRET_KEY=secret,
        DATABASE=str(Path(app.instance_path) / "estoque.sqlite3"),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE", "0") == "1",
    )
    if test_config:
        app.config.update(test_config)

    import db
    import auth
    import inventory

    db.init_app(app)
    app.register_blueprint(auth.bp)
    app.register_blueprint(inventory.bp)
    app.jinja_env.globals["csrf_token"] = auth.csrf_token

    @app.after_request
    def headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'; style-src 'self'; script-src 'self'; img-src 'self' data:; base-uri 'self'; form-action 'self'"
        return response

    @app.cli.command("init-db")
    def init_db_command():
        db.init_db()
        click.echo("Banco de dados inicializado.")

    @app.cli.command("create-user")
    @click.option("--name", prompt="Nome")
    @click.option("--login", prompt="Login")
    @click.password_option("--password", confirmation_prompt=True)
    def create_user_command(name, login, password):
        if not name.strip() or not login.strip() or len(password) < 8:
            raise click.ClickException("Informe nome, login e senha com pelo menos 8 caracteres.")
        db.init_db()
        try:
            db.get_db().execute(
                "INSERT INTO usuarios(nome, login, senha_hash) VALUES (?, ?, ?)",
                (name.strip(), login.strip(), generate_password_hash(password)),
            )
            db.get_db().commit()
        except Exception as exc:
            if "UNIQUE constraint" in str(exc):
                raise click.ClickException("Este login já existe.") from exc
            raise
        click.echo("Usuário cadastrado com segurança.")

    @app.context_processor
    def inject_user():
        return {"current_user": getattr(g, "user", None)}

    with app.app_context():
        db.init_db()
    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=5000, debug=False)
