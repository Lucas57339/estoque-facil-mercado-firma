"""Autenticação básica, cookies de sessão e proteção CSRF para formulários."""
import functools
import hmac
import secrets
from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for, abort
from werkzeug.security import check_password_hash
from db import get_db

bp = Blueprint("auth", __name__)


def csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(32)
    return session["csrf_token"]


def verify_csrf():
    expected = session.get("csrf_token", "")
    received = request.form.get("csrf_token", "")
    if not expected or not hmac.compare_digest(expected, received):
        abort(400, description="Formulário expirado. Recarregue a página e tente novamente.")


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get("user_id")
    g.user = None
    if user_id:
        g.user = get_db().execute(
            "SELECT id_usuario, nome, login FROM usuarios WHERE id_usuario=? AND ativo=1",
            (user_id,),
        ).fetchone()


def login_required(view):
    @functools.wraps(view)
    def wrapped(**kwargs):
        if g.user is None:
            return redirect(url_for("auth.login"))
        return view(**kwargs)
    return wrapped


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        verify_csrf()
        username = request.form.get("login", "").strip()
        password = request.form.get("senha", "")
        user = get_db().execute(
            "SELECT * FROM usuarios WHERE login=? AND ativo=1", (username,)
        ).fetchone()
        if not user or not check_password_hash(user["senha_hash"], password):
            flash("Usuário ou senha inválidos.", "error")
        else:
            session.clear()
            session["user_id"] = user["id_usuario"]
            csrf_token()
            return redirect(url_for("inventory.dashboard"))
    return render_template("login.html")


@bp.post("/sair")
def logout():
    verify_csrf()
    session.clear()
    return redirect(url_for("auth.login"))
