import { useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import useAppStore from "../store/appStore";
import { fileToBase64, comprimirImagem } from "../utils/imageUtils";
import { processarBatch } from "../services/api";
import PageTransition from "../components/layout/PageTransition";
import BatchItemCard from "../components/upload/BatchItemCard";

const FORMATS = [
    { id: "original", label: "Orig.", icon: "📐" },
    { id: "feed_quadrado", label: "1:1", icon: "⬜" },
    { id: "stories", label: "Story", icon: "📱" },
    { id: "feed_retrato", label: "4:5", icon: "🖼️" },
];

const PALETTES = [
    { id: "vogue", label: "Vogue", color: "#FFFFFF" },
    { id: "classico", label: "Clássico", color: "#C9A96E" },
];

export default function WorkspacePage() {
    const navigate = useNavigate();
    const fileInputRef = useRef(null);
    const {
        itens,
        addItem,
        removeItem,
        updateTexto,
        formato,
        setFormato,
        paleta,
        setPaleta,
        setBatchResultados,
        setProcessing,
    } = useAppStore();

    const [isProcessing, setIsProcessing] = useState(false);
    const [showErrors, setShowErrors] = useState(false);

    const handleFileSelect = async (files) => {
        for (const file of files) {
            if (!file.type.startsWith("image/")) continue;

            try {
                const compressed = await comprimirImagem(file);
                const base64 = await fileToBase64(compressed);

                addItem({
                    file: compressed,
                    base64,
                    preview: URL.createObjectURL(compressed),
                    texto: "",
                });
            } catch (error) {
                console.error("Erro ao processar imagem:", error);
            }
        }
    };

    const todosPreenchidos = itens.length > 0 && itens.every((item) => item.texto.trim().length > 0);

    const handleGenerate = async () => {
        if (itens.length === 0) {
            return;
        }

        // Validação visual (sem alert)
        if (!todosPreenchidos) {
            setShowErrors(true);
            setTimeout(() => setShowErrors(false), 3000);
            return;
        }

        setIsProcessing(true);
        setProcessing("Lapidando peças...");

        try {
            const payload = itens.map((item) => ({
                image: item.base64,
                texto: item.texto,
            }));

            const result = await processarBatch(payload, { formato, paleta });

            setBatchResultados(result.resultados || []);
            navigate("/preview");
        } catch (error) {
            alert(`Erro: ${error.message}`);
        } finally {
            setIsProcessing(false);
        }
    };

    return (
        <PageTransition>
            <div className="min-h-screen bg-background-light p-6 pb-24">
                {/* Header */}
                <div className="flex items-center justify-between mb-6">
                    <h1 className="font-serif text-3xl bg-gradient-to-r from-primary-dark to-primary bg-clip-text text-transparent">
                        Precifica.AI
                    </h1>
                    <button className="p-2 hover:bg-gray-100 rounded-lg">
                        <svg
                            className="w-6 h-6"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                        >
                            <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
                            />
                            <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                            />
                        </svg>
                    </button>
                </div>

                {/* Upload Zone */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="mb-6"
                >
                    <input
                        ref={fileInputRef}
                        type="file"
                        accept="image/*"
                        multiple
                        onChange={(e) => handleFileSelect(Array.from(e.target.files))}
                        className="hidden"
                    />

                    <button
                        onClick={() => fileInputRef.current?.click()}
                        className="w-full p-8 border-2 border-dashed border-primary/30 rounded-2xl hover:border-primary transition-colors bg-white"
                    >
                        <div className="text-center">
                            <div className="w-16 h-16 mx-auto mb-4 bg-primary/10 rounded-full flex items-center justify-center">
                                <svg
                                    className="w-8 h-8 text-primary"
                                    fill="none"
                                    stroke="currentColor"
                                    viewBox="0 0 24 24"
                                >
                                    <path
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                        strokeWidth={2}
                                        d="M12 4v16m8-8H4"
                                    />
                                </svg>
                            </div>
                            <p className="text-lg font-medium text-gray-900">
                                Adicionar Fotos
                            </p>
                            <p className="text-sm text-gray-500 mt-1">1 a 30 imagens</p>
                        </div>
                    </button>
                </motion.div>

                {/* Lista de Cards Pareados */}
                {itens.length > 0 && (
                    <div className="mb-6 space-y-3">
                        <AnimatePresence>
                            {itens.map((item, idx) => (
                                <BatchItemCard
                                    key={item.preview}
                                    index={idx}
                                    preview={item.preview}
                                    texto={item.texto}
                                    onTextoChange={updateTexto}
                                    onRemove={removeItem}
                                    showErrors={showErrors}
                                />
                            ))}
                        </AnimatePresence>
                    </div>
                )}

                {/* Format Selector (Inline) */}
                {itens.length > 0 && (
                    <div className="mb-4">
                        <label className="block text-xs font-medium text-gray-600 mb-2">
                            Formato
                        </label>
                        <div className="grid grid-cols-4 gap-2">
                            {FORMATS.map((f) => (
                                <motion.button
                                    key={f.id}
                                    whileTap={{ scale: 0.95 }}
                                    onClick={() => setFormato(f.id)}
                                    className={`py-2 px-3 rounded-lg text-xs font-medium transition-all ${formato === f.id
                                            ? "bg-primary text-white"
                                            : "bg-white text-gray-600"
                                        }`}
                                >
                                    {f.icon} {f.label}
                                </motion.button>
                            ))}
                        </div>
                    </div>
                )}

                {/* Palette Selector (Inline) */}
                {itens.length > 0 && (
                    <div className="mb-8">
                        <label className="block text-xs font-medium text-gray-600 mb-2">
                            Paleta
                        </label>
                        <div className="grid grid-cols-2 gap-2">
                            {PALETTES.map((p) => (
                                <motion.button
                                    key={p.id}
                                    whileTap={{ scale: 0.95 }}
                                    onClick={() => setPaleta(p.id)}
                                    className={`py-3 px-4 rounded-lg text-sm font-medium transition-all flex items-center gap-2 ${paleta === p.id
                                            ? "bg-primary text-white ring-2 ring-primary"
                                            : "bg-white text-gray-600"
                                        }`}
                                >
                                    <div
                                        className="w-4 h-4 rounded-full border border-gray-300"
                                        style={{ backgroundColor: p.color }}
                                    />
                                    {p.label}
                                </motion.button>
                            ))}
                        </div>
                    </div>
                )}

                {/* Generate Button */}
                {itens.length > 0 && (
                    <motion.button
                        whileTap={{ scale: 0.97 }}
                        onClick={handleGenerate}
                        disabled={isProcessing}
                        className="w-full py-4 bg-gradient-to-r from-primary-dark to-primary text-white rounded-xl font-semibold text-lg shadow-luxury disabled:opacity-50"
                    >
                        {isProcessing
                            ? `Processando...`
                            : `✨ Gerar ${itens.length} ${itens.length === 1 ? "Arte" : "Artes"}`}
                    </motion.button>
                )}

                {/* Loading Overlay */}
                <AnimatePresence>
                    {isProcessing && (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50"
                        >
                            <div className="bg-white rounded-2xl p-8 max-w-sm mx-4 text-center">
                                <motion.div
                                    animate={{ rotateY: 360 }}
                                    transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                                    className="w-16 h-16 mx-auto mb-4"
                                >
                                    <svg viewBox="0 0 24 24" className="text-primary">
                                        <path
                                            d="M12 2L3.5 9L12 22L20.5 9L12 2Z"
                                            stroke="currentColor"
                                            strokeWidth="0.5"
                                            fill="none"
                                        />
                                    </svg>
                                </motion.div>
                                <p className="font-serif text-xl mb-2">Lapidando peças...</p>
                                <p className="text-sm text-gray-500">{itens.length} artes</p>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </PageTransition>
    );
}
