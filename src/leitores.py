# -*- coding: utf-8 -*-
"""Um leitor por formato. Le o arquivo como o cliente manda; nao altera a origem.
Toda linha sai daqui ja carregando arquivo_origem e ref_origem."""
import os, re, glob, email, email.policy, io
import openpyxl
from .comum import brl, pct, data_br, cnpj14, digitos

# Os arquivos sao localizados por PADRAO, nao por nome exato: em outubro o nome muda.
PADROES = {
    "orbe":     ["*orbe*comiss*.csv", "*orbe*.csv"],
    "taxas":    ["*taxas*contratadas*.xlsx", "*taxas*.xlsx"],
    "ponte":    ["*ponte*cambio*.eml", "*cambio*.eml", "*.eml"],
    "plano":    ["*plano*contas*.csv"],
    "aurora":   ["*aurora*.csv"],
    "meridiano":["*meridiano*.ofx", "*.ofx"],
}

def achar(pasta, chave):
    for p in PADROES[chave]:
        hits = sorted(glob.glob(os.path.join(pasta, p)))
        hits = [h for h in hits if os.path.isfile(h)]
        if hits:
            if len(hits) > 1:
                raise RuntimeError(f"mais de um arquivo para '{chave}' em {pasta}: {hits}")
            return hits[0]
    raise FileNotFoundError(f"nao achei arquivo de '{chave}' em {pasta} (padroes {PADROES[chave]})")

def _texto(caminho):
    """CSV do cliente vem ora em utf-8, ora em latin-1. Detecta."""
    bruto = open(caminho, "rb").read()
    for enc in ("utf-8", "utf-8-sig", "cp1252", "latin-1"):
        try: return bruto.decode(enc)
        except UnicodeDecodeError: continue
    return bruto.decode("latin-1", "replace")

# ---------------------------------------------------------------- ORBE
def ler_orbe(pasta):
    f = achar(pasta, "orbe"); nome = os.path.basename(f)
    linhas = _texto(f).splitlines()
    cab = [c.strip() for c in linhas[0].split(";")]
    out = []
    for l in linhas[1:]:
        if not l.strip(): continue
        p = l.split(";")
        d = dict(zip(cab, p))
        out.append(dict(
            arquivo_origem=nome, ref_origem=d["id_transacao"],
            id_transacao=d["id_transacao"],
            data_movimento=data_br(d["data_movimento"]),
            ec=d["cod_estabelecimento"].strip(),
            nome_orbe=d["nome_estabelecimento"].strip(),
            tipo=d["tipo_lancamento"].strip(),
            modalidade=(d.get("modalidade") or "").strip() or None,
            parcelas=int(d["qtd_parcelas"]) if (d.get("qtd_parcelas") or "").strip() else None,
            bandeira=(d.get("bandeira") or "").strip() or None,
            valor_bruto=brl(d["valor_bruto"]),
            taxa_aplicada=brl(d["taxa_aplicada_pct"]),
            valor_taxa=brl(d["valor_taxa"]),
            valor_liquido=brl(d["valor_liquido"]),
            id_referencia=(d.get("id_referencia") or "").strip() or None,
            data_venda_original=data_br(d.get("data_venda_original")),
        ))
    return out

# ---------------------------------------------------------------- TAXAS
def ler_taxas(pasta):
    """So a aba 'Taxas vigentes'. A aba 'ANTIGO 2025 - nao usar' e ignorada de proposito."""
    f = achar(pasta, "taxas"); nome = os.path.basename(f)
    wb = openpyxl.load_workbook(f, data_only=True)
    aba = next((s for s in wb.sheetnames if "vigente" in s.lower()), wb.sheetnames[0])
    ws = wb[aba]
    out = []
    for i, r in enumerate(ws.iter_rows(min_row=6, values_only=True), start=6):
        if not r or not r[0]: continue
        rot = str(r[0]).strip()
        if rot.startswith("*"): continue            # rodape "spread em branco = padrao"
        obs = str(r[11] or "")
        out.append(dict(
            arquivo_origem=nome, ref_origem=f"{aba}!A{i}", linha_planilha=i,
            lojista=rot, cnpj=cnpj14(r[1]), ec=digitos(r[2]),
            DEBITO=pct(r[3]), AVISTA=pct(r[4]), C26=pct(r[5]), C712=pct(r[6]), PIX=pct(r[7]),
            ANTEC=pct(r[8]), SPREAD=pct(r[9]),
            vigencia_txt=str(r[10] or "").strip(), obs=obs,
            inativo=("INATIVO" in obs.upper()),
        ))
    for t in out:
        t["vig_de"], t["vig_ate"] = _vigencia(t["vigencia_txt"])
    return out

def _vigencia(txt):
    """'ate 14/09/2026' | 'a partir de 15/09/2026' | '01/01/2026' -> (de, ate)."""
    t = txt.lower()
    datas = re.findall(r"\d{2}/\d{2}/\d{4}", txt)
    d = data_br(datas[0]) if datas else None
    if t.startswith("até") or t.startswith("ate"): return (None, d)
    if "a partir" in t: return (d, None)
    return (d, None)

# ---------------------------------------------------------------- PONTE (e-mail + anexo)
def ler_ponte(pasta):
    f = achar(pasta, "ponte"); nome = os.path.basename(f)
    msg = email.message_from_binary_file(open(f, "rb"), policy=email.policy.default)
    corpo, anexo, nome_anexo = "", None, None
    for p in msg.walk():
        if p.get_filename():
            anexo = p.get_payload(decode=True); nome_anexo = p.get_filename()
        elif p.get_content_type() == "text/plain":
            corpo = p.get_content()
    if anexo is None:
        raise RuntimeError("e-mail da Ponte sem anexo")
    wb = openpyxl.load_workbook(io.BytesIO(anexo), data_only=True)
    ws = wb[next((s for s in wb.sheetnames if "opera" in s.lower()), wb.sheetnames[0])]
    rows = list(ws.iter_rows(min_row=6, values_only=True))
    ops = []
    for r in rows:
        if not r or not r[0]: continue
        op = str(r[0]).strip()
        if not op.startswith("PC-"): continue        # corta o rodape "Total de operacoes:"
        ops.append(dict(
            arquivo_origem=f"{nome}::{nome_anexo}", ref_origem=op, operacao=op,
            data_contratacao=data_br(r[1]), data_liquidacao=data_br(r[2]),
            cnpj=cnpj14(r[3]), cliente=str(r[4] or "").strip(), moeda=r[5],
            valor_me=brl(r[6]), taxa_cliente=brl(r[7]), ptax=brl(r[8]),
            valor_brl=brl(r[9]), spread_brl=brl(r[10]), spread_pct=pct(r[11]),
            spread_estimado=brl(r[12]), iof=brl(r[13]),
            status=str(r[14] or "").strip() or None, obs=str(r[15] or "").strip() or None,
        ))
    rodape = {}
    for r in rows:
        if r and r[0] and "Total de opera" in str(r[0]): rodape["qtd"] = r[1]
        if r and r[0] and "Spread total" in str(r[0]):   rodape["spread"] = brl(r[1])
    return ops, {"corpo": corpo, "rodape": rodape, "arquivo": nome}

# ---------------------------------------------------------------- AURORA (CSV com preambulo)
def ler_aurora(pasta):
    """ref_origem = L<numero da linha fisica no arquivo>, contado no arquivo cru."""
    f = achar(pasta, "aurora"); nome = os.path.basename(f)
    out = []
    for i, l in enumerate(_texto(f).splitlines(), start=1):
        p = l.split(";")
        if len(p) < 4: continue
        if not re.match(r"^\d{2}/\d{2}/\d{4}$", p[0].strip()): continue   # pula preambulo e rodape
        v = brl(p[3])
        if v is None: continue                                             # pula SALDO ANTERIOR
        out.append(dict(arquivo_origem=nome, ref_origem=f"L{i}", banco="AURORA",
                        data=data_br(p[0]), descricao=p[1].strip(),
                        documento=p[2].strip() or None, valor=v,
                        saldo=brl(p[4]) if len(p) > 4 else None))
    return out

# ---------------------------------------------------------------- MERIDIANO (OFX SGML)
def ler_meridiano(pasta):
    """OFX 1.0 e SGML: tags nao fechadas. Parser de XML quebra aqui."""
    f = achar(pasta, "meridiano"); nome = os.path.basename(f)
    txt = _texto(f)
    def tag(bloco, t):
        m = re.search(r"<" + t + r">([^<\n]*)", bloco)
        return m.group(1).strip() if m else None
    out = []
    for b in re.findall(r"<STMTTRN>(.*?)</STMTTRN>", txt, re.S):
        out.append(dict(arquivo_origem=nome, ref_origem=tag(b, "FITID"), banco="MERIDIANO",
                        data=data_br(_ofxdata(tag(b, "DTPOSTED"))),
                        descricao=(tag(b, "MEMO") or tag(b, "NAME") or "").strip(),
                        documento=tag(b, "CHECKNUM"), valor=float(tag(b, "TRNAMT")),
                        tipo_ofx=tag(b, "TRNTYPE")))
    return out

def _ofxdata(s):
    if not s: return None
    s = s[:8]
    return f"{s[0:4]}-{s[4:6]}-{s[6:8]}"

# ---------------------------------------------------------------- PLANO DE CONTAS
def ler_plano(pasta):
    f = achar(pasta, "plano"); nome = os.path.basename(f)
    linhas = _texto(f).splitlines()
    cab = [c.strip() for c in linhas[0].split(";")]
    out = []
    for l in linhas[1:]:
        if not l.strip(): continue
        d = dict(zip(cab, l.split(";")))
        out.append(dict(arquivo_origem=nome, codigo=d["COD_CONTA"].strip(),
                        descricao=d["DESCRICAO"].strip(), tipo=d["TIPO"].strip(),
                        natureza=d["NATUREZA"].strip(),
                        aceita=(d["ACEITA_LANCTO"].strip().upper() == "S")))
    return out
