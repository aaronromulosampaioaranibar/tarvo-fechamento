# -*- coding: utf-8 -*-
"""Classificacao dos extratos no plano de contas.

Camada 1 (REGRA): padroes do historico, deterministicos, confianca 1.0.
Camada 2 (IA): so o residuo que a camada 1 nao cobriu. Devolve conta + confianca.
Camada 3 (HUMANO): confianca abaixo do corte, ou caso que e decisao de negocio.

A conta registrada e a CONTRAPARTIDA do lancamento: a conta do proprio banco
(1.1.01.001 Aurora / 1.1.01.002 Meridiano) e implicita no campo `banco`.
"""
import re
from .comum import CORTE_CONFIANCA_IA

# (regex na descricao, conta, exige_lojista, rotulo)
REGRAS_AURORA = [
    (r"^TED RECEBIDA .*ORBE",                  "1.1.03.001", False, "liquidacao da adquirente Orbe"),
    (r"^TRANSF ENTRE CONTAS",                  "1.1.09.001", False, "transferencia entre contas proprias"),
    (r"^DEVOLUCAO PIX",                        "2.1.01.001", True,  "repasse a lojista devolvido"),
    (r"^PIX RECEBIDO .*SEM IDENTIFICACAO",     "1.1.09.002", False, "credito sem identificacao"),
    (r"^PIX ENVIADO CONTABILIDADE",            "4.2.06",     False, "servicos contabeis"),
    (r"^PIX ENVIADO ",                         "2.1.01.001", True,  "repasse a lojista"),
    (r"^PAGTO SALARIOS",                       "2.1.04.001", False, "folha de pagamento"),
    (r"^GPS INSS",                             "2.1.04.002", False, "INSS"),
    (r"^GRF FGTS",                             "2.1.04.003", False, "FGTS"),
    (r"^PAGTO ISS",                            "2.1.03.003", False, "ISS"),
    (r"DARF .*IRRF",                           "2.1.03.004", False, "IRRF"),
    (r"DARF .*PIS",                            "2.1.03.001", False, "PIS"),
    (r"DARF .*COFINS",                         "2.1.03.002", False, "COFINS"),
    (r"^BOLETO CONDOMINIO|^ALUGUEL",           "4.2.02",     False, "aluguel e condominio"),
    (r"AMAZON WEB SERVICES|^DEB AUT .*CLOUD",  "4.2.03",     False, "cloud e infraestrutura"),
    (r"GOOGLE WORKSPACE|^CARTAO PJ",           "4.2.04",     False, "softwares e assinaturas"),
    (r"^TAR |^TARIFA",                         "4.2.01",     False, "tarifa bancaria"),
]
REGRAS_MERIDIANO = [
    # ATENCAO: "PIX RECEB PONTE A..." e a Ponte Aerea (lojista), nao a Ponte Cambio.
    # A disciplina de prefixo (PIX RECEB = lojista, TED = parceiro) e o que separa os dois.
    (r"^PIX RECEB ",                           "2.1.02.001", True,  "recurso de lojista para remessa"),
    (r"^TED ENVIADA PONTE CAMBIO",             "2.1.02.001", False, "liquidacao de remessas na Ponte Cambio"),
    (r"^TED RECEB(IDA)? PONTE CAMBIO.*COMISSAO","1.1.03.002", False, "repasse de comissao de cambio de competencia anterior"),
    (r"MESMA TITULARIDADE|^TED RECEBIDA TARVO","1.1.09.001", False, "transferencia entre contas proprias"),
    (r"^APLICACAO AUTOMATICA|^RESGATE AUTOMATICO","1.1.02.001",False,"aplicacao financeira automatica"),
    (r"^RENDIMENTO",                           "3.2.01",     False, "rendimento de aplicacao"),
    (r"^SEGURO",                               "4.2.05",     False, "seguro empresarial"),
    (r"^IOF",                                  "4.3.01",     False, "IOF"),
    (r"^TARIFA|^TAR ",                         "4.2.01",     False, "tarifa bancaria"),
]

def classificar(lanc, cadastro, agente_ia=None):
    """-> dict(conta, metodo, confianca, rotulo, cnpj_lojista, motivo_pendencia)"""
    desc = (lanc["descricao"] or "").upper()
    regras = REGRAS_AURORA if lanc["banco"] == "AURORA" else REGRAS_MERIDIANO
    for rx, conta, exige_lojista, rotulo in regras:
        if not re.search(rx, desc): continue
        cnpj, met, conf = (None, "REGRA", 1.0)
        if exige_lojista:
            nome = re.sub(r"^(PIX ENVIADO|PIX RECEB(IDO)?|DEVOLUCAO PIX -)\s*", "", desc).strip()
            cnpj, met, conf = cadastro.por_nome_truncado(nome)
            if cnpj is None:
                return dict(conta=conta, metodo="HUMANO", confianca=0.0, rotulo=rotulo,
                            cnpj_lojista=None,
                            motivo=f"nome '{nome}' nao resolve para um unico lojista do cadastro")
            met, conf = "REGRA", min(1.0, conf)
        return dict(conta=conta, metodo="REGRA", confianca=conf, rotulo=rotulo,
                    cnpj_lojista=cnpj, motivo=None)
    # residuo -> IA
    if agente_ia is not None:
        s = agente_ia(lanc)
        if s and s.get("confianca", 0) >= CORTE_CONFIANCA_IA:
            return dict(conta=s["conta"], metodo="IA", confianca=s["confianca"],
                        rotulo=s.get("rotulo", "classificado por IA"),
                        cnpj_lojista=None, motivo=None)
        if s:
            return dict(conta=s.get("conta"), metodo="HUMANO", confianca=s.get("confianca", 0.0),
                        rotulo=s.get("rotulo", ""), cnpj_lojista=None,
                        motivo=f"IA sugeriu {s.get('conta')} com confianca {s.get('confianca')}, abaixo do corte")
    return dict(conta=None, metodo="HUMANO", confianca=0.0, rotulo="",
                cnpj_lojista=None, motivo="descricao fora de todos os padroes conhecidos")
