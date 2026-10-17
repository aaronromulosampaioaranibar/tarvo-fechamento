# Hipóteses, perguntas e decisões

Três seções: o que o financeiro **respondeu** (com autor e horário, porque o canal é público e a
resposta vale para todos), o que ele **delegou** para nós decidirmos, e o que ainda é **premissa**.

Toda decisão delegada está escrita aqui com o motivo, que foi o que a Helena pediu:
*"Escolham um critério e escrevam qual."*

---

## A. Respondido pelo financeiro — vira regra no código

| # | Regra | Onde está no código | Fonte |
|---|---|---|---|
| A1 | **A comissão é `valor_bruto × taxa CONTRATADA`, não o `valor_taxa` que a Orbe aplicou.** A taxa inteira, sem desconto de custo da adquirente. | `fechamento.checkout()` | resposta à Fox AI, 16/10 22h34 |
| A2 | Arredondamento comum para o centavo, **meio centavo para cima, inclusive no negativo** (−0,005 → −0,01). **Linha por linha, depois soma.** A Orbe trunca; a Tarvo não. | `comum.n2()` | Fox AI, 16/10 21h13 |
| A3 | Divergência = `valor_bruto × (taxa aplicada − taxa contratada)`. Diferença de centavo pelo truncamento da Orbe **não** é divergência. | `divergencias_checkout()` | Fox AI, 16/10 21h13 |
| A4 | Estorno abate a comissão **do mês do estorno**, pela **taxa da data da venda original**. Agosto não reabre. A faixa (modalidade/parcelas) sai da própria linha do estorno. | `checkout()`, campo `_dref` | MN AI 16/10 20h06; Southlands 17/10 11h38 |
| A5 | Antecipação entra na **mesma nota** do checkout; a reversão anula a taxa da antecipação que ela reverte. | `checkout()` | MN AI, 16/10 20h47 |
| A6 | Comissão do mês **zero ou negativa: não emite nota**, vira pendência para o financeiro. O negativo não passa para o mês seguinte. | `notas()` | MN AI, 16/10 20h47 |
| A7 | **Casa do Estudante: tarifa zerada de set a dez/2026**, MDR e antecipação. A Orbe não foi avisada e cobrou pela tabela. | `cadastro/condicoes_especiais.csv` | Lucca Landeiro, 16/10 20h49 |
| A8 | A isenção vale **por data da venda, a partir de 01/09/2026**. Estorno de venda anterior segue a taxa da venda. | `Cadastro.condicao()` | Mateus 17/10 9h44; Prime 17/10 11h41 |
| A9 | **O que decide se cobramos da contraparte é o contrato, não o aviso.** Bridge e Mundo Aberto têm condição contratada: é divergência, contesta-se e o lojista é ressarcido. A Casa é concessão fora do contrato: a devolução sai do bolso da Tarvo. | `natureza` = CONTRATO ou ISENCAO | Theo Garcia, 17/10 11h37 |
| A10 | Remessa: comissão é **50% do `Spread R$` realizado**. Spread "padrão" ou em branco = **1,5%** sobre a PTAX. | `comum.PARTICIPACAO_SPREAD`, `SPREAD_PADRAO_PCT` | MN AI, 16/10 20h48 |
| A11 | **Spread negativo não é aceito**: a trava vale 2h por contrato e essas passaram do prazo. Fica fora da comissão e da nota, e vira contestação. | `INCLUI_SPREAD_NEGATIVO = False` | MN AI, 16/10 20h48 |
| A12 | Na pendência de spread negativo vão **os dois valores**: o spread negativo do relatório (o que aconteceu) e a diferença até o spread do contrato (o que se pede de volta). | `remessa()` | Theo Garcia, 17/10 11h37 |
| A13 | Número de operação é único: **duplicata conta uma vez** e entra na lista para a Ponte corrigir o relatório. | `DEDUP_PONTE = True` | MN AI 16/10 20h48; Insper 16/10 22h34 |
| A14 | `APROVADO C/ RESSALVA` **não muda nada**. Competência pela **data de contratação**. | `COMPETENCIA_REMESSA` | MN AI, 16/10 20h48 |
| A15 | A nota de câmbio é **uma só, tomadora Ponte Câmbio**, pelo total da participação do mês. Sai pelo **realizado**, mesmo incluindo o excesso que será contestado. | `TOMADOR_NF_REMESSA = "PONTE"` | MN AI 16/10 20h47; Theo Garcia 16/10 21h45 |
| A16 | `conta_codigo` é a **contrapartida do movimento**. Se o valor já estava registrado, o pagamento baixa a conta onde ele estava e **não vira receita ou despesa de novo**. Folha e tributos ficam provisionados **todo mês**. | `classificacao.py` | Fox AI 16/10 21h14; Desbravadores 17/10 9h48 |
| A17 | Tarifas, aluguel, cloud, assinaturas e serviços **não** são provisionados: entram direto na despesa do mês. | `classificacao.py` | Fox AI, 16/10 21h14 |
| A18 | **Atlas:** sem contrato assinado, **não fatura**. O CNPJ 39.566.044/0001-19 da aba de 2025 **é da mesma empresa** e pode ser usado para identificar; só a taxa daquela aba não vale. **O repasse ao lojista não para** — o dinheiro é dele. | `de_para_ec.csv`, `apuravel = 0` | Prime 17/10 11h41; Lucca 17/10 11h03 |
| A19 | PIX de R$ 7.350 sem identificação: **não é receita** até alguém identificar. Devolução de PIX e transferência de 30/09 (cai em 01/10): decisão nossa, pendência. | `lancamentos()` | Lucca Landeiro, 16/10 20h49 |
| A20 | A Orbe deposita **tudo** no Aurora e não paga lojista direto. O saldo negativo é a **conta garantida**. Conciliar Orbe contra banco parcela a parcela **não é o que este fechamento precisa**. | fora do escopo | Insper AI, 16/10 22h34 |
| A21 | A **provisão de setembro** é feita pela contabilidade, fora do fechamento automático. O fechamento classifica o que passou nos extratos. | fora do escopo | Datarmos, 17/10 11h49 |
| A22 | Tarvo **não vende acima de 12x**. Se aparecer, é pendência. | `comum.MAX_PARCELAS` | Casa Barton, 17/10 11h01 |

---

## B. Delegado a nós — critério escolhido e por quê

| # | Decisão | O que escolhemos | Por quê |
|---|---|---|---|
| **B1** | Tolerância para dizer que a taxa divergiu | **0,01 p.p.** | A Ponte grava 0,015007 onde o contrato diz 0,015 e a Orbe trunca centavos. Abaixo de 0,01 p.p. é representação, não condição comercial diferente. Acima, é sempre diferença de verdade: o menor caso real do mês é 0,30 p.p. (Mundo Aberto). O critério não deixa passar nada e não acende centavo. |
| **B2** | Atlas em `comissoes_por_lojista.csv` | **Sai zerada, com pendência** e as 57 transações no rastro | A Helena disse que as duas formas servem. Zerada preserva a rastreabilidade: o volume existe, o lojista existe, e a linha mostra que a apuração está travada, em vez de simplesmente sumir. A coluna `apuravel=0` diz por quê. |
| **B3** | As 118 transações da Casa em `divergencias_taxa.csv` | **Não.** Vão para `devolucoes_lojista.csv`, com o total na pendência e o detalhe no rastro | A Helena disse "basta a pendência, não precisa". Misturar com as divergências de contrato arriscaria somar R$ 15.397,42 numa cobrança à Orbe que não existe. Arquivo separado dá o detalhe por transação sem poluir o total a cobrar. |
| **B4** | Critério do alerta de antecipação | **Só acende para lojista sem venda anterior à competência que antecipa acima do que vendeu no mês.** Em setembro: só a Atlas | A antecipação é sobre a agenda inteira, com parcelas de meses anteriores que este arquivo não traz. "Antecipou mais do que vendeu no mês" acenderia **6 lojistas**, cinco deles sem nenhum problema — Canguru antecipou R$ 31.765 com R$ 1.934 vendidos, sobre parcelas de agosto. O risco que a Helena descreveu é lojista novo sem histórico, e é isso que o critério captura. |
| **B5** | Antecipação revertida conta no alerta? | **Alerta pelo pico, com as reversões citadas no próprio alerta** | O risco existiu quando o dinheiro foi adiantado. Na Atlas o antecipado líquido no fim do mês (R$ 127.230,96) fica *abaixo* das vendas, então olhar só o saldo final apagaria o caso inteiro. O alerta nomeia as duas reversões para a Helena julgar. Proposta equivalente da Fox AI aprovada em 17/10 12h50. |
| **B6** | Conta da devolução de PIX da Mundo Aberto | **2.1.01.001 Repasses a lojistas a pagar** | O repasse voltou, então a obrigação com o lojista volta a existir. A 2.1.01.002 é para crédito concedido ao lojista, que não é o caso aqui. Mesmo critério para qualquer repasse devolvido. |
| **B6b** | Valor da **devolução** ao lojista | **O que a Orbe descontou de fato (`valor_taxa`) menos a comissão contratada** — R$ 15.396,77 na Casa, e não os R$ 15.397,42 da fórmula da divergência | São dois números com propósitos diferentes, e a Helena confirmou os dois: a divergência é o que se cobra do parceiro (`valor_bruto ×` diferença de taxa, A3); a devolução é o que saiu do bolso do lojista. A diferença de R$ 0,65 é o truncamento da Orbe. *"Devolvo o que saiu do bolso do lojista"* (17/10 12h50). As duas colunas saem em `devolucoes_lojista.csv`. |
| **B7** | Os três centavos da divergência da Mundo Aberto | **`valor_bruto × (aplicada − contratada)`**, como a Helena pediu em A3 → R$ 1.418,87 | É a fórmula que ela própria definiu para o valor da divergência. Usar o `Spread R$` do relatório daria R$ 1.418,88, mas misturaria o arredondamento da Ponte no nosso número. |
| **B8** | `quem_decide` | Texto livre com **área + papel** (ex.: "Financeiro Tarvo + Parceiro Orbe") | A organização confirmou que é texto livre. Nomear as duas pontas deixa claro quem contesta e quem ressarce. |
| **B9** | Vários `ref_origem` numa pendência | Separados por **`|`** | A organização confirmou que vale. Usamos `;` como separador do CSV, então `|` evita qualquer ambiguidade de parsing. |

---

## B-bis. Comportamento quando falta fonte

> *"Prefiro que a solução avise a que quebre sem ninguém perceber."*
> *"Quando falta alguma coisa, eu não seguro o mês inteiro. Fecha o que não depende daquilo,
> marca o que é provisório e deixa claro o que está bloqueado e por quê. Quem libera sou eu."*
> — Helena, 17/10 12h31

`src/validacao.py` confere as seis fontes antes de ler qualquer número: arquivo presente,
sem ambiguidade, e com as colunas que o layout do mês passado tinha. Um problema **não**
derruba o fechamento:

| Situação | O que acontece |
|---|---|
| Arquivo não chegou | Bloqueia só a parte que depende dele; o resto fecha |
| Parceiro mudou o layout sem avisar | O fechamento diz **quais colunas sumiram**, e bloqueia aquela parte |
| Dois arquivos candidatos ao mesmo padrão | Bloqueia e nomeia os dois, em vez de escolher um |

A parte bloqueada vira pendência `FONTE_INDISPONIVEL` com o motivo e `quem_decide =
Financeiro Tarvo (comercial decide antes se for taxa ou cadastro)`, a saída sai marcada
`[PROVISORIO]`, e uma pendência `FECHAMENTO_PROVISORIO` resume o que ficou de fora.

`testes/teste_fontes.py` prova os três cenários. Com o e-mail da Ponte ausente, o checkout
fecha em **exatamente** os mesmos R$ 207.039,73; com o Aurora de layout trocado, o Meridiano
classifica seus 100 lançamentos sozinho. Nos três casos o rastro continua fechando.

---

## C. Ainda premissa — nada bloqueia o fechamento

| # | Premissa | O que muda se estiver errada |
|---|---|---|
| C1 | O ajuste de contestação da Ponte (linha nova, `Nº` próprio, spread negativo, obs `AJUSTE REF PC-…`) abate a participação do mês em que aparece, com rastro para a operação original. | Nada em setembro: o relatório não traz nenhum. Implementado para outubro em diante. |
| C2 | Operação da Ponte de CNPJ que não está na planilha: calcula-se a participação mesmo assim (a Ponte paga e a nota tem de bater com o repasse) e abre-se pendência de cadastro. | Não aconteceu em setembro. A Helena chamou o tratamento de razoável. |
| C3 | Lojista com comissão negativa não emite nota e o saldo não passa para o mês seguinte automaticamente; a Helena trata com o lojista. | Só a Casa do Estudante, com −R$ 5,50. |

---

## D. O que fica de fora de propósito

- **Conciliação do repasse ao lojista parcela a parcela.** A Helena disse que não é o que ela precisa
  neste fechamento, e que fica para quando houver agenda de recebíveis.
- **Provisão de folha e tributos de setembro.** É da contabilidade, com dados que não estão no pacote.
- **Apuração de PIS/COFINS/ISS/IRRF sobre as notas.** A saída pede o valor da nota.
- **Divergência da Atlas.** Sem contrato assinado não há taxa contra a qual comparar. Buraco explicado
  em vez de alarme falso.
