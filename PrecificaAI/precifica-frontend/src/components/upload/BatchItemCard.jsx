import { motion } from "framer-motion";

export default function BatchItemCard({ index, item, onUpdateNome, onUpdatePreco, onRemove }) {
    return (
        <motion.div
            layout
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, x: -100 }}
            transition={{ delay: index * 0.05 }}
            className="flex gap-3 rounded-xl p-3 shadow-sm border transition-all border-gray-100 bg-white"
        >
            {/* Thumbnail */}
            <div className="relative w-20 h-20 shrink-0">
                <img
                    src={item.webPath}
                    alt={`Foto #${index + 1}`}
                    className="w-full h-full object-cover rounded-lg"
                />
                <span className="absolute bottom-1 left-1 bg-primary text-white text-[10px] font-bold px-1.5 py-0.5 rounded shadow-sm">
                    #{index + 1}
                </span>

                {/* Botão remover */}
                <button
                    onClick={() => onRemove(item.id)}
                    className="absolute -top-2 -right-2 w-5 h-5 bg-red-500 text-white rounded-full
                     flex items-center justify-center text-xs shadow-md hover:bg-red-600 transition-colors z-10"
                >
                    ✕
                </button>
            </div>

            {/* Inputs de detalhes */}
            <div className="flex-1 flex flex-col gap-2 justify-center">
                <input
                    type="text"
                    value={item.nome}
                    onChange={(e) => onUpdateNome(item.id, e.target.value)}
                    placeholder="Nome do produto"
                    className="w-full bg-gray-50 rounded-lg px-2.5 py-1.5 text-sm border border-transparent focus:bg-white focus:border-primary/30 focus:ring-2 focus:ring-primary/20 outline-none transition-all placeholder:text-gray-400"
                />
                <input
                    type="text"
                    value={item.preco}
                    onChange={(e) => onUpdatePreco(item.id, e.target.value)}
                    placeholder="Preço (ex: R$ 99)"
                    className="w-full bg-gray-50 rounded-lg px-2.5 py-1.5 text-sm font-semibold text-gray-800 border border-transparent focus:bg-white focus:border-primary/30 focus:ring-2 focus:ring-primary/20 outline-none transition-all placeholder:text-gray-400 placeholder:font-normal"
                />
            </div>
        </motion.div>
    );
}
