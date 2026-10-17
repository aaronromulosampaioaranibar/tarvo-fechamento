#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tela do fechamento. Nenhuma dependencia alem do openpyxl que o motor ja usa.

    python3 abrir.py          (ou duplo clique em rodar.bat / rodar.command)

Sobe um servidor so na propria maquina (127.0.0.1), abre o navegador, e a pessoa
arrasta os arquivos do mes. Nada sai do computador dela: nao ha envio para nenhum
servidor externo, nenhuma chave de API, e funciona sem internet.
"""
import os, sys, io, re, json, zipfile, shutil, socket, webbrowser, datetime as dt
import email, email.policy
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

RAIZ = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, RAIZ)
from src.fechamento import Fechamento
from src.saida import gravar, autoteste
from src.contestacoes import gerar as gerar_contestacoes
from src.execucao import registrar
from src import web

EXECUCOES = os.path.join(RAIZ, "execucoes")
SEGURO = re.compile(r"^[A-Za-z0-9._ ()\-\u00C0-\u017F]+$")

ARQS = [("comissoes_por_lojista.csv", "comissao por lojista e linha"),
        ("divergencias_taxa.csv", "o que cobrar dos parceiros"),
        ("devolucoes_lojista.csv", "o que devolver do nosso bolso"),
        ("notas_a_emitir.csv", "notas do mes"),
        ("lancamentos_classificados.csv", "extratos no plano de contas"),
        ("pendencias.csv", "o que precisa de voce"),
        ("rastro.csv", "de onde sai cada numero"),
        ("execucao.json", "registro desta rodada")]

def partes(headers, corpo):
    """multipart/form-data sem o modulo cgi, que saiu do Python 3.13."""
    bruto = (b"Content-Type: " + headers.get("Content-Type", "").encode()
             + b"\r\nMIME-Version: 1.0\r\n\r\n" + corpo)
    msg = email.message_from_bytes(bruto, policy=email.policy.default)
    campos, arquivos = {}, []
    for p in msg.iter_parts():
        nome = p.get_param("name", header="content-disposition")
        fn = p.get_filename()
        dados = p.get_payload(decode=True)
        if fn:
            if dados: arquivos.append((os.path.basename(fn), dados))
        elif nome:
            campos[nome] = (dados or b"").decode("utf-8", "replace").strip()
    return campos, arquivos

class App(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def _envia(self, corpo, tipo="text/html; charset=utf-8", codigo=200, nome=None):
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(corpo)))
        if nome:
            self.send_header("Content-Disposition", f'attachment; filename="{nome}"')
        self.end_headers()
        self.wfile.write(corpo)

    def do_GET(self):
        u = urlparse(self.path); q = parse_qs(u.query)
        if u.path == "/":
            hoje = dt.date.today()
            mes = (hoje.replace(day=1) - dt.timedelta(days=1)).strftime("%Y-%m")
            return self._envia(web.form(mes))
        if u.path in ("/baixar", "/baixar-tudo"):
            pasta = self._pasta(q.get("p", [""])[0])
            if not pasta: return self._envia(b"pasta invalida", "text/plain", 400)
            if u.path == "/baixar":
                nome = q.get("a", [""])[0]
                if not SEGURO.match(nome or ""):
                    return self._envia(b"arquivo invalido", "text/plain", 400)
                cam = os.path.join(pasta, "saida", nome)
                if not os.path.isfile(cam):
                    return self._envia(b"nao encontrado", "text/plain", 404)
                return self._envia(open(cam, "rb").read(), "text/csv; charset=utf-8", 200, nome)
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
                for sub in ("saida", "contestacoes"):
                    base = os.path.join(pasta, sub)
                    for r, _, fs in os.walk(base):
                        for fn in fs:
                            c = os.path.join(r, fn)
                            z.write(c, os.path.join(sub, os.path.relpath(c, base)))
            return self._envia(buf.getvalue(), "application/zip", 200, "fechamento.zip")
        self._envia(b"nao encontrado", "text/plain", 404)

    def _pasta(self, rel):
        if not rel or not SEGURO.match(rel): return None
        p = os.path.join(EXECUCOES, rel)
        return p if os.path.isdir(p) else None

    def do_POST(self):
        if urlparse(self.path).path != "/fechar":
            return self._envia(b"nao encontrado", "text/plain", 404)
        try:
            n = int(self.headers.get("Content-Length", 0))
            campos, arquivos = partes(self.headers, self.rfile.read(n))
            comp = campos.get("competencia", "")
            if not re.match(r"^\d{4}-\d{2}$", comp):
                return self._envia(web.form(comp, "Competencia precisa estar no formato AAAA-MM."))
            if not arquivos:
                return self._envia(web.form(comp, "Nenhum arquivo foi enviado."))

            marca = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
            rel = f"{comp}_{marca}"
            pasta = os.path.join(EXECUCOES, rel)
            ent = os.path.join(pasta, "entrada")
            os.makedirs(ent, exist_ok=True)
            for fn, dados in arquivos:
                with open(os.path.join(ent, fn), "wb") as fh: fh.write(dados)

            inicio = dt.datetime.now()
            f = Fechamento(ent, raiz=RAIZ, competencia=comp).executar()
            ok, falhas, conferencias = autoteste(f)
            sai = os.path.join(pasta, "saida")
            if ok:
                gravar("comissoes_por_lojista.csv", f.cms_checkout + f.cms_remessa, sai)
                gravar("divergencias_taxa.csv", f.div_checkout + f.div_remessa, sai)
                gravar("devolucoes_lojista.csv", f.devolucoes, sai)
                gravar("notas_a_emitir.csv", f.nfs, sai)
                gravar("lancamentos_classificados.csv", f.lcts, sai)
                gravar("pendencias.csv", f.pend, sai)
                gravar("rastro.csv", f.rastro, sai)
            cont = gerar_contestacoes(f, os.path.join(pasta, "contestacoes")) if ok else []
            reg = registrar(f, ent, sai, inicio)
            tem = [(nome, t) for nome, t in ARQS if os.path.isfile(os.path.join(sai, nome))]
            return self._envia(web.resultado(f, reg, ok, falhas, conferencias, rel, tem, cont))
        except FileNotFoundError as e:
            return self._envia(web.form(campos.get("competencia", ""),
                f"Faltou um arquivo que o fechamento precisa: {e}"))
        except Exception as e:
            import traceback; traceback.print_exc()
            return self._envia(web.form(campos.get("competencia", "") if "campos" in dir() else "",
                f"Nao consegui ler os arquivos: {type(e).__name__}: {e}"))

def porta_livre(inicio=8777):
    for p in range(inicio, inicio + 40):
        with socket.socket() as s:
            if s.connect_ex(("127.0.0.1", p)) != 0: return p
    return 0

def main():
    os.makedirs(EXECUCOES, exist_ok=True)
    p = porta_livre()
    url = f"http://127.0.0.1:{p}/"
    srv = ThreadingHTTPServer(("127.0.0.1", p), App)
    print(f"""
  Fechamento Tarvo

  A tela abriu no seu navegador. Se nao abrir, copie este endereco:

      {url}

  Tudo roda nesta maquina. Nenhum arquivo sai daqui.
  Para encerrar, feche esta janela.
""")
    try: webbrowser.open(url)
    except Exception: pass
    try: srv.serve_forever()
    except KeyboardInterrupt: print("  encerrado.")

if __name__ == "__main__":
    main()
