# Momentos que importaram

O case pede de 2 a 4. Sao quatro, e em tres deles a IA errou.

O que nao esta aqui porque nao foi um momento e sim o metodo: mapeamos as seis fontes
antes de escrever uma linha de codigo. Foi dai que saiu a causa raiz, e esta inteira no
`DIAGNOSTICO.md`.


---

## 1. A IA inverteu a vigência da Bridge e produziu 12 divergências falsas

**O que pedi:** calcular as divergências entre taxa contratada e taxa aplicada, respeitando
que a Bridge tem duas linhas de taxa no mesmo mês (até 14/09 e a partir de 15/09).

**O que a IA devolveu:** 17 divergências para a Bridge, R$ 35,48. O código ordenava as duas
linhas de vigência **alfabeticamente** (`sort_values("vigencia")`) e pegava a primeira —
e "a partir de 15/09/2026" vem antes de "até 14/09/2026" na ordem alfabética. Resultado:
a taxa nova foi aplicada às transações antigas e vice-versa.

**O que fizemos com isso:** o número só não passou porque conferimos a contagem contra os
dados brutos — 14 transações à vista pós-15/09, das quais 9 já estavam na taxa nova. Se a
divergência real fosse 17, não bateria. Trocamos a ordenação alfabética por comparação de
data real em `Cadastro.taxa()`. A divergência correta é **5 transações, R$ 29,95**.

Esse é o erro que a prova do case avisa: alarme falso conta contra. Doze dos dezessete
seriam alarme falso, e todos pareciam plausíveis.

---

## 2. O autoteste barrou a própria entrega por R$ 0,03

**O que pedi:** que nada fosse gravado se a soma do `rastro.csv` não batesse com o número
reportado.

**O que a IA devolveu:** na primeira execução completa, o autoteste falhou em cinco lojistas
de remessa. A comissão era calculada como 50% do spread **total** do lojista; o rastro somava
as parcelas de cada operação, cada uma arredondada em centavos. Diferença de R$ 0,02 a R$ 0,04.

**O que fizemos com isso:** não aumentamos a tolerância. A parcela de cada operação passou a
ser arredondada **antes** de somar, que é como ela é faturada de verdade. O total mudou de
R$ 38.625,85 para R$ 38.625,83 e passou a fechar com as 232 linhas que o compõem.

Um erro de R$ 0,03 é irrelevante no mês. A regra que o produziu — somar primeiro e arredondar
depois — não é.

---

## 3. O arquivo novo teria passado em silêncio

**O que aconteceu:** às 13h a organização avisou que a Orbe mandou
`06_orbe_ajustes_tardios_set2026.csv`, com 14 linhas, "no mesmo formato do arquivo 01",
e disse que "se a solução de vocês já recebe os arquivos do mês, deve bastar rodar de novo".

**O que a nossa solução fez:** nada. O padrão de busca era `*orbe*comiss*.csv`, que casa
só com o relatório principal. O arquivo novo ficaria na pasta e o fechamento rodaria
normalmente, com os números antigos, sem erro e sem aviso.

**O que fizemos com isso:** o padrão virou `*orbe*.csv` e o leitor passou a consumir
**todos** os arquivos da Orbe do mês, com cada linha carregando o arquivo de onde veio.
Impacto: −R$ 3.304,39 de comissão (10 estornos, 3 reversões de antecipação e uma venda),
com o checkout caindo de R$ 207.039,73 para R$ 203.735,34.

A ironia é que, uma hora antes, tínhamos acabado de implementar o aviso de fonte faltando
justamente porque a Helena disse "prefiro que a solução avise a que quebre sem ninguém
perceber". A validação olhava se os arquivos esperados estavam lá — não se tinha chegado
um a mais. Fonte que some e fonte que se multiplica são o mesmo risco, e só tínhamos
coberto metade dele.

---

## 4. A auditoria independente achou o que o autoteste não via

**O que pedi:** um auditor que conferisse o rastro **sem importar nada de `src/`** —
relendo os CSVs gravados e os arquivos crus, com parsing próprio. A ideia era não
deixar o fechamento se corrigir sozinho.

**O que ele devolveu:** 15 `id_saida` com valor e **zero** linhas de rastro. Todas
pendências. O autoteste do próprio motor conferia cinco arquivos — comissões,
divergências, devoluções, notas e lançamentos — e nunca o `pendencias.csv`. Mas a regra
central do case não tem exceção: *"todo número da saída aponta para a linha de origem"*,
e uma pendência de R$ 15.396,77 é um número da saída.

**O que fizemos com isso:** toda pendência com valor passou a decompor em linhas de
origem. Duas precisaram mudar de número para poder decompor: o alerta de antecipação
passou a reportar o antecipado bruto (R$ 235.943,10, que soma as antecipações) em vez do
excedente sobre as vendas (um número derivado, que não soma nada), com o excedente no
motivo; e a divergência contra o rodapé da Ponte passou a apontar para as duas coisas que
a compõem — a operação duplicada e os quatro spreads negativos.

E o autoteste do motor ganhou a sexta conferência, para não depender de alguém lembrar
de rodar o auditor. O rastro foi de 4.626 para 5.389 linhas.

Se o auditor tivesse sido escrito importando `src/`, ele teria passado. A independência
era a coisa toda.
