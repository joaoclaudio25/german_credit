const TAMANHO_PAGINA = 20;
let paginaAtual = 1;
let totalPaginas = 1;
let selectsPreenchidos = false;

const CAMPOS_TABELA = [
  "status_checking_account", "duration_months", "credit_history", "purpose",
  "credit_amount", "employment_since", "age", "credit_risk",
];
const CAMPOS_DISTRIBUICAO = ["duration_months", "credit_amount", "age"];

function preencherSelects() {
  if (selectsPreenchidos) return;
  const selectTaxa = document.getElementById("select-campo-taxa");
  for (const [campo, cfg] of Object.entries(CATEGORICAS)) {
    selectTaxa.appendChild(criarElemento("option", cfg.titulo)).value = campo;
  }

  const selectDist = document.getElementById("select-campo-dist");
  for (const campo of CAMPOS_DISTRIBUICAO) {
    selectDist.appendChild(criarElemento("option", NOMES_NUMERICOS[campo])).value = campo;
  }

  const selectFinalidade = document.getElementById("filtro-finalidade");
  selectFinalidade.appendChild(criarElemento("option", "Todas")).value = "";
  for (const [codigo, texto] of Object.entries(CATEGORICAS.purpose.opcoes)) {
    selectFinalidade.appendChild(criarElemento("option", texto)).value = codigo;
  }

  selectsPreenchidos = true;
}

async function carregarResumo() {
  const dados = await chamarApi("/api/base/resumo");
  const cards = document.getElementById("resumo-base");
  cards.replaceChildren();
  const itens = [
    ["Registros", dados.total],
    ["Bons pagadores", dados.bons],
    ["Maus pagadores", dados.maus],
    ["Taxa de maus pagadores", formatarPercentual(dados.taxa_mau)],
  ];
  for (const [rotulo, valor] of itens) {
    const card = criarElemento("div", null, "card");
    card.appendChild(criarElemento("span", rotulo, "card-rotulo"));
    card.appendChild(criarElemento("strong", valor));
    cards.appendChild(card);
  }
}

async function carregarTaxas() {
  const campo = document.getElementById("select-campo-taxa").value;
  const dados = await chamarApi(`/api/base/taxas?campo=${encodeURIComponent(campo)}`);
  const grafico = document.getElementById("grafico-taxas");
  grafico.replaceChildren();
  for (const item of dados.itens) {
    const linha = criarElemento("div", null, "barra-linha");
    linha.appendChild(criarElemento("span", rotuloCategoria(campo, item.categoria), "barra-rotulo"));
    const trilho = criarElemento("div", null, "barra-trilho");
    const preenchimento = criarElemento("div", null, "barra-preenchimento");
    preenchimento.style.width = `${item.taxa_mau * 100}%`;
    trilho.appendChild(preenchimento);
    linha.appendChild(trilho);
    linha.appendChild(criarElemento(
      "span",
      `${formatarPercentual(item.taxa_mau)} de ${item.quantidade} registros`,
      "barra-valor"
    ));
    grafico.appendChild(linha);
  }
}

async function carregarDistribuicao() {
  const campo = document.getElementById("select-campo-dist").value;
  const dados = await chamarApi(`/api/base/distribuicao?campo=${encodeURIComponent(campo)}&faixas=10`);
  const grafico = document.getElementById("grafico-dist");
  grafico.replaceChildren();
  const maximo = Math.max(...dados.itens.map((i) => i.bons + i.maus), 1);
  for (const item of dados.itens) {
    const linha = criarElemento("div", null, "barra-linha");
    linha.appendChild(criarElemento("span", item.faixa, "barra-rotulo"));
    const trilho = criarElemento("div", null, "barra-trilho");
    const bons = criarElemento("div", null, "barra-bons");
    bons.style.width = `${(item.bons / maximo) * 100}%`;
    const maus = criarElemento("div", null, "barra-maus");
    maus.style.width = `${(item.maus / maximo) * 100}%`;
    trilho.appendChild(bons);
    trilho.appendChild(maus);
    linha.appendChild(trilho);
    linha.appendChild(criarElemento("span", `${item.bons} bons · ${item.maus} maus`, "barra-valor"));
    grafico.appendChild(linha);
  }
}

function lerFiltros() {
  const params = new URLSearchParams();
  const finalidade = document.getElementById("filtro-finalidade").value;
  const risco = document.getElementById("filtro-risco").value;
  if (finalidade) params.set("finalidade", finalidade);
  if (risco !== "") params.set("risco", risco);
  for (const [id, nome] of [
    ["filtro-idade-min", "idade_min"],
    ["filtro-idade-max", "idade_max"],
    ["filtro-valor-min", "valor_min"],
    ["filtro-valor-max", "valor_max"],
  ]) {
    const valor = document.getElementById(id).value;
    if (valor !== "") params.set(nome, valor);
  }
  params.set("pagina", paginaAtual);
  params.set("tamanho", TAMANHO_PAGINA);
  return params;
}

async function carregarRegistros() {
  const dados = await chamarApi(`/api/base/registros?${lerFiltros()}`);
  totalPaginas = Math.max(1, Math.ceil(dados.total / TAMANHO_PAGINA));
  const tbody = document.querySelector("#tabela-registros tbody");
  tbody.replaceChildren();
  for (const item of dados.itens) {
    const tr = criarElemento("tr");
    for (const campo of CAMPOS_TABELA) {
      let valor = item[campo];
      if (campo === "credit_risk") valor = valor === 1 ? "Mau" : "Bom";
      else if (CATEGORICAS[campo]) valor = rotuloCategoria(campo, valor);
      tr.appendChild(criarElemento("td", valor));
    }
    tbody.appendChild(tr);
  }
  document.getElementById("info-pagina").textContent =
    `Página ${paginaAtual} de ${totalPaginas} (${dados.total} registros)`;
  document.getElementById("btn-anterior").disabled = paginaAtual <= 1;
  document.getElementById("btn-proxima").disabled = paginaAtual >= totalPaginas;
}

async function carregarBase() {
  try {
    preencherSelects();
    await Promise.all([carregarResumo(), carregarTaxas(), carregarDistribuicao(), carregarRegistros()]);
  } catch (erro) {
    alert(erro.message);
  }
}

document.getElementById("select-campo-taxa").addEventListener("change", () => {
  carregarTaxas().catch((erro) => alert(erro.message));
});
document.getElementById("select-campo-dist").addEventListener("change", () => {
  carregarDistribuicao().catch((erro) => alert(erro.message));
});
document.getElementById("form-filtros").addEventListener("submit", (evento) => {
  evento.preventDefault();
  paginaAtual = 1;
  carregarRegistros().catch((erro) => alert(erro.message));
});
document.getElementById("btn-limpar-filtros").addEventListener("click", () => {
  document.getElementById("form-filtros").reset();
  paginaAtual = 1;
  carregarRegistros().catch((erro) => alert(erro.message));
});
document.getElementById("btn-anterior").addEventListener("click", () => {
  if (paginaAtual > 1) {
    paginaAtual -= 1;
    carregarRegistros().catch((erro) => alert(erro.message));
  }
});
document.getElementById("btn-proxima").addEventListener("click", () => {
  if (paginaAtual < totalPaginas) {
    paginaAtual += 1;
    carregarRegistros().catch((erro) => alert(erro.message));
  }
});
