#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fecha o mes da Tarvo.

    python fechar.py --entrada ".." --competencia 2026-09 --saida saida

Le os arquivos como o cliente manda (CSV pt-BR, XLSX feito a mao, .eml com anexo, OFX),
escreve os seis arquivos de saida e nao grava nada se o autoteste de fechamento falhar.
"""
import argparse, os, re, sys, datetime as dt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.fechamento import Fechamento
from src.saida import gravar, autoteste
from src.contestacoes import gerar as gerar_contestacoes
from src.execucao import registrar
from src import comum as C

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--entrada", default=None,
                    help="pasta com os arquivos do mes, do jeito que chegaram "
                         "(padrao: entrada/<competencia>)")
    ap.add_argument("--competencia", default=None,
                    help="AAAA-MM (padrao: a pasta mais recente dentro de entrada/)")
    ap.add_argument("--saida", default="saida")
    ap.add_argument("--forcar", action="store_true", help="grava mesmo com autoteste falhando")
    a = ap.parse_args()

    inicio = dt.datetime.now()
    raiz = os.path.dirname(os.path.abspath(__file__))

    # Sem --competencia, fechamos a pasta mais recente de entrada/. Quem roda pelo
    # atalho do Windows nao passa argumento nenhum: criar entrada/2026-10 e largar
    # os arquivos la dentro e tudo o que o mes seguinte vai exigir.
    comp = a.competencia
    if not comp:
        base = os.path.join(raiz, "entrada")
        meses = sorted(d for d in (os.listdir(base) if os.path.isdir(base) else [])
                       if re.fullmatch(r"\d{4}-\d{2}", d)
                       and os.path.isdir(os.path.join(base, d)))
        if not meses and not a.entrada:
            print(f"nenhuma pasta de mes encontrada em {base}\n"
                  f"crie entrada/AAAA-MM (ex.: entrada/2026-10) e coloque os arquivos la")
            return 2
        comp = meses[-1] if meses else "2026-09"
        if not a.entrada: print(f"competencia: {comp}  (pasta mais recente em entrada/)")
    a.competencia = comp
    entrada = a.entrada or os.path.join(raiz, "entrada", comp)
    if not os.path.isdir(entrada):
        print(f"pasta de entrada nao encontrada: {entrada}\n"
              f"use --entrada para apontar a pasta do mes")
        return 2
    f = Fechamento(entrada, raiz=raiz, competencia=a.competencia).executar()

    ok, falhas, conferencias = autoteste(f)
    print(f"\n=== FECHAMENTO {a.competencia}"
          f"{'  [PROVISORIO]' if f.provisorio else ''} ===")
    if f.problemas:
        print("\n  !! FONTES COM PROBLEMA:")
        for pb in f.problemas:
            print(f"     - {pb['fonte']}: {pb['tipo']} - {pb['detalhe'][:90]}")
        for parte, falta in f.bloqueios.items():
            print(f"     > {parte} BLOQUEADO (falta {', '.join(falta)})")
        print("     O restante fechou. Os numeros abaixo sao parciais.\n")
    for c in conferencias: print("  [ok]", c)
    if falhas:
        print("\n  !! AUTOTESTE FALHOU:")
        for x in falhas: print("     -", x)
    if not ok and not a.forcar:
        print("\nNada foi gravado. Corrija ou rode com --forcar.")
        return 1

    pasta = a.saida if os.path.isabs(a.saida) else os.path.join(raiz, a.saida)
    gravar("comissoes_por_lojista.csv", f.cms_checkout + f.cms_remessa, pasta)
    gravar("divergencias_taxa.csv", f.div_checkout + f.div_remessa, pasta)
    gravar("notas_a_emitir.csv", f.nfs, pasta)
    gravar("lancamentos_classificados.csv", f.lcts, pasta)
    gravar("pendencias.csv", f.pend, pasta)
    gravar("devolucoes_lojista.csv", f.devolucoes, pasta)
    gravar("rastro.csv", f.rastro, pasta)
    cont = gerar_contestacoes(f, os.path.join(raiz, "contestacoes"))
    reg = registrar(f, entrada, pasta, inicio)

    chk = sum(c["comissao_brl"] for c in f.cms_checkout)
    rem = sum(c["comissao_brl"] for c in f.cms_remessa)
    dv  = sum(d["diferenca_brl"] for d in f.div_checkout + f.div_remessa)
    de  = sum(d["valor_brl"] for d in f.devolucoes)
    print(f"""
  Comissao CHECKOUT ....... R$ {chk:>12,.2f}  ({len(f.cms_checkout)} lojistas)
  Comissao REMESSA ........ R$ {rem:>12,.2f}  ({len(f.cms_remessa)} lojistas)
  Receita do mes .......... R$ {chk+rem:>12,.2f}
  Divergencias de taxa .... R$ {dv:>12,.2f}  ({len(f.div_checkout)+len(f.div_remessa)} transacoes, a cobrar dos parceiros)
  Devolucoes ao lojista ... R$ {de:>12,.2f}  ({len(f.devolucoes)} transacoes, do bolso da Tarvo)
  Notas a emitir .......... {len(f.nfs):>14}
  Lancamentos classificados {len(f.lcts):>14}
  Pendencias p/ uma pessoa  {len(f.pend):>14}
  Linhas de rastro ........ {len(f.rastro):>14}

  Saida em {pasta}

  Registro desta execucao em execucao.json: {len(reg['entradas'])} arquivos de entrada,
  com hash e contagem de linhas, os parametros usados e os totais.""")
    if cont:
        print("\n  Rascunhos de contestacao (a Helena revisa e envia):")
        for destino, valor, n in cont:
            print(f"    {destino:<34} R$ {valor:>11,.2f}  ({n} operacoes)")
        print(f"    em {os.path.join(raiz, 'contestacoes')}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
