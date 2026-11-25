import json
import os
import sqlite3
from contextlib import closing
from datetime import datetime

import joblib
import pandas as pd
from flask import Flask, jsonify, request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONT_DIR = os.path.join(BASE_DIR, "..", "front")
MODEL_PATH = os.path.join(BASE_DIR, "model", "modelo_risco_credito.joblib")
CSV_PATH = os.path.join(BASE_DIR, "..", "MachineLearning", "data", "german_credit.csv")
DB_PATH = os.environ.get("SIMULACOES_DB", os.path.join(BASE_DIR, "data", "simulacoes.db"))

app = Flask(__name__, static_folder=FRONT_DIR, static_url_path="")

model = joblib.load(MODEL_PATH)
base = pd.read_csv(CSV_PATH)

FEATURES_CAT = ["status_checking_account", "credit_history", "purpose",
                "savings_account", "employment_since"]
FEATURES_NUM = ["duration_months", "credit_amount", "age"]
FEATURES = FEATURES_CAT + FEATURES_NUM

# Códigos aceitos para cada categórica (códigos do dataset German Credit).
# Ficam fixos aqui, e não lidos do modelo, para a API não depender da estrutura interna do pipeline.
CATEGORIAS_VALIDAS = {
    "status_checking_account": {"A11", "A12", "A13", "A14"},
    "credit_history": {"A30", "A31", "A32", "A33", "A34"},
    "purpose": {"A40", "A41", "A410", "A42", "A43", "A44", "A45", "A46", "A48", "A49"},
    "savings_account": {"A61", "A62", "A63", "A64", "A65"},
    "employment_since": {"A71", "A72", "A73", "A74", "A75"},
}

CAMPOS_BASE_CATEGORICOS = [c for c in base.columns if not pd.api.types.is_numeric_dtype(base[c])]
CAMPOS_BASE_NUMERICOS = [c for c in base.select_dtypes(include="number").columns
                         if c != "credit_risk"]

LIMITE = 0.5  # probabilidade acima deste valor é classificada como mau pagador


# ---------- Banco de simulações ----------

def conectar():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conexao = sqlite3.connect(DB_PATH)
    conexao.row_factory = sqlite3.Row
    return conexao


def iniciar_banco():
    with closing(conectar()) as conexao, conexao:
        conexao.execute(
            """
            CREATE TABLE IF NOT EXISTS simulacoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                criado_em TEXT NOT NULL,
                entrada TEXT NOT NULL,
                probabilidade REAL NOT NULL,
                mau_pagador INTEGER NOT NULL
            )
            """
        )


iniciar_banco()


def serializar_simulacao(linha):
    return {
        "id": linha["id"],
        "criado_em": linha["criado_em"],
        "entrada": json.loads(linha["entrada"]),
        "probabilidade_mau_pagador": linha["probabilidade"],
        "mau_pagador": bool(linha["mau_pagador"]),
    }


# ---------- Predição ----------

def validar_entrada(dados):
    """Devolve (entrada_limpa, None) ou (None, (corpo_do_erro, status))."""
    if not isinstance(dados, dict):
        return None, ({"erro": "Envie um JSON com as 8 features."}, 400)

    faltando = [campo for campo in FEATURES if campo not in dados]
    if faltando:
        return None, ({"erro": "Campos faltando.", "campos": faltando}, 400)

    entrada = {}
    for campo in FEATURES_NUM:
        try:
            entrada[campo] = float(dados[campo])
        except (TypeError, ValueError):
            return None, ({"erro": f"O campo '{campo}' precisa ser numérico."}, 400)

    for campo in FEATURES_CAT:
        valor = dados[campo]
        if not isinstance(valor, str) or valor not in CATEGORIAS_VALIDAS[campo]:
            return None, ({
                "erro": f"Valor inválido para '{campo}'.",
                "aceitos": sorted(CATEGORIAS_VALIDAS[campo]),
            }, 400)
        entrada[campo] = valor

    return entrada, None


def calcular(entrada):
    prob = float(model.predict_proba(pd.DataFrame([entrada]))[0, 1])
    return {
        "probabilidade_mau_pagador": round(prob, 4),
        "mau_pagador": prob >= LIMITE,
    }


@app.get("/")
def index():
    return app.send_static_file("index.html")


@app.get("/health")
def health():
    return jsonify(status="ok")


@app.post("/api/predict")
def predict():
    entrada, erro = validar_entrada(request.get_json(silent=True))
    if erro:
        return jsonify(erro[0]), erro[1]
    return jsonify(calcular(entrada))


# ---------- Simulações salvas ----------

@app.post("/api/simulacoes")
def salvar_simulacao():
    entrada, erro = validar_entrada(request.get_json(silent=True))
    if erro:
        return jsonify(erro[0]), erro[1]

    resultado = calcular(entrada)
    criado_em = datetime.now().isoformat(timespec="seconds")
    with closing(conectar()) as conexao, conexao:
        cursor = conexao.execute(
            "INSERT INTO simulacoes (criado_em, entrada, probabilidade, mau_pagador) "
            "VALUES (?, ?, ?, ?)",
            (
                criado_em,
                json.dumps(entrada, ensure_ascii=False),
                resultado["probabilidade_mau_pagador"],
                int(resultado["mau_pagador"]),
            ),
        )
        novo_id = cursor.lastrowid

    return jsonify(id=novo_id, criado_em=criado_em, **resultado), 201


@app.get("/api/simulacoes")
def listar_simulacoes():
    limite = max(1, min(request.args.get("limite", default=50, type=int), 500))
    with closing(conectar()) as conexao:
        linhas = conexao.execute(
            "SELECT * FROM simulacoes ORDER BY id DESC LIMIT ?", (limite,)
        ).fetchall()
    return jsonify([serializar_simulacao(l) for l in linhas])


@app.get("/api/simulacoes/<int:sim_id>")
def detalhar_simulacao(sim_id):
    with closing(conectar()) as conexao:
        linha = conexao.execute(
            "SELECT * FROM simulacoes WHERE id = ?", (sim_id,)
        ).fetchone()
    if linha is None:
        return jsonify(erro="Simulação não encontrada."), 404
    return jsonify(serializar_simulacao(linha))


# ---------- Base histórica ----------

@app.get("/api/base/resumo")
def resumo_base():
    total = len(base)
    maus = int(base["credit_risk"].sum())
    return jsonify(total=total, bons=total - maus, maus=maus,
                   taxa_mau=round(maus / total, 4))


@app.get("/api/base/taxas")
def taxas_por_categoria():
    campo = request.args.get("campo", "")
    if campo not in CAMPOS_BASE_CATEGORICOS:
        return jsonify(erro="Campo categórico inválido.",
                       aceitos=CAMPOS_BASE_CATEGORICOS), 400

    agrupado = base.groupby(campo)["credit_risk"].agg(["count", "mean"])
    itens = [
        {
            "categoria": categoria,
            "quantidade": int(linha["count"]),
            "taxa_mau": round(float(linha["mean"]), 4),
        }
        for categoria, linha in agrupado.iterrows()
    ]
    return jsonify(campo=campo, itens=itens)


@app.get("/api/base/distribuicao")
def distribuicao():
    campo = request.args.get("campo", "")
    if campo not in CAMPOS_BASE_NUMERICOS:
        return jsonify(erro="Campo numérico inválido.",
                       aceitos=CAMPOS_BASE_NUMERICOS), 400

    faixas = max(3, min(request.args.get("faixas", default=10, type=int), 30))
    cortes = pd.cut(base[campo], bins=faixas, include_lowest=True)
    tabela = pd.crosstab(cortes, base["credit_risk"])
    itens = [
        {
            "faixa": str(faixa),
            "bons": int(linha.get(0, 0)),
            "maus": int(linha.get(1, 0)),
        }
        for faixa, linha in tabela.iterrows()
    ]
    return jsonify(campo=campo, itens=itens)


@app.get("/api/base/registros")
def registros():
    df = base

    risco = request.args.get("risco", type=int)
    if risco in (0, 1):
        df = df[df["credit_risk"] == risco]

    finalidade = request.args.get("finalidade")
    if finalidade:
        df = df[df["purpose"] == finalidade]

    filtros_numericos = [
        ("idade_min", "age", ">="),
        ("idade_max", "age", "<="),
        ("valor_min", "credit_amount", ">="),
        ("valor_max", "credit_amount", "<="),
    ]
    for nome, coluna, operador in filtros_numericos:
        valor = request.args.get(nome, type=float)
        if valor is None:
            continue
        df = df[df[coluna] >= valor] if operador == ">=" else df[df[coluna] <= valor]

    pagina = max(1, request.args.get("pagina", default=1, type=int))
    tamanho = max(1, min(request.args.get("tamanho", default=50, type=int), 200))
    inicio = (pagina - 1) * tamanho
    trecho = df.iloc[inicio:inicio + tamanho]

    return jsonify(
        total=len(df),
        pagina=pagina,
        tamanho=tamanho,
        itens=json.loads(trecho.to_json(orient="records")),
    )


if __name__ == "__main__":
    app.run(debug=True)
