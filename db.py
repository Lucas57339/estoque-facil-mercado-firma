"""Conexão e esquema SQLite. A pasta instance/ fica fora do Git."""
import sqlite3
from flask import current_app, g


def get_db():
    if "db" not in g:
        connection = sqlite3.connect(current_app.config["DATABASE"])
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        g.db = connection
    return g.db


def close_db(_error=None):
    connection = g.pop("db", None)
    if connection is not None:
        connection.close()


def init_db():
    with current_app.open_resource("schema.sql") as file:
        get_db().executescript(file.read().decode("utf-8"))
    get_db().commit()


def init_app(app):
    app.teardown_appcontext(close_db)
