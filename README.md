# Fechamento Tarvo Pagamentos

Fecha o mês da Tarvo a partir dos arquivos **como o cliente manda** — CSV pt-BR com `;`,
planilha mantida à mão, e-mail com anexo, OFX — e entrega os seis arquivos de saída
com rastro de cada número até a linha de origem.

## Rodar do zero

```bash
python3 -m pip install openpyxl          # única dependência
python3 fechar.py --entrada "/caminho/da/pasta/do/mes" --competencia 2026-09
```

Sem chaves de API para o caminho padrão: **todo número sai de regra determinística.**
A camada de IA é opcional e só toca o resíduo da classificação contábil (veja abaixo).

Não há passo manual antes de rodar. Os arquivos são localizados por padrão de nome
(`*orbe*comiss*.csv`, `*taxas*.xlsx`, `*.eml`, `*aurora*.csv`, `*.ofx`, `*plano*contas*.csv`),
então outubro roda com arquivos novos sem tocar no código:

```bash
python3 fechar.py --entrada "./entrada/2026-10" --competencia 2026-10
```

## O que sai

| Arquivo | Linhas em set/2026 |
|---|---|
| `comissoes_por_lojista.csv` | 36 (22 checkout + 14 remessa) — R$ 207.039,73 + R$ 39.543,45 |
| `divergencias_taxa.csv` | 115 transações, R$ 2.995,10 a cobrar dos parceiros |
| `devolucoes_lojista.csv` | 118 transações, R$ 15.396,77 do bolso da Tarvo |
| `notas_a_emitir.csv` | 21 |
| `lancamentos_classificados.csv` | 184, 100% com conta, todos por regra |
| `pendencias.csv` | 31 |
| `rastro.csv` | 4.598 |

Mais `contestacoes/`: três rascunhos de e-mail por contraparte, com as operações em anexo,
para o financeiro revisar e enviar.

Formato fixo: `;` como separador, `.` decimal, datas `AAAA-MM-DD`, CNPJ com 14 dígitos.

## Quando falta uma fonte

O fechamento **não para**. `src/validacao.py` confere as seis fontes antes de ler qualquer
número e, se uma estiver ausente ou com o layout mudado, bloqueia só a parte que depende
dela, diz o motivo e marca a saída como `[PROVISORIO]`:

```
=== FECHAMENTO 2026-09  [PROVISORIO] ===
  !! FONTES COM PROBLEMA:
     - ponte: AUSENTE - nenhum arquivo bate com ['*ponte*cambio*.eml', ...]
     - aurora: LAYOUT_MUDOU - nao encontrei: Data, Lançamento, Valor (R$)
     > REMESSA BLOQUEADO (falta ponte)
     > EXTRATO_AURORA BLOQUEADO (falta aurora)
     O restante fechou. Os numeros abaixo sao parciais.
```

Para provar: `python3 testes/teste_fontes.py` monta os três cenários a partir dos arquivos
reais e confere que o checkout fecha no mesmo valor com a Ponte ausente, e que o Meridiano
fecha sozinho com o Aurora quebrado.

## Autoteste de fechamento

Antes de gravar, o programa verifica:

1. Todo `id_saida` tem linhas em `rastro.csv` e **a soma bate** (tolerância R$ 0,01).
2. Comissão de checkout == soma de `valor_taxa` do arquivo da Orbe.
3. Comissão de remessa == soma das parcelas por operação.
4. Todo EC da Orbe está resolvido **ou** tem pendência aberta.
5. Toda operação da Ponte aparece uma vez na saída ou em `pendencias.csv`.

**Se qualquer uma falhar, nada é gravado.** Total que não fecha é pior que total que falta.
Para inspecionar mesmo assim: `--forcar`.

> Esse teste já pagou por si: a primeira versão calculava a comissão de remessa como
> 50% do spread total e o rastro somava as parcelas arredondadas. Diferença de R$ 0,03
> em cinco lojistas. O autoteste barrou a gravação. A comissão agora nasce da parcela
> por operação, que é como ela é faturada.

## Estrutura

```
fechar.py                  CLI
src/comum.py               normalizacao (CNPJ, decimal pt-BR, taxa texto/float) + PARAMETROS
src/leitores.py            um leitor por formato; toda linha ja sai com arquivo_origem + ref_origem
src/identidade.py          cadastro de lojistas: EC Orbe -> CNPJ -> nome truncado em extrato
src/classificacao.py       extratos -> plano de contas (REGRA | IA | HUMANO)
src/fechamento.py          motor: comissao, divergencia, notas, pendencias
src/saida.py               gravacao no formato fixo + autoteste
cadastro/de_para_ec.csv    de-para versionado dos ECs que a planilha nao resolve
saida/                     os seis arquivos
```

## Onde mexer quando o financeiro responder

Todas as premissas discutíveis estão em **`src/comum.py`**, uma linha cada, com o número
da pergunta de `HIPOTESES.md`:

```python
TOLERANCIA_TAXA_PP     = 0.01        # Q10
PARTICIPACAO_SPREAD    = 0.50        # A7 (e-mail da Ponte)
SPREAD_PADRAO_PCT      = 1.50        # Q4
COMPETENCIA_REMESSA    = "contratacao"   # Q6: "contratacao" | "liquidacao"
INCLUI_SPREAD_NEGATIVO = True        # Q5
DEDUP_PONTE            = True        # Q7
CORTE_CONFIANCA_IA     = 0.95
```

E o de-para dos ECs ambíguos em `cadastro/de_para_ec.csv`. Mudar uma resposta é mudar
uma linha e rodar de novo — não é mexer em regra espalhada pelo código.

## Onde a IA atua

Por padrão **não atua**: as 184 linhas dos dois extratos foram classificadas por regra
determinística neste mês. O gancho existe para o mês em que aparecer uma despesa nova:

```python
from src.fechamento import Fechamento
Fechamento(pasta, agente_ia=meu_agente).executar()
```

O agente recebe o lançamento e devolve `{"conta": "4.2.0X", "confianca": 0.0–1.0, "rotulo": "..."}`.
Acima de `CORTE_CONFIANCA_IA` vira `metodo=IA`; abaixo vira `metodo=HUMANO` e pendência.
A IA **nunca** decide comissão, taxa, divergência ou identidade de lojista.

## Limitações conhecidas

- **Identidade de 4 lojistas por premissa, não por resposta.** Atlas, Kiwi e as duas
  Horizonte estão em `cadastro/de_para_ec.csv` com confiança < 1,0 e pendência aberta.
  Os dois Horizonte têm taxas diferentes: se a premissa estiver trocada, a divergência
  dos dois sai errada.
- **Atlas Idiomas não tem taxa vigente.** O CNPJ veio da aba "ANTIGO 2025" porque é a
  única fonte de identidade dela; as **taxas** daquela aba não são usadas, e por isso
  nenhuma divergência é calculada para a Atlas — preferimos buraco a alarme falso.
- **Spread padrão assumido em 1,5%** para Kiwi, Canguru e Ponte Aérea (rodapé da planilha
  diz "spread em branco = padrão" sem dizer qual é).
- **Conciliação do repasse ao lojista não está implementada.** Os PIX enviados do Aurora
  não são confrontados com o `valor_liquido` da Orbe. Fora do escopo dos seis arquivos.
- **Competência de remessa por data de contratação.** Seis operações liquidadas em
  01/10 entram em setembro e aparecem em `pendencias.csv` para a contabilidade ver.
- A classificação contábil registra a **contrapartida**; a conta do próprio banco
  (1.1.01.001 / 1.1.01.002) é implícita no campo `banco`.
