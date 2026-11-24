<<<<<<< HEAD
# Risco de crédito – classificação de inadimplência

MVP da disciplina **Engenharia de Software para Sistemas Inteligentes**.

O projeto classifica solicitantes de crédito como **bons pagadores (0)** ou **maus pagadores (1)**, a partir de 8 atributos do dataset German Credit. Ele tem três partes: um notebook de treino (Google Colab), uma API Flask que usa o modelo treinado e um portal web para uso pela equipe.

> **Atribuição de dados:** dataset *Statlog (German Credit Data)*, Hans Hofmann, UCI Machine Learning Repository, licença CC BY 4.0. DOI: [10.24432/C5NC77](https://doi.org/10.24432/C5NC77).

---

## 1. Arquitetura

```
 GitHub (german_credit.csv)
          │
          ▼
 Google Colab ── MachineLearning/treino.ipynb
          │
          │ exporta o pipeline completo
          ▼
 api/model/modelo_risco_credito.joblib
          │
          ▼
 API Flask (api/app.py) ◄──────────► Portal web (front/: HTML, CSS, JS)
          │                              │
          ├── SQLite (api/data/simulacoes.db)   histórico de simulações salvas
          └── CSV da base (MachineLearning/data) aba "Base histórica"
```

| Componente | Responsabilidade |
|---|---|
| `MachineLearning/treino.ipynb` | Carga, pré-processamento, modelagem, otimização, avaliação e exportação do modelo. |
| `api/model/` | Pipeline treinado (`prep` + `clf`), carregado uma vez na inicialização da API. |
| `api/app.py` | Endpoints de predição, de histórico e da base histórica. Também entrega o portal. |
| `api/data/simulacoes.db` | Banco SQLite com as simulações que o usuário decidiu salvar. Criado automaticamente. |
| `front/` | Portal em HTML, CSS e JavaScript puro, com três abas: calcular, histórico e base histórica. |

**Decisões de arquitetura**

- O **pipeline completo** (codificação, padronização e modelo) é salvo em um único arquivo. A API envia os valores originais, e a transformação é a mesma do treino.
- A API e o portal estão no mesmo servidor, então não há problemas de CORS.
- O histórico só é gravado quando o usuário clica em "Salvar no histórico". Cada registro guarda a data e todos os dados usados no cálculo.

---

## 2. Estrutura do projeto

```
mvp-risco-credito/
├── README.md
├── requirements.txt
├── pytest.ini
├── .gitignore
├── MachineLearning/
│   ├── treino.ipynb            # notebook de treino (executar no Colab)
│   ├── README.md
│   └── data/
│       └── german_credit.csv   # cópia local do dataset (a API lê daqui)
├── api/
│   ├── app.py                  # API Flask
│   ├── model/
│   │   └── modelo_risco_credito.joblib
│   ├── data/                   # criado na primeira execução (SQLite)
│   └── tests/
│       └── test_api.py
└── front/
    ├── index.html
    ├── css/style.css
    └── js/                     # comum.js, simulacao.js, historico.js, base.js, app.js
```

---

## 3. Requisitos técnicos

**Para o notebook (Colab)**

- Navegador e conta Google.
- Conexão com a internet, porque o CSV é lido do GitHub.
- CPU padrão do Colab. Não é preciso GPU.
- Bibliotecas já instaladas no Colab: `scikit-learn`, `pandas`, `numpy`, `matplotlib` e `joblib`.

**Para a aplicação local**

- Python **3.12** ou **3.13**. O projeto foi testado com Python 3.12.10 no Windows.
- Versão do scikit-learn: **1.6.1**, fixada em `requirements.txt`. Esta é a versão do modelo que está em `api/model/`.
- Demais dependências em `requirements.txt`: `flask`, `pandas`, `joblib`, `pytest`.
- Navegador moderno (Chrome, Edge ou Firefox).

> **Atenção à versão do scikit-learn.** Um modelo salvo com uma versão só carrega em uma versão compatível. A seção 1 do notebook imprime a versão usada no Colab. Se você exportar um novo modelo a partir do Colab para usá-lo na API, alinhe a versão em `requirements.txt` com a impressa e rode os testes de novo.

---

## 4. Como o professor valida o notebook no Colab

O notebook deve rodar do início ao fim, sem erros, em um ambiente limpo.

**Passo a passo**

1. Abra o notebook `MachineLearning/treino.ipynb` no Colab. Pode ser pelo link do repositório ou em **Arquivo → Fazer upload de notebook**.
2. Reinicie o ambiente para garantir um estado limpo: **Ambiente de execução → Redefinir ambiente de execução**.
3. Execute tudo: **Ambiente de execução → Executar tudo**.
4. Aguarde cerca de 1 a 2 minutos. Nenhuma célula deve parar com erro (mensagem vermelha).
5. Confira os resultados esperados, seção por seção:

| Seção | O que deve aparecer |
|---|---|
| 1. Preparação | Versões do scikit-learn e do pandas. |
| 2. Carga | `Linhas e colunas: (1000, 21)` e as 5 primeiras linhas. |
| 3. Exploração | Nenhum valor nulo. 700 bons e 300 maus. |
| 5. Holdout | Treino com 800 linhas e teste com 200. Proporção de maus de 0,3 nos dois. |
| 6. Transformação | 8 atributos viram 32 colunas após a codificação e a padronização. |
| 8. Modelagem | Tabela com ROC AUC, acurácia, precisão, recall, F1 e desvio para os 5 modelos. |
| 9. Otimização | Uma linha por modelo com o melhor ROC AUC na validação e os hiperparâmetros escolhidos. |
| 10. Avaliação | Tabela de métricas no teste e contagem de acertos e erros de cada modelo. |
| 11. Comparação | Dois gráficos: curvas ROC e barras de validação x teste. |
| 12. Exportação | `Modelo escolhido pela validação cruzada: SVM` e a mensagem de arquivo salvo. |
| 13. Teste do modelo | `Idênticas: True` e as etapas `['prep', 'clf']`. |

**Valores de referência** (execução de controle, com scikit-learn 1.9.1):

- Validação cruzada, após otimização: SVM 0,792, Naive Bayes 0,772, regressão logística 0,770, KNN 0,766 e árvore 0,729.
- Teste (ROC AUC): regressão logística 0,817, Naive Bayes 0,801, SVM 0,797, KNN 0,779 e árvore 0,732.

Pequenas diferenças são esperadas entre versões do scikit-learn. A ordem geral dos resultados deve se manter. A semente fixa (`SEED = 42`) faz com que, na mesma versão, os números sejam sempre os mesmos.

**Se o GitHub estiver indisponível:** faça o upload do arquivo `german_credit.csv` no painel de arquivos do Colab e troque a variável `URL` na seção 2 por `"german_credit.csv"`.

---

## 5. Como executar a aplicação localmente

Na pasta `mvp-risco-credito`:

**Windows (PowerShell)**

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pytest
python api\app.py
```

**Linux ou macOS**

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest
python api/app.py
```

Depois de iniciar, abra `http://127.0.0.1:5000/` no navegador.

Os testes do PyTest verificam os endpoints da API, o histórico de simulações e a base histórica. Eles criam um banco SQLite temporário, então não alteram o histórico real.

---

## 6. Portal

- **Calcular risco:** preencha os dados do solicitante e calcule. O resultado mostra a probabilidade de inadimplência e a classificação. O botão **Salvar no histórico** só fica disponível depois do cálculo.
- **Histórico:** cada simulação salva aparece como um cartão, com data, todos os dados usados e a probabilidade.
- **Base histórica:** resumo do dataset, taxa de maus pagadores por categoria, distribuição de valor, prazo e idade, e uma tabela da base com filtros e paginação.

O portal não tem login. Quem tiver acesso ao endereço do servidor pode ver o histórico. Use o projeto em rede local ou em ambiente controlado.

---

## 7. Endpoints da API

| Método | Rota | Descrição |
|---|---|---|
| GET | `/` | Portal web. |
| GET | `/health` | Verificação de funcionamento. |
| POST | `/api/predict` | Calcula a probabilidade sem salvar. |
| POST | `/api/simulacoes` | Calcula e salva a simulação no histórico. |
| GET | `/api/simulacoes?limite=N` | Lista as simulações salvas, da mais recente. |
| GET | `/api/simulacoes/<id>` | Detalha uma simulação salva. |
| GET | `/api/base/resumo` | Totais de bons e maus pagadores. |
| GET | `/api/base/taxas?campo=` | Taxa de maus pagadores por categoria. |
| GET | `/api/base/distribuicao?campo=&faixas=` | Distribuição de um atributo numérico por classe. |
| GET | `/api/base/registros` | Registros da base com filtros e paginação. |

Exemplo de corpo para `POST /api/predict`:

```json
{
  "status_checking_account": "A11",
  "duration_months": 24,
  "credit_history": "A32",
  "purpose": "A43",
  "credit_amount": 5000,
  "savings_account": "A61",
  "employment_since": "A73",
  "age": 35
}
```

---

## 8. Atendimento ao item 2 do enunciado

| Exigência | Onde está no notebook |
|---|---|
| Carga dos dados | Seções 2 e 3 |
| Separação entre treino e teste (*holdout*) | Seção 5 |
| Transformação dos dados (normalização e padronização) | Seção 6 |
| Modelagem com KNN, árvore de classificação, Naive Bayes e SVM | Seção 8 |
| Otimização de hiperparâmetros | Seção 9 |
| Avaliação e comparação dos modelos | Seções 10 e 11 |
| Exportação do modelo resultante | Seções 12 e 13 |
| Uso de validação cruzada (recomendado) | Seção 7, usada nas seções 8 e 9 |
| Uso de pipelines (recomendado) | Seção 6, função `criar_pipeline` |

---

## 9. Principais achados

- **A conta corrente é o sinal mais forte.** Só essa variável, com a taxa de maus pagadores por categoria, já dá ROC AUC de 0,743 no teste.
- **Os modelos aprendem mais que essa regra simples,** mas o ganho é modesto. O melhor ROC AUC no teste foi de 0,817.
- **A otimização de hiperparâmetros ajudou,** sobretudo o Naive Bayes, que subiu de 0,709 para 0,772 na validação cruzada.
- **A árvore de decisão foi a mais fraca,** com ROC AUC de 0,732 no teste.

---

## 10. Pontos de atenção e limitações

- **As diferenças entre os três melhores modelos estão dentro da margem de erro.** O teste tem apenas 60 maus pagadores, e o desvio-padrão da ROC AUC entre as partições é de cerca de 0,04. A escolha do SVM foi feita pela validação cruzada, que usa mais dados, e não pelo resultado do teste.
- **O limiar de 0,5 não é adequado para o SVM.** No teste, o SVM detecta apenas 45% dos maus pagadores com esse limiar, contra 78% da regressão logística. A ordenação de risco é boa, mas o limiar precisa refletir o custo de cada tipo de erro. Essa é uma decisão de negócio.
- **Atributos sensíveis foram excluídos** (`personal_status_sex` e `foreign_worker`). Isso evita discriminação por sexo ou nacionalidade, mas pode reduzir um pouco o desempenho. A decisão deve constar na documentação de uso.
- **A base é antiga e pequena.** Os dados são de 1994, com 1000 registros, em marco alemão. Um uso real exigiria dados atuais e validação em produção.
- **Não há autenticação no portal,** e o histórico contém dados financeiros de solicitantes. Para uso fora de um ambiente controlado, é preciso adicionar login e tratar esses dados conforme a LGPD.
- **O modelo na API ainda é o da regressão logística,** exportado nas etapas anteriores. Para usar o SVM na aplicação, rode o notebook, copie o arquivo exportado para `api/model/` e alinhe a versão do scikit-learn.

---

## 11. Referências

- Hofmann, H. (1994). *Statlog (German Credit Data)*. UCI Machine Learning Repository. https://doi.org/10.24432/C5NC77
- UCI Machine Learning Repository, dataset 144: https://archive.ics.uci.edu/dataset/144/statlog+german+credit+data
- Documentação do scikit-learn: https://scikit-learn.org/stable/
=======
# German Credit Data (Statlog)

Cópia em CSV, com cabeçalho e alvo binário, do dataset **Statlog (German Credit Data)** da UCI Machine Learning Repository.

- **Fonte:** Hofmann, H. (1994). Statlog (German Credit Data). UCI Machine Learning Repository. https://doi.org/10.24432/C5NC77
- **Licença:** CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Ao reutilizar, dê o crédito acima.
- **Registros:** 1.000 solicitações de crédito, 20 atributos e 1 alvo.

## Arquivo

`german_credit.csv`: versão do arquivo original `german.data` com as seguintes mudanças:

- Cabeçalho com nomes de colunas em inglês.
- Código original do alvo convertido: `credit_risk = 1` para mau pagador (classe original 2), `credit_risk = 0` para bom pagador (classe original 1).
- Os valores categóricos foram mantidos com os códigos originais (por exemplo, `A11`). A descrição de cada código está no documento original da UCI.

## Matriz de custo

A UCI indica que classificar um mau pagador como bom custa 5 vezes mais do que o inverso (custo 5 contra custo 1).

## Observação

A versão Statlog tem erros de codificação relatados na própria UCI. Este repositório não corrige esses erros.
>>>>>>> fa4b8313539ba85fb524ce1195387ca393f0aaf5
