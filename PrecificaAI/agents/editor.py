"""
Agente 02 — "O Editor" (v4.0 — Groq LLM)

FILOSOFIA: Sem regex. Sem Fast Lane. Sem falso positivo.
A LLM entende TUDO: giria, abreviacao, "reais", "conto", "10 de 2".
Provider: Groq (Llama 3.3 70B — rapido e gratuito)
"""

import os
import json
import time
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# PROMPT — O CEREBRO DO EDITOR
# ============================================================

PROMPT_SISTEMA = """Voce e o motor de extracao de dados do Precifica.AI, um app de design para joalherias brasileiras.

TAREFA: Receba o texto bruto digitado por um lojista de joias e retorne APENAS um JSON valido.

REGRAS DE EXTRACAO:
1. "produto" = nome da peca, limpo e capitalizado. Remover palavras de preco/parcela.
2. "preco_texto" = preco principal formatado como "R$ X,XX"
3. "preco_valor" = valor numerico float do preco principal
4. "modo" = detectar automaticamente:
   - "padrao" = preco simples (ex: "89", "R$ 89,90", "89 reais")
   - "parcelado" = so parcela (ex: "10x 7,50", "10 de 7,50", "10 vezes de 7,50")
   - "ambos" = preco + parcela (ex: "76 ou 10 de 7,50", "89,90 12x sem juros")
   - "promocao" = de/por (ex: "de 90 por 76", "antes 120 agora 89")
5. "parcelas" = se houver parcelamento, extrair quantidade e valor. Senao, null.
6. "preco_antigo" = se for promocao (de/por), o preco original. Senao, null.

INTERPRETACAO DE LINGUAGEM INFORMAL:
- "reais", "conto", "pila", "mango" = indicadores de preco, NAO parte do nome
- "10 de 2" = 10 parcelas de R$ 2,00 (parcelamento sem "x")
- "10 vezes de 7,50" = 10x R$ 7,50
- "a vista 76" = preco a vista R$ 76,00
- "de 90 por 76" = promocao, preco antigo 90, atual 76
- "antes 120 agora 89" = promocao
- "s/ juros" ou "sem juros" = informacao de parcela, manter no texto
- "18k", "925", "3cm" = atributos do produto, NAO preco
- Numeros sozinhos no final geralmente sao preco

ABREVIACOES COMUNS DE JOALHERIA:
- "bri" = Brinco, "col" = Colar, "pul" = Pulseira, "an" = Anel
- "ali" = Alianca, "conj" = Conjunto, "gar" = Gargantilha
- "ping" = Pingente, "torq" = Tornozeleira, "pirc" = Piercing
- "prt" = Prata, "our" = Ouro, "rod" = Rodio, "bnh" = Banhado
- "zirc" = Zirconia, "perl" = Perola, "crist" = Cristal
- Expandir sempre no "produto"

REGRA CRITICA:
- NAO invente informacoes. Se o texto nao tem preco, retorne preco_valor: 0 e preco_texto: "Consulte".
- Se o texto e muito curto ou ambiguo, extraia o maximo possivel sem inventar.
- Numeros como "18k", "925", "750" sao quilates/pureza, NAO preco.
- Numeros sozinhos no final geralmente sao preco

EXEMPLO:

Input: "Brinco Ouro 18k"
Output: {"produto": "Brinco Ouro 18k", "preco_texto": "Consulte", "preco_valor": 0, "modo": "padrao", "parcelas": null, "preco_antigo": null}

Entrada: "colar de quenga 20 reais ou 10 de 2"
Saida: {"produto": "Colar de Quenga", "preco_texto": "R$ 20,00", "preco_valor": 20.0, "modo": "ambos", "parcelas": {"quantidade": 10, "valor_parcela": 2.0}, "preco_antigo": null}

Entrada: "bri prata zirc 145"
Saida: {"produto": "Brinco Prata Zirconia", "preco_texto": "R$ 145,00", "preco_valor": 145.0, "modo": "padrao", "parcelas": null, "preco_antigo": null}

Entrada: "anel solitario de 250 por 189,90"
Saida: {"produto": "Anel Solitario", "preco_texto": "R$ 189,90", "preco_valor": 189.9, "modo": "promocao", "parcelas": null, "preco_antigo": 250.0}

Entrada: "conjnto col+bri perola 12x 29,90"
Saida: {"produto": "Conjunto Colar + Brinco Perola", "preco_texto": "R$ 358,80", "preco_valor": 358.8, "modo": "parcelado", "parcelas": {"quantidade": 12, "valor_parcela": 29.9}, "preco_antigo": null}

Entrada: "garg choker ouro rose 18k 899"
Saida: {"produto": "Gargantilha Choker Ouro Rose 18k", "preco_texto": "R$ 899,00", "preco_valor": 899.0, "modo": "padrao", "parcelas": null, "preco_antigo": null}

Entrada: "pulseira riviera 10 vezes de 45 sem juros"
Saida: {"produto": "Pulseira Riviera", "preco_texto": "R$ 450,00", "preco_valor": 450.0, "modo": "parcelado", "parcelas": {"quantidade": 10, "valor_parcela": 45.0}, "preco_antigo": null}

Entrada: "Alianca Ouro 18k Par 12x 150,00"
Saida: {"produto": "Alianca Ouro 18k Par", "preco_texto": "R$ 1.800,00", "preco_valor": 1800.0, "modo": "parcelado", "parcelas": {"quantidade": 12, "valor_parcela": 150.0}, "preco_antigo": null}

Entrada: "anel alianca 320 conto"
Saida: {"produto": "Anel Alianca", "preco_texto": "R$ 320,00", "preco_valor": 320.0, "modo": "padrao", "parcelas": null, "preco_antigo": null}

Entrada: "torq prt bali a vista 65"
Saida: {"produto": "Tornozeleira Prata Bali", "preco_texto": "R$ 65,00", "preco_valor": 65.0, "modo": "padrao", "parcelas": null, "preco_antigo": null}

Retorne APENAS o JSON, sem explicacao, sem markdown."""


# ============================================================
# FAIXAS DE PRECO (Validacao pos-LLM)
# ============================================================
FAIXAS_PRECO = {
    "Brinco":       {"min": 15,   "max": 5000},
    "Colar":        {"min": 30,   "max": 15000},
    "Anel":         {"min": 20,   "max": 20000},
    "Alianca":      {"min": 80,   "max": 30000},
    "Pulseira":     {"min": 25,   "max": 10000},
    "Conjunto":     {"min": 50,   "max": 25000},
    "Corrente":     {"min": 40,   "max": 12000},
    "Gargantilha":  {"min": 35,   "max": 8000},
    "Pingente":     {"min": 15,   "max": 5000},
    "Tornozeleira": {"min": 20,   "max": 3000},
}


def _validar_preco(categoria, preco):
    faixa = FAIXAS_PRECO.get(categoria, {"min": 10, "max": 50000})
    if preco < faixa["min"] or preco > faixa["max"]:
        return {
            "valido": False,
            "alerta": f"R$ {preco:.2f} fora da faixa tipica para {categoria} "
                      f"(R$ {faixa['min']:.2f} - R$ {faixa['max']:.2f})"
        }
    return {"valido": True}


def _formatar_preco_brl(valor):
    """Formata float para moeda brasileira."""
    if valor is None:
        return "Consulte"
    if valor >= 1000:
        parte_int = int(valor)
        centavos = int(round((valor - parte_int) * 100))
        int_fmt = f"{parte_int:,}".replace(",", ".")
        return f"R$ {int_fmt},{centavos:02d}"
    else:
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


# ============================================================
# CLASSE EDITOR
# ============================================================
class Editor:

    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY", "")
        if api_key:
            self.client = Groq(api_key=api_key)
            self.model_name = "llama-3.3-70b-versatile"
        else:
            self.client = None
            print("⚠️ MODO OFFLINE: Editor usando respostas simuladas (Falta API Key)")

    def processar_texto(self, texto_bruto):
        """
        Processa texto bruto -> dados estruturados.
        LLM always (Groq/Llama). Sem regex. Sem falso positivo.
        """
        texto_bruto = texto_bruto.strip()
        if not texto_bruto:
            return {"sucesso": False, "motivo": "texto_vazio"}

        if not self.client:
           return {
                "sucesso": True,
                "produto": "Produto Teste (Sem IA)",
                "preco_texto": "R$ 0,00",
                "preco_valor": 0.0,
                "modo_detectado": "padrao",
                "fonte": "offline_mock"
            }

        inicio = time.time()

        try:
            # ========================================
            # CHAMADA GROQ (com Retry)
            # ========================================
            response = None
            max_tentativas = 2
            
            for tentativa in range(max_tentativas):
                try:
                    response = self.client.chat.completions.create(
                        model=self.model_name,
                        messages=[
                            {"role": "system", "content": PROMPT_SISTEMA},
                            {"role": "user", "content": texto_bruto},
                        ],
                        temperature=0.0,
                        max_tokens=500,
                        response_format={"type": "json_object"},
                    )
                    break # Sucesso
                except Exception as e:
                    if tentativa < max_tentativas - 1:
                        print(f"   [RETRY] Groq falhou ({e}). Tentando novamente...")
                        time.sleep(1)
                        continue
                    raise e # Falhou 2x

            content = response.choices[0].message.content.strip()

            # Parse defensivo (remover markdown se houver)
            content = content.replace("```json", "").replace("```", "").strip()
            dados = json.loads(content)

            # ========================================
            # VALIDACAO DO RETORNO
            # ========================================
            produto = dados.get("produto")
            preco_valor = dados.get("preco_valor")
            preco_texto = dados.get("preco_texto")
            modo = dados.get("modo", "padrao")
            parcelas = dados.get("parcelas")
            preco_antigo = dados.get("preco_antigo")

            if not produto or preco_valor is None:
                return {
                    "sucesso": False,
                    "motivo": "llm_retorno_incompleto",
                    "dados_brutos": dados,
                }

            # Garantir tipos corretos
            preco_valor = float(preco_valor)
            if preco_antigo is not None:
                preco_antigo = float(preco_antigo)

            if parcelas and isinstance(parcelas, dict):
                parcelas = {
                    "quantidade": int(parcelas.get("quantidade", 0)),
                    "valor_parcela": float(parcelas.get("valor_parcela", 0)),
                }
                if parcelas["quantidade"] <= 0 or parcelas["valor_parcela"] <= 0:
                    parcelas = None

            # Se a LLM nao formatou o preco, formatar aqui
            if not preco_texto or "R$" not in preco_texto:
                preco_texto = _formatar_preco_brl(preco_valor)

            # ========================================
            # VALIDACAO DE FAIXA DE PRECO
            # ========================================
            primeira_palavra = produto.split()[0] if produto else ""
            categoria = primeira_palavra if primeira_palavra in FAIXAS_PRECO else "Generico"
            validacao = _validar_preco(categoria, preco_valor)

            tempo_ms = int((time.time() - inicio) * 1000)

            # ========================================
            # MONTAR TEXTO PARA RENDERIZACAO
            # ========================================
            linha_preco = preco_texto
            linha_parcelas = ""
            linha_preco_antigo = ""

            if modo == "parcelado" and parcelas:
                qtd = parcelas["quantidade"]
                val = parcelas["valor_parcela"]
                linha_preco = f"{qtd}x R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

            elif modo == "ambos" and parcelas:
                qtd = parcelas["quantidade"]
                val = parcelas["valor_parcela"]
                linha_parcelas = f"ou {qtd}x R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

            elif modo == "promocao" and preco_antigo:
                linha_preco_antigo = _formatar_preco_brl(preco_antigo)

            # ========================================
            # OUTPUT FINAL
            # ========================================
            resultado = {
                "sucesso": True,
                "produto": produto,
                "preco_texto": linha_preco,
                "preco_valor": preco_valor,
                "modo_detectado": modo,
                "parcelas": parcelas,
                "preco_antigo": preco_antigo,
                "linha_preco_antigo": linha_preco_antigo,
                "linha_parcelas": linha_parcelas,
                "categoria": categoria,
                "validacao_preco": validacao,
                "fonte": "groq",
                "tempo_ms": tempo_ms,
            }

            print(f"   -> Produto: {produto} | Preco: {linha_preco} | Modo: {modo} ({tempo_ms}ms)")

            return resultado

        except json.JSONDecodeError as e:
            print(f"   [AVISO] JSON invalido do Groq: {e}")
            return {"sucesso": False, "motivo": "json_invalido", "erro": str(e)}

        except Exception as e:
            print(f"   [AVISO] Erro no Editor: {e}")
            import traceback
            traceback.print_exc()
            return {"sucesso": False, "motivo": "erro_geral", "erro": str(e)}

    def processar_batch(self, textos):
        """Processa multiplos textos de uma vez."""
        resultados = []
        for i, texto in enumerate(textos):
            texto = texto.strip()
            if not texto:
                continue
            print(f"[{i+1}/{len(textos)}] Processando: '{texto}'")
            resultado = self.processar_texto(texto)
            resultados.append(resultado)
        return resultados


# ============================================================
# TESTE LOCAL
# ============================================================
if __name__ == "__main__":
    editor = Editor()

    testes = [
        "colar de quenga 20 reais ou 10 de 2",
        "bri prata zirc 145",
        "anel solitario de 250 por 189,90",
        "conjnto col+bri perola 12x 29,90",
        "Alianca Ouro 18k Par 12x 150,00",
        "garg choker ouro rose 18k 899",
        "torq prt bali a vista 65",
        "pulseira riviera 10 vezes de 45 sem juros",
        "anel alianca 320 conto",
        "piercing pressao rodio negro 45",
        "Conjunto Perola Classico de 450 por 320",
    ]

    print("=" * 60)
    print("TESTE DO EDITOR v4.0 -- GROQ / LLAMA 3.3 70B")
    print("=" * 60)

    sucesso = 0
    falha = 0

    for texto in testes:
        print(f"\nInput: '{texto}'")
        resultado = editor.processar_texto(texto)

        if resultado.get("sucesso"):
            sucesso += 1
            print(f"   [OK] {resultado['produto']}")
            print(f"      Preco: {resultado['preco_texto']}")
            print(f"      Modo:  {resultado['modo_detectado']}")
            if resultado.get("parcelas"):
                p = resultado["parcelas"]
                print(f"      Parcelas: {p['quantidade']}x R$ {p['valor_parcela']:.2f}")
            if resultado.get("preco_antigo"):
                print(f"      De: {resultado['linha_preco_antigo']}")
            if resultado.get("linha_parcelas"):
                print(f"      {resultado['linha_parcelas']}")
            if not resultado["validacao_preco"].get("valido", True):
                print(f"      [!] {resultado['validacao_preco']['alerta']}")
        else:
            falha += 1
            print(f"   [FALHA] {resultado.get('motivo')}")

    print(f"\n{'=' * 60}")
    print(f"Resultado: {sucesso}/{len(testes)} sucesso, {falha} falhas")
    print(f"{'=' * 60}")
