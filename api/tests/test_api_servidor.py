"""Testes de integração: sobem a API em um servidor HTTP real, em segundo plano,
e fazem as requisições pela rede local, como o navegador faria.

Diferente do test_api.py (que usa o cliente de teste do Flask), aqui o teste
passa pelo servidor HTTP de verdade: porta, cabeçalhos, status e arquivos estáticos.
Não é preciso iniciar a aplicação manualmente.
"""
import json
import os
import tempfile
import threading
import urllib.error
import urllib.request

# Banco temporário para não gravar no histórico real. Definido antes de importar o app.
os.environ["SIMULACOES_DB"] = os.path.join(tempfile.mkdtemp(), "teste_servidor.db")

import pytest  # noqa: E402
from werkzeug.serving import make_server  # noqa: E402

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


@pytest.fixture(scope="module")
def servidor_url():
    """Sobe o servidor em uma porta livre, em uma thread, e o derruba ao final dos testes."""
    flask_app.config["TESTING"] = True
    servidor = make_server("127.0.0.1", 0, flask_app, threaded=True)
    thread = threading.Thread(target=servidor.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{servidor.server_port}"
    finally:
        servidor.shutdown()
        servidor.server_close()
        thread.join(timeout=5)


def chamar(url, metodo="GET", corpo=None):
    """Faz uma requisição HTTP e devolve (status, texto_da_resposta).

    Usa só a biblioteca padrão. Erros 4xx e 5xx não levantam exceção:
    o status e o corpo voltam normalmente para o teste verificar.
    """
    dados = None
    cabecalhos = {}
    if corpo is not None:
        dados = json.dumps(corpo).encode("utf-8")
        cabecalhos["Content-Type"] = "application/json"
    requisicao = urllib.request.Request(url, data=dados, method=metodo, headers=cabecalhos)
    try:
        with urllib.request.urlopen(requisicao, timeout=10) as resposta:
            return resposta.status, resposta.read().decode("utf-8")
    except urllib.error.HTTPError as erro:
        return erro.code, erro.read().decode("utf-8")


# ---------- Servidor e página ----------

def test_health_responde_200(servidor_url):
    status, corpo = chamar(f"{servidor_url}/health")
    assert status == 200
    assert json.loads(corpo) == {"status": "ok"}


def test_pagina_inicial_e_entregue_pelo_servidor(servidor_url):
    status, corpo = chamar(f"{servidor_url}/")
    assert status == 200
    assert "Risco de crédito" in corpo
    assert 'id="form-risco"' in corpo


@pytest.mark.parametrize("caminho", ["/css/style.css", "/js/comum.js", "/js/app.js"])
def test_arquivos_do_front_sao_servidos(servidor_url, caminho):
    status, _ = chamar(f"{servidor_url}{caminho}")
    assert status == 200


def test_rota_inexistente_retorna_404(servidor_url):
    status, _ = chamar(f"{servidor_url}/rota_que_nao_existe")
    assert status == 404


# ---------- Predição ----------

def test_predict_via_http_retorna_probabilidade(servidor_url):
    status, corpo = chamar(f"{servidor_url}/api/predict", "POST", EXEMPLO)
    assert status == 200
    dados = json.loads(corpo)
    assert 0 <= dados["probabilidade_mau_pagador"] <= 1
    assert isinstance(dados["mau_pagador"], bool)


def test_predict_com_categoria_invalida_retorna_400(servidor_url):
    status, corpo = chamar(f"{servidor_url}/api/predict", "POST", {**EXEMPLO, "purpose": "XYZ"})
    assert status == 400
    assert "aceitos" in json.loads(corpo)


def test_predict_sem_corpo_json_retorna_400(servidor_url):
    status, _ = chamar(f"{servidor_url}/api/predict", "POST", None)
    assert status == 400


# ---------- Histórico ----------

def test_salvar_listar_e_detalhar_via_http(servidor_url):
    status, corpo = chamar(f"{servidor_url}/api/simulacoes", "POST", EXEMPLO)
    assert status == 201
    sim_id = json.loads(corpo)["id"]

    status, corpo = chamar(f"{servidor_url}/api/simulacoes?limite=500")
    assert status == 200
    assert any(item["id"] == sim_id for item in json.loads(corpo))

    status, corpo = chamar(f"{servidor_url}/api/simulacoes/{sim_id}")
    assert status == 200
    assert json.loads(corpo)["entrada"]["credit_amount"] == 5000


def test_detalhe_inexistente_retorna_404(servidor_url):
    status, _ = chamar(f"{servidor_url}/api/simulacoes/999999")
    assert status == 404


# ---------- Base histórica ----------

def test_base_resumo_via_http(servidor_url):
    status, corpo = chamar(f"{servidor_url}/api/base/resumo")
    assert status == 200
    dados = json.loads(corpo)
    assert dados["total"] == 1000
    assert dados["maus"] == 300
