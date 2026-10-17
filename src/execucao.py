# -*- coding: utf-8 -*-
"""Registro de cada execucao do fechamento.

Pedido da organizacao em 17/10 14h11, sobre o que torna o rastro auditavel de verdade:
"um registro de cada execucao: quais arquivos entraram, quantas linhas de cada, data e hora".

Grava saida/execucao.json. O hash de cada arquivo de entrada permite provar, meses depois,
que a saida veio daqueles arquivos e nao de outros.
"""
import os, json, hashlib, datetime as dt, platform, sys
from . import comum as C

def _sha(caminho):
    h = hashlib.sha256()
    with open(caminho, "rb") as fh:
        for b in iter(lambda: fh.read(65536), b""):
            h.update(b)
    return h.hexdigest()[:16]

def _linhas(caminho):
    if caminho.lower().endswith((".csv", ".ofx")):
        try:
            with open(caminho, "rb") as fh:
                return sum(1 for l in fh if l.strip())
        except OSError:
            return None
    return None

def registrar(f, pasta_entrada, pasta_saida, inicio):
    entradas = []
    for nome in sorted(os.listdir(pasta_entrada)):
        cam = os.path.join(pasta_entrada, nome)
        if not os.path.isfile(cam): continue
        entradas.append(dict(arquivo=nome, bytes=os.path.getsize(cam),
                             linhas=_linhas(cam), sha256_16=_sha(cam),
                             modificado=dt.datetime.fromtimestamp(
                                 os.path.getmtime(cam)).isoformat(timespec="seconds")))
    reg = dict(
        competencia=f.comp,
        executado_em=inicio.isoformat(timespec="seconds"),
        duracao_s=round((dt.datetime.now() - inicio).total_seconds(), 2),
        provisorio=f.provisorio,
        bloqueios={k: v for k, v in f.bloqueios.items()},
        problemas_de_fonte=f.problemas,
        python=sys.version.split()[0], plataforma=platform.platform(),
        parametros=dict(
            tolerancia_taxa_pp=C.TOLERANCIA_TAXA_PP,
            participacao_spread=C.PARTICIPACAO_SPREAD,
            spread_padrao_pct=C.SPREAD_PADRAO_PCT,
            competencia_remessa=C.COMPETENCIA_REMESSA,
            inclui_spread_negativo=C.INCLUI_SPREAD_NEGATIVO,
            dedup_ponte=C.DEDUP_PONTE,
            max_parcelas=C.MAX_PARCELAS,
            corte_confianca_ia=C.CORTE_CONFIANCA_IA,
        ),
        entradas=entradas,
        linhas_lidas=dict(orbe=len(f.orbe), ponte=len(f.ponte), taxas=len(f.taxas),
                          aurora=len(f.aurora), meridiano=len(f.merid), plano=len(f.plano)),
        saidas=dict(
            comissoes=len(f.cms_checkout) + len(f.cms_remessa),
            divergencias=len(f.div_checkout) + len(f.div_remessa),
            devolucoes=len(f.devolucoes), notas=len(f.nfs),
            lancamentos=len(f.lcts), pendencias=len(f.pend), rastro=len(f.rastro)),
        totais=dict(
            comissao_checkout_brl=C.n2(sum(c["comissao_brl"] for c in f.cms_checkout)),
            comissao_remessa_brl=C.n2(sum(c["comissao_brl"] for c in f.cms_remessa)),
            divergencias_brl=C.n2(sum(d["diferenca_brl"] for d in f.div_checkout + f.div_remessa)),
            devolucoes_brl=C.n2(sum(d["valor_brl"] for d in f.devolucoes)),
            cobrado_pela_orbe_brl=C.n2(sum(t["valor_taxa"] or 0 for t in f.orbe)),
        ),
    )
    os.makedirs(pasta_saida, exist_ok=True)
    cam = os.path.join(pasta_saida, "execucao.json")
    with open(cam, "w", encoding="utf-8") as fh:
        json.dump(reg, fh, ensure_ascii=False, indent=2)
    return reg
