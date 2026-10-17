# Preparação para a apresentação — Equipe Prime

Case Tarvo · 10 minutos de pitch + 5 de perguntas, às 19h30
Aaron Rômulo, Guilherme Barros, Guilherme Gonçalves

**Para quem falamos:** o time financeiro e o CFO da Tarvo. Não são engenheiros. Falamos
como quem vai usar a solução no fechamento de outubro, não como quem escreveu o código.

---

## 1 · Divisão dos 10 minutos

| Minuto | Slide | Quem fala |
|---|---|---|
| 0:00 – 1:00 | Capa + O problema | — |
| 1:00 – 2:30 | O que a solução faz | — |
| 2:30 – 4:00 | Setembro fechado + o rastro | — |
| 4:00 – 5:30 | Os dois achados | — |
| 5:30 – 7:00 | Outubro + pendências | — |
| 7:00 – 8:00 | Onde a IA atua | — |
| 8:00 – 9:00 | Onde falha + com mais um mês | — |
| 9:00 – 10:00 | Fecho | — |

Preencham a coluna "quem fala" antes de entrar. Quem não está falando fica de olho no
relógio e avisa com um gesto combinado quando faltar 1 minuto.

**Regra de corte:** se às 7 minutos vocês ainda estiverem nos achados, pulem o slide de
pendências e vão direto para IA. Nunca cortem "onde falha" nem "com mais um mês" — são dois
dos sete pontos que eles pediram, e são os que mais times vão esquecer.

## 2 · A demonstração ao vivo

Antes de começar: **feche o Excel** e deixe duas janelas prontas — o Explorador na pasta
`solucao` e a `saida/` já gerada, caso precise do plano B.

1. Duplo clique em `FECHAR O MES.bat`.
2. Enquanto roda, dizer: *"ela larga os arquivos numa pasta e clica — é isso."*
3. A janela imprime as 11 conferências e os totais; a pasta `saida` abre sozinha.
4. Apontar: **0,18 segundo**.

**Se falhar, não insista.** Abra os CSVs que já estão no repositório e diga *"o resultado é
este, e está publicado desde as 18h"*. Cinco segundos. Uma pessoa tentando consertar ao vivo
custa o pitch inteiro.

## 3 · O número com caminho até a origem

Eles escreveram: *"um número real com o caminho até a linha de origem convence mais do que
qualquer slide bonito."* Tenham **um** pronto para mostrar, e pratiquem o caminho:

> **R$ 29,95 — Escola Bridge de Idiomas**
>
> 1. `pendencias.csv`, linha PEN-014: a Orbe aplicou taxa diferente da contratada em 5 de
>    109 transações.
> 2. `divergencias_taxa.csv`: as cinco linhas, cada uma com a transação, a taxa contratada
>    (2,19%), a taxa aplicada (2,59%) e a diferença.
> 3. A coluna `ref_taxa_contratada` diz de onde veio o 2,19%: **`Taxas vigentes!A7`** — a
>    célula exata da planilha que o financeiro mantém.
> 4. `rastro.csv`, filtrando pelo `id_saida`: a linha do arquivo da Orbe que originou cada
>    centavo.

Esse é o caminho inteiro, da pendência até a célula da planilha. É curto o bastante para
caber em 40 segundos e é a melhor coisa que temos para mostrar.

## 4 · As perguntas, com a resposta curta

**"Como vocês sabem que o número está certo?"**
Seis invariantes travam a gravação: se qualquer uma falhar, nada é escrito. Além disso,
escrevemos um auditor que não importa nada do motor — lê só a saída e as fontes, e refaz as
contas por fora. E a prova que vocês podem repetir: clonem o repositório e rodem. Windows
com Python 3.14 de um lado, Linux do outro, saída **byte a byte idêntica, mesmo SHA-256**.

**"Esses R$ 15.396,77 a Tarvo não consegue recuperar da Orbe?"**
Não. A isenção foi concedida pelo comercial e nunca informada à adquirente, que cobrou
corretamente pela tabela vigente. Não há erro do parceiro para contestar. O dinheiro sai da
Tarvo e vai continuar saindo todo mês até alguém registrar a condição no cadastro da Orbe.
Por isso o primeiro item do nosso "próximo mês" é o cadastro único.

**"E os R$ 2.995,10 — vocês têm certeza de que é cobrança indevida?"**
São 115 transações em que a taxa aplicada difere da contratada, com a célula da planilha
citada linha a linha. Duas delas são padrão sistêmico, não caso isolado: 87 transações da
Rota Global e 23 operações de câmbio da Mundo Aberto. Os rascunhos de contestação já saem
prontos com o CSV anexo. Quem decide se envia é o financeiro.

**"Onde a IA entra de verdade?"**
Na classificação contábil de linha bancária que nenhuma regra alcança. Em setembro, nenhuma:
184 de 184 saíram por regra, e isso está escrito na coluna `metodo` da saída. O desenho é
esse de propósito — IA onde há ambiguidade de linguagem, regra onde há dinheiro.

**"Quanto tempo para rodar outubro? Precisa de vocês?"**
Criar a pasta `entrada/2026-10`, largar os arquivos, dois cliques. Não precisa de nós, e a
prova é que um arquivo novo chegou hoje às 13h07 e entrou sem tocar no código.

**"E se a Orbe mudar o layout do relatório?"**
Detecta e bloqueia só a parte que depende dela. Checkout não fecha, câmbio fecha, a saída vem
marcada PROVISÓRIO e a pendência diz o que faltou. Nunca entrega um total que parece certo e
não é.

**"Vocês confiam num número que a IA ajudou a produzir?"**
Nenhum número foi produzido por IA. A IA nos ajudou a escrever o código e a ler os arquivos;
cada valor sai de regra determinística, e o rastro mostra de onde. Inclusive erramos quatro
vezes durante o dia, e as quatro estão documentadas em `PROMPTS/MOMENTOS.md` — incluindo uma
de R$ 24.840,63, 12% da receita, que só corrigimos depois de uma resposta do financeiro.

**"Qual o maior risco de colocar isso em produção amanhã?"**
A planilha de taxas. Ela é a fonte da verdade contratual e é mantida à mão: três campos em
branco hoje, e um lojista sem taxa vigente. Enquanto a condição comercial não tiver um
cadastro único, o fechamento continua correto e continua apontando o mesmo buraco todo mês.

**"Por que devolver ao lojista o valor cheio descontado, e não a diferença?"**
Porque é o que saiu do bolso dele. A condição acertada era isenção total; a Orbe descontou
pela tabela. O que a Tarvo devolve é o que foi efetivamente debitado. Confirmamos esse
critério com o financeiro no canal antes de fechar.

## 5 · Três coisas para não dizer

**Não dizer que "a IA classificou os lançamentos".** Foram 184 de 184 por regra. A camada de
IA existe, está documentada e não precisou agir. Dito assim é mais forte, e é verdade.

**Não vender a tela do navegador.** O caminho suportado é o atalho de dois cliques.

**Não arredondar os números na fala.** São R$ 243.278,79, R$ 15.396,77, R$ 2.995,10. Eles vão
conferir contra os CSVs, e "mais ou menos 243 mil" enfraquece justamente o argumento de que
cada centavo tem origem.

## 6 · Se não formos finalistas

O pitch conta na avaliação individual do Junior Fellowship de qualquer forma. O deck e o
repositório já dizem tudo sozinhos — o `README.md` abre com como rodar, o `HIPOTESES.md`
separa o que foi respondido do que é premissa nossa, e o `PROMPTS/MOMENTOS.md` mostra o
raciocínio, inclusive os erros. É isso que eles pediram quando disseram "o pitch é a hora de
mostrar o raciocínio por trás disso".
