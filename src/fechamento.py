# -*- coding: utf-8 -*-
"""Motor do fechamento. Cada numero que sai daqui emite linhas em rastro.csv."""
import os, csv, datetime as dt
from collections import defaultdict
from . import leitores as L
from .identidade import Cadastro
from .classificacao import classificar
from . import comum as C

TOMADOR_NF_REMESSA = "PONTE"     # Q12: "PONTE" ou "LOJISTA"

class Fechamento:
    def __init__(self, pasta_entrada, raiz=".", competencia="2026-09", agente_ia=None):
        self.pasta, self.raiz, self.comp = pasta_entrada, raiz, competencia
        self.ano, self.mes = int(competencia[:4]), int(competencia[5:7])
        self.agente_ia = agente_ia
        self.rastro, self.pend, self._npend = [], [], 0
        self.avisos = []

    # ---------- utilitarios ----------
    def _r(self, id_saida, arquivo, ref, valor):
        self.rastro.append(dict(id_saida=id_saida, arquivo_origem=arquivo,
                                ref_origem=ref, valor=C.n2(valor)))

    def _p(self, tipo, ref, valor, motivo, quem, arquivo=None):
        self._npend += 1
        i = f"PEN-{self._npend:03d}"
        self.pend.append(dict(id_saida=i, tipo=tipo, ref_origem=ref,
                              valor_brl=C.n2(valor), motivo=motivo, quem_decide=quem))
        if arquivo: self._r(i, arquivo, ref, valor)
        return i

    def _na_competencia(self, d):
        return bool(d) and d.year == self.ano and d.month == self.mes

    # ---------- carga ----------
    def carregar(self):
        self.orbe   = L.ler_orbe(self.pasta)
        self.taxas  = L.ler_taxas(self.pasta)
        self.ponte, self.meta_ponte = L.ler_ponte(self.pasta)
        self.aurora = L.ler_aurora(self.pasta)
        self.merid  = L.ler_meridiano(self.pasta)
        self.plano  = {c["codigo"]: c for c in L.ler_plano(self.pasta)}
        self.cad    = Cadastro(self.taxas, self.raiz)

    # ---------- 1. CHECKOUT ----------
    def checkout(self):
        """Comissao = valor_bruto x taxa CONTRATADA, arredondada linha a linha, depois somada.
        NAO e o valor_taxa que a Orbe aplicou: a diferenca entre os dois e divergencia."""
        ids_orbe = {t["id_transacao"] for t in self.orbe}
        for t in self.orbe:
            cnpj = self.cad.cnpj_do_ec(t["ec"])
            col = "ANTEC" if "ANTECIPACAO" in t["tipo"] else C.faixa_mdr(t["modalidade"], t["parcelas"])
            # Q9 RESPONDIDA: estorno usa a taxa da data da VENDA ORIGINAL; a faixa sai da
            # propria linha do estorno (modalidade e parcelas dele).
            dref = t["data_venda_original"] or t["data_movimento"]
            tc, ref_taxa, especial = (self.cad.taxa(cnpj, col, dref) if (cnpj and col)
                                     else (None, None, False))
            t["_cnpj"], t["_col"], t["_dref"] = cnpj, col, dref
            t["_tc"], t["_ref_taxa"], t["_especial"] = tc, ref_taxa, especial
            t["_comissao"] = C.n2((t["valor_bruto"] or 0) * tc / 100) if tc is not None else None

        por = defaultdict(lambda: dict(mdr=0.0, antec=0.0, n=0, ecs=set(), linhas=[], apuravel=True))
        for t in self.orbe:
            chave = t["_cnpj"] or f"EC{t['ec']}"
            g = por[chave]
            g["n"] += 1; g["ecs"].add(t["ec"]); g["linhas"].append(t)
            if t["_comissao"] is None:
                g["apuravel"] = False
            elif "ANTECIPACAO" in t["tipo"]:
                g["antec"] += t["_comissao"]
            else:
                g["mdr"] += t["_comissao"]
            if t["tipo"] == "ESTORNO" and t["id_referencia"] and t["id_referencia"] not in ids_orbe:
                self._p("ESTORNO_DE_COMPETENCIA_ANTERIOR", t["id_transacao"], t["_comissao"],
                        f"estorno de venda de {C.iso(t['data_venda_original'])}, fora deste arquivo. "
                        f"Entra nesta competencia pela taxa da venda original (regra do canal)",
                        "Financeiro Tarvo", t["arquivo_origem"])

        linhas = []
        for chave, g in sorted(por.items()):
            cnpj = chave if not chave.startswith("EC") else ""
            ec = sorted(g["ecs"])[0]
            idx = f"CMS-CHK-{cnpj or chave}"
            total = C.n2(g["mdr"] + g["antec"]) if g["apuravel"] else 0.0
            linhas.append(dict(id_saida=idx, cnpj=cnpj,
                               lojista=self.cad.nome.get(cnpj, g["linhas"][0]["nome_orbe"]),
                               linha_negocio="CHECKOUT", comissao_brl=total,
                               comissao_mdr_brl=C.n2(g["mdr"]), comissao_antecipacao_brl=C.n2(g["antec"]),
                               qtd_transacoes=g["n"], ec_orbe="|".join(sorted(g["ecs"])),
                               confianca_identidade=self.cad.confianca_do_ec(ec),
                               origem_identidade=self.cad.origem_do_ec(ec),
                               apuravel=1 if g["apuravel"] else 0))
            for t in g["linhas"]:
                self._r(idx, t["arquivo_origem"], t["ref_origem"],
                        t["_comissao"] if t["_comissao"] is not None else 0.0)
            if not g["apuravel"]:
                cobrado = C.n2(sum(x["valor_taxa"] or 0 for x in g["linhas"]))
                self._p("SEM_TAXA_CONTRATADA", "|".join(sorted(g["ecs"])), cobrado,
                        f"{self.cad.nome.get(cnpj, g['linhas'][0]['nome_orbe'])} transacionou em "
                        f"{g['n']} linhas mas nao tem taxa vigente na planilha. Comissao sai ZERADA e "
                        f"sem nota ate o comercial confirmar o contrato; a Orbe ja cobrou "
                        f"R$ {cobrado:,.2f} do lojista. O repasse do liquido segue normal",
                        "Comercial Tarvo")
            if self.cad.confianca_do_ec(ec) < 1.0:
                self._p("IDENTIDADE_LOJISTA", "|".join(sorted(g["ecs"])), total,
                        f"EC {ec} resolvido por premissa ({self.cad.origem_do_ec(ec)}, "
                        f"confianca {self.cad.confianca_do_ec(ec)}) - confirmar antes de faturar",
                        "Financeiro Tarvo")
        self.cms_checkout = linhas
        self._alertas_checkout()
        return linhas

    # ---------- 1b. ALERTAS DE CHECKOUT ----------
    def _alertas_checkout(self):
        """Checagens que nao mudam numero, mas precisam de uma pessoa."""
        # parcelamento acima do que a Tarvo vende (resposta da Casa Barton: "nao vendemos acima de 12x")
        for t in self.orbe:
            if (t["parcelas"] or 0) > C.MAX_PARCELAS:
                self._p("PARCELAMENTO_ACIMA_DO_PADRAO", t["ref_origem"], t["valor_bruto"],
                        f"{t['parcelas']}x, acima das {C.MAX_PARCELAS}x que a Tarvo vende. "
                        f"Sem faixa de taxa contratada para essa condicao",
                        "Comercial Tarvo", t["arquivo_origem"])
        # antecipacao de lojista NOVO (sem historico antes da competencia).
        # Comparar antecipacao com as vendas do mes acenderia 6 lojistas, porque a antecipacao
        # e sobre a agenda inteira, com parcelas de meses anteriores que este arquivo nao traz
        # (resposta ao Theo Garcia). O alerta so faz sentido para quem nao tem agenda anterior.
        por_ec = defaultdict(lambda: dict(ant=0.0, ven=0.0, antigo=False, nome=""))
        for t in self.orbe:
            g = por_ec[t["ec"]]; g["nome"] = t["nome_orbe"]
            if t["tipo"] == "ANTECIPACAO": g["ant"] += t["valor_bruto"] or 0
            elif t["tipo"] == "VENDA":     g["ven"] += t["valor_bruto"] or 0
            if t["data_venda_original"] and t["data_venda_original"] < dt.date(self.ano, self.mes, 1):
                g["antigo"] = True
        for ec, g in sorted(por_ec.items()):
            if g["antigo"] or g["ant"] <= g["ven"] or g["ant"] <= 0: continue
            self._p("ANTECIPACAO_SEM_LASTRO", f"EC {ec}", C.n2(g["ant"] - g["ven"]),
                    f"{g['nome']} nao tem venda anterior a esta competencia e antecipou "
                    f"R$ {g['ant']:,.2f} contra R$ {g['ven']:,.2f} vendidos no mes. Lojista novo "
                    f"antecipando acima do que vendeu. Criterio nosso (ver HIPOTESES.md): o alerta "
                    f"so acende para quem nao tem agenda anterior, porque a antecipacao e sobre a "
                    f"agenda inteira e comparar com as vendas do mes acenderia lojista demais",
                    "Financeiro Tarvo + Comercial Tarvo")

    # ---------- 2. DIVERGENCIAS E DEVOLUCOES DE CHECKOUT ----------
    def divergencias_checkout(self):
        """Divergencia = valor_bruto x (taxa aplicada - taxa contratada), transacao por transacao.

        Duas naturezas diferentes, que nao podem ser somadas (resposta ao Theo Garcia, 11h37):
        - CONTRATO: a contraparte cobrou diferente de uma condicao contratada. Cobra-se dela.
          O aviso atrasado e problema de processo da Tarvo, nao muda quem deve.
        - ISENCAO_COMERCIAL: concessao do comercial fora do contrato. A Orbe cobrou o que estava
          contratado. A devolucao sai do bolso da Tarvo e vai para devolucoes_lojista.csv.
        """
        div, dev = [], []
        for t in self.orbe:
            if t["_tc"] is None: continue
            dif = (t["taxa_aplicada"] or 0) - t["_tc"]
            if abs(dif) < C.TOLERANCIA_TAXA_PP: continue
            dbrl = C.n2((t["valor_bruto"] or 0) * dif / 100)
            if t["_especial"]:
                idx = f"DEV-{t['id_transacao']}"
                dev.append(dict(id_saida=idx, cnpj=t["_cnpj"],
                                lojista=self.cad.nome.get(t["_cnpj"], t["nome_orbe"]),
                                ref_origem=t["ref_origem"], data=C.iso(t["data_movimento"]),
                                taxa_contratada_pct=round(t["_tc"], 4),
                                taxa_aplicada_pct=round(t["taxa_aplicada"], 4),
                                valor_bruto=C.n2(t["valor_bruto"]), valor_brl=dbrl,
                                motivo="isencao comercial nao informada a Orbe - devolucao da Tarvo "
                                       "ao lojista, fora da cobranca da adquirente"))
                self._r(idx, t["arquivo_origem"], t["ref_origem"], dbrl)
                continue
            idx = f"DIV-CHK-{t['id_transacao']}"
            div.append(dict(id_saida=idx, cnpj=t["_cnpj"], linha_negocio="CHECKOUT",
                            ref_origem=t["ref_origem"], taxa_contratada_pct=round(t["_tc"], 4),
                            taxa_aplicada_pct=round(t["taxa_aplicada"], 4), diferenca_brl=dbrl,
                            data=C.iso(t["data_movimento"]), modalidade=t["modalidade"] or t["tipo"],
                            valor_bruto=C.n2(t["valor_bruto"]),
                            sentido="COBRADO_A_MAIOR" if dbrl > 0 else "COBRADO_A_MENOR",
                            natureza="CONTRATO", cobrar_de="ORBE", ref_taxa_contratada=t["_ref_taxa"]))
            self._r(idx, t["arquivo_origem"], t["ref_origem"], dbrl)

        # uma pendencia por contraparte e por lojista, com o detalhe anexado (pedido da Helena)
        por_loj = defaultdict(list)
        for d in div: por_loj[d["cnpj"]].append(d)
        for cnpj, ds in por_loj.items():
            soma = C.n2(sum(x["diferenca_brl"] for x in ds))
            total_tx = sum(1 for t in self.orbe if t["_cnpj"] == cnpj)
            sistemico = len(ds) >= 10 and len(ds) / max(total_tx, 1) > 0.5
            self._p("COBRANCA_A_MAIOR_ORBE", "|".join(d["ref_origem"] for d in ds), soma,
                    f"{self.cad.nome.get(cnpj, cnpj)}: Orbe aplicou taxa diferente da contratada em "
                    f"{len(ds)} de {total_tx} transacoes (liquido de estornos). "
                    + ("Padrao sistemico - tabela desatualizada na Orbe. " if sistemico else "")
                    + "Contestar com a Orbe e ressarcir o lojista. Rascunho em contestacoes/",
                    "Financeiro Tarvo + Parceiro Orbe")
        por_dev = defaultdict(list)
        for d in dev: por_dev[d["cnpj"]].append(d)
        for cnpj, ds in por_dev.items():
            soma = C.n2(sum(x["valor_brl"] for x in ds))
            self._p("DEVOLUCAO_AO_LOJISTA", "|".join(d["ref_origem"] for d in ds), soma,
                    f"{self.cad.nome.get(cnpj, cnpj)}: condicao especial concedida pelo comercial e "
                    f"nao informada a Orbe, que cobrou pela tabela em {len(ds)} transacoes. "
                    f"NAO ha o que cobrar da Orbe: a devolucao sai da Tarvo. Detalhe por transacao "
                    f"em devolucoes_lojista.csv e no rastro",
                    "Financeiro Tarvo + Comercial Tarvo")
        self.div_checkout, self.devolucoes = div, dev
        return div

    # ---------- 3. REMESSA ----------
    def remessa(self):
        vistos, ops = set(), []
        for o in self.ponte:
            if C.DEDUP_PONTE and o["operacao"] in vistos:
                self._p("OPERACAO_DUPLICADA", o["operacao"], C.n2(o["spread_brl"] * C.PARTICIPACAO_SPREAD),
                        f"operacao repetida no relatorio da Ponte (obs: {o['obs']}). "
                        f"Mantida uma vez. O rodape do parceiro conta as duas",
                        "Parceiro Ponte Cambio", o["arquivo_origem"])
                continue
            vistos.add(o["operacao"])
            dcomp = o["data_contratacao"] if C.COMPETENCIA_REMESSA == "contratacao" else o["data_liquidacao"]
            if not self._na_competencia(dcomp):
                self._p("FORA_DA_COMPETENCIA", o["operacao"], C.n2(o["spread_brl"] * C.PARTICIPACAO_SPREAD),
                        f"contratada {C.iso(o['data_contratacao'])}, liquidada {C.iso(o['data_liquidacao'])}. "
                        f"Criterio adotado: {C.COMPETENCIA_REMESSA} (Q6)",
                        "Financeiro Tarvo", o["arquivo_origem"])
                continue
            if o["spread_brl"] is not None and o["spread_brl"] < 0:
                contratado, _, _ = self.cad.taxa(o["cnpj"], "SPREAD", o["data_contratacao"])
                if contratado is None: contratado = C.SPREAD_PADRAO_PCT
                base = o["spread_brl"] / (o["spread_pct"] / 100) if o["spread_pct"] else 0
                ate_contrato = C.n2(base * ((o["spread_pct"] or 0) - contratado) / 100)
                self._p("SPREAD_NEGATIVO", o["operacao"], C.n2(o["spread_brl"]),
                        f"spread negativo de R$ {o['spread_brl']:.2f} ({o['spread_pct']:.4f}% contra "
                        f"{contratado:.2f}% contratados; obs: {o['obs']}). A trava de taxa vale 2h por "
                        f"contrato e esta passou do prazo, entao fica FORA da comissao e da nota. "
                        f"Para a contestacao com a Ponte: o que aconteceu foi R$ {o['spread_brl']:,.2f}; "
                        f"o que se pede de volta e a diferenca ate o contrato, R$ {ate_contrato:,.2f}",
                        "Financeiro Tarvo + Parceiro Ponte Cambio", o["arquivo_origem"])
                if not C.INCLUI_SPREAD_NEGATIVO: continue
            ops.append(o)
        # informativa: liquidacoes que caem no mes seguinte
        fora = [o for o in ops if not self._na_competencia(o["data_liquidacao"])]
        if fora:
            self._p("LIQUIDACAO_NO_MES_SEGUINTE", "|".join(o["operacao"] for o in fora),
                    C.n2(sum(o["spread_brl"] for o in fora) * C.PARTICIPACAO_SPREAD),
                    f"{len(fora)} operacoes contratadas na competencia e liquidadas no mes seguinte. "
                    f"Receita reconhecida aqui, caixa so no mes seguinte",
                    "Contabilidade")
        # confronto com o rodape do parceiro
        rod = self.meta_ponte["rodape"].get("spread")
        soma = sum(o["spread_brl"] for o in ops)
        if rod and abs(rod - soma) > 0.01:
            self._p("DIVERGENCIA_COM_PARCEIRO", "rodape do relatorio Ponte", C.n2(rod - soma),
                    f"rodape do parceiro diz R$ {rod:,.2f} de spread; apurado R$ {soma:,.2f} "
                    f"apos deduplicacao e competencia. Responder o e-mail em ate 5 dias uteis",
                    "Financeiro Tarvo + Parceiro Ponte Cambio")
        # A parcela de cada operacao e arredondada em centavos ANTES de somar: e assim que
        # o valor e faturado, e e o que mantem o rastro batendo com o total reportado.
        for o in ops:
            o["comissao_tarvo"] = C.n2(o["spread_brl"] * C.PARTICIPACAO_SPREAD)
        por = defaultdict(lambda: dict(spread=0.0, com=0.0, n=0, linhas=[]))
        for o in ops:
            g = por[o["cnpj"]]
            g["spread"] += o["spread_brl"]; g["com"] += o["comissao_tarvo"]
            g["n"] += 1; g["linhas"].append(o)
        linhas, divs = [], []
        for cnpj, g in sorted(por.items()):
            idx = f"CMS-REM-{cnpj}"
            com = C.n2(g["com"])
            linhas.append(dict(id_saida=idx, cnpj=cnpj, lojista=self.cad.nome.get(cnpj, g["linhas"][0]["cliente"]),
                               linha_negocio="REMESSA", comissao_brl=com,
                               spread_total_brl=C.n2(g["spread"]), qtd_operacoes=g["n"],
                               participacao_pct=C.PARTICIPACAO_SPREAD * 100,
                               confianca_identidade=1.0, origem_identidade="CNPJ_NO_RELATORIO"))
            for o in g["linhas"]:
                self._r(idx, o["arquivo_origem"], o["ref_origem"], o["comissao_tarvo"])
        # divergencias de spread
        assumido = set()
        for o in ops:
            if o["spread_brl"] is None or o["spread_brl"] < 0: continue   # negativo ja virou pendencia
            contratado, ref_taxa, _esp = self.cad.taxa(o["cnpj"], "SPREAD", o["data_contratacao"])
            if contratado is None:
                contratado, ref_taxa = C.SPREAD_PADRAO_PCT, "premissa Q4 (spread padrao)"
                assumido.add(o["cnpj"])
            dif = (o["spread_pct"] or 0) - contratado
            if abs(dif) < C.TOLERANCIA_TAXA_PP: continue
            idx = f"DIV-REM-{o['operacao']}"
            base = o["spread_brl"] / (o["spread_pct"] / 100) if o["spread_pct"] else 0
            dbrl = C.n2(base * dif / 100)
            divs.append(dict(id_saida=idx, cnpj=o["cnpj"], linha_negocio="REMESSA",
                             ref_origem=o["ref_origem"], taxa_contratada_pct=round(contratado, 4),
                             taxa_aplicada_pct=round(o["spread_pct"], 4), diferenca_brl=dbrl,
                             data=C.iso(o["data_contratacao"]), modalidade=f"REMESSA {o['moeda']}",
                             valor_bruto=C.n2(o["valor_brl"]),
                             sentido="COBRADO_A_MAIOR" if dbrl > 0 else "COBRADO_A_MENOR",
                             natureza="CONTRATO", cobrar_de="PONTE", ref_taxa_contratada=ref_taxa))
            self._r(idx, o["arquivo_origem"], o["ref_origem"], dbrl)
        for cnpj in sorted(assumido):
            vol = C.n2(sum(o["spread_brl"] for o in ops if o["cnpj"] == cnpj))
            self._p("SPREAD_PADRAO_ASSUMIDO", cnpj, vol,
                    f"{self.cad.nome.get(cnpj, cnpj)} esta com 'Spread remessa' em branco na planilha. "
                    f"Premissa Q4: padrao = {C.SPREAD_PADRAO_PCT}%. Confirmar",
                    "Comercial Tarvo")
        por_loj = defaultdict(list)
        for d in divs: por_loj[d["cnpj"]].append(d)
        for cnpj, ds in por_loj.items():
            soma = C.n2(sum(x["diferenca_brl"] for x in ds))
            if len(ds) >= 5 and soma > 0:
                self._p("COBRANCA_A_MAIOR_PONTE", "|".join(d["ref_origem"] for d in ds), soma,
                        f"{self.cad.nome.get(cnpj, cnpj)}: Ponte aplicou spread acima do contratado em "
                        f"{len(ds)} operacoes. A condicao esta registrada na planilha, entao e divergencia "
                        f"de contrato: contestar com a Ponte e ressarcir o lojista. "
                        f"Rascunho em contestacoes/",
                        "Financeiro Tarvo + Parceiro Ponte Cambio")
        self.cms_remessa, self.div_remessa, self.ops_remessa = linhas, divs, ops
        return linhas, divs

    # ---------- 4. LANCAMENTOS ----------
    def lancamentos(self):
        out = []
        for lanc in self.aurora + self.merid:
            cl = classificar(lanc, self.cad, self.agente_ia)
            idx = f"LCT-{lanc['banco']}-{lanc['ref_origem']}"
            out.append(dict(id_saida=idx, banco=lanc["banco"], ref_origem=lanc["ref_origem"],
                            data=C.iso(lanc["data"]), descricao=lanc["descricao"],
                            valor=C.n2(lanc["valor"]), conta_codigo=cl["conta"] or "",
                            metodo=cl["metodo"], confianca=round(cl["confianca"], 2),
                            conta_descricao=self.plano.get(cl["conta"], {}).get("descricao", ""),
                            cnpj_lojista=cl["cnpj_lojista"] or ""))
            self._r(idx, lanc["arquivo_origem"], lanc["ref_origem"], lanc["valor"])
            if cl["metodo"] == "HUMANO" or cl["conta"] is None:
                self._p("CLASSIFICACAO_MANUAL", lanc["ref_origem"], lanc["valor"],
                        cl["motivo"] or "lancamento sem regra", "Financeiro Tarvo", lanc["arquivo_origem"])
            if cl["conta"] == "1.1.09.002":
                self._p("CREDITO_NAO_IDENTIFICADO", lanc["ref_origem"], lanc["valor"],
                        f"'{lanc['descricao']}' - origem desconhecida. Identificar o pagador antes de baixar",
                        "Financeiro Tarvo")
            if "DEVOLUCAO" in (lanc["descricao"] or "").upper():
                self._p("REPASSE_DEVOLVIDO", lanc["ref_origem"], lanc["valor"],
                        f"'{lanc['descricao']}' - repasse voltou. Reenviar ou abater do proximo repasse?",
                        "Financeiro Tarvo")
        self._conciliar_transferencias()
        self.lcts = out
        return out

    def _conciliar_transferencias(self):
        """4 transferencias saem do Aurora, 3 entram no Meridiano. A diferenca e trânsito ou erro."""
        saidas = [l for l in self.aurora if "TRANSF ENTRE CONTAS" in (l["descricao"] or "").upper()]
        entradas = [l for l in self.merid if "MESMA TITULARIDADE" in (l["descricao"] or "").upper()]
        disp = [e["valor"] for e in entradas]
        for s in saidas:
            alvo = -s["valor"]
            if any(abs(v - alvo) < 0.01 for v in disp):
                disp.remove(next(v for v in disp if abs(v - alvo) < 0.01))
            else:
                self._p("TRANSFERENCIA_SEM_CONTRAPARTIDA", s["ref_origem"], s["valor"],
                        f"transferencia de R$ {alvo:,.2f} em {C.iso(s['data'])} sai do Aurora e nao "
                        f"aparece no Meridiano na competencia. Confirmar se e trânsito D+1 (Q17)",
                        "Financeiro Tarvo", s["arquivo_origem"])

    # ---------- 5. NOTAS ----------
    def notas(self):
        out = []
        for c in self.cms_checkout:
            if not c.get("apuravel", 1):
                continue   # ja virou pendencia SEM_TAXA_CONTRATADA: nao fatura
            if c["comissao_brl"] <= 0:
                self._p("COMISSAO_NEGATIVA", c["id_saida"], c["comissao_brl"],
                        f"{c['lojista']} fechou o mes com comissao nao positiva (estornos > vendas). "
                        f"Nao emite NF - avaliar nota de credito (Q14)", "Financeiro Tarvo")
                continue
            if not c["cnpj"]:
                self._p("NF_SEM_TOMADOR", c["id_saida"], c["comissao_brl"],
                        "comissao apurada mas sem CNPJ confirmado. NF nao emitida", "Financeiro Tarvo")
                continue
            idx = f"NF-CHK-{c['cnpj']}"
            out.append(dict(id_saida=idx, tomador_cnpj=c["cnpj"], tomador=c["lojista"],
                            linha_negocio="CHECKOUT", valor_brl=c["comissao_brl"],
                            discriminacao=(f"Intermediacao de pagamentos {self.comp}: MDR R$ "
                                           f"{c['comissao_mdr_brl']:.2f} + antecipacao R$ "
                                           f"{c['comissao_antecipacao_brl']:.2f} sobre "
                                           f"{c['qtd_transacoes']} transacoes")))
            for r in [x for x in self.rastro if x["id_saida"] == c["id_saida"]]:
                self._r(idx, r["arquivo_origem"], r["ref_origem"], r["valor"])
        total = C.n2(sum(c["comissao_brl"] for c in self.cms_remessa))
        if TOMADOR_NF_REMESSA == "PONTE" and total > 0:
            idx = "NF-REM-PONTE"
            nops = sum(c["qtd_operacoes"] for c in self.cms_remessa)
            out.append(dict(id_saida=idx, tomador_cnpj=C.CNPJ_PONTE_CAMBIO, tomador=C.NOME_PONTE_CAMBIO,
                            linha_negocio="REMESSA", valor_brl=total,
                            discriminacao=(f"Intermediacao de cambio {self.comp}: participacao de "
                                           f"{C.PARTICIPACAO_SPREAD*100:.0f}% sobre o spread realizado de "
                                           f"{nops} operacoes")))
            for c in self.cms_remessa:
                for r in [x for x in self.rastro if x["id_saida"] == c["id_saida"]]:
                    self._r(idx, r["arquivo_origem"], r["ref_origem"], r["valor"])
            self._p("TOMADOR_DA_NF_DE_CAMBIO", idx, total,
                    "NF de intermediacao emitida contra a Ponte Cambio (premissa Q12, baseada no e-mail: "
                    "repasse 'mediante recebimento da nota fiscal de intermediacao'). "
                    "Se o tomador correto for cada lojista, trocar TOMADOR_NF_REMESSA", "Financeiro Tarvo")
        else:
            for c in self.cms_remessa:
                if c["comissao_brl"] <= 0: continue
                idx = f"NF-REM-{c['cnpj']}"
                out.append(dict(id_saida=idx, tomador_cnpj=c["cnpj"], tomador=c["lojista"],
                                linha_negocio="REMESSA", valor_brl=c["comissao_brl"],
                                discriminacao=f"Intermediacao de cambio {self.comp}: {c['qtd_operacoes']} operacoes"))
                for r in [x for x in self.rastro if x["id_saida"] == c["id_saida"]]:
                    self._r(idx, r["arquivo_origem"], r["ref_origem"], r["valor"])
        self.nfs = out
        return out

    # ---------- orquestracao ----------
    def executar(self):
        self.carregar()
        self.checkout()
        self.divergencias_checkout()
        self.remessa()
        self.lancamentos()
        self.notas()
        return self
