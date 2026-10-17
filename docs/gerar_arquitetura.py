# -*- coding: utf-8 -*-
"""Mapa da arquitetura da solucao: dos seis arquivos do cliente aos sete de saida."""
import html

W, H = 1300, 960
S = []
def add(s): S.append(s)
def esc(t): return html.escape(str(t), quote=True)

COL = [(24, 212), (272, 158), (466, 268), (770, 180), (984, 292)]
CH = ["O QUE O CLIENTE MANDA", "CONFERE", "APURA", "FECHA", "O QUE A ANALISTA RECEBE"]

def chip(ci, y, h, titulo, sub, classe="cp", mk=None):
    x, w = COL[ci]
    add(f'<rect class="{classe}" x="{x}" y="{y}" width="{w}" height="{h}" rx="5"/>')
    add(f'<text class="ct" x="{x+11}" y="{y+17}">{esc(titulo)}</text>')
    if sub:
        add(f'<text class="cs" x="{x+11}" y="{y+31}">{esc(sub)}</text>')
    if mk:
        add(f'<text class="cm" x="{x+w-10}" y="{y+17}">{esc(mk)}</text>')

def caixa(ci, y, h, titulo, linhas, classe="bx"):
    x, w = COL[ci]
    add(f'<rect class="{classe}" x="{x}" y="{y}" width="{w}" height="{h}" rx="7"/>')
    add(f'<text class="bt" x="{x+13}" y="{y+23}">{esc(titulo)}</text>')
    ty = y + 41
    for l in linhas:
        add(f'<text class="bd" x="{x+13}" y="{ty}">{esc(l)}</text>')
        ty += 14
    return x, w

def seta(x1, y1, x2, y2, classe="fl"):
    add(f'<path class="{classe}" d="M{x1},{y1} L{x2},{y2}" marker-end="url(#p)"/>')

def cot(x1, y1, x2, y2, classe="fl"):
    """cotovelo horizontal-vertical-horizontal"""
    mx = (x1 + x2) / 2
    add(f'<path class="{classe}" d="M{x1},{y1} H{mx} V{y2} H{x2}" marker-end="url(#p)"/>')

# ---- cabecalhos ----
for i, t in enumerate(CH):
    add(f'<text class="ch" x="{COL[i][0]}" y="25">{esc(t)}</text>')
add(f'<line class="rl" x1="24" y1="36" x2="{W-24}" y2="36"/>')

# ---- ENTRADA ----
ENT = [("01 orbe relatorio .csv", "1.943 linhas · CSV pt-BR"),
       ("06 orbe ajustes .csv", "14 linhas · chegou as 13h"),
       ("02 taxas contratadas .xlsx", "planilha feita a mao · 2 abas"),
       ("03 ponte cambio .eml", "e-mail + anexo .xlsx"),
       ("05a aurora .csv", "8 linhas de preambulo"),
       ("05b meridiano .ofx", "OFX 1.0 SGML · cp1252"),
       ("04 plano de contas .csv", "latin-1 · 30 contas analiticas")]
y = 58
for t, s in ENT:
    chip(0, y, 40, t, s)
    y += 48
add(f'<text class="nt" x="{COL[0][0]}" y="{y+8}">achados por padrao de nome,</text>')
add(f'<text class="nt" x="{COL[0][0]}" y="{y+22}">nao por nome exato</text>')

# ---- VALIDACAO ----
vx, vw = caixa(1, 58, 322, "validacao.py", [
    "o arquivo chegou?", "o layout e o do mes", "passado?", "ha dois candidatos",
    "ao mesmo padrao?", "", "FONTE OK", "-> segue", "", "FONTE COM PROBLEMA",
    "-> bloqueia so a parte", "   que depende dela", "-> pendencia com", "   quem libera",
    "-> saida [PROVISORIO]"], "bx bx-gate")
for i in range(7):
    seta(COL[0][0] + COL[0][1] + 4, 78 + i * 48, vx - 8, 78 + i * 48, "fl fl-fino")

# ---- MOTOR ----
MX = COL[2][0]
caixa(2, 58, 56, "leitores.py", [
    "um leitor por formato · toda linha ja sai com arquivo_origem + ref_origem"])
caixa(2, 126, 72, "identidade.py", [
    "EC Orbe -> CNPJ -> nome truncado no extrato",
    "nome NUNCA e chave primaria: prefixo normalizado unico,",
    "empate ou ausencia viram pendencia"], "bx bx-chave")
caixa(2, 210, 72, "fechamento.py · CHECKOUT", [
    "comissao = valor_bruto x taxa CONTRATADA, linha a linha",
    "divergencia de contrato  x  devolucao por concessao",
    "estorno pela taxa da venda original"])
caixa(2, 294, 58, "fechamento.py · REMESSA", [
    "dedup por N da operacao · 50% do spread realizado",
    "spread negativo fora · competencia por contratacao"])
caixa(2, 364, 72, "classificacao.py", [
    "extrato -> conta analitica do plano Fenix",
    "REGRA 184/184 neste mes  ·  IA no residuo, com confianca",
    "abaixo de 0,95 -> HUMANO e pendencia"])
for a, b in ((114, 126), (198, 210), (282, 294), (352, 364)):
    seta(MX + 134, a, MX + 134, b - 4)
seta(vx + vw + 6, 86, MX - 8, 86)

# ---- AUTOTESTE ----
ax, aw = caixa(3, 150, 250, "saida.py", [
    "SEIS INVARIANTES", "", "1 todo id_saida fecha", "   com o rastro",
    "2 checkout = soma das", "   comissoes por linha", "3 remessa = soma das",
    "   parcelas por operacao", "4 todo EC resolvido ou", "   com pendencia",
    "5 toda operacao da Ponte", "   aparece uma vez", "6 toda pendencia com",
    "   valor fecha", "", "falhou -> NAO GRAVA"], "bx bx-gate")
for yy in (240, 324, 398):
    cot(MX + COL[2][1] + 4, yy, ax - 8, 275)

# ---- SAIDA ----
SAI = [("comissoes_por_lojista.csv", "36 linhas · R$ 243.278,79", "cp cp-ok"),
       ("divergencias_taxa.csv", "115 · R$ 2.995,10 a cobrar", "cp cp-ok"),
       ("devolucoes_lojista.csv", "118 · R$ 15.396,77 da Tarvo", "cp cp-ok"),
       ("notas_a_emitir.csv", "21 notas", "cp cp-ok"),
       ("lancamentos_classificados.csv", "184 · 100% com conta", "cp cp-ok"),
       ("pendencias.csv", "31 · o que a analista le", "cp cp-pend"),
       ("rastro.csv", "5.389 linhas · 505 id_saida", "cp cp-rastro"),
       ("contestacoes/", "3 e-mails + anexos", "cp cp-ok")]
y = 58
for t, s, c in SAI:
    chip(4, y, 40, t, s, c)
    y += 48
seta(ax + aw + 6, 275, COL[4][0] - 8, 275)

# ---- CADASTRO (espinha) ----
add(f'<rect class="sp" x="{MX}" y="462" width="{COL[2][1]}" height="86" rx="7"/>')
add(f'<text class="spt" x="{MX+13}" y="482">cadastro/ — a regra sai da cabeca da analista</text>')
add(f'<text class="bd" x="{MX+13}" y="500">de_para_ec.csv — os ECs que a planilha nao resolve</text>')
add(f'<text class="bd" x="{MX+13}" y="514">condicoes_especiais.csv — o que o comercial fecha</text>')
add(f'<text class="bd" x="{MX+13}" y="528">comum.py — toda premissa discutivel, uma linha cada</text>')
add(f'<text class="bd" x="{MX+13}" y="542">versionado no git: quem mudou, quando e por que</text>')
add(f'<path class="up" d="M{MX+40},458 V202" marker-end="url(#pu)"/>')
add(f'<path class="up" d="M{MX+150},458 V286" marker-end="url(#pu)"/>')
add(f'<path class="up" d="M{MX+240},458 V440" marker-end="url(#pu)"/>')

# resposta do financeiro -> cadastro
add(f'<rect class="hm" x="24" y="462" width="{COL[0][1]+COL[1][1]+36}" height="86" rx="7"/>')
add(f'<text class="hmt" x="37" y="482">#tarvo-financeiro</text>')
add(f'<text class="bd" x="37" y="500">22 regras respondidas, com autor e horario</text>')
add(f'<text class="bd" x="37" y="514">9 decisoes delegadas, com o motivo escrito</text>')
add(f'<text class="bd" x="37" y="528">3 premissas abertas, pelo efeito na mesa dela</text>')
add(f'<text class="bd" x="37" y="542">HIPOTESES.md</text>')
seta(24 + COL[0][1] + COL[1][1] + 42, 505, MX - 8, 505, "fl")

# ---- TESTES POR FORA ----
add(f'<rect class="tf" x="24" y="598" width="{W-48}" height="96" rx="7"/>')
add(f'<text class="tft" x="40" y="621">testes/ — rodam POR FORA do motor</text>')
tt = [("conformidade_formato.py", "separador, decimal, datas, CNPJ, dominios,",
       "ref_origem por fonte, conta que aceita lancamento"),
      ("teste_fontes.py", "tres cenarios: tudo no lugar, Ponte ausente,",
       "layout do banco trocado. O checkout fecha igual nos tres"),
      ("auditoria_rastro.py", "NAO importa nada de src/. Rele os CSVs gravados",
       "e os arquivos crus. Achou 15 pendencias sem rastro")]
for i, (a, b, c) in enumerate(tt):
    x = 40 + i * 412
    add(f'<text class="tn" x="{x}" y="645">{esc(a)}</text>')
    add(f'<text class="bd" x="{x}" y="661">{esc(b)}</text>')
    add(f'<text class="bd" x="{x}" y="675">{esc(c)}</text>')
add(f'<path class="up" d="M{COL[4][0]+140},594 V{58+8*48-4}" marker-end="url(#pu)"/>')

# ---- rodape ----
add(f'<text class="ft" x="24" y="726">python3 fechar.py  —  sem argumento, sem chave de API, sem passo manual antes de rodar.</text>')
add(f'<text class="ft2" x="24" y="744">Em outubro: mesma pasta, arquivos novos, mesmo comando. O que mudar de regra mora em cadastro/ e em comum.py.</text>')

svg = f'''<svg viewBox="0 0 {W} 770" width="{W}" role="img"
 aria-label="Arquitetura da solucao de fechamento: seis arquivos de entrada passam por validacao, leitores, cadastro de identidade, motores de checkout e remessa, classificacao contabil e seis invariantes, e saem como sete arquivos mais os rascunhos de contestacao">
<defs>
 <marker id="p" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
  <path d="M0,1 L9,5 L0,9 z" fill="var(--seta)"/></marker>
 <marker id="pu" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
  <path d="M0,1 L9,5 L0,9 z" fill="var(--raiz)"/></marker>
</defs>
{chr(10).join(S)}
</svg>'''

page = '''<title>Arquitetura do fechamento</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Serif:wght@600;700&display=swap">
<style>
/* Fluxo da esquerda para a direita com dois portoes; o cadastro atravessa por baixo. */
:root{
  --papel:#f6f7f9; --carta:#ffffff; --tinta:#131821; --meio:#5c6675; --fraco:#8d97a6;
  --risco:#dde2e9; --borda:#cbd3dd;
  --sis:#2c4a7c; --rec:#0f6b5c; --gar:#a8322a; --raiz:#9a6412; --seta:#9aa5b4;
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
.wrap{max-width:1340px;margin:0 auto;
  padding-left:max(16px,env(safe-area-inset-left,0px));
  padding-right:max(16px,env(safe-area-inset-right,0px));
  padding-block:28px 52px}
header{border-bottom:2px solid var(--tinta);padding-bottom:16px;margin-bottom:20px}
.eyebrow{font-family:var(--m);font-size:11px;letter-spacing:.16em;text-transform:uppercase;
  color:var(--meio);margin:0 0 8px}
h1{font-family:var(--d);font-weight:700;font-size:clamp(26px,4.6vw,40px);line-height:1.1;
  margin:0 0 10px;text-wrap:balance;letter-spacing:-.015em}
.lead{font-size:clamp(14px,2.1vw,16px);color:var(--meio);max-width:66ch;margin:0}
.mapa{background:var(--carta);border:1px solid var(--borda);border-radius:10px;
  overflow-x:auto;padding:14px;margin-bottom:10px}
.mapa svg{display:block;min-width:1180px;height:auto}
.leg{display:flex;flex-wrap:wrap;gap:8px 20px;font-size:12px;color:var(--meio);margin-bottom:34px}
.leg i{display:inline-block;width:11px;height:11px;border-radius:3px;margin-right:6px;
  vertical-align:-1px;border:1px solid var(--borda)}
.leg .i1{background:var(--carta);border-color:var(--borda)}
.leg .i2{background:color-mix(in srgb,var(--sis) 10%,var(--carta));border-color:var(--sis)}
.leg .i3{background:color-mix(in srgb,var(--rec) 10%,var(--carta));border-color:var(--rec)}
.leg .i4{background:color-mix(in srgb,var(--raiz) 10%,var(--carta));border-color:var(--raiz)}
h2{font-family:var(--d);font-size:clamp(19px,3vw,24px);margin:0 0 14px;letter-spacing:-.01em}
.grade{display:grid;gap:12px;grid-template-columns:repeat(auto-fill,minmax(290px,1fr))}
.p{background:var(--carta);border:1px solid var(--borda);border-left:3px solid var(--sis);
  border-radius:8px;padding:14px 15px;min-width:0}
.p h3{font-size:14px;font-weight:600;margin:0 0 6px}
.p p{font-size:13px;color:var(--meio);margin:0}
.p code{font-family:var(--m);font-size:11.5px;background:var(--papel);padding:1px 4px;border-radius:3px}
.p.g{border-left-color:var(--raiz)}
.p.v{border-left-color:var(--rec)}
footer{margin-top:30px;border-top:1px solid var(--risco);padding-top:14px;
  font-size:12.5px;color:var(--fraco)}

/* SVG */
.ch{font-family:var(--m);font-size:10px;letter-spacing:.13em;fill:var(--fraco)}
.rl{stroke:var(--risco);stroke-width:1}
.cp{fill:var(--carta);stroke:var(--borda);stroke-width:1}
.cp-ok{stroke:var(--rec)}
.cp-pend{stroke:var(--gar);stroke-width:1.4}
.cp-rastro{stroke:var(--raiz);stroke-width:1.4}
.ct{font-family:var(--m);font-size:11.5px;font-weight:500;fill:var(--tinta)}
.cs{font-family:var(--s);font-size:10.2px;fill:var(--fraco)}
.bx{fill:var(--carta);stroke:var(--borda);stroke-width:1}
.bx-gate{fill:color-mix(in srgb,var(--sis) 7%,var(--carta));stroke:var(--sis);stroke-width:1.3}
.bx-chave{stroke:var(--rec);stroke-width:1.4}
.bt{font-family:var(--m);font-size:12.5px;font-weight:600;fill:var(--tinta)}
.bd{font-family:var(--s);font-size:10.6px;fill:var(--meio)}
.nt{font-family:var(--s);font-size:10.5px;font-style:italic;fill:var(--fraco)}
.fl{stroke:var(--seta);stroke-width:1.4;fill:none}
.fl-fino{stroke-width:1}
.sp{fill:color-mix(in srgb,var(--raiz) 9%,var(--carta));stroke:var(--raiz);stroke-width:1.3}
.spt{font-family:var(--m);font-size:12px;font-weight:600;fill:var(--raiz)}
.hm{fill:color-mix(in srgb,var(--gar) 7%,var(--carta));stroke:var(--gar);stroke-width:1.2}
.hmt{font-family:var(--m);font-size:12px;font-weight:600;fill:var(--gar)}
.tf{fill:none;stroke:var(--risco);stroke-width:1;stroke-dasharray:4 3}
.tft{font-family:var(--m);font-size:12px;font-weight:600;letter-spacing:.06em;fill:var(--meio)}
.tn{font-family:var(--m);font-size:11.5px;font-weight:600;fill:var(--tinta)}
.up{stroke:var(--raiz);stroke-width:1.2;stroke-dasharray:3 3;fill:none;opacity:.85}
.ft{font-family:var(--m);font-size:12px;font-weight:600;fill:var(--tinta)}
.ft2{font-family:var(--s);font-size:11.5px;fill:var(--meio)}
@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
</style>

<div class="wrap">
<header>
  <p class="eyebrow">Time Prime &middot; case Tarvo &middot; competencia 09/2026</p>
  <h1>Como a nossa solu&ccedil;&atilde;o est&aacute; montada</h1>
  <p class="lead">Dos seis arquivos como o cliente manda at&eacute; os sete que a analista recebe.
  Dois port&otilde;es no caminho: um confere se as fontes chegaram inteiras, o outro recusa a gravar
  se algum total n&atilde;o fechar com as linhas de origem.</p>
</header>

<div class="mapa">__SVG__</div>
<div class="leg">
  <span><i class="i1"></i>arquivo do cliente</span>
  <span><i class="i2"></i>port&atilde;o: confere e pode barrar</span>
  <span><i class="i3"></i>onde o n&uacute;mero nasce e sai</span>
  <span><i class="i4"></i>onde a regra mora, versionada</span>
</div>

<h2>As quatro decis&otilde;es que sustentam isso</h2>
<div class="grade">
  <article class="p v"><h3>Nome nunca &eacute; chave prim&aacute;ria</h3>
    <p>A chave &eacute; o CNPJ de 14 d&iacute;gitos e, no checkout, o <code>cod_estabelecimento</code>.
    Onde s&oacute; existe nome truncado, a resolu&ccedil;&atilde;o &eacute; por prefixo normalizado
    <strong>&uacute;nico</strong>: empate ou aus&ecirc;ncia viram pend&ecirc;ncia, nunca palpite.</p></article>
  <article class="p g"><h3>A regra sai da cabe&ccedil;a da analista</h3>
    <p>O de-para dos ECs, as condi&ccedil;&otilde;es que o comercial fecha e toda premissa
    discut&iacute;vel moram em arquivos versionados. Mudar uma resposta do financeiro &eacute;
    mudar uma linha e rodar de novo.</p></article>
  <article class="p"><h3>Nenhum palpite silencioso</h3>
    <p>O que n&atilde;o casa por chave vira linha em <code>pendencias.csv</code> com motivo e dono.
    Nunca um <code>fillna</code>, nunca um casamento aproximado aceito sozinho. A IA sugere e
    devolve confian&ccedil;a; abaixo de 0,95 &eacute; pessoa, n&atilde;o c&oacute;digo.</p></article>
  <article class="p"><h3>Nada &eacute; gravado sem fechar</h3>
    <p>Seis invariantes rodam antes da grava&ccedil;&atilde;o. Se uma falhar, a sa&iacute;da
    n&atilde;o sai. Total que n&atilde;o fecha com as linhas de origem &eacute; pior que total
    que falta.</p></article>
</div>

<footer>
  O mapa do processo do cliente &mdash; do cart&atilde;o do aluno at&eacute; o lan&ccedil;amento
  cont&aacute;bil, com os sete gargalos &mdash; &eacute; a outra metade desta hist&oacute;ria e est&aacute;
  em <strong>Fluxo e gargalos da Tarvo</strong>. Este aqui &eacute; o que a gente construiu em cima dele.
</footer>
</div>'''

page = page.replace("__SVG__", svg)
open("/tmp/claude-0/-home-claude/6993142e-a011-5c4d-8c6e-0cb243ffe1f2/scratchpad/mapa/arquitetura-tarvo.html",
     "w", encoding="utf-8").write(page)
print("ok", len(page))
