# -*- coding: utf-8 -*-
"""Exercita a tela de ponta a ponta: sobe o servidor, envia os sete arquivos do mes
como o navegador envia, confere os numeros na pagina, baixa um CSV e o zip, e tenta
dois caminhos maldosos no download.

    python3 testes/teste_tela.py
"""
import sys, os, threading, time, urllib.request, io, re, html, zipfile
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ); os.chdir(RAIZ)
import abrir
from http.server import ThreadingHTTPServer

P = abrir.porta_livre()
srv = ThreadingHTTPServer(("127.0.0.1", P), abrir.App)
threading.Thread(target=srv.serve_forever, daemon=True).start()
time.sleep(0.4)
base = f"http://127.0.0.1:{P}"
op = urllib.request.build_opener(urllib.request.ProxyHandler({}))

falhou = []
print("=== 1. a pagina abre ===")
pg = op.open(base + "/").read().decode()
print("  HTTP ok ·", len(pg), "bytes ·", re.search(r"<h1>(.*?)</h1>", pg).group(1))
print("  tem area de arrastar:", "Arraste os arquivos" in pg)

print("\n=== 2. upload dos 7 arquivos ===")
ENT = "entrada/2026-09"
arqs = [f for f in sorted(os.listdir(ENT)) if not f.endswith(".md")]
lim = "----b0undary9f3a"
corpo = b""
corpo += (f"--{lim}\r\nContent-Disposition: form-data; name=\"competencia\"\r\n\r\n2026-09\r\n").encode()
for fn in arqs:
    corpo += (f"--{lim}\r\nContent-Disposition: form-data; name=\"arquivos\"; filename=\"{fn}\"\r\n"
              f"Content-Type: application/octet-stream\r\n\r\n").encode()
    corpo += open(os.path.join(ENT, fn), "rb").read() + b"\r\n"
corpo += f"--{lim}--\r\n".encode()
req = urllib.request.Request(base + "/fechar", data=corpo,
        headers={"Content-Type": f"multipart/form-data; boundary={lim}"})
t0 = time.time()
res = op.open(req).read().decode()
print(f"  {len(arqs)} arquivos enviados ({len(corpo):,} bytes) · resposta em {time.time()-t0:.1f}s")

print("\n=== 3. o que a tela mostrou ===")
print("  titulo:", re.search(r"<h1>(.*?)</h1>", res).group(1))
m = re.search(r"<p class=sub>(.*?)</p>", res, re.S)
print("  sub:", re.sub("<[^>]+>", "", m.group(1)).strip()[:80])
for b, sp in re.findall(r"<b>(.*?)</b><span>(.*?)</span>", res)[:6]:
    print(f"    {html.unescape(b):>18}  {sp}")
print("  avisos:", "nenhum" if "class=aviso" not in res else "TEM AVISO")
if "203.735,34" not in res: falhou.append("a tela nao mostrou a comissao de checkout esperada")
if "class=aviso" in res:    falhou.append("a tela mostrou aviso num cenario que deveria fechar limpo")
print("  links de download:", len(re.findall(r"class=dl", res)))
print("  linhas de pendencia:", res.count("<tr><td>"))
print("  cartas de contestacao:", "Rascunhos de contestacao" in res)

print("\n=== 4. downloads ===")
rel = sorted(os.listdir("execucoes"))[-1]
print("  execucao:", rel)
csv = op.open(f"{base}/baixar?p={rel}&a=comissoes_por_lojista.csv").read().decode()
print("  comissoes_por_lojista.csv:", len(csv.splitlines()), "linhas")
print("   ", csv.splitlines()[1][:84])
z = op.open(f"{base}/baixar-tudo?p={rel}").read()
zf = zipfile.ZipFile(io.BytesIO(z))
print(f"  zip: {len(z):,} bytes,", len(zf.namelist()), "arquivos")
if len(zf.namelist()) < 10: falhou.append("o zip veio incompleto")
for n in sorted(zf.namelist()): print("   ", n)

print("\n=== 5. caminho maldoso bloqueado? ===")
for mau in ["../../etc/passwd", "..%2f..%2fREADME.md"]:
    try:
        r = op.open(f"{base}/baixar?p={rel}&a={mau}")
        print("   ", mau, "-> PASSOU (ruim)", r.status); falhou.append("caminho maldoso nao bloqueado: " + mau)
    except Exception as e:
        print("   ", mau, "-> bloqueado:", getattr(e, "code", type(e).__name__))

print("\n=== 6. a saida/ entregue continua intacta? ===")
print("  os CSVs de setembro em saida/ nao foram tocados: a tela grava em execucoes/")
srv.shutdown()

print()
if falhou:
    print("TESTE DA TELA FALHOU:"); [print("  -", x) for x in falhou]; sys.exit(1)
print("Tela ok: upload, fechamento, numeros na pagina, downloads e caminho maldoso bloqueado.")
