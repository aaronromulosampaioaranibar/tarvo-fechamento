# -*- coding: utf-8 -*-
"""Rascunhos de contestacao, um por contraparte.

A Helena revisa e envia; o fechamento nao manda nada sozinho. Cada rascunho leva o
anexo com as operacoes, porque e isso que ela precisa mandar junto.

Tres destinos, por natureza diferente (resposta ao Theo Garcia, 17/10 11h37):
- ORBE  : condicao contratada cobrada errada -> cobra-se da adquirente
- PONTE : idem no cambio, mais spread negativo fora da trava e operacao duplicada
- LOJISTA: concessao comercial fora do contrato -> devolucao sai do bolso da Tarvo
"""
import os, csv
from collections import defaultdict
from . import comum as C

def _brl(v):
    """1234.5 -> '1.234,50'. Carta para parceiro brasileiro nao sai em formato americano."""
    s = f"{abs(float(v)):,.2f}".replace(",", "@").replace(".", ",").replace("@", ".")
    return ("-" if float(v) < 0 else "") + s

def _tab(linhas, cols, larg):
    s = "  ".join(c.ljust(w) for c, w in zip(cols, larg)) + "\n"
    s += "  ".join("-" * w for w in larg) + "\n"
    for l in linhas:
        s += "  ".join(str(v)[:w].ljust(w) for v, w in zip(l, larg)) + "\n"
    return s

def gerar(f, pasta):
    os.makedirs(pasta, exist_ok=True)
    comp = f.comp
    feitos = []

    # ---------------- ORBE ----------------
    por_loj = defaultdict(list)
    for d in f.div_checkout: por_loj[d["cnpj"]].append(d)
    if por_loj:
        total = C.n2(sum(d["diferenca_brl"] for ds in por_loj.values() for d in ds))
        corpo = [f"Assunto: Contestacao de taxas aplicadas - competencia {comp} - TARVO PAGAMENTOS",
                 "Para: suporte.parceiros@orbe.com.br", "", "Prezados,", "",
                 f"No fechamento de {comp} identificamos transacoes em que a taxa aplicada por",
                 "essa adquirente difere da taxa contratada com o lojista. Seguem os casos,",
                 "com o detalhe transacao a transacao em anexo.", ""]
        for cnpj, ds in sorted(por_loj.items(), key=lambda x: -sum(d["diferenca_brl"] for d in x[1])):
            soma = C.n2(sum(d["diferenca_brl"] for d in ds))
            faixas = sorted({(d["taxa_contratada_pct"], d["taxa_aplicada_pct"]) for d in ds})
            corpo.append(f"{f.cad.nome.get(cnpj, cnpj)} - CNPJ {cnpj}")
            corpo.append(f"  {len(ds)} transacoes, diferenca liquida de R$ {_brl(soma)}")
            for tc, ta in faixas:
                n = sum(1 for d in ds if d["taxa_contratada_pct"] == tc and d["taxa_aplicada_pct"] == ta)
                corpo.append(f"    contratado {tc:.2f}%  aplicado {ta:.2f}%  ({n} transacoes)")
            corpo.append("")
        corpo += [f"Total a restituir: R$ {_brl(total)}", "",
                  "As condicoes estao contratadas e registradas na nossa tabela de taxas. Pedimos",
                  "a correcao do cadastro e a restituicao da diferenca, que sera repassada aos",
                  "lojistas afetados.", "",
                  "Anexo: contestacao_orbe_operacoes.csv", "",
                  "Atenciosamente,", "Financeiro - Tarvo Pagamentos Ltda"]
        _escrever(pasta, "contestacao_orbe.txt", corpo)
        _anexo(pasta, "contestacao_orbe_operacoes.csv",
               ["ref_origem", "cnpj", "lojista", "data", "modalidade", "valor_bruto",
                "taxa_contratada_pct", "taxa_aplicada_pct", "diferenca_brl"],
               [[d["ref_origem"], d["cnpj"], f.cad.nome.get(d["cnpj"], ""), d["data"],
                 d["modalidade"], d["valor_bruto"], d["taxa_contratada_pct"],
                 d["taxa_aplicada_pct"], d["diferenca_brl"]] for d in f.div_checkout])
        feitos.append(("ORBE", total, len(f.div_checkout)))

    # ---------------- PONTE CAMBIO ----------------
    negs = [p for p in f.pend if p["tipo"] == "SPREAD_NEGATIVO"]
    dups = [p for p in f.pend if p["tipo"] == "OPERACAO_DUPLICADA"]
    if f.div_remessa or negs or dups:
        t_div = C.n2(sum(d["diferenca_brl"] for d in f.div_remessa))
        corpo = [f"Assunto: Divergencias no relatorio de {comp} - parceiro TARVO PAGAMENTOS",
                 "Para: relatorios@pontecambio.com.br", "Cc: comercial.parceiros@pontecambio.com.br",
                 "", "Prezados,", "",
                 f"Conferimos o relatorio de {comp} recebido em 02/10 e identificamos tres pontos.",
                 "Respondemos dentro do prazo de 5 dias uteis previsto no e-mail de envio.", ""]
        if f.div_remessa:
            pl = defaultdict(list)
            for d in f.div_remessa: pl[d["cnpj"]].append(d)
            corpo.append("1) SPREAD ACIMA DO CONTRATADO")
            for cnpj, ds in pl.items():
                soma = C.n2(sum(d["diferenca_brl"] for d in ds))
                ctr = ds[0]["taxa_contratada_pct"]
                corpo.append(f"   {f.cad.nome.get(cnpj, cnpj)} - CNPJ {cnpj}")
                corpo.append(f"   Spread contratado: {ctr:.2f}%. Aplicado: cerca de "
                             f"{sum(d['taxa_aplicada_pct'] for d in ds)/len(ds):.2f}% "
                             f"em {len(ds)} de {len(ds)} operacoes do mes.")
                corpo.append(f"   Excesso cobrado do cliente: R$ {_brl(soma)}")
            corpo += ["", "   A condicao esta registrada no nosso contrato com o lojista desde a",
                      "   renegociacao. Pedimos a correcao do cadastro e a restituicao ao cliente.", ""]
        if negs:
            sn = getattr(f, "spread_neg", [])
            tn = C.n2(sum(x["spread_realizado"] for x in sn))
            tp = C.n2(sum(x["ate_contrato"] for x in sn))
            corpo.append("2) OPERACOES COM SPREAD NEGATIVO")
            corpo.append(f"   {len(sn)} operacoes vieram com spread negativo, somando "
                         f"R$ {_brl(tn)},")
            corpo.append('   todas com a observacao "Taxa travada no pedido (D-1)".')
            corpo.append("   A trava de taxa vale 2 horas pelo contrato de parceria e essas")
            corpo.append("   operacoes passaram do prazo. Elas ficam fora da nossa participacao")
            corpo.append("   deste mes.")
            corpo.append("")
            for x in sn:
                corpo.append(f"     {x['operacao']}  {x['data']}  {x['cliente'][:22]:<22} "
                             f"realizado {x['spread_pct']:>7.4f}%  contratado {x['contratado_pct']:.2f}%")
                corpo.append(f"       spread do relatorio R$ {_brl(x['spread_realizado'])}  |  "
                             f"ate o contrato R$ {_brl(x['ate_contrato'])}")
            corpo.append("")
            corpo.append(f"   Pedimos o ajuste ate o spread contratado: R$ {_brl(abs(tp))}.")
            corpo.append("")
        if dups:
            corpo.append("3) OPERACAO DUPLICADA NO RELATORIO")
            for p in dups:
                corpo.append(f"   {p['ref_origem']} aparece duas vezes, a segunda marcada")
                corpo.append(f"   \"reprocessada\". Consideramos uma vez.")
            rod = f.meta_ponte["rodape"].get("spread")
            if rod:
                corpo.append(f"   O rodape do relatorio soma R$ {_brl(rod)} de spread, contando as")
                corpo.append("   duas linhas. Pedimos a correcao do relatorio do mes.")
            corpo.append("")
        corpo += ["Anexo: contestacao_ponte_operacoes.csv", "",
                  "Atenciosamente,", "Financeiro - Tarvo Pagamentos Ltda"]
        _escrever(pasta, "contestacao_ponte.txt", corpo)
        linhas = [[d["ref_origem"], "SPREAD_ACIMA_DO_CONTRATADO", d["cnpj"],
                   f.cad.nome.get(d["cnpj"], ""), d["data"], d["valor_bruto"],
                   d["taxa_contratada_pct"], d["taxa_aplicada_pct"], d["diferenca_brl"]]
                  for d in f.div_remessa]
        linhas += [[x["operacao"], "SPREAD_NEGATIVO", x["cnpj"], x["cliente"], x["data"],
                    x["valor_brl"], x["contratado_pct"], round(x["spread_pct"], 4),
                    x["ate_contrato"]] for x in getattr(f, "spread_neg", [])]
        linhas += [[p["ref_origem"], "OPERACAO_DUPLICADA", "", "", "", "", "", "", p["valor_brl"]]
                   for p in dups]
        _anexo(pasta, "contestacao_ponte_operacoes.csv",
               ["ref_origem", "motivo", "cnpj", "cliente", "data", "valor_brl",
                "spread_contratado_pct", "spread_aplicado_pct", "valor_em_disputa_brl"], linhas)
        feitos.append(("PONTE", t_div, len(f.div_remessa) + len(negs) + len(dups)))

    # ---------------- DEVOLUCAO AO LOJISTA ----------------
    if f.devolucoes:
        pl = defaultdict(list)
        for d in f.devolucoes: pl[d["cnpj"]].append(d)
        for cnpj, ds in pl.items():
            soma = C.n2(sum(d["valor_brl"] for d in ds))
            nome = ds[0]["lojista"]
            corpo = [f"Assunto: Devolucao de taxas - competencia {comp}",
                     f"Para: financeiro@{_slug(nome)}.com.br", "", f"Prezados,", "",
                     f"Durante {comp} esteve em vigor a condicao especial acordada com o nosso",
                     "time comercial. A adquirente nao foi informada a tempo e seguiu cobrando",
                     "pela tabela anterior em todas as transacoes do periodo.",
                     "",
                     f"Valor cobrado a maior: R$ {_brl(soma)}, em {len(ds)} transacoes.",
                     "",
                     "O erro e nosso, nao da adquirente, e a devolucao sera feita integralmente",
                     "no proximo repasse. O detalhe transacao a transacao segue em anexo.", "",
                     "Pedimos desculpas pelo transtorno.", "",
                     f"Anexo: devolucao_{cnpj}_transacoes.csv", "",
                     "Atenciosamente,", "Financeiro - Tarvo Pagamentos Ltda"]
            _escrever(pasta, f"devolucao_{cnpj}.txt", corpo)
            _anexo(pasta, f"devolucao_{cnpj}_transacoes.csv",
                   ["ref_origem", "data", "valor_bruto", "taxa_contratada_pct",
                    "taxa_aplicada_pct", "valor_a_devolver_brl"],
                   [[d["ref_origem"], d["data"], d["valor_bruto"], d["taxa_contratada_pct"],
                     d["taxa_aplicada_pct"], d["valor_brl"]] for d in ds])
            feitos.append((f"LOJISTA {nome}", soma, len(ds)))
    return feitos

def _slug(nome):
    import re, unicodedata
    s = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"\bltda\b|\bs\.?a\.?\b", "", s)
    return re.sub(r"[^a-z0-9]+", "", s)[:24] or "lojista"

def _escrever(pasta, nome, linhas):
    with open(os.path.join(pasta, nome), "w", encoding="utf-8") as fh:
        fh.write("\n".join(linhas) + "\n")

def _anexo(pasta, nome, cols, linhas):
    with open(os.path.join(pasta, nome), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, delimiter=";")
        w.writerow(cols)
        for l in linhas: w.writerow(l)
