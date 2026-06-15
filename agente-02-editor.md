"""
Agente 02 — "O Editor"
Processamento de Linguagem Natural para Dados de Produto

Correções aplicadas:
- Regex de extração de preço com proteção contra unidades de medida (cm, g, k, mm, ml)
- Pipeline `.trim()` antes de todos os regex
- Fallback LLM integrado com flag de confiança
"""

import re
import json
from typing import Optional

# ---------------------------------------------------------------------------
# Dicionários de Domínio
# ---------------------------------------------------------------------------

ABREVIACOES = {
    # Tipos de produto
    "bri": "Brinco", "brinco": "Brinco",
    "col": "Colar", "colar": "Colar",
    "pul": "Pulseira", "pulseira": "Pulseira",
    "an": "Anel", "anel": "Anel",
    "ali": "Aliança", "aliança": "Aliança",
    "conj": "Conjunto", "conjnto": "Conjunto", "conjunto": "Conjunto",
    "torq": "Tornozeleira",
    "pirc": "Piercing", "piercing": "Piercing",
    "brch": "Broche",
    "ping": "Pingente", "pingente": "Pingente",
    "corrente": "Corrente", "corr": "Corrente",
    "gar": "Gargantilha", "garg": "Gargantilha",
    # Materiais
    "prt": "Prata", "prata": "Prata",
    "our": "Ouro", "ouro": "Ouro",
    "aço": "Aço Inoxidável",
    "rod": "Ródio",
    "rose": "Rosé",
    "bnh": "Banhado",
    # Pedras
    "zirc": "Zircônia", "zirconia": "Zircônia",
    "perl": "Pérola", "perola": "Pérola",
    "crist": "Cristal",
    "ametst": "Ametista",
    "rubi": "Rubi",
    "safr": "Safira",
    "esmer": "Esmeralda",
}

# Unidades de medida que NUNCA são preço
UNIDADES_MEDIDA = re.compile(
    r'^\d+(?:[.,]\d+)?\s*(?:cm|mm|m|g|kg|ml|l|k|kt|pol|"|\'|x\d)$',
    re.IGNORECASE
)

FAIXAS_PRECO = {
    "Brinco":       {"min": 15,   "max": 5000},
    "Colar":        {"min": 30,   "max": 15000},
    "Anel":         {"min": 20,   "max": 20000},
    "Aliança":      {"min": 80,   "max": 30000},
    "Pulseira":     {"min": 25,   "max": 10000},
    "Conjunto":     {"min": 50,   "max": 25000},
    "Corrente":     {"min": 40,   "max": 12000},
    "Gargantilha":  {"min": 35,   "max": 8000},
    "Pingente":     {"min": 15,   "max": 5000},
    "Tornozeleira": {"min": 20,   "max": 3000},
}


# ---------------------------------------------------------------------------
# Extração de Preço — Robusto contra unidades de medida
# ---------------------------------------------------------------------------

def extrair_preco(texto: str) -> tuple[Optional[float], Optional[str]]:
    """
    Extrai o valor monetário do texto ignorando unidades de medida.

    Retorna: (valor_float, substring_original_do_preco)

    Exemplos:
        "brinco 3cm prata 89"         → (89.0,  "89")
        "anel 18k ouro 320"           → (320.0, "320")
        "colar 2.5mm corrente 1.200"  → (1200.0,"1.200")
        "pulseira 89,90"              → (89.9,  "89,90")
        "conjunto 3g prata 250"       → (250.0, "250")
        "promoção de 120 por 89"      → (89.0,  "89")   ← captura "por X"
        "anel 18k 1.450,00"           → (1450.0,"1.450,00")
    """
    texto = texto.strip()

    # Remover "R$" para simplificar
    texto_limpo = re.sub(r'[Rr]\$\s*', '', texto).strip()

    # --- Prioridade 1: Padrão "por X" (promoção) ---
    m = re.search(r'\bpor\s+([\d.,]+)', texto_limpo, re.IGNORECASE)
    if m:
        val = _parse_numero(m.group(1))
        if val is not None:
            return val, m.group(1)

    # --- Coletar todos os candidatos numéricos com posição ---
    # Captura números como: 1.450,00 | 1.450 | 89,90 | 89 | 1200
    candidatos = []
    for m in re.finditer(r'(\d{1,3}(?:\.\d{3})*(?:,\d{1,2})?|\d+(?:,\d{1,2})?)', texto_limpo):
        numero_str = m.group(1)
        pos_fim = m.end()

        # Checar se a substring ao redor forma uma unidade de medida
        # Pega até 5 chars depois para ver se há sufixo de unidade
        contexto = texto_limpo[m.start():min(len(texto_limpo), pos_fim + 5)]
        if UNIDADES_MEDIDA.match(contexto.strip()):
            continue  # ignorar — é uma medida, não preço

        # Checar sufixo numérico colado (ex: "18k" → ignorar o "18")
        char_depois = texto_limpo[pos_fim:pos_fim+2].strip() if pos_fim < len(texto_limpo) else ''
        if re.match(r'^[kKgGmMcC]', char_depois):
            continue  # ignorar — "18k", "3g", "2mm" etc.

        val = _parse_numero(numero_str)
        if val is not None and val >= 1:  # Preços de joia >= R$1
            candidatos.append((val, numero_str, m.start()))

    if not candidatos:
        return None, None

    # Usar o ÚLTIMO candidato válido (convenção: preço vem no fim)
    val, num_str, _ = candidatos[-1]
    return val, num_str


def _parse_numero(s: str) -> Optional[float]:
    """Converte string numérica BR para float."""
    s = s.strip()
    # Padrão com centavos: 1.450,00 ou 89,90
    if re.match(r'^\d{1,3}(?:\.\d{3})*,\d{2}$', s):
        return float(s.replace('.', '').replace(',', '.'))
    # Milhar sem centavos: 1.450
    if re.match(r'^\d{1,3}\.\d{3}$', s):
        return float(s.replace('.', ''))
    # Inteiro ou decimal simples
    if re.match(r'^\d+$', s):
        return float(s)
    # Decimal com vírgula: 89,9
    if re.match(r'^\d+,\d{1,2}$', s):
        return float(s.replace(',', '.'))
    return None


# ---------------------------------------------------------------------------
# Extração e Correção do Nome
# ---------------------------------------------------------------------------

def _corrigir_palavra(palavra: str) -> str:
    """Expande abreviação ou retorna capitalizada."""
    p = palavra.lower().strip('.,;:')
    if p in ABREVIACOES:
        return ABREVIACOES[p]
    # Fuzzy simples: verifica prefixos (sem dependência externa)
    for abrev, expansao in ABREVIACOES.items():
        if len(p) >= 3 and abrev.startswith(p[:3]) and len(abrev) <= len(p) + 2:
            return expansao
    return palavra.capitalize()


def extrair_produto(texto: str, preco_str: Optional[str]) -> str:
    """Remove o preço e corrige o nome do produto."""
    texto = texto.strip()

    # Remove "R$" e o valor do preço
    nome = re.sub(r'[Rr]\$\s*', '', texto)
    if preco_str:
        # Remove exatamente a substring do preço (com possível "por" antes)
        nome = re.sub(r'\bpor\s+' + re.escape(preco_str), '', nome, flags=re.IGNORECASE)
        nome = nome.replace(preco_str, '')

    # Remove tokens que sobram como "reais" ou "por"
    nome = re.sub(r'\breais\b|\bpor\b', '', nome, flags=re.IGNORECASE)
    nome = re.sub(r'\s{2,}', ' ', nome).strip(' .,;')

    palavras = nome.split()
    return ' '.join(_corrigir_palavra(p) for p in palavras if p)


# ---------------------------------------------------------------------------
# Formatação Monetária
# ---------------------------------------------------------------------------

def formatar_preco_brl(valor: float) -> str:
    """89.0 → 'R$ 89,00' | 1450.0 → 'R$ 1.450,00'"""
    inteiro = int(valor)
    centavos = round((valor - inteiro) * 100)
    if inteiro >= 1000:
        milhar = f"{inteiro:,}".replace(',', '.')
        return f"R$ {milhar},{centavos:02d}"
    return f"R$ {inteiro},{centavos:02d}"


# ---------------------------------------------------------------------------
# Validação de Preço
# ---------------------------------------------------------------------------

def validar_preco(categoria: str, valor: float) -> dict:
    faixa = FAIXAS_PRECO.get(categoria, {"min": 5, "max": 50000})
    if valor < faixa["min"] or valor > faixa["max"]:
        return {
            "valido": False,
            "alerta": f"Preço R$ {valor:.2f} fora da faixa típica para {categoria} "
                      f"(R$ {faixa['min']:.2f} – R$ {faixa['max']:.2f}). Confirmar?"
        }
    return {"valido": True}


# ---------------------------------------------------------------------------
# Pipeline Principal
# ---------------------------------------------------------------------------

def processar_texto(texto_bruto: str) -> dict:
    """
    Camada 1: Regex + Dicionário.
    Retorna dict com 'usar_llm: True' se não conseguiu processar.
    """
    texto = texto_bruto.strip()

    if not texto:
        return {"sucesso": False, "motivo": "texto_vazio", "usar_llm": False}

    valor, preco_str = extrair_preco(texto)

    if valor is None:
        return {"sucesso": False, "motivo": "preco_nao_encontrado", "usar_llm": True}

    produto = extrair_produto(texto, preco_str)

    if not produto:
        return {"sucesso": False, "motivo": "produto_nao_identificado", "usar_llm": True}

    primeira_palavra = produto.split()[0]
    categoria = primeira_palavra if primeira_palavra in FAIXAS_PRECO else "Genérico"
    validacao = validar_preco(categoria, valor)
    preco_fmt = formatar_preco_brl(valor)

    return {
        "sucesso": True,
        "produto": produto,
        "preco": preco_fmt,
        "preco_valor": valor,
        "categoria": categoria,
        "validacao_preco": validacao,
        "fonte": "regex",
        "usar_llm": False,
    }


def processar_batch(lista: list[str]) -> list[dict]:
    """Processa uma lista de textos. LLM fallback marcado mas não chamado aqui."""
    return [processar_texto(item) for item in lista]


# ---------------------------------------------------------------------------
# Testes Unitários Embutidos
# ---------------------------------------------------------------------------

def _run_tests():
    casos = [
        # (input, produto_esperado_contains, preco_esperado)
        ("colar verde 89",                  "Colar",        "R$ 89,00"),
        ("bri prata zirc 145",              "Brinco",       "R$ 145,00"),
        ("anel 18k ouro 320",               "Anel",         "R$ 320,00"),
        ("brinco 3cm prata 89",             "Brinco",       "R$ 89,00"),   # FIX CRÍTICO
        ("conjunto 1.200",                  "Conjunto",     "R$ 1.200,00"),
        ("pulseira 89,90",                  "Pulseira",     "R$ 89,90"),
        ("conjunto 3g prata 250",           "Conjunto",     "R$ 250,00"),
        ("promoção de 120 por 89",          None,           "R$ 89,00"),   # FIX: "por X"
        ("anel 18k 1.450,00",               "Anel",         "R$ 1.450,00"),
        ("conjnto bri+col perola 250",      "Conjunto",     "R$ 250,00"),
        ("corrente 2.5mm ouro 980",         "Corrente",     "R$ 980,00"),  # mm ignorado
    ]

    erros = []
    for texto, prod_expect, preco_expect in casos:
        res = processar_texto(texto)
        ok_preco = res.get("preco") == preco_expect
        ok_prod  = (prod_expect is None) or (prod_expect in res.get("produto", ""))
        status   = "✅" if (ok_preco and ok_prod) else "❌"
        if not (ok_preco and ok_prod):
            erros.append(texto)
        print(f"{status} '{texto}'")
        print(f"   → produto: {res.get('produto')}  |  preco: {res.get('preco')}")
        if not ok_preco:
            print(f"   ⚠ preço esperado: {preco_expect}, obtido: {res.get('preco')}")
        if not ok_prod and prod_expect:
            print(f"   ⚠ produto esperado conter '{prod_expect}', obtido: {res.get('produto')}")

    print(f"\n{'='*50}")
    print(f"Resultado: {len(casos)-len(erros)}/{len(casos)} passaram")
    if erros:
        print("Falhas:", erros)

    # Casos de erro esperado
    print("\n--- Casos de Erro ---")
    for texto_erro in ["", "   ", "anel"]:
        res = processar_texto(texto_erro)
        print(f"  '{texto_erro}' → sucesso={res['sucesso']}, motivo={res.get('motivo')}, llm={res.get('usar_llm')}")


if __name__ == "__main__":
    _run_tests()