#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Auditoria independente do rastro.

    python3 testes/auditoria_rastro.py [--n 10] [--semente 42]

Este script NAO importa nada de src/. Ele le os CSVs ja gravados em saida/ e os
arquivos crus de entrada/, com parsing proprio, e refaz a conta por fora. O objetivo
e nao deixar o fechamento se corrigir sozinho: se o motor e o auditor usassem o mesmo
codigo, o teste nao provaria nada.

Tres conferencias:
  A. Toda linha de rastro.csv aponta para uma linha que existe mesmo no arquivo citado.
  B. A soma do rastro por id_saida bate com o valor reportado no arquivo de saida.
  C. Numa amostra sorteada, o valor e refeito a partir da linha crua e comparado.
"""
import argparse, csv, os, random, re, sys, unicodedata
from decimal import Decimal, ROUND_HALF_UP

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAIDA = os.path.join(RAIZ, "saida")
ENTRADA = os.path.join(RAIZ, "entrada", "2026-09")

def brl(v):
    s = str(v or "").strip()
    if not s: return None
    if "," in s: s = s.replace(".", "").replace(",", ".")
    try: return float(s)
    except ValueError: return None

def cent(x):
    return float(Decimal(str(float(x))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

def texto(caminho):
    b = open(caminho, "rb").read()
    for enc in ("utf-8", "utf-8-sig", "cp1252", "latin-1"):
        try: return b.decode(enc)
        except UnicodeDecodeError: pass
    return b.decode("latin-1", "replace")

def ler_csv(nome):
    with open(os.path.join(SAIDA, nome), encoding="utf-8") as fh:
        return list(csv.DictReader(fh, delimiter=";"))

# ---------- indice das fontes cruas, montado do zero ----------
def indexar_fontes():
    idx = {}
    for nome in os.listdir(ENTRADA):
        cam = os.path.join(ENTRADA, nome)
        if not os.path.isfile(cam): continue
        if nome.endswith(".csv") and "orbe" in nome.lower():
            d = {}
            linhas = texto(cam).splitlines()
            cab = [c.strip() for c in linhas[0].split(";")]
            for l in linhas[1:]:
                if not l.strip(): continue
                p = dict(zip(cab, l.split(";")))
                d[p["id_transacao"]] = p
            idx[nome] = ("orbe", d)
        elif nome.endswith(".csv") and "aurora" in nome.lower():
            d = {}
            for i, l in enumerate(texto(cam).splitlines(), start=1):
                p = l.split(";")
                if len(p) >= 4 and re.match(r"^\d{2}/\d{2}/\d{4}$", p[0].strip()) and p[3].strip():
                    d[f"L{i}"] = dict(data=p[0], descricao=p[1].strip(), valor=brl(p[3]))
            idx[nome] = ("aurora", d)
        elif nome.endswith(".ofx"):
            d = {}
            t = texto(cam)
            for b in re.findall(r"<STMTTRN>(.*?)</STMTTRN>", t, re.S):
                g = lambda tag: (re.search("<" + tag + ">([^<\n]*)", b) or [None, ""])[1].strip()
                d[g("FITID")] = dict(descricao=g("MEMO"), valor=float(g("TRNAMT")))
            idx[nome] = ("meridiano", d)
        elif nome.endswith(".eml"):
            import email, email.policy, io, openpyxl
            m = email.message_from_binary_file(open(cam, "rb"), policy=email.policy.default)
            an = next(p.get_payload(decode=True) for p in m.walk() if p.get_filename())
            wb = openpyxl.load_workbook(io.BytesIO(an), data_only=True)
            ws = wb[next(s for s in wb.sheetnames if "opera" in s.lower())]
            d = {}
            for r in ws.iter_rows(min_row=6, values_only=True):
                if r and r[0] and str(r[0]).startswith("PC-"):
                    d.setdefault(str(r[0]), dict(valor_brl=r[9], spread=r[10], spread_pct=r[11],
                                                 cnpj=r[3], moeda=r[5]))
            for k in list(idx):   # o anexo entra sob o nome composto usado no rastro
                pass
            idx[nome] = ("ponte", d)
    return idx

def achar_fonte(idx, arquivo_origem):
    """O rastro da Ponte usa 'arquivo.eml::anexo.xlsx'. Casa pelo prefixo."""
    base = arquivo_origem.split("::")[0]
    return idx.get(base)

# ---------- execucao ----------
ap = argparse.ArgumentParser()
ap.add_argument("--n", type=int, default=10)
ap.add_argument("--semente", type=int, default=42)
a = ap.parse_args()

rastro = ler_csv("rastro.csv")
saidas = {
    "comissoes_por_lojista.csv":     "comissao_brl",
    "divergencias_taxa.csv":         "diferenca_brl",
    "devolucoes_lojista.csv":        "valor_brl",
    "notas_a_emitir.csv":            "valor_brl",
    "lancamentos_classificados.csv": "valor",
    "pendencias.csv":                "valor_brl",
}
reportado, de_qual = {}, {}
for arq, col in saidas.items():
    for r in ler_csv(arq):
        reportado[r["id_saida"]] = brl(r[col])
        de_qual[r["id_saida"]] = arq

idx = indexar_fontes()
print(f"fontes indexadas: {len(idx)}")
for k, (tipo, d) in sorted(idx.items()):
    print(f"  {k} -> {tipo}, {len(d)} registros")

falhas = []

# ---- A. toda referencia do rastro existe na fonte citada ----
sem_fonte, sem_linha = 0, []
for r in rastro:
    f = achar_fonte(idx, r["arquivo_origem"])
    if f is None:
        sem_fonte += 1; continue
    if r["ref_origem"] not in f[1]:
        sem_linha.append((r["id_saida"], r["arquivo_origem"], r["ref_origem"]))
print(f"\nA. referencias do rastro: {len(rastro)} linhas")
print(f"   arquivo citado nao encontrado em entrada/: {sem_fonte}")
print(f"   ref_origem que NAO existe na fonte: {len(sem_linha)}")
for x in sem_linha[:5]: print("     ", x)
if sem_linha: falhas.append(f"{len(sem_linha)} referencias de rastro apontam para linha inexistente")
if sem_fonte: falhas.append(f"{sem_fonte} linhas de rastro citam arquivo fora de entrada/")

# ---- B. soma do rastro == valor reportado ----
soma = {}
for r in rastro:
    soma[r["id_saida"]] = soma.get(r["id_saida"], 0.0) + (brl(r["valor"]) or 0.0)
ruins = [(i, reportado[i], cent(soma.get(i, 0.0)))
         for i in reportado if abs(cent(soma.get(i, 0.0)) - (reportado[i] or 0)) > 0.011]
orfaos = [i for i in reportado if i not in soma and (reportado[i] or 0) != 0]
print(f"\nB. fechamento por id_saida: {len(reportado)} ids reportados")
print(f"   ids cuja soma de rastro NAO bate: {len(ruins)}")
for x in ruins[:5]: print(f"      {x[0]}: reportado {x[1]:.2f}, rastro {x[2]:.2f}")
print(f"   ids com valor e sem rastro: {len(orfaos)}")
if ruins: falhas.append(f"{len(ruins)} ids nao fecham com o rastro")
if orfaos: falhas.append(f"{len(orfaos)} ids com valor e sem rastro")

# ---- C. amostra refeita a mao ----
random.seed(a.semente)
amostra = random.sample(sorted(reportado), min(a.n, len(reportado)))
print(f"\nC. amostra de {len(amostra)} ids (semente {a.semente}), refeita a partir da linha crua:\n")
for i in sorted(amostra):
    linhas = [r for r in rastro if r["id_saida"] == i]
    val = reportado[i]
    print(f"  {i}   [{de_qual[i]}]   reportado R$ {val:,.2f}   ({len(linhas)} linha(s) de rastro)")
    conferido, detalhe = 0.0, []
    for r in linhas[:3]:
        f = achar_fonte(idx, r["arquivo_origem"])
        if f is None: detalhe.append(f"      {r['ref_origem']}: fonte nao indexada"); continue
        tipo, d = f
        bruto = d.get(r["ref_origem"])
        if bruto is None: detalhe.append(f"      {r['ref_origem']}: NAO EXISTE na fonte"); continue
        if tipo == "orbe":
            detalhe.append(f"      {r['ref_origem']}  {bruto['tipo_lancamento']:<20} "
                           f"bruto {brl(bruto['valor_bruto']):>12,.2f}  "
                           f"orbe aplicou {bruto['taxa_aplicada_pct']}%  "
                           f"-> rastro R$ {brl(r['valor']):>10,.2f}")
        elif tipo in ("aurora", "meridiano"):
            v = bruto["valor"]
            ok = "confere" if abs(v - (brl(r["valor"]) or 0)) < 0.011 else "DIVERGE"
            detalhe.append(f"      {r['ref_origem']}  {bruto['descricao'][:42]:<42} "
                           f"extrato {v:>12,.2f}  rastro {brl(r['valor']):>12,.2f}  {ok}")
            if ok == "DIVERGE": falhas.append(f"{i}/{r['ref_origem']}: rastro != extrato")
        elif tipo == "ponte":
            sp = float(bruto["spread"] or 0)
            esperado = cent(sp * 0.5)
            ok = "confere (50% do spread)" if abs(esperado - (brl(r["valor"]) or 0)) < 0.011 else "DIVERGE"
            detalhe.append(f"      {r['ref_origem']}  spread {sp:>10,.2f}  "
                           f"50% = {esperado:>10,.2f}  rastro {brl(r['valor']):>10,.2f}  {ok}")
            if "DIVERGE" in ok: falhas.append(f"{i}/{r['ref_origem']}: participacao != 50% do spread")
    for x in detalhe: print(x)
    if len(linhas) > 3: print(f"      ... e mais {len(linhas)-3} linha(s)")
    print()

print("=" * 72)
if falhas:
    print("AUDITORIA FALHOU:")
    for x in dict.fromkeys(falhas): print("  -", x)
    sys.exit(1)
print(f"AUDITORIA OK: {len(rastro)} linhas de rastro, {len(reportado)} ids reportados.")
print("Toda referencia existe na fonte citada e toda soma fecha com o valor reportado.")
