# Diagnóstico — por que o fechamento da Tarvo leva 8 dias e erra

Baseado só no data pack de set/2026. Todo número abaixo foi recalculado a partir dos arquivos
de origem; a conta está em `src/` e pode ser refeita.

## 1. O mês da Tarvo em números

| Linha | Base | Receita da Tarvo |
|---|---|---|
| Checkout (MDR) | 1.840 vendas + 59 estornos | R$ 207.449,64 |
| Checkout (antecipação) | 38 antecipações + 6 reversões | R$ 24.430,72 |
| **Checkout total** | 1.943 linhas Orbe | **R$ 231.880,36** |
| Remessa (50% do spread) | 232 operações únicas | **R$ 38.625,85** |
| **Total setembro** | | **≈ R$ 270.506** |

22 lojistas transacionaram no checkout, 14 em remessa (Nórdica e Ponte Aérea são só remessa).
A tabela de taxas lista 23 lojistas ativos — e **não lista a Atlas Idiomas**, que transacionou.

## 2. A causa raiz não é "falta de automação"

O fechamento não é lento porque alguém digita devagar. É lento porque **nenhum dos arquivos
compartilha uma chave com os outros**, e a chave que faltava foi substituída por nome.

```
Orbe         ->  cod_estabelecimento (10 dígitos), SEM CNPJ, 31 grafias para 22 lojistas
Taxas .xlsx  ->  CNPJ (3 formatos diferentes, 2 com dígito faltando) + "EC Orbe" (4 em branco)
Ponte .xlsx  ->  CNPJ (2 formatos) + nome truncado em 20 caracteres
Aurora .csv  ->  só nome, truncado em 26 caracteres, com acentuação corrompida
Meridiano .ofx -> só nome no MEMO, truncado
```

A planilha de taxas é a única ponte entre a Orbe e o resto — e ela é mantida à mão
("atualizar sempre que o comercial fechar!!", "última atualização: 02/09 - Bia").
**Toda a operação depende de uma coluna que uma pessoa preenche na mão.** Quando ela
fica em branco, o analista fecha o buraco de cabeça. É isso que não escala e é isso que
some quando ela sai de férias.

Os três sintomas do cliente são o mesmo problema:

- *"tem regra que só eu sei"* → a chave EC→CNPJ e os desempates de nome moram na cabeça dela.
- *"o lojista reclamou e tinha razão"* → ninguém compara taxa contratada x aplicada; a planilha
  é a fonte do contrato e o relatório da Orbe é a fonte do que aconteceu, e eles nunca se cruzam.
- *"bato uma fonte por vez"* → são 6 arquivos em 5 formatos, e a conferência é linha a linha.

## 3. Onde o dinheiro está vazando

### 3.1 Cobrança a maior não detectada — R$ 2.995,10 em um mês (≈ R$ 36 mil/ano)

| Caso | Evidência | Valor |
|---|---|---|
| **Rota Global** — Orbe aplica +0,50 p.p. em **todas** as faixas de crédito | 87 transações: 2,99% onde o contrato diz 2,49%; 3,49% onde diz 2,99%; 4,09% onde diz 3,59% | **R$ 1.546,28** |
| **Mundo Aberto** — spread de remessa renegociado para 1,2% em jul/26, Ponte segue aplicando 1,5% | 23 de 23 operações a 1,50% | **R$ 1.418,87** |
| **Bridge Idiomas** — renegociação do crédito à vista (2,59% → 2,19%) vigente em 15/09 não foi aplicada em 5 transações | 5 de 14 transações pós-15/09 ainda a 2,59% | **R$ 29,95** |

Os dois primeiros são **sistemáticos e recorrentes**: não é erro de uma transação, é um parceiro
operando com uma tabela desatualizada há meses. Rodando o mesmo cálculo em agosto e julho,
o passivo acumulado é previsível.

Nenhum deles aparece hoje, porque a comparação taxa contratada x taxa aplicada simplesmente
não é feita.

### 3.2 R$ 35.368,67 de comissão (15% do checkout) não tem dono certo

Quatro códigos de estabelecimento da Orbe **não existem na planilha de taxas**:

| EC | Nome na Orbe | Comissão | Por quê |
|---|---|---|---|
| 1076801732 | ATLAS IDIOMAS | R$ 7.876,05 | não está na aba "Taxas vigentes" — só na aba "ANTIGO 2025 - nao usar" |
| 1038867654 | KIWI EXPERIENCE TURISMO | R$ 10.711,06 | linha existe, campo "EC Orbe" vazio com obs. "EC pendente" |
| 1043396662 | HORIZONTE VIAGENS TURISMO | R$ 9.014,07 | dois lojistas de nome parecido, nenhum com EC preenchido |
| 1043300981 | HORIZONTE INTERCAMBIO | R$ 7.767,49 | idem |

O caso Horizonte é a armadilha cara: **"Horizonte Viagens" e "Novo Horizonte Intercâmbio"
têm taxas diferentes** (crédito à vista 2,69% x 2,39%; 2-6x 3,19% x 2,89%). Trocar os dois
não só joga comissão no lojista errado — **gera divergências falsas** nas duas pontas.
Casamento aproximado de nome aqui não é atalho, é erro com cara de acerto.

### 3.3 O relatório da Ponte Câmbio não pode ser somado como vem

| Problema | Impacto no spread | Impacto na comissão (50%) |
|---|---|---|
| Operação **PC-0926-0162 duplicada** (2ª linha marcada "reprocessada") | +R$ 821,88 | **+R$ 410,94 inflados** |
| Coluna **"Spread Estimado R$ (D-1)"** ao lado da realizada | 80.892,62 x 78.073,59 | **R$ 1.409 se somar a coluna errada** |
| **4 operações com spread negativo** (obs. "Taxa travada no pedido (D-1)") | −R$ 1.834,05 | **R$ 917,03 em disputa** |
| **6 operações contratadas em 30/09, liquidadas em 01/10** | R$ 2.078,71 | **R$ 1.039,36 de competência** |

O próprio rodapé da Ponte ("Total de operações: 233 / Spread total R$ 78.073,59") **já conta a
duplicata**. Quem confere contra o total do parceiro valida o erro do parceiro.

### 3.4 Competência: dinheiro de agosto entrando como se fosse de setembro

- Meridiano, 04/09: `TED RECEB PONTE CAMBIO SA REPASSE COMISSAO 08/2026` — **R$ 61.884,12**.
  É receita de agosto liquidando em setembro. Somar isso como receita de setembro infla o mês em 23%.
- O e-mail da Ponte diz que o repasse de setembro só cai em **06/10**, mediante nota fiscal.
  Ou seja: **a receita de remessa de setembro não tem contrapartida no extrato de setembro.**
- 9 estornos de setembro são de vendas de **agosto** (R$ 941,70 de MDR devolvido), e seus
  `id_referencia` não existem no arquivo de setembro.

### 3.5 Conciliação bancária: 3 itens que precisam de gente

| Onde | O quê | Valor |
|---|---|---|
| Aurora L50, 16/09 | `PIX RECEBIDO 38686002000180 SEM IDENTIFICACAO` — CNPJ não é de nenhum lojista conhecido | R$ 7.350,00 |
| Aurora L65, 23/09 | `DEVOLUCAO PIX - MUNDO ABERTO INTERC` — repasse que voltou | R$ 12.400,00 |
| Aurora L92 x Meridiano | 4 transferências saem do Aurora (350k, 420k, 380k, **300k em 30/09**); **só 3 entram no Meridiano**. A de 30/09 não aparece. | R$ 300.000,00 |

## 4. Os dez pontos onde a solução quebra se for ingênua

1. Casar por nome: 31 grafias Orbe / 26 caracteres no Aurora / 20 na Ponte / "ANDES EXPEDICÕES" com acento corrompido.
2. Ignorar vigência: Bridge tem **duas linhas de taxa no mesmo mês** (até 14/09 e a partir de 15/09).
3. Ler a planilha como números: Oxford Prep e Sol Nascente têm as taxas gravadas como **texto** ("1,49%").
4. Confiar no CNPJ da planilha: dois estão com **13 dígitos** (Fluente, Campus Global) — falta o zero à esquerda.
5. Usar a aba errada: "ANTIGO 2025 - nao usar" tem CNPJs e taxas plausíveis e é a única que contém a Atlas.
6. Somar a coluna de spread estimado em vez da realizada.
7. Não deduplicar o relatório da Ponte.
8. Tratar `APROVADO C/ RESSALVA` (16 ops, R$ 4.829,37 de spread) como pendência — **o e-mail diz que seguem normalmente**. Alarme falso conta contra.
9. Aplicar a taxa contratada da data do movimento em estornos, quando o correto é a data da venda original.
10. Classificar `PIX RECEB PONTE A...` (truncado) como se fosse a Ponte Câmbio, quando é a **Ponte Aérea Estudantil**, um lojista.

## 5. O que isso significa para a Tarvo

- **Hoje**: 8 dias úteis, 3 pessoas, zero rastro, e um erro de taxa só aparece quando o lojista reclama.
- **O que está em jogo por mês**: R$ 2.995 de cobrança a maior a devolver, R$ 35.369 de comissão sem
  dono definido, R$ 1.828 de receita de remessa que depende de 4 decisões que ninguém tomou,
  e uma nota fiscal de intermediação contra a Ponte sem a qual o repasse de 06/10 não entra.
- **O gargalo que escala**: a Tarvo cresceu 3x e o time não vai crescer 3x. Cada lojista novo
  adiciona uma linha na planilha da Bia e um nome novo para desempatar na cabeça dela.
