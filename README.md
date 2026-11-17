# Estoque Fácil — Mercado Firma

MVP acadêmico para cadastro de produtos, movimentações de entrada/saída e alertas de vencimento (até 7 dias), vencidos e estoque mínimo. Projeto vinculado ao **ODS 12 — Consumo e Produção Responsáveis**.

## Tecnologias

- Python 3.12, Flask 3.x, HTML, CSS e SQLite
- Hash de senha com Werkzeug, consultas SQL parametrizadas, CSRF e sessão de usuário
- pytest para testes unitários e de integração; GitHub Actions para CI

## Iniciar no Windows (PowerShell)

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
flask --app app init-db
flask --app app create-user
flask --app app run
```

Caso o PowerShell bloqueie a ativação, execute `.venv\Scripts\python.exe -m pip install -r requirements.txt` e, para os comandos, `.venv\Scripts\python.exe -m flask --app app init-db`, `.venv\Scripts\python.exe -m flask --app app create-user` e `.venv\Scripts\python.exe -m flask --app app run`.

No comando `create-user`, informe um usuário de teste e uma senha de pelo menos oito caracteres. **Não use senhas reais** em demonstrações. Abra http://127.0.0.1:5000.

## Executar testes

```powershell
python -m pytest -q
```

O arquivo `.github/workflows/testes.yml` executa automaticamente os testes ao receber `push` ou `pull_request` no GitHub.

## Estrutura

- `app.py`: aplicação Flask, configuração e criação de usuário via CLI
- `db.py` e `schema.sql`: SQLite e tabelas de usuários, produtos e movimentações
- `auth.py`: autenticação e proteção de formulários
- `inventory.py`: cadastro, consulta, entradas, saídas e alertas
- `templates/` e `static/`: telas responsivas e acessíveis
- `tests/`: testes automatizados

## Limites do MVP

A data de validade é armazenada por produto cadastrado (sem gestão de lotes). Uso local para fins acadêmicos; para publicar na internet são necessários HTTPS, hospedagem com dados persistentes e revisão adicional de segurança. O banco `instance/estoque.sqlite3` e a chave de sessão local **não** devem ser enviados ao GitHub.

As rodadas de validação com o representante do Mercado Firma devem ser registradas com evidências reais, sem dados pessoais sensíveis.
