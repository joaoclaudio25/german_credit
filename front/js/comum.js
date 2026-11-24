// Rótulos dos códigos do dataset German Credit (valores monetários em DM, marco alemão).
const CATEGORICAS = {
  status_checking_account: {
    titulo: "Situação da conta corrente",
    opcoes: {
      A11: "Saldo negativo (menos de 0 DM)",
      A12: "Entre 0 e 200 DM",
      A13: "200 DM ou mais, ou salário depositado há pelo menos 1 ano",
      A14: "Sem conta corrente",
    },
  },
  credit_history: {
    titulo: "Histórico de crédito",
    opcoes: {
      A30: "Nenhum crédito, ou todos já pagos",
      A31: "Todos os créditos neste banco pagos em dia",
      A32: "Créditos existentes pagos em dia até agora",
      A33: "Atraso no pagamento no passado",
      A34: "Conta crítica ou outros créditos existentes (em outro banco)",
    },
  },
  purpose: {
    titulo: "Finalidade do crédito",
    opcoes: {
      A40: "Carro novo",
      A41: "Carro usado",
      A42: "Móveis ou equipamentos",
      A43: "Rádio ou TV",
      A44: "Eletrodomésticos",
      A45: "Reparos",
      A46: "Educação",
      A48: "Reciclagem profissional",
      A49: "Negócios",
      A410: "Outros",
    },
  },
  savings_account: {
    titulo: "Poupança ou aplicações",
    opcoes: {
      A61: "Menos de 100 DM",
      A62: "De 100 a 500 DM",
      A63: "De 500 a 1000 DM",
      A64: "1000 DM ou mais",
      A65: "Desconhecido ou sem poupança",
    },
  },
  employment_since: {
    titulo: "Tempo no emprego atual",
    opcoes: {
      A71: "Desempregado",
      A72: "Menos de 1 ano",
      A73: "De 1 a 4 anos",
      A74: "De 4 a 7 anos",
      A75: "7 anos ou mais",
    },
  },
};

const NUMERICAS = {
  duration_months: { titulo: "Prazo do empréstimo (meses)", min: 4, max: 72, valor: 24 },
  credit_amount: { titulo: "Valor do crédito (DM)", min: 250, max: 20000, valor: 5000 },
  age: { titulo: "Idade do solicitante", min: 18, max: 100, valor: 35 },
};

const NOMES_NUMERICOS = {
  duration_months: "Prazo (meses)",
  credit_amount: "Valor (DM)",
  age: "Idade",
};

function rotuloCategoria(campo, codigo) {
  const cfg = CATEGORICAS[campo];
  return (cfg && cfg.opcoes[codigo]) || codigo;
}

function criarElemento(tag, texto, classe) {
  const el = document.createElement(tag);
  if (texto !== undefined && texto !== null) el.textContent = texto;
  if (classe) el.className = classe;
  return el;
}

async function chamarApi(url, opcoes = {}) {
  const resposta = await fetch(url, opcoes);
  const json = await resposta.json().catch(() => ({}));
  if (!resposta.ok) {
    throw new Error(json.erro || `Erro ${resposta.status} ao acessar ${url}`);
  }
  return json;
}

function formatarPercentual(valor) {
  return `${(valor * 100).toFixed(1)}%`;
}
