# -*- coding: utf-8 -*-
"""Gera o mapa do fluxo de pagamentos da Tarvo como SVG + pagina HTML."""
import html

W, H = 1260, 812
COLS = [(30, 170), (240, 180), (460, 210), (710, 220), (970, 250)]  # (x, largura)
CH = ["ORIGEM DO DINHEIRO", "O PARCEIRO PROCESSA", "O QUE CHEGA NA TARVO",
      "A APURACAO DO MES", "O REGISTRO FINAL"]

S = []
def add(s): S.append(s)
def esc(t): return html.escape(t, quote=True)

def caixa(ci, y, h, titulo, linhas, classe="cx", marcador=None, mx=None):
    x, w = COLS[ci]
    add(f'<rect class="{classe}" x="{x}" y="{y}" width="{w}" height="{h}" rx="7"/>')
    add(f'<text class="bt" x="{x+14}" y="{y+25}">{esc(titulo)}</text>')
    ty = y + 45
    for ln in linhas:
        add(f'<text class="bd" x="{x+14}" y="{ty}">{esc(ln)}</text>')
        ty += 15
    if marcador:
        cx = mx if mx is not None else x + w - 17
        add(f'<circle class="mk" cx="{cx}" cy="{y+16}" r="11.5"/>')
        add(f'<text class="mkt" x="{cx}" y="{y+20.5}">{marcador}</text>')

def seta(ci_de, ci_para, y, tracejada=False, rotulo=None):
    x1 = COLS[ci_de][0] + COLS[ci_de][1] + 5
    x2 = COLS[ci_para][0] - 9
    cl = "fl fl-d" if tracejada else "fl"
    add(f'<line class="{cl}" x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" marker-end="url(#pt)"/>')
    if rotulo:
        add(f'<text class="fr" x="{(x1+x2)/2}" y="{y-8}">{esc(rotulo)}</text>')

def faixa(y, h, rotulo, sub, classe):
    add(f'<rect class="fx {classe}" x="20" y="{y}" width="{W-40}" height="{h}" rx="11"/>')
    add(f'<text class="fxt {classe}-t" x="38" y="{y+24}">{esc(rotulo)}</text>')
    add(f'<text class="fxs" x="{38 + 11*len(rotulo)}" y="{y+24}">{esc(sub)}</text>')

# ---- cabecalho de colunas ----
for i, t in enumerate(CH):
    x, w = COLS[i]
    add(f'<text class="ch" x="{x}" y="26">{esc(t)}</text>')
add(f'<line class="rl" x1="20" y1="38" x2="{W-20}" y2="38"/>')

# ---- FAIXA A: CHECKOUT ----
AY, ABY, ABH = 52, 90, 128
faixa(AY, 190, "CHECKOUT", "o aluno paga o curso — a Tarvo ganha MDR e antecipacao", "la")
caixa(0, ABY, ABH, "Aluno paga", [
    "cartao de credito, debito ou Pix", "na agencia de intercambio",
    "~2.000 transacoes por mes"])
caixa(1, ABY, ABH, "Orbe processa", [
    "aplica a taxa por estabelecimento", "credita o liquido em TED no Aurora",
    "antecipa recebivel a 2,10%"])
caixa(2, ABY, ABH, "CSV do portal", [
    "1.943 linhas: venda, estorno,", "antecipacao e reversao",
    "sem CNPJ — so cod_estabelecimento", "31 grafias para 22 lojistas"], marcador="1")
caixa(3, ABY, ABH, "Apuracao", [
    "atribuir cada EC a um lojista", "somar valor_taxa com sinal",
    "conferir taxa aplicada x contratada", "hoje: a olho, contra a planilha"], marcador="3")
caixa(4, ABY, ABH, "Registro", [
    "3.1.01 MDR  ·  3.1.02 antecipacao", "NF de servico por lojista",
    "repasse do liquido via Aurora", "R$ 231.880,36 em set/2026"], classe="cx cx-ok", marcador="7")
for i in range(4):
    seta(i, i+1, ABY + ABH/2)

# ---- FAIXA B: REMESSA ----
BY, BBY, BBH = 256, 294, 128
faixa(BY, 190, "REMESSA", "o lojista paga a escola no exterior — a Tarvo ganha metade do spread", "lb")
caixa(0, BBY, BBH, "Lojista envia R$", [
    "Pix para a conta Meridiano", "para pagar escola no exterior",
    "~230 operacoes por mes"])
caixa(1, BBY, BBH, "Ponte Cambio fecha", [
    "spread sobre a PTAX do dia", "IOF e status de compliance",
    "Tarvo fica com 50% do spread"])
caixa(2, BBY, BBH, "XLSX por e-mail", [
    "233 linhas + rodape do parceiro", "1 operacao duplicada",
    "4 com spread negativo", "coluna 'estimado' ao lado da realizada"], marcador="4")
caixa(3, BBY, BBH, "Apuracao", [
    "deduplicar por N da operacao", "aplicar os 50% sobre o realizado",
    "conferir spread x contratado", "a regra dos 50% so existe no e-mail"], marcador="3",
      mx=COLS[3][0] + COLS[3][1] - 44)
caixa(4, BBY, BBH, "Registro", [
    "3.1.03 intermediacao de cambio", "NF contra a Ponte destrava o",
    "repasse de 06/10", "R$ 38.625,83 em set/2026"], classe="cx cx-ok", marcador="5")
for i in range(4):
    seta(i, i+1, BBY + BBH/2)

# ---- FAIXA C: CAIXA ----
CY, CBY, CBH = 460, 498, 112
faixa(CY, 174, "CAIXA E CONTABILIDADE", "onde o dinheiro de verdade entra, sai e vira lancamento", "lc")
add(f'<text class="vz" x="{COLS[0][0]+14}" y="{CBY+60}">as duas linhas</text>')
add(f'<text class="vz" x="{COLS[0][0]+14}" y="{CBY+76}">desaguam aqui</text>')
caixa(1, CBY, CBH, "Banco Aurora", [
    "recebe a Orbe, paga os lojistas,", "folha e tributos",
    "CSV: nome truncado em 26 caracteres"])
caixa(2, CBY, CBH, "Banco Meridiano", [
    "recebe lojistas, envia a Ponte,", "aplicacao automatica em CDB",
    "OFX: nome so dentro do MEMO"], marcador="6")
caixa(3, CBY, CBH, "Conciliacao", [
    "184 lancamentos conferidos a mao", "credito sem identificacao, devolucao",
    "e transferencia que nao chegou"])
caixa(4, CBY, CBH, "Plano de contas", [
    "ERP Fenix · 30 contas analiticas", "classificacao refeita todo mes",
    "nenhum lancamento aponta para a origem"], classe="cx cx-ok", marcador="7",
      mx=COLS[4][0] + COLS[4][1] - 44)
for i in range(1, 4):
    seta(i, i+1, CBY + CBH/2)

# ---- SPINE: CADASTRO ----
SY = 662
add(f'<rect class="sp" x="20" y="{SY}" width="{W-40}" height="112" rx="11"/>')
add(f'<circle class="mk" cx="46" cy="{SY+24}" r="11.5"/>')
add(f'<text class="mkt" x="46" y="{SY+28.5}">2</text>')
add(f'<text class="spt" x="68" y="{SY+29}">A PLANILHA DE TAXAS — a unica ponte entre tudo isso, mantida a mao</text>')
itens = [
    ("23 lojistas, 3 formatos de CNPJ", "dois com o zero a esquerda faltando"),
    ("4 linhas com o EC Orbe em branco", "a Atlas nem esta na aba vigente"),
    ("vigencia que vira no meio do mes", "Bridge: 2,59% ate 14/09, 2,19% depois"),
    ("taxas ora numero, ora texto", "e uma aba antiga marcada 'nao usar'"),
]
for i, (a, b) in enumerate(itens):
    x = 68 + i * 292
    add(f'<text class="spa" x="{x}" y="{SY+58}">{esc(a)}</text>')
    add(f'<text class="spb" x="{x}" y="{SY+76}">{esc(b)}</text>')
add(f'<text class="spc" x="68" y="{SY+99}">Se a Bia sai de ferias, o mes nao fecha: o de-para entre o relatorio da Orbe e o lojista real so existe aqui e na cabeca dela.</text>')

# setas do cadastro para as duas apuracoes e para a conciliacao
for cx_ in (COLS[3][0] + 40, COLS[3][0] + 150, COLS[2][0] + 100):
    add(f'<line class="up" x1="{cx_}" y1="{SY-4}" x2="{cx_}" y2="{CBY+CBH+9}" marker-end="url(#ptu)"/>')

svg = f'''<svg viewBox="0 0 {W} {H}" width="{W}" role="img"
  aria-label="Mapa do fluxo de pagamentos da Tarvo nas duas linhas de negocio, do pagamento ao registro contabil, com sete gargalos marcados">
<defs>
  <marker id="pt" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
    <path d="M0,1 L9,5 L0,9 z" fill="var(--seta)"/></marker>
  <marker id="ptu" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
    <path d="M0,1 L9,5 L0,9 z" fill="var(--raiz)"/></marker>
</defs>
{chr(10).join(S)}
</svg>'''

GARGALOS = [
    ("1", "A Orbe nao manda CNPJ",
     "O relatorio so traz <code>cod_estabelecimento</code>. Quatro codigos nao existem na planilha de taxas: Atlas, Kiwi e duas Horizonte de nome parecido e taxas diferentes.",
     "R$ 35.369", "de comissao sem dono certo", "Financeiro + Comercial"),
    ("2", "A planilha e a unica ponte, e e feita a mao",
     "CNPJ em tres formatos, EC em branco, taxa ora numero ora texto, vigencia que vira no meio do mes. Tudo o que falta ali vira decisao de cabeca.",
     "raiz", "dos outros seis gargalos", "Comercial"),
    ("3", "Ninguem compara taxa contratada com taxa aplicada",
     "A Orbe cobra 0,50 p.p. a mais da Rota Global em 87 de 87 transacoes de credito. A Ponte aplica 1,5% na Mundo Aberto, que renegociou 1,2% em julho. Nenhum dos dois e erro pontual.",
     "R$ 2.995", "por mes, a devolver", "Comercial + parceiros"),
    ("4", "O relatorio da Ponte nao pode ser somado como vem",
     "Uma operacao repetida que o rodape do proprio parceiro ja conta, quatro com spread negativo e uma coluna de spread estimado ao lado da realizada.",
     "R$ 2.249", "entre erro e disputa", "Ponte Cambio"),
    ("5", "Competencia quebrada nas duas pontas",
     "R$ 61.884 de comissao de agosto entram no extrato de setembro. A receita de setembro so vira caixa em 06/10, e depende de uma NF que ainda nao foi emitida.",
     "R$ 1.039", "de receita na virada do mes", "Contabilidade"),
    ("6", "Os extratos so tem nome truncado",
     "Aurora corta em 26 caracteres e corrompe acento; Meridiano esconde o nome dentro do MEMO. 'PIX RECEB PONTE A' e a Ponte Aerea, lojista, e nao a Ponte Cambio, parceiro.",
     "184", "lancamentos conferidos a mao", "Financeiro"),
    ("7", "Nenhum numero aponta para a origem",
     "A comissao sai pronta da planilha. Quando o lojista contesta, a analista refaz a conta do zero — foi assim que a cobranca a maior do mes passado so apareceu porque ele reclamou.",
     "8 dias", "uteis de fechamento", "Financeiro"),
]

cards = []
for n, tit, txt, val, leg, dono in GARGALOS:
    cards.append(f'''<article class="g">
  <div class="g-h"><span class="g-n">{n}</span><h3>{esc(tit)}</h3></div>
  <p>{txt}</p>
  <div class="g-f"><span class="g-v">{esc(val)}</span><span class="g-l">{esc(leg)}</span>
  <span class="g-d">{esc(dono)}</span></div>
</article>''')

page = '''<title>Fluxo e gargalos da Tarvo</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Serif:wght@600;700&display=swap">
<style>
/* Mapa de processo em faixas: duas linhas de negocio + caixa, sobre a planilha que sustenta tudo. */
:root{
  --papel:#f6f7f9; --carta:#ffffff; --tinta:#131821; --meio:#5c6675; --fraco:#8d97a6;
  --risco:#dde2e9; --borda:#cbd3dd;
  --sis:#2c4a7c;        /* sistema de origem */
  --rec:#0f6b5c;        /* onde a Tarvo ganha */
  --gar:#a8322a;        /* gargalo */
  --raiz:#9a6412;       /* a planilha, raiz de tudo */
  --seta:#9aa5b4;
  --d:'IBM Plex Serif',Georgia,serif;
  --s:'IBM Plex Sans',system-ui,-apple-system,sans-serif;
  --m:'IBM Plex Mono',ui-monospace,SFMono-Regular,Menlo,monospace;
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --papel:#0f131a; --carta:#171d27; --tinta:#e6eaf0; --meio:#9aa5b4; --fraco:#6d7786;
  --risco:#262e3a; --borda:#323c4a;
  --sis:#8fb1e8; --rec:#4fc0a8; --gar:#f0847a; --raiz:#e0ad5c; --seta:#5a6575; color-scheme:dark;}}
:root[data-theme="dark"]{
  --papel:#0f131a; --carta:#171d27; --tinta:#e6eaf0; --meio:#9aa5b4; --fraco:#6d7786;
  --risco:#262e3a; --borda:#323c4a;
  --sis:#8fb1e8; --rec:#4fc0a8; --gar:#f0847a; --raiz:#e0ad5c; --seta:#5a6575; color-scheme:dark;}

body{background:var(--papel);color:var(--tinta);font-family:var(--s);line-height:1.5;margin:0}
.wrap{max-width:1300px;margin:0 auto;
  padding-left:max(16px,env(safe-area-inset-left,0px));
  padding-right:max(16px,env(safe-area-inset-right,0px));
  padding-block:28px 56px}

header{border-bottom:2px solid var(--tinta);padding-bottom:18px;margin-bottom:22px}
.eyebrow{font-family:var(--m);font-size:11px;letter-spacing:.16em;text-transform:uppercase;
  color:var(--meio);margin:0 0 8px}
h1{font-family:var(--d);font-weight:700;font-size:clamp(28px,5vw,44px);line-height:1.08;
  margin:0 0 10px;text-wrap:balance;letter-spacing:-.015em}
.lead{font-size:clamp(15px,2.2vw,17px);color:var(--meio);max-width:62ch;margin:0}

.kpis{display:flex;flex-wrap:wrap;gap:10px;margin:20px 0 26px}
.k{flex:1 1 170px;min-width:0;background:var(--carta);border:1px solid var(--borda);
  border-radius:8px;padding:12px 14px}
.k b{display:block;font-family:var(--m);font-size:clamp(17px,2.6vw,21px);font-weight:600;
  font-variant-numeric:tabular-nums;letter-spacing:-.02em}
.k span{display:block;font-size:11.5px;color:var(--meio);margin-top:3px;line-height:1.35}
.k.r b{color:var(--gar)}
.k.v b{color:var(--rec)}

.mapa{background:var(--carta);border:1px solid var(--borda);border-radius:10px;
  overflow-x:auto;padding:14px;margin-bottom:10px}
.mapa svg{display:block;min-width:1100px;height:auto}

.leg{display:flex;flex-wrap:wrap;gap:8px 20px;font-size:12px;color:var(--meio);margin-bottom:36px}
.leg i{display:inline-block;width:11px;height:11px;border-radius:3px;margin-right:6px;
  vertical-align:-1px;border:1px solid var(--borda)}
.leg .i1{background:color-mix(in srgb,var(--sis) 10%,var(--carta));border-color:var(--sis)}
.leg .i2{background:color-mix(in srgb,var(--rec) 10%,var(--carta));border-color:var(--rec)}
.leg .i3{background:var(--gar);border-color:var(--gar)}
.leg .i4{background:color-mix(in srgb,var(--raiz) 12%,var(--carta));border-color:var(--raiz)}

h2{font-family:var(--d);font-size:clamp(20px,3.2vw,26px);margin:0 0 4px;letter-spacing:-.01em}
.sub{color:var(--meio);font-size:14px;margin:0 0 20px}

.grade{display:grid;gap:12px;grid-template-columns:repeat(auto-fill,minmax(300px,1fr))}
.g{background:var(--carta);border:1px solid var(--borda);border-left:3px solid var(--gar);
  border-radius:8px;padding:15px 16px 13px;display:flex;flex-direction:column;min-width:0}
.g-h{display:flex;align-items:baseline;gap:9px;margin-bottom:7px}
.g-n{font-family:var(--m);font-size:11px;font-weight:600;color:var(--carta);background:var(--gar);
  width:19px;height:19px;border-radius:50%;display:grid;place-items:center;flex:none;
  align-self:center}
.g h3{font-size:14.5px;font-weight:600;margin:0;line-height:1.3}
.g p{font-size:13px;color:var(--meio);margin:0 0 12px;flex:1}
.g code{font-family:var(--m);font-size:11.5px;background:var(--papel);padding:1px 4px;border-radius:3px}
.g-f{display:flex;align-items:baseline;gap:7px;flex-wrap:wrap;border-top:1px solid var(--risco);
  padding-top:10px}
.g-v{font-family:var(--m);font-size:16px;font-weight:600;color:var(--gar);
  font-variant-numeric:tabular-nums}
.g-l{font-size:11.5px;color:var(--fraco)}
.g-d{margin-left:auto;font-family:var(--m);font-size:10px;letter-spacing:.05em;
  text-transform:uppercase;color:var(--meio);background:var(--papel);
  border:1px solid var(--risco);border-radius:20px;padding:2px 8px;white-space:nowrap}

footer{margin-top:34px;border-top:1px solid var(--risco);padding-top:16px;
  font-size:12.5px;color:var(--fraco)}
footer b{color:var(--meio);font-weight:600}

/* --- SVG --- */
.ch{font-family:var(--m);font-size:10px;letter-spacing:.13em;fill:var(--fraco)}
.rl{stroke:var(--risco);stroke-width:1}
.fx{fill:none;stroke:var(--risco);stroke-width:1}
.fx.la{stroke:color-mix(in srgb,var(--sis) 32%,transparent)}
.fx.lb{stroke:color-mix(in srgb,var(--sis) 32%,transparent)}
.fx.lc{stroke:var(--risco)}
.fxt{font-family:var(--m);font-size:12px;font-weight:600;letter-spacing:.1em;fill:var(--sis)}
.lc-t{fill:var(--meio)}
.fxs{font-family:var(--s);font-size:11.5px;fill:var(--fraco)}
.cx{fill:var(--carta);stroke:var(--borda);stroke-width:1}
.cx-ok{stroke:var(--rec);stroke-width:1.4}
.bt{font-family:var(--s);font-size:13.5px;font-weight:600;fill:var(--tinta)}
.bd{font-family:var(--s);font-size:10.8px;fill:var(--meio)}
.vz{font-family:var(--s);font-size:11.5px;font-style:italic;fill:var(--fraco)}
.fl{stroke:var(--seta);stroke-width:1.4;fill:none}
.fl-d{stroke-dasharray:4 3}
.fr{font-family:var(--m);font-size:9px;fill:var(--fraco);text-anchor:middle}
.mk{fill:var(--gar)}
.mkt{font-family:var(--m);font-size:11.5px;font-weight:600;fill:var(--carta);text-anchor:middle}
.sp{fill:color-mix(in srgb,var(--raiz) 9%,var(--carta));stroke:var(--raiz);stroke-width:1.3}
.spt{font-family:var(--m);font-size:12px;font-weight:600;letter-spacing:.06em;fill:var(--raiz)}
.spa{font-family:var(--s);font-size:12px;font-weight:600;fill:var(--tinta)}
.spb{font-family:var(--s);font-size:10.8px;fill:var(--meio)}
.spc{font-family:var(--s);font-size:12px;font-style:italic;fill:var(--raiz)}
.up{stroke:var(--raiz);stroke-width:1.2;stroke-dasharray:3 3;fill:none;opacity:.8}

@media (max-width:560px){.g-d{margin-left:0}}
@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
</style>

<div class="wrap">
<header>
  <p class="eyebrow">Case Tarvo Pagamentos &middot; competencia 09/2026</p>
  <h1>Do cartao do aluno ate o lancamento contabil</h1>
  <p class="lead">Duas linhas de negocio, cinco sistemas e uma planilha no meio. O mapa segue o dinheiro
  de ponta a ponta e marca os sete pontos onde o fechamento trava, erra ou vaza.</p>
</header>

<div class="kpis">
  <div class="k v"><b>R$ 270.506</b><span>receita apurada em setembro</span></div>
  <div class="k r"><b>R$ 2.995</b><span>cobrado a maior, por mes</span></div>
  <div class="k r"><b>R$ 35.369</b><span>comissao sem dono certo</span></div>
  <div class="k"><b>184</b><span>lancamentos conferidos a mao</span></div>
  <div class="k"><b>8 dias</b><span>uteis para fechar, com 3 pessoas</span></div>
</div>

<div class="mapa">__SVG__</div>
<div class="leg">
  <span><i class="i1"></i>sistema de origem ou parceiro</span>
  <span><i class="i2"></i>onde a Tarvo ganha e registra</span>
  <span><i class="i3"></i>gargalo (numerado abaixo)</span>
  <span><i class="i4"></i>a planilha que sustenta tudo</span>
</div>

<h2>Os sete gargalos</h2>
<p class="sub">Na ordem do fluxo, com o valor em jogo em setembro e quem precisa decidir.</p>
<div class="grade">__CARDS__</div>

<footer>
  Numeros apurados a partir dos seis arquivos do data pack de 09/2026 e conferidos contra as linhas de
  origem: <b>1.943</b> linhas da Orbe, <b>233</b> do relatorio da Ponte Cambio, <b>84</b> do extrato Aurora e
  <b>100</b> do OFX Meridiano. Toda cifra desta pagina sai de <b>rastro.csv</b> e soma com as linhas que a compoem.
</footer>
</div>'''

page = page.replace("__SVG__", svg).replace("__CARDS__", "\n".join(cards))
open("/tmp/claude-0/-home-claude/6993142e-a011-5c4d-8c6e-0cb243ffe1f2/scratchpad/mapa/fluxo-tarvo.html",
     "w", encoding="utf-8").write(page)
print("ok", len(page))
