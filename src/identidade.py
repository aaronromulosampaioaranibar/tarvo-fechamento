# -*- coding: utf-8 -*-
"""Cadastro de lojistas: a unica ponte entre Orbe, Ponte Cambio e os dois bancos.

Regra dura: NOME NUNCA E CHAVE PRIMARIA. A chave e o CNPJ (14 digitos) e, no checkout,
o cod_estabelecimento da Orbe. Quando so existe nome truncado (extratos), a resolucao
e por prefixo normalizado UNICO; empate ou ausencia viram pendencia, nunca palpite.
"""
import os, csv, datetime as _dt
from .comum import cnpj14, chave_nome, digitos

def _d(s):
    s = (s or "").strip()
    if not s: return None
    return _dt.datetime.strptime(s, "%Y-%m-%d").date()

ARQ_OVERRIDES = "cadastro/de_para_ec.csv"
ARQ_CONDICOES = "cadastro/condicoes_especiais.csv"

class Cadastro:
    def __init__(self, taxas, raiz="."):
        self.taxas = [t for t in taxas if t["cnpj"]]
        self.por_cnpj = {}
        for t in self.taxas:
            self.por_cnpj.setdefault(t["cnpj"], []).append(t)
        # nome "oficial" = o da primeira linha de taxa do CNPJ
        self.nome = {c: v[0]["lojista"] for c, v in self.por_cnpj.items()}
        self.inativo = {c: all(x["inativo"] for x in v) for c, v in self.por_cnpj.items()}

        # EC -> CNPJ vindo da propria planilha (fonte primaria)
        self.ec2cnpj, self.ec_origem = {}, {}
        for t in self.taxas:
            if t["ec"]:
                self.ec2cnpj[t["ec"]] = t["cnpj"]
                self.ec_origem[t["ec"]] = "PLANILHA_TAXAS"
        # overrides: ECs que a planilha nao resolve, respondidos pelo financeiro
        # ou assumidos como premissa (ver HIPOTESES.md)
        self.ec_conf = {e: 1.0 for e in self.ec2cnpj}
        cam = os.path.join(raiz, ARQ_OVERRIDES)
        self.overrides = []
        if os.path.exists(cam):
            with open(cam, encoding="utf-8") as fh:
                for r in csv.DictReader(fh, delimiter=";"):
                    if not r.get("ec"): continue
                    ec = digitos(r["ec"]); c = cnpj14(r["cnpj"])
                    if not c: continue
                    self.ec2cnpj[ec] = c
                    self.ec_origem[ec] = r.get("origem", "OVERRIDE")
                    try: self.ec_conf[ec] = float(r.get("confianca") or 0.8)
                    except ValueError: self.ec_conf[ec] = 0.8
                    if c not in self.nome: self.nome[c] = r.get("lojista") or c
                    self.overrides.append(r)

        # condicoes especiais: o que o comercial fecha e nao chega na planilha de taxas.
        # Elas VENCEM a tabela contratada dentro da vigencia, e sao marcadas na divergencia
        # com natureza propria, porque nao ha o que cobrar do parceiro.
        self.condicoes = []
        camc = os.path.join(raiz, ARQ_CONDICOES)
        if os.path.exists(camc):
            with open(camc, encoding="utf-8") as fh:
                for r in csv.DictReader(fh, delimiter=";"):
                    if not r.get("cnpj"): continue
                    self.condicoes.append(dict(
                        cnpj=cnpj14(r["cnpj"]), coluna=r["coluna"].strip(),
                        taxa=float(r["taxa_pct"]), de=_d(r.get("vig_de")),
                        ate=_d(r.get("vig_ate")), origem=r.get("origem", ""),
                        obs=r.get("observacao", ""), lojista=r.get("lojista", "")))

        # indice de nome -> cnpj, para os extratos
        self._idx = {}
        for c, nm in self.nome.items():
            self._idx.setdefault(chave_nome(nm), set()).add(c)
        for t in self.taxas:
            self._idx.setdefault(chave_nome(t["lojista"]), set()).add(t["cnpj"])

    # ---------------- checkout ----------------
    def cnpj_do_ec(self, ec):
        return self.ec2cnpj.get(ec)

    def confianca_do_ec(self, ec):
        return self.ec_conf.get(ec, 0.0)

    def origem_do_ec(self, ec):
        return self.ec_origem.get(ec, "NAO_RESOLVIDO")

    # ---------------- taxa vigente ----------------
    def condicao(self, cnpj, coluna, data_ref):
        """Condicao especial vigente na data (isencao, tarifa promocional). None se nao houver."""
        for c in self.condicoes:
            if c["cnpj"] != cnpj or c["coluna"] != coluna: continue
            if data_ref and c["de"] and data_ref < c["de"]: continue
            if data_ref and c["ate"] and data_ref > c["ate"]: continue
            return c
        return None

    def taxa(self, cnpj, coluna, data_ref):
        """Taxa que a Tarvo tem direito de cobrar na data.
        Devolve (taxa_pct, ref_origem, especial). `especial` marca condicao comercial
        que o parceiro nao conhece - a diferenca vira devolucao ao lojista, nao cobranca."""
        c = self.condicao(cnpj, coluna, data_ref)
        if c is not None:
            return c["taxa"], f"condicoes_especiais.csv!{c['cnpj']}/{c['coluna']}", True
        linhas = [t for t in self.por_cnpj.get(cnpj, []) if t.get(coluna) is not None]
        if not linhas: return None, None, False
        validas = []
        for t in linhas:
            de, ate = t["vig_de"], t["vig_ate"]
            if data_ref and de and data_ref < de: continue
            if data_ref and ate and data_ref > ate: continue
            validas.append(t)
        if not validas: return None, None, False
        # mais de uma vigente: a de inicio mais recente ganha
        validas.sort(key=lambda t: (t["vig_de"] or __import__("datetime").date(1900, 1, 1)))
        esc = validas[-1]
        return esc[coluna], esc["ref_origem"], False

    # ---------------- extratos ----------------
    def por_nome_truncado(self, nome):
        """Nome de extrato (truncado, sem acento confiavel) -> (cnpj, metodo, confianca).
        Casa por prefixo normalizado nos dois sentidos e exige resultado UNICO."""
        k = chave_nome(nome)
        if not k: return None, "HUMANO", 0.0
        exato = self._idx.get(k)
        if exato and len(exato) == 1:
            return next(iter(exato)), "REGRA", 1.0
        cand = {c for kk, cs in self._idx.items() if kk and (kk.startswith(k) or k.startswith(kk))
                for c in cs}
        if len(cand) == 1:
            return next(iter(cand)), "REGRA", 0.98
        if len(cand) > 1:
            return None, "HUMANO", 0.0          # ambiguo: Horizonte x Novo Horizonte
        return None, "HUMANO", 0.0
