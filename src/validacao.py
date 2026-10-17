# -*- coding: utf-8 -*-
"""Conferencia das fontes antes de fechar.

Duas regras do financeiro (resposta a Turma do Barulho, 17/10 12h31):

  "Prefiro que a solucao avise a que quebre sem ninguem perceber."
  "Quando falta alguma coisa, eu nao seguro o mes inteiro. Fecha o que nao depende
   daquilo, marca o que e provisorio e deixa claro o que esta bloqueado e por que."

Entao: arquivo ausente ou layout mudado NAO derruba o fechamento. Bloqueia so a parte
que depende daquela fonte, marca a saida como PROVISORIA e escreve o motivo em
pendencias.csv, com quem libera.
"""
import os
from . import leitores as L

# colunas/marcadores que cada fonte tem de trazer. Se o parceiro mudar o layout sem
# avisar - ja aconteceu, segundo o financeiro - o fechamento diz exatamente o que mudou.
ESPERADO = {
    "orbe":      ["id_transacao", "data_movimento", "cod_estabelecimento", "tipo_lancamento",
                  "modalidade", "qtd_parcelas", "valor_bruto", "taxa_aplicada_pct",
                  "valor_taxa", "id_referencia", "data_venda_original"],
    "ponte":     ["Nº Operação", "Data Contratação", "CNPJ Cliente", "Valor R$", "Spread R$",
                  "Spread %", "Status Compliance"],
    "taxas":     ["Lojista", "CNPJ", "EC Orbe", "Vigência"],
    "aurora":    ["Data", "Lançamento", "Valor (R$)"],
    "meridiano": ["<STMTTRN>", "<FITID>", "<TRNAMT>", "<MEMO>"],
    "plano":     ["COD_CONTA", "DESCRICAO", "ACEITA_LANCTO"],
}

# que parte do fechamento depende de que fonte
DEPENDE = {
    "CHECKOUT":     ["orbe", "taxas"],
    "REMESSA":      ["ponte", "taxas"],
    "EXTRATO_AURORA":    ["aurora", "plano"],
    "EXTRATO_MERIDIANO": ["meridiano", "plano"],
}

def conferir(pasta):
    """-> (fontes_ok: set, problemas: [dict])"""
    ok, problemas = set(), []
    for chave in ESPERADO:
        try:
            caminho = L.achar(pasta, chave)
        except FileNotFoundError:
            problemas.append(dict(fonte=chave, tipo="AUSENTE",
                                  detalhe=f"nenhum arquivo bate com {L.PADROES[chave]}"))
            continue
        except RuntimeError as e:
            problemas.append(dict(fonte=chave, tipo="AMBIGUO", detalhe=str(e)))
            continue
        falta = _colunas_faltando(chave, caminho)
        if falta:
            problemas.append(dict(fonte=chave, tipo="LAYOUT_MUDOU", arquivo=os.path.basename(caminho),
                                  detalhe="nao encontrei: " + ", ".join(falta)))
            continue
        ok.add(chave)
    return ok, problemas

def _colunas_faltando(chave, caminho):
    try:
        bruto = open(caminho, "rb").read()
    except OSError as e:
        return [f"nao consegui ler o arquivo ({e})"]
    if chave in ("orbe", "aurora", "plano", "meridiano"):
        texto = _decodificar(bruto)[:20000]
        return [c for c in ESPERADO[chave] if c not in texto]
    # xlsx / eml: procura os rotulos no conteudo extraido
    try:
        if chave == "taxas":
            import openpyxl
            wb = openpyxl.load_workbook(caminho, data_only=True, read_only=True)
            aba = next((s for s in wb.sheetnames if "vigente" in s.lower()), wb.sheetnames[0])
            texto = " | ".join(str(c) for r in wb[aba].iter_rows(min_row=1, max_row=6, values_only=True)
                               for c in (r or ()) if c is not None)
        else:
            ops, _ = L.ler_ponte(os.path.dirname(caminho))
            texto = " | ".join(ops[0].keys()) if ops else ""
            return [] if ops else ["o anexo do e-mail nao trouxe nenhuma operacao"]
    except Exception as e:
        return [f"nao consegui abrir ({type(e).__name__}: {e})"]
    return [c for c in ESPERADO[chave] if c not in texto]

def _decodificar(bruto):
    for enc in ("utf-8", "utf-8-sig", "cp1252", "latin-1"):
        try: return bruto.decode(enc)
        except UnicodeDecodeError: continue
    return bruto.decode("latin-1", "replace")

def partes_bloqueadas(fontes_ok):
    """-> {parte: [fontes que faltam]}"""
    return {parte: [f for f in fontes if f not in fontes_ok]
            for parte, fontes in DEPENDE.items()
            if any(f not in fontes_ok for f in fontes)}
