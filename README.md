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
