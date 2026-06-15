import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import useAppStore from "../store/appStore";
import PageTransition from "../components/layout/PageTransition";

export default function PreviewPage() {
    const navigate = useNavigate();
    const { batchResultados, resetAll } = useAppStore();

    if (!batchResultados || batchResultados.length === 0) {
        navigate("/");
        return null;
    }

    const handleDownloadAll = async () => {
        // Download individual de cada arte
        for (const resultado of batchResultados) {
            const link = document.createElement("a");
            link.href = resultado.url_resultado;
            link.download = resultado.arquivo_saida || "arte.jpg";
            link.click();
            await new Promise((resolve) => setTimeout(resolve, 300));
        }
    };

    const handleReset = () => {
        resetAll();
        navigate("/");
    };

    return (
        <PageTransition>
            <div className="min-h-screen bg-background-light p-6 pb-24">
                {/* Header */}
                <div className="flex items-center justify-between mb-6">
                    <button
                        onClick={() => navigate("/")}
                        className="p-2 hover:bg-gray-100 rounded-lg"
                    >
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
                                d="M15 19l-7-7 7-7"
                            />
                        </svg>
                    </button>
                    <h1 className="font-serif text-2xl">
                        {batchResultados.length}{" "}
                        {batchResultados.length === 1 ? "Arte Gerada" : "Artes Geradas"}
                    </h1>
                    <button
                        onClick={handleReset}
                        className="text-sm text-primary font-medium"
                    >
                        Nova
                    </button>
                </div>

                {/* Grid de Resultados */}
                <div className="grid grid-cols-2 gap-4 mb-6">
                    {batchResultados.map((resultado, idx) => (
                        <motion.div
                            key={idx}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: idx * 0.1 }}
                            className="bg-white rounded-2xl shadow-soft overflow-hidden"
                        >
                            <img
                                src={resultado.url_resultado}
                                alt={resultado.dados_extraidos?.produto || `Arte #${idx + 1}`}
                                className="w-full aspect-[4/5] object-cover"
                            />
                            <div className="p-3">
                                <p className="text-sm font-medium text-gray-900 truncate">
                                    {resultado.dados_extraidos?.produto || "Produto"}
                                </p>
                                <p className="text-xs text-primary font-semibold">
                                    {resultado.dados_extraidos?.preco_texto || "Preço"}
                                </p>
                            </div>
                        </motion.div>
                    ))}
                </div>

                {/* Action Buttons */}
                <div className="space-y-3">
                    <motion.button
                        whileTap={{ scale: 0.97 }}
                        onClick={handleDownloadAll}
                        className="w-full py-4 bg-gradient-to-r from-primary-dark to-primary text-white rounded-xl font-semibold shadow-luxury flex items-center justify-center gap-2"
                    >
                        <svg
                            className="w-5 h-5"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                        >
                            <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                            />
                        </svg>
                        📥 Salvar Todas na Galeria
                    </motion.button>

                    <motion.button
                        whileTap={{ scale: 0.97 }}
                        onClick={() => {
                            if (navigator.share) {
                                navigator.share({
                                    title: "Minhas artes do Precifica.AI",
                                    text: `${batchResultados.length} artes profissionais`,
                                });
                            }
                        }}
                        className="w-full py-4 bg-white text-gray-900 rounded-xl font-semibold shadow-soft flex items-center justify-center gap-2"
                    >
                        <svg
                            className="w-5 h-5"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                        >
                            <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z"
                            />
                        </svg>
                        Compartilhar
                    </motion.button>
                </div>
            </div>
        </PageTransition>
    );
}
