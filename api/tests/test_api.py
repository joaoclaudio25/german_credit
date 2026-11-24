import os
import tempfile

# Banco temporário para os testes, definido antes de importar o app.
os.environ["SIMULACOES_DB"] = os.path.join(tempfile.mkdtemp(), "teste.db")

import pytest  # noqa: E402
from app import app as flask_app  # noqa: E402

EXEMPLO = {
    "status_checking_account": "A11",
    "duration_months": 24,
    "credit_history": "A32",
    "purpose": "A43",
    "credit_amount": 5000,
    "savings_account": "A61",
    "employment_since": "A73",
    "age": 35,
}


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c


# ---------- Página e predição ----------

def test_health(client):
    resposta = client.get("/health")
    assert resposta.status_code == 200
    assert resposta.get_json()["status"] == "ok"


def test_pagina_inicial(client):
    resposta = client.get("/")
    assert resposta.status_code == 200
    assert "form-risco" in resposta.get_data(as_text=True)


def test_predict_retorna_probabilidade(client):
    resposta = client.post("/api/predict", json=EXEMPLO)
    assert resposta.status_code == 200
    dados = resposta.get_json()
    assert 0 <= dados["probabilidade_mau_pagador"] <= 1
    assert isinstance(dados["mau_pagador"], bool)


def test_campo_faltando_retorna_400(client):
    dados = {k: v for k, v in EXEMPLO.items() if k != "age"}
    resposta = client.post("/api/predict", json=dados)
    assert resposta.status_code == 400
    assert "age" in resposta.get_json()["campos"]


def test_categoria_invalida_retorna_400(client):
    resposta = client.post("/api/predict", json={**EXEMPLO, "purpose": "XYZ"})
    assert resposta.status_code == 400


def test_numero_invalido_retorna_400(client):
    resposta = client.post("/api/predict", json={**EXEMPLO, "age": "trinta"})
    assert resposta.status_code == 400


# ---------- Simulações salvas ----------

def test_salvar_e_consultar_simulacao(client):
    salvo = client.post("/api/simulacoes", json=EXEMPLO)
    assert salvo.status_code == 201
    dados_salvos = salvo.get_json()
    sim_id = dados_salvos["id"]

    lista = client.get("/api/simulacoes").get_json()
    assert any(item["id"] == sim_id for item in lista)

    detalhe = client.get(f"/api/simulacoes/{sim_id}").get_json()
    assert detalhe["entrada"]["purpose"] == "A43"
    assert detalhe["probabilidade_mau_pagador"] == dados_salvos["probabilidade_mau_pagador"]


def test_simulacao_inexistente_retorna_404(client):
    assert client.get("/api/simulacoes/999999").status_code == 404


def test_salvar_simulacao_invalida_retorna_400(client):
    resposta = client.post("/api/simulacoes", json={**EXEMPLO, "age": "x"})
    assert resposta.status_code == 400


# ---------- Base histórica ----------

def test_resumo_base(client):
    dados = client.get("/api/base/resumo").get_json()
    assert dados["total"] == 1000
    assert dados["maus"] == 300
    assert dados["bons"] + dados["maus"] == dados["total"]


def test_taxas_campo_invalido_retorna_400(client):
    assert client.get("/api/base/taxas?campo=nao_existe").status_code == 400


def test_taxas_por_categoria(client):
    dados = client.get("/api/base/taxas?campo=status_checking_account").get_json()
    assert len(dados["itens"]) == 4
    assert sum(item["quantidade"] for item in dados["itens"]) == 1000


def test_distribuicao_soma_todos_os_registros(client):
    dados = client.get("/api/base/distribuicao?campo=credit_amount&faixas=8").get_json()
    total = sum(item["bons"] + item["maus"] for item in dados["itens"])
    assert total == 1000


def test_registros_filtro_risco(client):
    dados = client.get("/api/base/registros?risco=1&tamanho=200").get_json()
    assert dados["total"] == 300
    assert all(item["credit_risk"] == 1 for item in dados["itens"])


def test_registros_paginacao(client):
    dados = client.get("/api/base/registros?pagina=2&tamanho=10").get_json()
    assert dados["pagina"] == 2
    assert len(dados["itens"]) == 10
