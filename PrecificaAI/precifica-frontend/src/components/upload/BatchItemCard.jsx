import { motion } from "framer-motion";

export default function BatchItemCard({ index, preview, texto, onTextoChange, onRemove, showErrors }) {
    const hasError = showErrors && !texto.trim();

    return (
        <motion.div
            layout
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, x: -100 }}
            transition={{ delay: index * 0.05 }}
            className={`flex gap-3 rounded-xl p-3 shadow-sm border transition-all ${hasError
                    ? "border-red-300 bg-red-50 animate-shake"
                    : "border-gray-100 bg-white"
                }`}
        >
            {/* Thumbnail */}
            <div className="relative w-20 h-20 shrink-0">
                <img
                    src={preview}
                    alt={`Foto #${index + 1}`}
                    className="w-full h-full object-cover rounded-lg"
                />
                <span className="absolute bottom-1 left-1 bg-primary text-white text-[10px] font-bold px-1.5 py-0.5 rounded">
                    #{index + 1}
                </span>

                {/* Botão remover */}
                <button
                    onClick={() => onRemove(index)}
                    className="absolute -top-2 -right-2 w-5 h-5 bg-red-500 text-white rounded-full
                     flex items-center justify-center text-xs shadow-md hover:bg-red-600 transition-colors"
                >
                    ✕
                </button>
            </div>

            {/* Input de texto PAREADO com a imagem */}
            <div className="flex-1">
                <textarea
                    value={texto}
                    onChange={(e) => onTextoChange(index, e.target.value)}
                    placeholder="Ex: Anel ródio 76 ou 10x 7,50"
                    rows={2}
                    className={`w-full bg-gray-50 rounded-lg p-2.5 text-sm resize-none
                     border-none focus:ring-2 focus:ring-primary/30
                     placeholder:text-gray-300 ${hasError ? "ring-2 ring-red-400" : ""
                        }`}
                />
                {hasError && (
                    <p className="text-xs text-red-500 mt-1">
                        ⚠️ Preencha o texto deste produto
                    </p>
                )}
            </div>
        </motion.div>
    );
}
