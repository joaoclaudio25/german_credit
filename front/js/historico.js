const listaHistorico = document.getElementById("lista-historico");

function criarCardSimulacao(sim) {
  const card = criarElemento("article", null, "card sim-card");

  const topo = criarElemento("div", null, "sim-topo");
  topo.appendChild(criarElemento(
    "span",
    `#${sim.id} · ${new Date(sim.criado_em).toLocaleString("pt-BR")}`,
    "sim-data"
  ));
  const badge = criarElemento("span", sim.mau_pagador ? "Risco alto" : "Risco baixo",
    `badge ${sim.mau_pagador ? "badge-alto" : "badge-baixo"}`);
  topo.appendChild(badge);
  card.appendChild(topo);

  const lista = criarElemento("dl", null, "detalhe");
  for (const [campo, cfg] of Object.entries(CATEGORICAS)) {
    lista.appendChild(criarElemento("dt", cfg.titulo));
    lista.appendChild(criarElemento("dd", rotuloCategoria(campo, sim.entrada[campo])));
  }
  for (const [campo, nome] of Object.entries(NOMES_NUMERICOS)) {
    lista.appendChild(criarElemento("dt", nome));
    lista.appendChild(criarElemento("dd", sim.entrada[campo]));
  }
  card.appendChild(lista);

  const rodape = criarElemento("div", null, "sim-rodape");
  rodape.appendChild(criarElemento("span", "Probabilidade de inadimplência"));
  rodape.appendChild(criarElemento("strong", formatarPercentual(sim.probabilidade_mau_pagador)));
  card.appendChild(rodape);

  return card;
}

async function carregarHistorico() {
  listaHistorico.replaceChildren();
  try {
    const simulacoes = await chamarApi("/api/simulacoes?limite=100");
    if (simulacoes.length === 0) {
      listaHistorico.appendChild(criarElemento("p", "Nenhuma simulação salva ainda.", "vazio"));
      return;
    }
    for (const sim of simulacoes) {
      listaHistorico.appendChild(criarCardSimulacao(sim));
    }
  } catch (erro) {
    alert(erro.message);
  }
}

document.getElementById("btn-atualizar-historico").addEventListener("click", carregarHistorico);
