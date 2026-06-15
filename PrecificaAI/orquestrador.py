"""
Orquestrador: chama os 3 agentes em sequência.
É o único arquivo que importa os agentes. O server.py só fala com ele.
"""

import os
import time
import uuid
import re
import unicodedata
import numpy as np
from dotenv import load_dotenv

# Carregar variáveis de ambiente ANTES de importar os agentes
load_dotenv()

from agents.topografo import Topografo
from agents.editor import Editor
from agents.diagramador import Diagramador
from config import settings


def gerar_nome_arquivo(produto, preco_texto, indice=None):
    """
    Gera nome de arquivo limpo e legível.
    
    Input:  "Colar Quenga", "R$ 20,00"
    Output: "Colar_Quenga_R$20,00.jpg"
    
    Input:  "Anel Ródio Negro", "10x R$ 7,50"  
    Output: "Anel_Rodio_Negro_10x_R$7,50.jpg"
    """
    # Normalizar acentos (ódio → odio)
    nome = unicodedata.normalize('NFKD', produto)
    nome = nome.encode('ascii', 'ignore').decode('ascii')
    
    # Limpar preço (remover espaços extras)
    preco = preco_texto.replace(" ", "")
    
    # Juntar
    base = f"{nome}_{preco}"
    
    # Substituir espaços por _
    base = base.replace(" ", "_")
    
    # Remover caracteres inválidos para nome de arquivo
    base = re.sub(r'[<>:"/\\|?*]', '', base)
    
    # Adicionar índice se batch
    if indice is not None:
        base = f"{indice:02d}_{base}"
    
    return f"{base}.jpg"


class PipelinePrecifica:
    
    def __init__(self):
        """Inicializa os 3 agentes uma vez (singleton por worker)."""
        print("[...] Carregando agentes...")
        self.topografo = Topografo()
        self.editor = Editor()
        self.diagramador = Diagramador()
        print("[OK] Agentes prontos!")
    
    def executar(self, imagem_path, texto_bruto, formato, paleta, modo_preco):
        """
        Pipeline completo: Agente 01 → 02 → 03.
        
        Args:
            imagem_path: Caminho da imagem no disco
            texto_bruto: Texto digitado pelo usuário ("colar ouro 89,90")
            formato: "original" | "feed_quadrado" | "feed_retrato" | "stories"
            paleta: "classico" | "moderno" | "jovem"
            modo_preco: "padrao" | "parcelado" | "ambos" | "promocao"
        
        Returns:
            Dict com resultado ou erro
        """
        inicio = time.time()
        
        try:
            # =============================================
            # AGENTE 01 — TOPÓGRAFO (Computer Vision)
            # =============================================
            # Input:  imagem bruta
            # Output: máscara, mapa de zonas livres, luminância
            print(f"[1/3] Agente 01 escaneando terreno...")
            analise_imagem = self.topografo.analisar_terreno(imagem_path)

            # analise_imagem = {
            #     "mascara": np.array,
            #     ...
            # }

            if "erro" in analise_imagem:
                return {
                    "sucesso": False,
                    "erro_code": "TOPOGRAFO_ERRO",
                    "mensagem": analise_imagem["erro"],
                }

            # =============================================
            # AGENTE 02 — EDITOR (NLP)
            # =============================================
            # Input:  texto bruto
            # Output: produto, preço, categoria, métricas
            print(f"[2/3] Agente 02 processando texto: '{texto_bruto}'")
            dados_editor = self.editor.processar_texto(texto_bruto)
            
            if not dados_editor.get("sucesso"):
                return {
                    "sucesso": False,
                    "erro_code": "TEXTO_INVALIDO",
                    "mensagem": dados_editor.get("motivo", "Não foi possível interpretar o texto."),
                    "dados_parciais": dados_editor,
                }
            
            print(f"   -> Produto: {dados_editor.get('produto')} | Preco: {dados_editor.get('preco_texto')}")
            
            # =============================================
            # AGENTE 03 — DIAGRAMADOR (Layout)
            # =============================================
            # Input:  imagem + análise + dados do editor + config visual
            # Output: imagem final renderizada
            print(f"[3/3] Agente 03 aplicando: {paleta} / {formato}")
            
            # Nome legível automático
            nome_saida = gerar_nome_arquivo(
                dados_editor.get("produto", "Produto"),
                dados_editor.get("preco_texto", "Preco")
            )
            caminho_saida = os.path.join(settings.OUTPUT_DIR, nome_saida)
            
            # Correção no nome do argumento 'dados_texto' vs 'dados'
            # No diagrama original era 'dados_texto'
            self.diagramador.renderizar(
                image_path_original=imagem_path,
                dados_texto=dados_editor,
                output_path=caminho_saida,
                dados_visuais=analise_imagem,
                formato=formato,
                paleta=paleta,
                modo_preco=modo_preco
            )
            
            tempo_total = int((time.time() - inicio) * 1000)
            print(f"[OK] Concluido em {tempo_total}ms -> {nome_saida}")
            
            return {
                "sucesso": True,
                "arquivo_saida": nome_saida,
                "dados_editor": dados_editor,
                "tempo_ms": tempo_total,
            }
        
        except Exception as e:
            print(f"[ERRO] Erro no pipeline: {e}")
            import traceback
            traceback.print_exc()
            return {
                "sucesso": False,
                "erro_code": "PIPELINE_ERRO",
                "mensagem": str(e),
            }
    
    def executar_com_dados_confirmados(self, imagem_path, dados_confirmados, formato, paleta, modo_preco):
        """
        Pipeline SEM Agente 02 — usado quando o usuário editou
        os dados no Card de Confirmação (Passo 3.5).
        
        Agente 01 → (pula 02) → Agente 03.
        """
        inicio = time.time()
        
        try:
            # Agente 01
            print(f"[1/3] Agente 01 escaneando terreno...")
            analise_imagem = self.topografo.analisar_terreno(imagem_path)
            
            # Montar dados no formato que o Agente 03 espera
            # Note que o Diagramador espera as chaves 'produto', 'preco_texto', 'parcelas'
            dados_editor = {
                "sucesso": True,
                "produto": dados_confirmados.get("produto", "Peça Exclusiva"),
                "preco_texto": dados_confirmados.get("preco_texto", "Consulte"),
                "preco_valor": dados_confirmados.get("preco_valor"),
                "parcelas": dados_confirmados.get("parcelas"),
                "fonte": "confirmado_usuario",
            }
            
            # texto_metricas removido — Diagramador v2 calcula internamente
            
            # Agente 03
            print(f"[3/3] Agente 03 aplicando: {paleta} / {formato}")
            
            # Nome legível automático
            nome_saida = gerar_nome_arquivo(
                dados_editor.get("produto", "Produto"),
                dados_editor.get("preco_texto", "Preco")
            )
            caminho_saida = os.path.join(settings.OUTPUT_DIR, nome_saida)
            
            self.diagramador.renderizar(
                image_path_original=imagem_path,
                dados_texto=dados_editor, # Passando como dados_texto para manter compatibilidade com sua assinatura
                output_path=caminho_saida,
                dados_visuais=analise_imagem,
                formato=formato,
                paleta=paleta,
                modo_preco=modo_preco
            )
            
            tempo_total = int((time.time() - inicio) * 1000)
            print(f"[OK] Concluido em {tempo_total}ms -> {nome_saida}")
            
            return {
                "sucesso": True,
                "arquivo_saida": nome_saida,
                "dados_editor": dados_editor,
                "tempo_ms": tempo_total,
            }
        
        except Exception as e:
            print(f"[ERRO] Erro no pipeline: {e}")
            return {
                "sucesso": False,
                "erro_code": "PIPELINE_ERRO",
                "mensagem": str(e),
            }
