# Momentos que importaram

## 1. Pedi para ler os arquivos antes de escrever qualquer código

**O que pedi:** mapear os seis arquivos do data pack — estrutura, chaves, volumes, onde eles
se ligam — antes de desenhar solução.

**O que a IA devolveu:** que nenhum dos seis arquivos compartilha chave com os outros. A Orbe
só tem `cod_estabelecimento`, a planilha de taxas tem CNPJ em três formatos com quatro ECs em
branco, e os dois bancos só têm nome truncado. Quatro dos 22 ECs da Orbe não existem na
planilha: R$ 35.369 de comissão sem dono.

**O que fizemos com isso:** virou a causa raiz do diagnóstico e a primeira decisão de
arquitetura — cadastro de identidade como camada própria, com nome proibido de ser chave
primária. Se tivéssemos começado pelo código, teríamos feito casamento de nome e os dois
Horizonte (taxas diferentes) teriam entrado trocados sem ninguém perceber.

---

## 2. A IA inverteu a vigência da Bridge e produziu 12 divergências falsas

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

## 3. O autoteste barrou a própria entrega por R$ 0,03

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

## 4. O arquivo novo teria passado em silêncio

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
