# Roteiro do pitch — Equipe Prime

Case Tarvo · Aaron Rômulo, Guilherme Barros, Guilherme Gonçalves

Alvo: 4 a 5 minutos. Os tempos são do roteiro falado; cada bloco é um slide.
Quem apresenta lê o **negrito** devagar — são os números que a banca anota.

---

## 1 · O problema (30s)

A Helena fecha o mês da Tarvo à mão. São seis fontes que não conversam entre si:
o relatório da adquirente, uma planilha de taxas mantida à mão, um e-mail com anexo
do parceiro de câmbio, o plano de contas do ERP, e dois extratos bancários em
formatos diferentes.

Nenhuma delas tem a mesma chave. O extrato traz **"PIX ENVIADO MAPLE STUDY ASSESSORIA EDU"**,
truncado em 30 caracteres. O relatório da Orbe traz um código de estabelecimento.
A planilha de taxas traz CNPJ. Casar isso é o trabalho — e é onde o erro mora.

## 2 · O que entregamos (30s)

Um fechamento que roda em **dois cliques**, na máquina dela, sem navegador e sem
internet. Ela larga os arquivos numa pasta, clica, e sai a apuração completa.

Rodou agora, no Windows 11 de um de nós, em **0,18 segundo**. Nenhum arquivo sai
do computador. Nenhuma chave de API no caminho padrão. E o mesmo repositório rodado no
Linux produz saída **byte a byte idêntica** — o fechamento é reproduzível, não só correto.

## 3 · Setembro fechado (45s)

| | |
|---|---|
| Receita do mês | **R$ 243.278,79** |
| — comissão de checkout | R$ 203.735,34 (22 lojistas) |
| — participação no spread de câmbio | R$ 39.543,45 (14 lojistas) |
| A cobrar dos parceiros | **R$ 2.995,10** (115 transações) |
| A devolver ao lojista, do bolso da Tarvo | **R$ 15.396,77** (118 transações) |
| Notas a emitir | 21 |
| Lançamentos classificados | 184, **100% por regra** |
| Pendências com dono | 31 |

## 4 · O que nos diferencia (90s)

**Todo número volta à linha de origem.** São **5.389 linhas de rastro** para 505
resultados. Qualquer valor da apuração se decompõe até o arquivo, a linha e a
referência que o geraram. E quem confere isso não é o próprio motor: escrevemos um
auditor independente, em `testes/auditoria_rastro.py`, que não importa nada de `src/`.
Ele lê só a saída e as fontes e refaz as contas por fora.

**Pendência não é erro — é trabalho endereçado.** Cada uma das 31 tem valor, motivo
e **quem decide**: Financeiro, Comercial, Contabilidade ou o parceiro. A Helena não
recebe "confira isto"; recebe uma fila de trabalho já separada por mesa.

**A IA está onde deve estar, e em setembro não precisou agir.** Todo número sai de
regra determinística. A camada de IA só toca o resíduo da classificação contábil,
sempre com método (`REGRA` / `IA` / `HUMANO`), confiança e corte em 0,95. Neste mês,
**184 de 184 lançamentos saíram por regra** — a IA ficou de fora, e isso está escrito
na saída, não na nossa palavra.

**Um arquivo novo chegou às 13h07 e entrou sem tocar no código.** Era o `06_orbe_ajustes_tardios`.
Os arquivos são achados por padrão de nome, então outubro roda com arquivos novos
do mesmo jeito. E se uma fonte faltar ou mudar de layout, o motor fecha só a parte
que dá, marca `[PROVISÓRIO]` e diz o que faltou — **um total que não fecha é pior
que um total que falta.**

**Erramos quatro vezes e documentamos as quatro.** Estão em `PROMPTS/MOMENTOS.md`.
A mais cara: a base da comissão estava no valor que a Orbe descontou, e não no bruto
vezes a taxa contratada. A diferença era de **R$ 24.840,63 — 12% da receita do mês**,
e a correção só veio de uma resposta do financeiro às 22h34 de ontem. O motor dá a
resposta; a premissa é da operação.

## 5 · Dois achados que a Tarvo leva para a mesa (30s)

**A Casa do Estudante custa R$ 15.396,77 por mês à Tarvo.** O comercial concedeu
isenção e não informou a Orbe, que seguiu cobrando pela tabela. Não há o que
contestar com ninguém: a Tarvo devolve do próprio bolso, todo mês, enquanto a
condição não for registrada na adquirente.

**A Atlas Idiomas antecipou R$ 235.943,10 sem agenda anterior.** Lojista novo,
R$ 135.428,90 vendidos no mês, antecipou R$ 235.943,10. E não tem taxa vigente na
planilha — a comissão dela sai zerada e sem nota até o comercial confirmar o contrato.

## 6 · Fecho (20s)

Não entregamos um número. Entregamos um fechamento que a Helena consegue **defender
numa auditoria** — com a origem de cada centavo, com o que ficou em aberto escrito
na cara, e com as premissas separadas do código, num arquivo que o financeiro revisa
sem programador.

---

## Perguntas prováveis da banca

**"E se a Orbe mudar o layout do relatório?"**
O motor detecta e bloqueia só a parte que depende dela: checkout não fecha, câmbio
fecha, a saída vem marcada `[PROVISÓRIO]` e a pendência diz o que faltou.

**"Como vocês sabem que o número está certo?"**
Seis invariantes travam a gravação: se qualquer uma falhar, nada é escrito. Mais o
auditor independente, que refaz as contas sem olhar o código do motor. E mais uma prova
que vocês podem repetir agora: clonem o repositório e rodem. Nós fizemos isso — Windows 11
com Python 3.14 de um lado, Linux do outro — e **os sete arquivos de saída saem byte a byte
idênticos, mesmo SHA-256**. O fechamento é determinístico entre máquinas e entre versões de
Python. Não é "confie no número": é reproduza o número.

**"Onde entra a IA de verdade?"**
Na classificação contábil de linha bancária que não casa com nenhuma regra. Em
setembro, nenhuma. O desenho é esse de propósito: IA onde há ambiguidade de
linguagem, regra onde há dinheiro.

**"Quanto tempo para rodar outubro?"**
Criar a pasta `entrada/2026-10`, largar os arquivos, dois cliques. Sem tocar no código.

---

## O que aparece na tela em cada bloco

| Bloco | Na tela |
|---|---|
| 1 · O problema | `docs/fluxo-tarvo.html` — o mapa das seis fontes. Apontar para a linha do extrato truncado. |
| 2 · O que entregamos | A pasta `solucao` no Explorador. Dar o duplo clique ao vivo (ver abaixo). |
| 3 · Setembro fechado | A janela preta com os totais, ainda aberta do clique. |
| 4 · O que nos diferencia | `rastro.csv` aberto; depois `pendencias.csv` na coluna `quem_decide`; depois `PROMPTS/MOMENTOS.md`. |
| 5 · Os dois achados | `pendencias.csv` nas linhas PEN-015 (Casa do Estudante) e PEN-012 (Atlas). |
| 6 · Fecho | `docs/arquitetura-tarvo.html` — o desenho do motor. |

## A demonstração ao vivo (30 segundos, no bloco 2)

Antes de começar: **feche o Excel** e deixe duas janelas prontas — o Explorador na pasta
`solucao` e o navegador no `docs/fluxo-tarvo.html`.

1. Duplo clique em `FECHAR O MES.bat`.
2. Enquanto roda, dizer a frase: *"ela larga os arquivos numa pasta e clica — é isso."*
3. A janela imprime as 11 conferências e os totais. A pasta `saida` abre sozinha.
4. Apontar: **0,18 segundo**.

**Se algo der errado ao vivo**, não insista: a `saida/` já está no repositório, pronta.
Abra os CSVs direto e diga *"o resultado é este, e está no repositório desde as 18h"*.
Uma demonstração que falha e é contornada em cinco segundos não custa ponto nenhum;
uma pessoa tentando consertar ao vivo custa o pitch inteiro.

## Três coisas para não dizer

**Não dizer que "a IA classificou os lançamentos".** Em setembro, 184 de 184 saíram por
regra determinística. A camada de IA existe, está desenhada e documentada, e não precisou
agir. Dizer isso como está é mais forte, e é verdade.

**Não vender a tela do navegador.** Ela está no repositório como alternativa, mas o caminho
suportado é o atalho de dois cliques. Se perguntarem, responder exatamente isso.

**Não arredondar os números na fala.** São R$ 243.278,79, R$ 15.396,77, R$ 2.995,10. A banca
vai conferir contra os CSVs, e "mais ou menos 243 mil" enfraquece justamente o argumento de
que cada centavo tem origem.
