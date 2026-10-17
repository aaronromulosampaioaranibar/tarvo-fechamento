# Arquitetura da solução

## Princípio

O cliente pediu "um agente que feche o mês". O que ele precisa é de **um fechamento determinístico
com um agente onde o determinismo não alcança**. Número de comissão não pode sair de um modelo de
linguagem: tem que sair de uma regra que alguém consegue ler. A IA entra onde hoje entra a cabeça
da analista — desempatar nome, classificar despesa nova, redigir o porquê de uma pendência.

Três invariantes, verificadas por teste automático que quebra o build:

1. **Nenhum número sem origem.** Todo `id_saida` tem linhas em `rastro.csv` e a soma bate.
2. **Nenhum palpite silencioso.** O que não casa por chave vira linha em `pendencias.csv` com dono.
   Nunca um `fillna`, nunca um casamento aproximado aceito sozinho.
3. **Nenhuma data no código.** A competência é parâmetro. Outubro roda com `--competencia 2026-10`.

## Pipeline

```
   entrada/2026-09/                      (os arquivos como o cliente manda, sem limpeza)
        |
   [1] INGESTAO            um leitor por formato -> tabela normalizada
        |                  toda linha carrega arquivo_origem + ref_origem desde o 1o segundo
        |
   [2] IDENTIDADE          cadastro de lojistas: EC Orbe -> CNPJ -> nome em banco
        |                  de-para explicito e versionado, nao inferido em tempo de execucao
        |
   [3] REGRAS              taxas vigentes por data | comissao | divergencia | competencia
        |
   [4] CLASSIFICACAO       extratos -> plano de contas (regra primeiro, IA no residuo)
        |
   [5] SAIDA + AUTOTESTE   6 CSVs + rastro.csv + verificacao de fechamento
        |
   saida/
```

### [1] Ingestão — ler o que o cliente manda, não o que seria bom receber

| Fonte | Formato real | Cuidado obrigatório |
|---|---|---|
| Orbe | CSV `;`, UTF-8, decimal `,`, data `dd/mm/aaaa` | `ref_origem = id_transacao` |
| Taxas | XLSX feito à mão, 2 abas, taxas ora `float` ora texto `"1,49%"` | ler **só** "Taxas vigentes"; CNPJ com `zfill(14)`; duas linhas por lojista quando há vigência |
| Ponte | `.eml` → anexo XLSX com 5 linhas de cabeçalho e 2 de rodapé | extrair o anexo do e-mail em código; **o corpo do e-mail é fonte de regra** (50%, ressalva, data do repasse) |
| Aurora | CSV `;` com 8 linhas de preâmbulo, milhar `.`, nome truncado | `ref_origem = L<nº da linha física>` — contar a linha no arquivo cru, antes de qualquer filtro |
| Meridiano | OFX 1.0 SGML, cp1252, tags não fechadas | `ref_origem = FITID`; não usar parser de XML |
| Plano de contas | CSV `;` em **latin-1** (acentos quebram em UTF-8) | detectar encoding, não assumir |

Nenhum dos leitores altera o arquivo de entrada. Nenhum passo manual antes de rodar.

### [2] Identidade — o coração do problema

Uma tabela, `cadastro/lojistas.csv`, versionada no repositório, com três colunas de chave:
`cnpj` (14 dígitos) · `ec_orbe` · `aliases_banco`.

- **Vem da planilha de taxas** quando o campo "EC Orbe" está preenchido: 18 dos 22 ECs resolvem aqui, sem ambiguidade.
- **Os 4 que não resolvem** (Atlas, Kiwi, Horizonte x Novo Horizonte) entram com `origem=RESPOSTA_FINANCEIRO`
  e data. Enquanto não houver resposta, a comissão sai com o EC como identificador e **uma linha em
  `pendencias.csv` por lojista**, não um CNPJ chutado.
- **Nome nunca é chave.** Para o extrato bancário, onde só existe nome truncado, a resolução é:
  1. match exato contra `aliases_banco` (determinístico, `metodo=REGRA`, `confianca=1.0`);
  2. se falhar, a IA **sugere** o lojista e devolve confiança;
  3. `confianca < 0.95` → pendência, não classificação. O alias aprovado por uma pessoa volta para
     o cadastro e nunca mais é perguntado.

É isso que tira a regra da cabeça da analista: o de-para vira arquivo, o arquivo vira histórico.

### [3] Regras — comissão e divergência

```
taxa_contratada(cnpj, modalidade, parcelas, data_referencia)
    data_referencia = data_venda_original se ESTORNO, senao data_movimento
    seleciona a linha de taxa cuja vigencia cobre data_referencia   <- Bridge 15/09

comissao_checkout(lojista) = SOMA(valor_taxa) com sinal        -> MDR + antecipacao
comissao_remessa(lojista)  = SOMA(Spread R$) x 50%             -> apos dedup por No Operacao

divergencia(tx) = taxa_aplicada - taxa_contratada    se |dif| > tolerancia
    diferenca_brl = valor_bruto x dif / 100
```

Deduplicação da Ponte por `Nº Operação`, mantendo a primeira ocorrência e registrando a descartada
como pendência contra o rodapé do parceiro.

### [4] Classificação contábil

| Camada | Cobertura esperada | `metodo` | `confianca` |
|---|---|---|---|
| Regra determinística sobre o padrão do histórico (`TED RECEBIDA ... ORBE`, `PIX ENVIADO <alias>`, `TED ENVIADA PONTE CAMBIO`, DARF, GPS, GRF, tarifa, aplicação/resgate) | ~90% dos 184 lançamentos | `REGRA` | 1.00 |
| IA classifica o resíduo contra as 30 contas analíticas do plano, devolvendo conta + justificativa + confiança | ~8% | `IA` | 0.70–0.95 |
| Abaixo do corte, ou caso que exige decisão de negócio | ~2% | `HUMANO` | < 0.70 |

Toda sugestão da IA que uma pessoa confirmar vira regra na rodada seguinte. A cobertura de `REGRA`
sobe mês a mês; a conta de API cai.

### [5] Saída e autoteste

Os 6 CSVs no formato fixo (`;`, decimal `.`, data `AAAA-MM-DD`, CNPJ 14 dígitos). E, antes de gravar:

```
assert  para todo id_saida:  soma(rastro.valor) == valor_reportado      (tolerancia R$ 0,01)
assert  comissao_checkout_total == soma(valor_taxa do arquivo Orbe)
assert  todo EC da Orbe esta no cadastro OU tem pendencia aberta
assert  toda operacao da Ponte aparece exatamente uma vez na saida ou em pendencias
```

Se um assert falha, **a solução não grava a saída**. Total que não fecha é pior que total que falta.

## Onde a IA atua e onde não atua

| Atua | Não atua |
|---|---|
| Sugerir o de-para entre nome truncado no banco e lojista do cadastro | Decidir comissão, taxa ou divergência |
| Classificar lançamento bancário fora do padrão conhecido | Escolher entre dois lojistas de nome parecido sem confirmação |
| Redigir o motivo da pendência em português para o financeiro | Preencher dado que falta na origem |
| Ler o corpo do e-mail da Ponte e extrair regra (50%, ressalva, data do repasse) | Arredondar, completar ou "consertar" valor |

## Como a analista usa em outubro

1. Joga os arquivos de outubro em `entrada/2026-10/`, do jeito que chegaram.
2. Roda um comando.
3. Abre `pendencias.csv` — é a **única** coisa que ela lê inteira. Hoje seriam ~12 linhas.
4. Responde o que é dela, encaminha o que é do comercial e o que é da Ponte.
5. Roda de novo. As respostas dela viraram cadastro e não voltam em novembro.

Oito dias viram a tarde em que ela resolve doze exceções. E se ela sair de férias, o mês fecha,
porque a regra está no repositório e não nela.

## Prioridade de construção (hoje)

| Ordem | O quê | Por quê |
|---|---|---|
| 1 | Ingestão + identidade + `comissoes_por_lojista.csv` (CHECKOUT) + `rastro.csv` | é o nível **mínimo**, e o rastro é a regra central |
| 2 | Comissão de REMESSA (dedup, 50%, negativos, competência) | fecha a segunda linha de negócio |
| 3 | `divergencias_taxa.csv` | é onde está o dinheiro do pitch |
| 4 | `lancamentos_classificados.csv` | volume alto, regra simples |
| 5 | `notas_a_emitir.csv` + `pendencias.csv` | derivam dos anteriores |
| 6 | Autoteste de fechamento | **não é o último se der tempo: é parte do item 1** |
