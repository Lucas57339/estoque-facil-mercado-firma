from datetime import date, timedelta
from inventory import classify_product, validate_product
from db import get_db


def test_estoque_baixo_e_validade_proxima():
    today = date(2026, 11, 16)
    row = {"data_validade": "2026-11-20", "quantidade_atual": 3, "estoque_minimo": 5}
    state = classify_product(row, today)
    assert state["expiring"] is True
    assert state["low"] is True
    assert state["expired"] is False
    assert state["days"] == 4


def test_validade_vencida():
    state = classify_product({"data_validade": "2026-11-14", "quantidade_atual": 7, "estoque_minimo": 3}, date(2026, 11, 16))
    assert state["expired"] is True
    assert state["expiring"] is False


def test_quantidade_invalida():
    try:
        validate_product({"nome": "Leite", "codigo": "101", "quantidade_atual": "-1", "data_validade": "2026-11-20", "estoque_minimo": "2"})
        assert False, "Era esperado erro de validação"
    except ValueError as exc:
        assert "negativos" in str(exc)


def test_acesso_exige_login(client):
    response = client.get("/")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_csrf_obrigatorio(logged_client):
    response = logged_client.post("/produtos", data={"nome": "Leite"})
    assert response.status_code == 400


def test_cadastro_duplicado_e_movimentacao_sem_saldo(app, logged_client):
    expiry = (date.today() + timedelta(days=3)).isoformat()
    product = {"nome": "Iogurte Natural 170g", "codigo": "1001", "quantidade_atual": "20", "data_validade": expiry, "estoque_minimo": "5", "csrf_token": "test-csrf-token"}
    response = logged_client.post("/produtos", data=product, follow_redirects=True)
    assert "Produto cadastrado com sucesso".encode() in response.data

    response = logged_client.post("/produtos", data=product, follow_redirects=True)
    assert "Já existe um produto".encode() in response.data

    response = logged_client.post("/movimentacoes", data={"id_produto": "1", "tipo": "saida", "quantidade": "3", "csrf_token": "test-csrf-token"}, follow_redirects=True)
    assert "Movimentação registrada".encode() in response.data
    with app.app_context():
        count = get_db().execute("SELECT quantidade_atual FROM produtos WHERE id_produto=1").fetchone()[0]
        assert count == 17

    response = logged_client.post("/movimentacoes", data={"id_produto": "1", "tipo": "saida", "quantidade": "99", "csrf_token": "test-csrf-token"}, follow_redirects=True)
    assert "quantidade insuficiente".encode() in response.data
    with app.app_context():
        count = get_db().execute("SELECT quantidade_atual FROM produtos WHERE id_produto=1").fetchone()[0]
        assert count == 17
        num_movements = get_db().execute("SELECT COUNT(*) FROM movimentacoes").fetchone()[0]
        assert num_movements == 1

    response = logged_client.get("/alertas?tipo=proximos")
    assert response.status_code == 200
    assert "Iogurte Natural".encode() in response.data
