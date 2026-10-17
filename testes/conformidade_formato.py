#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Conferencia do formato fixo dos seis arquivos de saida.

    python3 testes/conformidade_formato.py

Parte da correcao do case e automatica, entao o formato e requisito, nao detalhe:
separador ";", decimal com ponto, datas AAAA-MM-DD, CNPJ com 14 digitos, dominios
fechados (CHECKOUT/REMESSA, AURORA/MERIDIANO, REGRA/IA/HUMANO), ref_origem no padrao
de cada fonte e conta_codigo que aceita lancamento no plano Fenix.
"""
import sys
import os as _os
_os.chdir(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
import csv, os, re
S="saida"
OBRIG = {
 "comissoes_por_lojista.csv": ["id_saida","cnpj","lojista","linha_negocio","comissao_brl"],
 "divergencias_taxa.csv": ["id_saida","cnpj","linha_negocio","ref_origem","taxa_contratada_pct","taxa_aplicada_pct","diferenca_brl"],
 "notas_a_emitir.csv": ["id_saida","tomador_cnpj","tomador","linha_negocio","valor_brl","discriminacao"],
 "lancamentos_classificados.csv": ["id_saida","banco","ref_origem","data","descricao","valor","conta_codigo","metodo","confianca"],
 "pendencias.csv": ["id_saida","tipo","ref_origem","valor_brl","motivo","quem_decide"],
 "rastro.csv": ["id_saida","arquivo_origem","ref_origem","valor"],
}
prob=[]
def linhas(a):
    with open(os.path.join(S,a),encoding="utf-8") as fh: return list(csv.DictReader(fh,delimiter=";"))
print("=== 1. arquivos e colunas obrigatorias na ordem ===")
for arq, cols in OBRIG.items():
    cam=os.path.join(S,arq)
    if not os.path.exists(cam): prob.append(arq+" NAO EXISTE"); continue
    with open(cam,encoding="utf-8") as fh: cab=next(csv.reader(fh,delimiter=";"))
    falta=[c for c in cols if c not in cab]; ordem = cab[:len(cols)]==cols
    print("  %-34s %2d colunas  obrigatorias:%s  ordem:%s"%(arq,len(cab),"ok" if not falta else falta,"ok" if ordem else "NAO"))
    if falta: prob.append(arq+": faltam "+str(falta))
    if not ordem: prob.append(arq+": ordem errada -> "+str(cab[:len(cols)]))
print()
print("=== 2. formato dos valores ===")
num=re.compile(r"^-?\d+(\.\d+)?$"); dt=re.compile(r"^\d{4}-\d{2}-\d{2}$"); cn=re.compile(r"^\d{14}$")
for arq in OBRIG:
    rs=linhas(arq)
    if not rs: continue
    for col in rs[0].keys():
        vals=[r[col] for r in rs if r[col]]
        if not vals: continue
        if col.endswith(("_brl","_pct","confianca")) or col in ("valor","valor_bruto"):
            ruins=[v for v in vals if not num.match(v)]
            if ruins: prob.append("%s.%s: %d nao numericos ex %s"%(arq,col,len(ruins),ruins[:2]))
        if col=="data":
            ruins=[v for v in vals if not dt.match(v)]
            if ruins: prob.append("%s.%s: data fora do padrao ex %s"%(arq,col,ruins[:2]))
        if "cnpj" in col:
            ruins=[v for v in vals if not cn.match(v)]
            if ruins: prob.append("%s.%s: CNPJ invalido ex %s"%(arq,col,ruins[:2]))
print("  decimal com ponto / datas AAAA-MM-DD / CNPJ 14 digitos:", "ok" if not prob else "ver abaixo")
print()
print("=== 3. dominios fechados ===")
ln=set(); 
for a in ("comissoes_por_lojista.csv","divergencias_taxa.csv","notas_a_emitir.csv"):
    ln |= {r["linha_negocio"] for r in linhas(a)}
L=linhas("lancamentos_classificados.csv")
bc={r["banco"] for r in L}; mt={r["metodo"] for r in L}; cf=[float(r["confianca"]) for r in L]
print("  linha_negocio:",ln); print("  banco:",bc); print("  metodo:",mt)
print("  confianca: %.2f a %.2f"%(min(cf),max(cf)))
if ln-{"CHECKOUT","REMESSA"}: prob.append("linha_negocio invalida")
if bc-{"AURORA","MERIDIANO"}: prob.append("banco invalido")
if mt-{"REGRA","IA","HUMANO"}: prob.append("metodo invalido")
if min(cf)<0 or max(cf)>1: prob.append("confianca fora de 0..1")
print()
print("=== 4. ref_origem no formato exigido ===")
pL=re.compile(r"^L\d+$"); pM=re.compile(r"^MRD\d+$"); pT=re.compile(r"^(TX|AN)\d+$"); pP=re.compile(r"^PC-")
au=[r for r in L if r["banco"]=="AURORA"]; me=[r for r in L if r["banco"]=="MERIDIANO"]
print("  AURORA   %3d lancamentos  ex %-14s padrao L<n>: %s"%(len(au),au[0]["ref_origem"],"ok" if all(pL.match(r["ref_origem"]) for r in au) else "NAO"))
print("  MERIDIANO %3d lancamentos ex %-14s padrao FITID: %s"%(len(me),me[0]["ref_origem"],"ok" if all(pM.match(r["ref_origem"]) for r in me) else "NAO"))
dv=linhas("divergencias_taxa.csv")
c=[r for r in dv if r["linha_negocio"]=="CHECKOUT"]; m=[r for r in dv if r["linha_negocio"]=="REMESSA"]
print("  divergencias CHECKOUT %3d  id_transacao: %s"%(len(c),"ok" if all(pT.match(r["ref_origem"]) for r in c) else "NAO"))
print("  divergencias REMESSA  %3d  No Operacao : %s"%(len(m),"ok" if all(pP.match(r["ref_origem"]) for r in m) else "NAO"))
print()
print("=== 5. conta_codigo existe no plano e aceita lancamento ===")
plano={}
for l in open("entrada/2026-09/04_plano_de_contas_fenix_erp.csv",encoding="latin-1").read().splitlines()[1:]:
    p=l.split(";")
    if len(p)>4: plano[p[0]]=p[4].strip().upper()
ruins=[r["conta_codigo"] for r in L if plano.get(r["conta_codigo"])!="S"]
print("  %d lancamentos, contas invalidas ou sinteticas: %d %s"%(len(L),len(ruins),set(ruins) if ruins else ""))
if ruins: prob.append("%d lancamentos em conta que nao aceita lancamento"%len(ruins))
print()
print("=== 6. codificacao ===")
for arq in OBRIG:
    b=open(os.path.join(S,arq),"rb").read()
    try: b.decode("utf-8"); e="utf-8 ok"
    except UnicodeDecodeError: e="NAO E UTF-8"; prob.append(arq+" nao e utf-8")
    print("  %-34s %-12s %9d bytes"%(arq,e,len(b)))
print()
print("="*62)
if prob:
    print("PROBLEMAS:")
    for x in prob: print("  -",x)
else:
    print("FORMATO CONFORME em todos os seis arquivos.")

sys.exit(1 if prob else 0)
