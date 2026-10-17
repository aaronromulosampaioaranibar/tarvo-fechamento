#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Prova que a solucao AVISA em vez de quebrar sem ninguem perceber.

    python3 testes/teste_fontes.py

Monta tres cenarios numa pasta temporaria, a partir dos arquivos reais do mes:
  1. tudo no lugar                      -> fecha completo
  2. o e-mail da Ponte nao chegou       -> REMESSA bloqueada, checkout fecha igual
  3. o banco mudou o layout sem avisar  -> EXTRATO_AURORA bloqueado, Meridiano fecha

Em 2 e 3 a saida sai marcada PROVISORIA, com o motivo e quem libera em pendencias.csv.
O criterio e do financeiro (17/10 12h31): "nao seguro o mes inteiro; fecha o que nao
depende daquilo e deixa claro o que esta bloqueado e por que".
"""
import os, sys, shutil, tempfile, io
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
from src.fechamento import Fechamento
from src.saida import autoteste

ENTRADA = os.path.join(RAIZ, "entrada", "2026-09")
falhou = []

def cenario(nome, estragar=None):
    tmp = tempfile.mkdtemp(prefix="tarvo-teste-")
    try:
        for f in os.listdir(ENTRADA):
            shutil.copy2(os.path.join(ENTRADA, f), os.path.join(tmp, f))
        if estragar: estragar(tmp)
        f = Fechamento(tmp, raiz=RAIZ, competencia="2026-09").executar()
        ok, falhas, _ = autoteste(f)
        chk = sum(c["comissao_brl"] for c in f.cms_checkout)
        rem = sum(c["comissao_brl"] for c in f.cms_remessa)
        print(f"\n--- {nome} ---")
        print(f"    provisorio: {f.provisorio} | bloqueios: {sorted(f.bloqueios) or 'nenhum'}")
        print(f"    checkout R$ {chk:,.2f} | remessa R$ {rem:,.2f} | "
              f"lancamentos {len(f.lcts)} | pendencias {len(f.pend)}")
        print(f"    autoteste de rastro: {'PASSOU' if ok else 'FALHOU - ' + str(falhas)}")
        return f, ok, chk, rem
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

def _sem_ponte(d):
    for f in os.listdir(d):
        if f.endswith(".eml"): os.remove(os.path.join(d, f))

def _layout_aurora(d):
    alvo = next(f for f in os.listdir(d) if "aurora" in f.lower())
    p = os.path.join(d, alvo)
    s = io.open(p, encoding="utf-8").read()
    s = s.replace("Data;Lançamento;Documento;Valor (R$);Saldo (R$)",
                  "Dt;Historico;Doc;Montante;Saldo")
    io.open(p, "w", encoding="utf-8").write(s)

f1, ok1, chk1, rem1 = cenario("1. tudo no lugar")
if not ok1 or f1.provisorio: falhou.append("cenario 1 deveria fechar completo e sem falha de rastro")
if rem1 <= 0:                falhou.append("cenario 1 deveria ter comissao de remessa")

f2, ok2, chk2, rem2 = cenario("2. e-mail da Ponte nao chegou", _sem_ponte)
if not ok2:                       falhou.append("cenario 2: o rastro tem de fechar mesmo parcial")
if not f2.provisorio:             falhou.append("cenario 2: deveria sair PROVISORIO")
if "REMESSA" not in f2.bloqueios: falhou.append("cenario 2: REMESSA deveria estar bloqueada")
if abs(chk2 - chk1) > 0.011:      falhou.append("cenario 2: o checkout nao pode mudar por falta da Ponte")
if not any(p["tipo"] == "FONTE_INDISPONIVEL" for p in f2.pend):
    falhou.append("cenario 2: faltou a pendencia FONTE_INDISPONIVEL")

f3, ok3, chk3, rem3 = cenario("3. banco mudou o layout", _layout_aurora)
if not ok3:                              falhou.append("cenario 3: o rastro tem de fechar")
if "EXTRATO_AURORA" not in f3.bloqueios: falhou.append("cenario 3: AURORA deveria estar bloqueado")
if len(f3.lcts) != 100:                  falhou.append("cenario 3: o Meridiano deveria fechar sozinho (100 lancamentos)")
if abs(chk3 - chk1) > 0.011:             falhou.append("cenario 3: o checkout nao pode mudar")

print()
if falhou:
    print("FALHOU:"); [print("  -", x) for x in falhou]; sys.exit(1)
print("Os tres cenarios passaram. Fonte ausente ou layout mudado bloqueia so a parte")
print("que depende dela, avisa o motivo e marca a saida como provisoria.")
