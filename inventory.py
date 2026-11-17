"""Cadastro, consulta, movimentação e alertas de vencimento e estoque mínimo."""
from datetime import date, timedelta
import sqlite3
from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from auth import login_required, verify_csrf
from db import get_db

bp = Blueprint("inventory", __name__)


def validate_product(form):
    name = form.get("nome", "").strip()
    code = form.get("codigo", "").strip()
    expiry = form.get("data_validade", "").strip()
    if not name or not code:
        raise ValueError("Informe o nome e o código do produto.")
    if len(name) > 120 or len(code) > 40:
        raise ValueError("Nome ou código muito longo.")
    try:
        quantity = int(form.get("quantidade_atual", ""))
        minimum = int(form.get("estoque_minimo", ""))
        date.fromisoformat(expiry)
    except (ValueError, TypeError) as exc:
        raise ValueError("Informe quantidade, estoque mínimo e validade válidos.") from exc
    if quantity < 0 or minimum < 0:
        raise ValueError("Quantidade e estoque mínimo não podem ser negativos.")
    return name, code, quantity, expiry, minimum


def classify_product(row, reference=None):
    reference = reference or date.today()
    expiry = date.fromisoformat(row["data_validade"])
    return {
        "expired": expiry < reference,
        "expiring": reference <= expiry <= reference + timedelta(days=7),
        "low": row["quantidade_atual"] <= row["estoque_minimo"],
        "days": (expiry - reference).days,
    }


def all_products():
    return get_db().execute("SELECT * FROM produtos ORDER BY nome COLLATE NOCASE").fetchall()


def products_with_status():
    return [(p, classify_product(p)) for p in all_products()]


@bp.get("/")
@login_required
def dashboard():
    products = products_with_status()
    counts = {
        "total": len(products),
        "expired": sum(1 for _, s in products if s["expired"]),
        "expiring": sum(1 for _, s in products if s["expiring"]),
        "low": sum(1 for _, s in products if s["low"]),
    }
    recent = get_db().execute("""
        SELECT m.*, p.nome AS produto, u.nome AS usuario FROM movimentacoes m
        JOIN produtos p ON p.id_produto=m.id_produto
        JOIN usuarios u ON u.id_usuario=m.id_usuario
        ORDER BY m.id_movimentacao DESC LIMIT 5
    """).fetchall()
    return render_template("dashboard.html", counts=counts, recent=recent)


@bp.route("/produtos", methods=["GET", "POST"])
@login_required
def products():
    if request.method == "POST":
        verify_csrf()
        try:
            values = validate_product(request.form)
            get_db().execute("""
                INSERT INTO produtos(nome, codigo, quantidade_atual, data_validade, estoque_minimo)
                VALUES (?, ?, ?, ?, ?)
            """, values)
            get_db().commit()
            flash("Produto cadastrado com sucesso.", "success")
            return redirect(url_for("inventory.products"))
        except ValueError as exc:
            flash(str(exc), "error")
        except sqlite3.IntegrityError:
            get_db().rollback()
            flash("Já existe um produto com esse código.", "error")
    return render_template("products.html", products=all_products())


@bp.route("/movimentacoes", methods=["GET", "POST"])
@login_required
def movements():
    selected = request.args.get("produto", "")
    if request.method == "POST":
        verify_csrf()
        try:
            product_id = int(request.form.get("id_produto", ""))
            quantity = int(request.form.get("quantidade", ""))
            movement_type = request.form.get("tipo", "")
            if quantity <= 0 or movement_type not in {"entrada", "saida"}:
                raise ValueError("Informe uma quantidade positiva e um tipo válido.")
            db = get_db()
            if movement_type == "saida":
                cursor = db.execute("""
                    UPDATE produtos SET quantidade_atual=quantidade_atual-?
                    WHERE id_produto=? AND quantidade_atual>=?
                """, (quantity, product_id, quantity))
                if cursor.rowcount == 0:
                    raise ValueError("Produto não encontrado ou quantidade insuficiente em estoque.")
            else:
                cursor = db.execute("""
                    UPDATE produtos SET quantidade_atual=quantidade_atual+?
                    WHERE id_produto=?
                """, (quantity, product_id))
                if cursor.rowcount == 0:
                    raise ValueError("Produto não encontrado.")
            db.execute("""
                INSERT INTO movimentacoes(id_produto, id_usuario, tipo, quantidade)
                VALUES (?, ?, ?, ?)
            """, (product_id, g.user["id_usuario"], movement_type, quantity))
            db.commit()
            flash("Movimentação registrada com sucesso.", "success")
            return redirect(url_for("inventory.movements", produto=product_id))
        except (TypeError, ValueError) as exc:
            get_db().rollback()
            flash(str(exc) if isinstance(exc, ValueError) else "Dados inválidos.", "error")
    return render_template("movements.html", products=all_products(), selected=selected)


@bp.get("/alertas")
@login_required
def alerts():
    selected_filter = request.args.get("tipo", "todos")
    if selected_filter not in {"todos", "vencidos", "proximos", "baixos"}:
        selected_filter = "todos"
    data = []
    for product, status in products_with_status():
        include = {
            "todos": any((status["expired"], status["expiring"], status["low"])),
            "vencidos": status["expired"],
            "proximos": status["expiring"],
            "baixos": status["low"],
        }[selected_filter]
        if include:
            data.append((product, status))
    return render_template("alerts.html", products=data, selected_filter=selected_filter)
