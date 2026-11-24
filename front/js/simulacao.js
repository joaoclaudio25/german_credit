let ultimaEntrada = null;

const formRisco = document.getElementById("form-risco");
const botaoCalcular = document.getElementById("btn-calcular");
const estadoInicial = document.getElementById("estado-inicial");
const resultadoBox = document.getElementById("resultado-box");
const badgeRisco = document.getElementById("badge-risco");
const resultadoTexto = document.getElementById("resultado");
const probFill = document.getElementById("prob-fill");
const botaoSalvar = document.getElementById("btn-salvar");
const statusSalvo = document.getElementById("status-salvo");

function montarFormularioSimulacao() {
  for (const [campo, cfg] of Object.entries(CATEGORICAS)) {
    const label = criarElemento("label", cfg.titulo, "campo");
    const select = criarElemento("select");
    select.name = campo;
    for (const [codigo, texto] of Object.entries(cfg.opcoes)) {
      const opt = criarElemento("option", texto);
      opt.value = codigo;
      select.appendChild(opt);
    }
    label.appendChild(select);
    formRisco.insertBefore(label, botaoCalcular);
  }

  for (const [campo, cfg] of Object.entries(NUMERICAS)) {
    const label = criarElemento("label", cfg.titulo, "campo");
    const input = criarElemento("input");
    input.type = "number";
    input.name = campo;
    input.min = cfg.min;
    input.max = cfg.max;
    input.step = 1;
    input.value = cfg.valor;
    input.required = true;
    label.appendChild(input);
    formRisco.insertBefore(label, botaoCalcular);
  }
}

function lerEntrada() {
  const entrada = {};
  for (const campo of Object.keys(CATEGORICAS)) {
    entrada[campo] = formRisco.elements[campo].value;
  }
  for (const campo of Object.keys(NUMERICAS)) {
    entrada[campo] = Number(formRisco.elements[campo].value);
  }
  return entrada;
}

function mostrarResultado(dados) {
  const pct = dados.probabilidade_mau_pagador;
  estadoInicial.hidden = true;
  resultadoBox.hidden = false;
  resultadoTexto.textContent = formatarPercentual(pct);
  probFill.style.width = `${pct * 100}%`;
  badgeRisco.textContent = dados.mau_pagador ? "Risco alto" : "Risco baixo";
  badgeRisco.className = `badge ${dados.mau_pagador ? "badge-alto" : "badge-baixo"}`;
}

formRisco.addEventListener("submit", async (evento) => {
  evento.preventDefault();
  ultimaEntrada = lerEntrada();
  botaoSalvar.disabled = true;
  statusSalvo.textContent = "";
  botaoCalcular.disabled = true;
  try {
    const dados = await chamarApi("/api/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(ultimaEntrada),
    });
    mostrarResultado(dados);
    botaoSalvar.disabled = false;
  } catch (erro) {
    estadoInicial.hidden = false;
    resultadoBox.hidden = true;
    estadoInicial.textContent = erro.message;
  } finally {
    botaoCalcular.disabled = false;
  }
});

botaoSalvar.addEventListener("click", async () => {
  if (!ultimaEntrada) return;
  botaoSalvar.disabled = true;
  statusSalvo.textContent = "Salvando...";
  try {
    const dados = await chamarApi("/api/simulacoes", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(ultimaEntrada),
    });
    statusSalvo.textContent = `Salvo no histórico como registro nº ${dados.id}.`;
  } catch (erro) {
    statusSalvo.textContent = erro.message;
    botaoSalvar.disabled = false;
  }
});

montarFormularioSimulacao();
