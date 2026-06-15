import { create } from "zustand";

const useAppStore = create((set, get) => ({
    // ============================
    // ITENS (Array para batch)
    // ============================
    itens: [], // [{ file, base64, preview, texto }]

    addItem: (item) =>
        set((s) => ({
            itens: [...s.itens, item],
        })),

    removeItem: (idx) =>
        set((s) => ({
            itens: s.itens.filter((_, i) => i !== idx),
        })),

    updateTexto: (idx, texto) =>
        set((s) => ({
            itens: s.itens.map((item, i) => (i === idx ? { ...item, texto } : item)),
        })),

    // ============================
    // CONFIG (Global para todas as imagens)
    // ============================
    formato: "original",
    paleta: "vogue",

    setFormato: (f) => set({ formato: f }),
    setPaleta: (p) => set({ paleta: p }),

    // ============================
    // RESULTADOS (Batch)
    // ============================
    batchResultados: [], // [{ url_resultado, dados_extraidos, arquivo_saida }]
    isProcessing: false,
    processingStep: "",
    progressCount: 0,
    progressTotal: 0,

    setBatchResultados: (r) => set({ batchResultados: r, isProcessing: false }),
    setProcessing: (step) => set({ isProcessing: true, processingStep: step }),
    setProgress: (count, total) =>
        set({ progressCount: count, progressTotal: total }),

    // ============================
    // RESET
    // ============================
    resetAll: () =>
        set({
            itens: [],
            batchResultados: [],
            isProcessing: false,
            progressCount: 0,
            progressTotal: 0,
        }),
}));

export default useAppStore;
