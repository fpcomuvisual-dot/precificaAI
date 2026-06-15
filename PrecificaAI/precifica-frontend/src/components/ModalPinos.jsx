import React, { useState } from 'react';

const ModalPinos = ({ imagemBase64, boxes = [], onClose, onSave }) => {
    // State to hold values for each pin (box)
    // Initial values empty
    const [valores, setValores] = useState({});

    const handleChange = (index, value) => {
        setValores(prev => ({ ...prev, [index]: value }));
    };

    const handleSalvar = () => {
        onSave(valores);
    };

    return (
        <div className="fixed inset-0 bg-black/90 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-fade-in">
            <div className="bg-white rounded-[2rem] p-6 max-w-sm w-full shadow-2xl flex flex-col max-h-[90vh]">

                <div className="flex items-center justify-between mb-6">
                    <h2 className="text-xl font-bold font-display text-gray-900">
                        Preços Detectados
                    </h2>
                    <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-full transition-colors">
                        <span className="material-icons-outlined text-gray-400">close</span>
                    </button>
                </div>

                {/* Preview Image Area */}
                <div className="relative aspect-square bg-gray-100 rounded-2xl overflow-hidden mb-6 shrink-0 group">
                    <img
                        src={`data:image/png;base64,${imagemBase64}`}
                        className="w-full h-full object-contain"
                        alt="Preview"
                    />

                    {/* Render Pins Overlay */}
                    {boxes.map((box, index) => {
                        // Rescale box from 1024x1024 to current container size
                        // This assumes the container is square. 
                        // CSS aspect-square handles the container.
                        // We need the size in % to be responsive.
                        // box = [x, y, w, h] relative to 1024
                        const left = (box[0] / 1024) * 100;
                        const top = (box[1] / 1024) * 100;
                        const width = (box[2] / 1024) * 100;
                        const height = (box[3] / 1024) * 100;

                        return (
                            <div
                                key={index}
                                style={{
                                    left: `${left}%`,
                                    top: `${top}%`,
                                    width: `${width}%`,
                                    height: `${height}%`
                                }}
                                className="absolute border-2 border-primary bg-primary/20 rounded-lg flex items-center justify-center animate-pulse"
                            >
                                <span className="bg-primary text-white text-[10px] font-bold px-1.5 rounded-full shadow-sm">
                                    {index + 1}
                                </span>
                            </div>
                        );
                    })}
                </div>

                {/* Inputs List */}
                <div className="flex-1 overflow-y-auto space-y-3 pr-1 custom-scrollbar">
                    {boxes.map((_, index) => (
                        <div key={index} className="flex items-center gap-3 p-3 bg-gray-50 rounded-xl border border-gray-100 focus-within:ring-2 focus-within:ring-primary/20 transition-all">
                            <div className="w-8 h-8 bg-primary/10 rounded-full flex items-center justify-center text-primary font-bold text-sm shrink-0">
                                {index + 1}
                            </div>
                            <input
                                type="text"
                                placeholder="R$ 0,00"
                                value={valores[index] || ''}
                                onChange={(e) => handleChange(index, e.target.value)}
                                className="flex-1 bg-transparent border-none p-0 text-gray-800 font-medium focus:ring-0 placeholder-gray-400"
                                autoFocus={index === 0}
                            />
                        </div>
                    ))}
                    {boxes.length === 0 && (
                        <p className="text-gray-400 text-center text-sm py-4">Nenhum preço detectado automaticamente.</p>
                    )}
                </div>

                {/* Actions */}
                <div className="pt-6 mt-2 border-t border-gray-100">
                    <button
                        onClick={handleSalvar}
                        className="w-full py-4 bg-primary hover:bg-primary-dark text-white font-bold rounded-xl shadow-lg shadow-primary/25 transform active:scale-95 transition-all flex items-center justify-center gap-2"
                    >
                        <span>Confirmar Preços</span>
                        <span className="material-icons-outlined">check_circle</span>
                    </button>
                </div>

            </div>
        </div>
    );
};

export default ModalPinos;
