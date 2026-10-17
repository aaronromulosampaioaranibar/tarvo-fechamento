# Fechamento Tarvo Pagamentos

Fecha o mês da Tarvo a partir dos arquivos **como o cliente manda** — CSV pt-BR com `;`,
planilha mantida à mão, e-mail com anexo, OFX — e entrega os seis arquivos de saída
com rastro de cada número até a linha de origem.

## Rodar

**Como a Helena usa.** A pasta é a interface: ela larga os arquivos do mês, do jeito
que chegaram, em `entrada/AAAA-MM` (para outubro, cria `entrada/2026-10`) e dá dois
cliques:

| | |
|---|---|
| Windows | `FECHAR O MES.bat` |
| Mac e Linux | `fechar.command` |

Uma janela mostra os totais, as pendências com motivo e dono, e abre a pasta `saida/`
no final. Se alguma fonte faltar ou vier com o layout trocado, ela diz o que faltou,
fecha o que dá e marca o resultado como `[PROVISÓRIO]` — nada é gravado pela metade.
Não precisa escolher competência nem digitar nada: sem argumento, o programa fecha a
pasta de mês mais recente que encontrar em `entrada/`.

Tudo roda na própria máquina. Nenhum arquivo sai dela, não há chave de API e funciona
sem internet.

**Opcional, uma tela no navegador** (`abrir.py`) faz o mesmo por upload, para quem
prefere arrastar os arquivos em vez de copiá-los para a pasta. É conveniência: o
caminho suportado, e o que a banca deve rodar, é o acima.

**Pelo terminal**, que é como a banca roda:

```bash
python3 -m pip install -r requirements.txt   # só openpyxl
python3 fechar.py                            # fecha a pasta mais recente de entrada/
python3 fechar.py --entrada "/pasta/do/mes" --competencia 2026-10
```

Sem chaves de API para o caminho padrão: **todo número sai de regra determinística.**
A camada de IA é opcional e só toca o resíduo da classificação contábil (veja abaixo).

Não há passo manual antes de rodar. Os arquivos são localizados por padrão de nome
(`*orbe*.csv`, `*taxas*.xlsx`, `*.eml`, `*aurora*.csv`, `*.ofx`, `*plano*contas*.csv`),
então outubro roda com arquivos novos sem tocar no código.

## O que sai

| Arquivo | Linhas em set/2026 |
|---|---|
| `comissoes_por_lojista.csv` | 36 (22 checkout + 14 remessa) — R$ 203.735,34 + R$ 39.543,45 |
| `divergencias_taxa.csv` | 115 transações, R$ 2.995,10 a cobrar dos parceiros |
| `devolucoes_lojista.csv` | 118 transações, R$ 15.396,77 do bolso da Tarvo |
| `notas_a_emitir.csv` | 21 |
| `lancamentos_classificados.csv` | 184, 100% com conta, todos por regra |
| `pendencias.csv` | 31 |
| `rastro.csv` | 5.389, com a **regra aplicada** em cada linha |
| `saida/execucao.json` | registro da rodada: arquivos, linhas, hash, parâmetros e totais |

Mais `contestacoes/`: três rascunhos de e-mail por contraparte, com as operações em anexo,
para o financeiro revisar e enviar.

Formato fixo: `;` como separador, `.` decimal, datas `AAAA-MM-DD`, CNPJ com 14 dígitos.

## Auditabilidade

Cada linha de `rastro.csv` carrega a **regra aplicada**, não só o valor:

```
CMS-CHK-00520815000100 ; TX88410932 ; 0.00  ; isencao comercial 0.00% desde 01/09
                                              (condicoes_especiais.csv!...) · 608.88 x 0.00%
DIV-CHK-TX88423890     ; TX88423890 ; 32.25 ; divergencia = 6449.10 x (aplicada 4.09% -
                                              contratada 3.59%)
LCT-AURORA-L9          ; L9  ; 66026.00     ; 1.1.03.001 liquidacao da adquirente Orbe ·
                                              REGRA (confianca 1.00)
```

E `saida/execucao.json` registra cada rodada: quais arquivos entraram, com quantas linhas,
tamanho e hash SHA-256, os parâmetros usados, e os totais que saíram. Meses depois dá para
provar que aquela saída veio daqueles arquivos.

## Prova de que roda do zero

Clonando o repositório numa pasta limpa e rodando sem nenhum argumento, a saída sai
**byte a byte idêntica** à versionada em `saida/`:

```bash
git clone https://github.com/aaronromulosampaioaranibar/tarvo-fechamento.git
cd tarvo-fechamento
python3 -m pip install -r requirements.txt
python3 fechar.py
diff -r saida/ ../tarvo-fechamento-original/saida/   # sem diferencas
```

A Orbe pode mandar o relatório do mês **e** ajustes tardios depois. O leitor consome
todos os arquivos que batem com `*orbe*.csv`, e cada linha carrega o arquivo de onde veio,
então o rastro distingue um estorno do relatório de um que chegou no ajuste.

Nada fora do repositório é necessário: nem chave de API, nem arquivo solto, nem
configuração local. Os arquivos do mês estão em `entrada/2026-09/`, exatamente como o
cliente os manda.

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
6. Toda pendência com valor também fecha com o rastro.

Três scripts rodam por fora do motor:

| | |
|---|---|
| `testes/conformidade_formato.py` | o formato fixo dos seis arquivos: separador, decimal, datas, CNPJ, domínios fechados, `ref_origem` por fonte, conta que aceita lançamento |
| `testes/teste_fontes.py` | os três cenários de fonte ausente ou layout mudado |
| `testes/auditoria_rastro.py` | o rastro, **sem importar nada de `src/`** |
| `testes/teste_tela.py` | a tela de ponta a ponta: upload dos sete arquivos, números na página, downloads, e caminho maldoso bloqueado |

`auditoria_rastro.py` refaz a conferência **sem
importar nada de `src/`**: relê os CSVs gravados e os arquivos crus com parsing próprio,
confere que toda referência existe na fonte citada, que toda soma fecha, e refaz uma
amostra sorteada a partir da linha crua. Foi ele que encontrou as pendências sem rastro.

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
