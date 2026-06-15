# 💎 Precifica.AI — Especificação para Front-End (v1.0)

## 1. Visão do Produto
O **Precifica.AI** é uma ferramenta de automação de design para joalherias. Ele transforma fotos brutas de produtos e descrições informais em cards de marketing profissionais, prontos para Instagram (Feed/Stories) e E-commerce.

**Problema:** O lojista perde horas no Canva tentando remover fundo, escolher fontes e diagramar preços.
**Solução:** O usuário sobe a foto, digita o preço de qualquer jeito, e a IA entrega a arte pronta em instantes.

---

## 2. Jornada do Usuário (User Flow)

### Passo 1: Upload (A Entrada)
- **Input de Imagem:** Área de drag & drop ou seleção de câmera.
- **Preview:** Mostrar a imagem carregada.
- **Validação:** Aceitar apenas imagens (JPG/PNG).

### Passo 2: Dados do Produto (O Contexto)
- **Input de Texto:** Um campo de texto livre (TextArea).
- **Placeholder:** _"Ex: Colar de Ouro 18k com Zircônia por 250 em 10x"_
- **Ação:** O usuário digita de forma natural. O Backend (Agente 02) fará a "mágica" de extrair Nome, Preço e Parcelas.

### Passo 3: Configuração de Estilo (O Design)
O usuário deve ter controles simples para personalizar o resultado:

**A. Formato (Abas ou Seletores):**
1.  **Original** (1:1 ou nativo)
2.  **Feed Quadrado** (1080x1080)
3.  **Stories** (1080x1920)
4.  **Feed Retrato** (4:5)

**B. Paleta de Estilo (Cards Selecionáveis):**
As paletas vêm do backend. O Front deve mostrar um preview visual (ícone ou cor) para:
1.  **Clássico:** (Fundo Branco/Preto, Detalhes Dourados, Fonte Serifada) — *Vibe Luxo*
2.  **Moderno:** (Minimalista, Tons Pastéis/Rosé, Fonte Sans-Serif) — *Vibe Clean*
3.  **Jovem:** (Contraste alto, Fonte Bold/Caixa Alta) — *Vibe Promoção*

**C. Exibição de Preço (Toggle/Radio):**
1.  **Padrão:** R$ 199,90
2.  **Parcelado:** 10x R$ 19,99
3.  **Ambos:** R$ 199,90 ou 10x R$ 19,99

### Passo 4: Resultado (O Output)
- Exibir a **Imagem Processada** retornada pela API.
- Botão **Download** (Salvar na galeria/computador).
- Botão **Compartilhar** (Nativo do mobile/browser).
- Botão **Refazer** (Voltar ajustes sem perder a foto).

---

## 3. Integração com Backend (API Spec Simplificada)

O Front-end enviará um POST para o endpoint `/processar`.

**Request (JSON):**
```json
{
  "image": "base64_string_ou_url",
  "texto": "Colar Ouro 18k pedra verde 12x 89,90",
  "config": {
    "formato": "stories",      // "original" | "feed_quadrado" | "feed_retrato" | "stories"
    "paleta": "moderno",       // "classico" | "moderno" | "jovem"
    "modo_preco": "parcelado"  // "padrao" | "parcelado" | "ambos" | "promocao"
  }
}
```

**Response (JSON):**
```json
{
  "status": "success",
  "url_resultado": "https://api.precifica.ai/output/result_123.jpg",
  "dados_extraidos": {
    "produto": "Colar Ouro 18k Pedra Verde",
    "preco": "R$ 1.078,80",
    "parcelas": "12x R$ 89,90"
  }
  // Útil para mostrar ao usuário o que a IA entendeu
}
```

---

## 4. Guia de Estilo (UI Kit Sugerido)

### Cores da Interface
*   **Background:** #F8F9FA (Cinza muito claro, limpo).
*   **Surface:** #FFFFFF (Cards brancos com sombra sutil).
*   **Primary:** #1A1A1A (Preto suave) ou #C9A96E (Dourado da marca).
*   **Accent:** #E8B4B8 (Rosé para destaques sutis).

### Tipografia
*   **Headings:** *Playfair Display* (trazendo a identidade clássica da joalheria).
*   **Body/Inputs:** *Inter* ou *Montserrat* (leitura fácil).

### Componentes Chave
*   **Loading State:** Essencial. O processamento (rembg + AI) leva de 5 a 10 segundos. Use um loader elegante (ex: silhueta de joia ou barra de progresso "Lapidando imagem...").
*   **Comparação:** Se possível, componente de "Antes/Depois" (slider) para valorizar o recorte de fundo.

---

## 5. Requisitos Técnicos
*   **Responsividade:** O app deve funcionar perfeitamente em Mobile (prioridade 1) e Desktop.
*   **Feedback Visual:** Notificações de erro amigáveis se a imagem for ruim ou o texto ilegível.
*   **Performance:** Comprimir a imagem no cliente antes de enviar (máx 2048px) para poupar banda.
