# -*- coding: utf-8 -*-
"""Paginas da tela de fechamento. HTML inline, sem CDN: tem de funcionar sem internet."""
import html, json

def esc(t): return html.escape(str(t), quote=True)

def brl(v):
    s = f"{abs(float(v or 0)):,.2f}".replace(",", "@").replace(".", ",").replace("@", ".")
    return ("-" if float(v or 0) < 0 else "") + "R$ " + s

CSS = """
*{box-sizing:border-box}
:root{--papel:#f6f7f9;--carta:#fff;--tinta:#131821;--meio:#5c6675;--fraco:#8d97a6;
 --risco:#dde2e9;--borda:#cbd3dd;--sis:#2c4a7c;--rec:#0f6b5c;--gar:#a8322a;--raiz:#9a6412;
 --s:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
 --m:ui-monospace,SFMono-Regular,Consolas,Menlo,monospace}
@media (prefers-color-scheme:dark){:root{--papel:#0f131a;--carta:#171d27;--tinta:#e6eaf0;
 --meio:#9aa5b4;--fraco:#6d7786;--risco:#262e3a;--borda:#323c4a;--sis:#8fb1e8;--rec:#4fc0a8;
 --gar:#f0847a;--raiz:#e0ad5c;color-scheme:dark}}
body{background:var(--papel);color:var(--tinta);font-family:var(--s);line-height:1.5;margin:0;
 padding:32px 20px 64px}
.w{max-width:960px;margin:0 auto}
h1{font-size:28px;margin:0 0 6px;letter-spacing:-.02em}
.sub{color:var(--meio);margin:0 0 26px;font-size:15px}
.card{background:var(--carta);border:1px solid var(--borda);border-radius:10px;padding:22px;
 margin-bottom:18px}
label{display:block;font-weight:600;font-size:14px;margin-bottom:6px}
.hint{color:var(--fraco);font-size:12.5px;margin:4px 0 0}
input[type=text]{font-family:var(--m);font-size:15px;padding:9px 11px;border:1px solid var(--borda);
 border-radius:7px;background:var(--papel);color:var(--tinta);width:160px}
.drop{border:2px dashed var(--borda);border-radius:10px;padding:34px 20px;text-align:center;
 background:var(--papel);cursor:pointer;transition:border-color .15s,background .15s}
.drop:hover,.drop.on{border-color:var(--sis);background:color-mix(in srgb,var(--sis) 6%,var(--papel))}
.drop b{display:block;font-size:16px;margin-bottom:4px}
.drop span{color:var(--fraco);font-size:13px}
#lista{margin:14px 0 0;padding:0;list-style:none}
#lista li{font-family:var(--m);font-size:12.5px;padding:5px 0;border-bottom:1px solid var(--risco);
 display:flex;justify-content:space-between;gap:12px}
#lista li span{color:var(--fraco)}
button{font-family:var(--s);font-size:15px;font-weight:600;padding:12px 22px;border:0;
 border-radius:8px;background:var(--sis);color:#fff;cursor:pointer;margin-top:18px}
button:disabled{background:var(--borda);color:var(--fraco);cursor:not-allowed}
button:not(:disabled):hover{filter:brightness(1.1)}
table{width:100%;border-collapse:collapse;font-size:13.5px}
th,td{text-align:left;padding:8px 10px;border-bottom:1px solid var(--risco);vertical-align:top}
th{font-size:11px;text-transform:uppercase;letter-spacing:.07em;color:var(--fraco);font-weight:600}
td.n{text-align:right;font-family:var(--m);font-variant-numeric:tabular-nums;white-space:nowrap}
h2{font-size:18px;margin:0 0 14px}
.kpi{display:flex;flex-wrap:wrap;gap:12px;margin-bottom:18px}
.k{flex:1 1 180px;background:var(--carta);border:1px solid var(--borda);border-radius:9px;padding:14px 16px}
.k b{display:block;font-family:var(--m);font-size:21px;font-variant-numeric:tabular-nums;letter-spacing:-.02em}
.k span{display:block;font-size:12px;color:var(--meio);margin-top:3px}
.k.v b{color:var(--rec)} .k.r b{color:var(--gar)}
.ok{color:var(--rec);font-weight:600} .err{color:var(--gar);font-weight:600}
.aviso{border-left:4px solid var(--gar);background:color-mix(in srgb,var(--gar) 7%,var(--carta));
 padding:14px 16px;border-radius:0 8px 8px 0;margin-bottom:18px;font-size:14px}
.aviso.b{border-left-color:var(--raiz);background:color-mix(in srgb,var(--raiz) 8%,var(--carta))}
a.dl{display:inline-flex;align-items:center;gap:8px;font-family:var(--m);font-size:13px;
 padding:9px 13px;border:1px solid var(--borda);border-radius:7px;text-decoration:none;
 color:var(--tinta);background:var(--papel);margin:0 8px 8px 0}
a.dl:hover{border-color:var(--sis)}
a.dl em{font-style:normal;color:var(--fraco);font-size:11.5px}
a.zip{border-color:var(--rec);color:var(--rec);font-weight:600}
a.volta{display:inline-block;margin-top:22px;color:var(--meio);font-size:14px}
.ck{font-family:var(--m);font-size:12.5px;line-height:1.75;margin:0;padding:0;list-style:none}
details{margin-top:10px}summary{cursor:pointer;font-size:13.5px;color:var(--meio)}
"""

def pagina(titulo, corpo):
    return ("<!doctype html><html lang=pt-BR><head><meta charset=utf-8>"
            "<meta name=viewport content='width=device-width,initial-scale=1'>"
            f"<title>{esc(titulo)}</title><style>{CSS}</style></head>"
            f"<body><div class=w>{corpo}</div></body></html>").encode("utf-8")

def form(competencia, erro=None):
    av = f"<div class=aviso>{esc(erro)}</div>" if erro else ""
    return pagina("Fechamento Tarvo", f"""
<h1>Fechamento do mes</h1>
<p class=sub>Coloque aqui os arquivos do mes, do jeito que eles chegaram.
Nao precisa renomear, converter nem limpar nada.</p>
{av}
<form method=post action=/fechar enctype=multipart/form-data id=f>
  <div class=card>
    <label for=c>Competencia</label>
    <input type=text id=c name=competencia value="{esc(competencia)}" pattern="\\d{{4}}-\\d{{2}}" required>
    <p class=hint>No formato AAAA-MM. E o mes que vai ser fechado.</p>
  </div>
  <div class=card>
    <label>Arquivos do mes</label>
    <div class=drop id=d onclick="document.getElementById('a').click()">
      <b>Arraste os arquivos para ca</b>
      <span>ou clique para escolher &mdash; relatorio da Orbe, planilha de taxas,
      e-mail da Ponte, os dois extratos e o plano de contas</span>
    </div>
    <input type=file id=a name=arquivos multiple hidden>
    <ul id=lista></ul>
    <p class=hint id=obs></p>
    <button type=submit id=b disabled>Fechar o mes</button>
  </div>
</form>
<script>
var d=document.getElementById('d'),a=document.getElementById('a'),
    L=document.getElementById('lista'),b=document.getElementById('b'),o=document.getElementById('obs');
function kb(n){{return n<1024?n+' B':n<1048576?(n/1024).toFixed(0)+' KB':(n/1048576).toFixed(1)+' MB';}}
function pinta(){{
  L.innerHTML='';
  var fs=a.files;
  for(var i=0;i<fs.length;i++){{
    var li=document.createElement('li');
    li.innerHTML='<span style="color:var(--tinta)">'+fs[i].name+'</span><span>'+kb(fs[i].size)+'</span>';
    L.appendChild(li);
  }}
  b.disabled = fs.length===0;
  o.textContent = fs.length ? fs.length+' arquivo(s) prontos.' : '';
}}
a.addEventListener('change',pinta);
['dragenter','dragover'].forEach(function(e){{d.addEventListener(e,function(ev){{
  ev.preventDefault();d.classList.add('on');}});}});
['dragleave','drop'].forEach(function(e){{d.addEventListener(e,function(ev){{
  ev.preventDefault();d.classList.remove('on');}});}});
d.addEventListener('drop',function(ev){{a.files=ev.dataTransfer.files;pinta();}});
document.getElementById('f').addEventListener('submit',function(){{
  b.disabled=true;b.textContent='Fechando...';}});
</script>""")


def resultado(f, reg, ok, falhas, conferencias, pasta_rel, arquivos, cont):
    chk = sum(c["comissao_brl"] for c in f.cms_checkout)
    rem = sum(c["comissao_brl"] for c in f.cms_remessa)
    dv  = sum(d["diferenca_brl"] for d in f.div_checkout + f.div_remessa)
    de  = sum(d["valor_brl"] for d in f.devolucoes)

    avisos = ""
    if f.provisorio:
        bl = "; ".join(f"{k} (falta {', '.join(v)})" for k, v in f.bloqueios.items())
        avisos += (f"<div class='aviso b'><b>Fechamento provisorio.</b> "
                   f"Parte do mes ficou bloqueada: {esc(bl)}. O resto fechou e os numeros "
                   f"abaixo sao parciais. Assim que o arquivo chegar, e so rodar de novo.</div>")
    if not ok:
        avisos += ("<div class=aviso><b>Os numeros nao fecharam com as linhas de origem.</b> "
                   "Nada foi gravado. " + esc("; ".join(falhas[:3])) + "</div>")

    kpi = f"""<div class=kpi>
      <div class='k v'><b>{brl(chk + rem)}</b><span>receita do mes</span></div>
      <div class=k><b>{brl(chk)}</b><span>checkout, {len(f.cms_checkout)} lojistas</span></div>
      <div class=k><b>{brl(rem)}</b><span>remessa, {len(f.cms_remessa)} lojistas</span></div>
      <div class='k r'><b>{brl(dv)}</b><span>a cobrar dos parceiros</span></div>
      <div class='k r'><b>{brl(de)}</b><span>a devolver ao lojista</span></div>
      <div class=k><b>{len(f.pend)}</b><span>pendencias para voce</span></div>
    </div>"""

    pend = "".join(
        f"<tr><td>{esc(p['tipo'].replace('_',' ').title())}</td>"
        f"<td>{esc(p['motivo'][:170])}</td>"
        f"<td>{esc(p['quem_decide'])}</td>"
        f"<td class=n>{brl(p['valor_brl']) if abs(p['valor_brl'])>0.005 else '&mdash;'}</td></tr>"
        for p in sorted(f.pend, key=lambda x: -abs(x["valor_brl"])))

    dls = "".join(
        f"<a class=dl href='/baixar?p={esc(pasta_rel)}&a={esc(n)}' download>{esc(n)} "
        f"<em>{t}</em></a>" for n, t in arquivos)
    dls += (f"<a class='dl zip' href='/baixar-tudo?p={esc(pasta_rel)}' download>"
            f"baixar tudo (.zip)</a>")

    cartas = ""
    if cont:
        linhas = "".join(f"<tr><td>{esc(d)}</td><td class=n>{brl(v)}</td>"
                         f"<td class=n>{n}</td></tr>" for d, v, n in cont)
        cartas = f"""<div class=card><h2>Rascunhos de contestacao</h2>
          <p class=sub style='margin-bottom:14px'>Prontos para voce revisar e enviar.
          Cada um vai com o anexo das operacoes. Estao dentro do .zip, na pasta
          <code>contestacoes/</code>.</p>
          <table><thead><tr><th>Para</th><th>Valor</th><th>Operacoes</th></tr></thead>
          <tbody>{linhas}</tbody></table></div>"""

    cks = "".join(f"<li><span class=ok>ok</span> {esc(c)}</li>" for c in conferencias)

    return pagina("Fechamento pronto", f"""
<h1>Fechamento de {esc(f.comp)}</h1>
<p class=sub>{len(reg['entradas'])} arquivos lidos em {reg['duracao_s']}s.
Rodado em {esc(reg['executado_em'].replace('T',' as '))}.</p>
{avisos}
{kpi}
<div class=card>
  <h2>Baixar</h2>
  {dls}
  <details><summary>o que foi conferido antes de gravar</summary>
  <ul class=ck>{cks}</ul></details>
</div>
{cartas}
<div class=card>
  <h2>O que precisa de voce &mdash; {len(f.pend)} itens</h2>
  <table><thead><tr><th>Tipo</th><th>Motivo</th><th>Quem decide</th><th>Valor</th></tr></thead>
  <tbody>{pend}</tbody></table>
</div>
<a class=volta href='/'>&larr; fechar outro mes</a>""")
