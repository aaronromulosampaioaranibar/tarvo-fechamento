# -*- coding: utf-8 -*-
"""Gravacao no formato fixo e autoteste de fechamento.
Se um assert falha, NADA e gravado. Total que nao fecha e pior que total que falta."""
import os, csv
from collections import defaultdict
from . import comum as C

COLUNAS = {
  "comissoes_por_lojista.csv": ["id_saida","cnpj","lojista","linha_negocio","comissao_brl",
      "comissao_mdr_brl","comissao_antecipacao_brl","spread_total_brl","participacao_pct",
      "qtd_transacoes","qtd_operacoes","ec_orbe","confianca_identidade","origem_identidade","apuravel"],
  "divergencias_taxa.csv": ["id_saida","cnpj","linha_negocio","ref_origem","taxa_contratada_pct",
      "taxa_aplicada_pct","diferenca_brl","data","modalidade","valor_bruto","sentido",
      "natureza","cobrar_de","ref_taxa_contratada"],
  "devolucoes_lojista.csv": ["id_saida","cnpj","lojista","ref_origem","data","taxa_contratada_pct",
      "taxa_aplicada_pct","valor_bruto","valor_descontado_pela_orbe","comissao_contratada",
      "valor_brl","diferenca_pela_formula_brl","motivo"],
  "notas_a_emitir.csv": ["id_saida","tomador_cnpj","tomador","linha_negocio","valor_brl","discriminacao"],
  "lancamentos_classificados.csv": ["id_saida","banco","ref_origem","data","descricao","valor",
      "conta_codigo","metodo","confianca","conta_descricao","cnpj_lojista"],
  "pendencias.csv": ["id_saida","tipo","ref_origem","valor_brl","motivo","quem_decide"],
  "rastro.csv": ["id_saida","arquivo_origem","ref_origem","valor","regra"],
}

def conferir_escrita(pasta):
    """Quais arquivos de saida estao travados por outro programa.

    No Windows, um CSV aberto no Excel nao pode ser regravado. Se descobrirmos isso
    no meio da gravacao, metade dos arquivos ja foi trocada e a outra metade continua
    sendo a do mes passado - uma saida incoerente, que e exatamente o que este projeto
    promete nunca entregar. Entao perguntamos ANTES de apurar qualquer coisa.

    Devolve a lista de nomes travados (vazia quando esta tudo livre)."""
    travados = []
    if not os.path.isdir(pasta): return travados
    for nome in list(COLUNAS) + ["execucao.json"]:
        caminho = os.path.join(pasta, nome)
        if not os.path.exists(caminho): continue
        try:
            with open(caminho, "a"): pass
        except OSError:
            travados.append(nome)
    return travados

def _fmt(v):
    if v is None: return ""
    if isinstance(v, bool): return "1" if v else "0"
    if isinstance(v, float): return f"{v:.2f}" if abs(v) >= 0.005 or v == 0 else f"{v:.4f}"
    return str(v)

def gravar(nome, linhas, pasta):
    os.makedirs(pasta, exist_ok=True)
    cols = COLUNAS[nome]
    with open(os.path.join(pasta, nome), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, delimiter=";", quoting=csv.QUOTE_MINIMAL)
        w.writerow(cols)
        for l in linhas:
            w.writerow([_fmt(l.get(c)) for c in cols])

def autoteste(f):
    """As tres invariantes. Devolve (ok, lista de falhas, lista de conferencias)."""
    falhas, ok_ = [], []
    soma = defaultdict(float)
    for r in f.rastro: soma[r["id_saida"]] += r["valor"]

    def confere(rotulo, linhas, campo):
        for l in linhas:
            i = l["id_saida"]
            if i not in soma:
                falhas.append(f"{rotulo}: {i} nao tem linha em rastro.csv"); continue
            if abs(soma[i] - l[campo]) > 0.011:
                falhas.append(f"{rotulo}: {i} reporta {l[campo]:.2f} e o rastro soma {soma[i]:.2f}")
        ok_.append(f"{rotulo}: {len(linhas)} ids conferidos contra o rastro")

    confere("comissoes", f.cms_checkout + f.cms_remessa, "comissao_brl")
    confere("divergencias", f.div_checkout + f.div_remessa, "diferenca_brl")
    confere("devolucoes", f.devolucoes, "valor_brl")
    confere("notas", f.nfs, "valor_brl")
    confere("lancamentos", f.lcts, "valor")
    # A auditoria independente (testes/auditoria_rastro.py) descobriu que as pendencias
    # com valor ficavam de fora desta conferencia. O invariante vale para TODO numero
    # da saida, nao so para os cinco arquivos principais.
    confere("pendencias", [p for p in f.pend if abs(p["valor_brl"]) > 0.005], "valor_brl")

    # fechamento contra a origem
    t_linha = C.n2(sum(t["_comissao"] for t in f.orbe if t.get("_comissao") is not None))
    t_chk = C.n2(sum(c["comissao_brl"] for c in f.cms_checkout))
    if abs(t_linha - t_chk) > 0.011:
        falhas.append(f"comissao de checkout {t_chk:.2f} != soma das comissoes por linha {t_linha:.2f}")
    cobrado = C.n2(sum(t["valor_taxa"] or 0 for t in f.orbe))
    ok_.append(f"checkout: R$ {t_chk:,.2f} apurado pela taxa contratada "
               f"(a Orbe cobrou R$ {cobrado:,.2f}; a diferenca esta em divergencias e devolucoes)")

    t_rem = C.n2(sum(c["comissao_brl"] for c in f.cms_remessa))
    t_sp = C.n2(sum(o["comissao_tarvo"] for o in f.ops_remessa))
    if abs(t_rem - t_sp) > 0.011:
        falhas.append(f"comissao de remessa {t_rem:.2f} != soma das parcelas por operacao {t_sp:.2f}")
    bruto = C.n2(sum(o["spread_brl"] for o in f.ops_remessa) * C.PARTICIPACAO_SPREAD)
    ok_.append(f"remessa: R$ {t_rem:,.2f} == soma das parcelas por operacao "
               f"(diferenca de arredondamento vs {C.PARTICIPACAO_SPREAD:.0%} do spread total: R$ {t_rem-bruto:+.2f})")

    # cobertura: todo EC da Orbe resolvido OU com pendencia aberta
    ecs = {t["ec"] for t in f.orbe}
    pend_txt = " ".join(p["ref_origem"] + " " + p["motivo"] for p in f.pend)
    for ec in sorted(ecs):
        if f.cad.cnpj_do_ec(ec) is None and ec not in pend_txt:
            falhas.append(f"EC {ec} da Orbe nao resolve e nao tem pendencia aberta")
    ok_.append(f"identidade: {len(ecs)} ECs da Orbe resolvidos ou com pendencia")

    # toda operacao da Ponte aparece uma vez na saida ou em pendencias
    usadas = {o["operacao"] for o in f.ops_remessa}
    pend_ops = {p["ref_origem"] for p in f.pend}
    faltando = [o["operacao"] for o in f.ponte
                if o["operacao"] not in usadas and o["operacao"] not in pend_ops]
    if faltando:
        falhas.append(f"{len(faltando)} operacoes da Ponte sumiram: {faltando[:5]}")
    ok_.append(f"remessa: {len(f.ponte)} linhas do relatorio da Ponte -> {len(usadas)} na saida + pendencias")

    # todo lancamento bancario classificado ou com pendencia
    sem = [l for l in f.lcts if not l["conta_codigo"]]
    ok_.append(f"extratos: {len(f.lcts)} lancamentos, {len(sem)} sem conta")
    return (len(falhas) == 0), falhas, ok_
