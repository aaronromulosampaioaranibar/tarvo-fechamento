# -*- coding: utf-8 -*-
"""Normalizacao e parametros. Nada aqui depende de setembro."""
import re, unicodedata, datetime as dt
from decimal import Decimal, ROUND_HALF_UP

# --- parametros do fechamento (premissas versionadas; ver HIPOTESES.md) ---
TOLERANCIA_TAXA_PP   = 0.01     # Q10: criterio nosso. Abaixo disso e truncamento da Orbe,
                                #      nao divergencia de contrato (resposta de 21h13)
BASE_COMISSAO        = "CONTRATADA"  # RESPONDIDA: a comissao e valor_bruto x taxa CONTRATADA,
                                     # nao o valor_taxa que a Orbe aplicou
PARTICIPACAO_SPREAD  = 0.50     # A7: e-mail da Ponte Cambio
SPREAD_PADRAO_PCT    = 1.50     # Q4: premissa ate o financeiro responder
COMPETENCIA_REMESSA  = "contratacao"   # Q6: "contratacao" ou "liquidacao"
INCLUI_SPREAD_NEGATIVO = False  # Q5 RESPONDIDA: "nao aceito, fica fora da comissao e da nota"
DEDUP_PONTE          = True     # Q7
CORTE_CONFIANCA_IA   = 0.95     # abaixo disso vira pendencia, nao classificacao
MAX_PARCELAS         = 12       # "a gente nao vende acima de 12x" - acima disso e pendencia
CNPJ_PONTE_CAMBIO    = "75374179000146"
NOME_PONTE_CAMBIO    = "PONTE CAMBIO S.A."

SUFIXOS = (" LTDA"," L.T.D.A"," S.A"," SA"," ME"," EPP"," EIRELI")

def digitos(v):
    return re.sub(r"\D","",str(v or ""))

def cnpj14(v):
    """CNPJ com e sem mascara, e com zero a esquerda faltando, vira sempre 14 digitos."""
    d = digitos(v)
    if not d: return ""
    if len(d) > 14: return d[:14]
    return d.zfill(14)

def sem_acento(s):
    s = unicodedata.normalize("NFKD", str(s or ""))
    return "".join(c for c in s if not unicodedata.combining(c))

def chave_nome(s):
    """Chave para comparar nomes truncados de banco com nomes de cadastro.
    Sem acento, sem pontuacao, sem espaco, sem sufixo societario, maiuscula."""
    s = sem_acento(s).upper()
    s = re.sub(r"[^A-Z0-9 ]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    for suf in SUFIXOS:
        if s.endswith(suf): s = s[: -len(suf)].strip()
    return s.replace(" ", "")

def brl(v):
    """Decimal pt-BR ('1.234,56') ou en ('1234.56') -> float."""
    if v is None: return None
    s = str(v).strip()
    if s == "" or s.lower() == "nan": return None
    s = s.replace("R$", "").replace(" ", "")
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    try: return float(s)
    except ValueError: return None

def pct(v):
    """Taxa como 0.0149 (float), '1,49%' (texto) ou 1.49 -> sempre em pontos percentuais."""
    if v is None: return None
    if isinstance(v, str):
        s = v.strip()
        if s == "" or s.lower() in ("padrao", "padrão"): return None
        if s.endswith("%"):
            x = brl(s[:-1]); return x
        x = brl(s)
        if x is None: return None
        return x * 100 if x < 0.5 else x
    try: x = float(v)
    except (TypeError, ValueError): return None
    # 0.0149 -> 1.49 ; 1.49 ja esta em p.p.
    return x * 100 if abs(x) < 0.5 else x

def data_br(v):
    if v is None: return None
    if isinstance(v, (dt.date, dt.datetime)): return v.date() if isinstance(v, dt.datetime) else v
    s = str(v).strip()[:10]
    for f in ("%d/%m/%Y", "%Y-%m-%d", "%d/%m/%y"):
        try: return dt.datetime.strptime(s, f).date()
        except ValueError: pass
    return None

def iso(d):
    return d.isoformat() if d else ""

def n2(x):
    """Arredondamento comum para o centavo, meio centavo para cima, inclusive no negativo:
    -0,005 vira -0,01. (Python arredonda para o par; a Orbe trunca. Nenhum dos dois serve.)"""
    return float(Decimal(str(float(x or 0))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

def faixa_mdr(modalidade, parcelas):
    """Modalidade da Orbe -> coluna da tabela de taxas contratadas."""
    m = (modalidade or "").strip().upper()
    if m == "DEBITO": return "DEBITO"
    if m == "PIX": return "PIX"
    if m == "CREDITO A VISTA": return "AVISTA"
    if m == "CREDITO PARCELADO":
        p = int(parcelas or 0)
        return "C26" if 2 <= p <= 6 else "C712"
    return None
