// Navegação entre as abas do portal.
const botoesAba = document.querySelectorAll(".abas button");

botoesAba.forEach((botao) => {
  botao.addEventListener("click", () => {
    const alvo = botao.dataset.aba;
    document.querySelectorAll(".aba").forEach((secao) => {
      secao.hidden = secao.id !== alvo;
    });
    botoesAba.forEach((b) => b.classList.toggle("ativa", b === botao));

    if (alvo === "historico") carregarHistorico();
    if (alvo === "base") carregarBase();
  });
});
