import React, { useState, useEffect } from 'react';
import { gerarArteDataURL } from '../utils/renderArteFinal';

const StyleSettings = ({ imagemLimpaBase64, onVoltar, onGerarArte }) => {
    const [detalhes, setDetalhes] = useState('Anel de Ouro 18k');
    const [preco, setPreco] = useState('R$ 259,90');
    const [formato, setFormato] = useState('1:1');
    const [mostrarPreco, setMostrarPreco] = useState(true);
    const [mostrarParcelas, setMostrarParcelas] = useState(true);
    const [previewUrl, setPreviewUrl] = useState(null);

    // Update preview whenever inputs change
    useEffect(() => {
        let isMounted = true;
        const updatePreview = async () => {
            if (!imagemLimpaBase64) return;
            try {
                // Generate a lightweight preview
                const url = await gerarArteDataURL({
                    imagemBase64: imagemLimpaBase64,
                    detalhes,
                    preco,
                    formato,
                    mostrarPreco,
                    mostrarParcelas,
                    // Pass empty/default for pins/boxes since this is single text mode
                    valoresPinos: {},
                    boxes: []
                });
                if (isMounted) setPreviewUrl(url);
            } catch (error) {
                console.error("Erro ao gerar preview:", error);
            }
        };

        const timeoutId = setTimeout(updatePreview, 300); // 300ms debounce
        return () => {
            isMounted = false;
            clearTimeout(timeoutId);
        };
    }, [imagemLimpaBase64, detalhes, preco, formato, mostrarPreco, mostrarParcelas]);

    const handleGerarArte = () => {
        onGerarArte({
            detalhes,
            preco,
            formato,
            mostrarPreco,
            mostrarParcelas
        });
    };

    return (
        <div className="min-h-screen bg-background-light font-display text-gray-800 pb-24">
            {/* 1. Navbar Minimalista */}
            <nav className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-6 py-4 bg-background-light/80 backdrop-blur-md border-b border-gray-100/50">
                <button
                    onClick={onVoltar}
                    className="w-10 h-10 flex items-center justify-center rounded-full bg-white shadow-sm hover:bg-gray-50 transition-colors"
                >
                    <span className="material-icons-outlined text-gray-600">chevron_left</span>
                </button>
                <h1 className="text-lg font-semibold tracking-tight text-gray-900">Style Settings</h1>
                <div className="w-10" /> {/* Spacer for centering */}
            </nav>

            {/* Main Content */}
            <div className="pt-24 px-6 space-y-8 max-w-md mx-auto">

                {/* 2. Live Preview */}
                <div className="relative w-full aspect-square rounded-3xl overflow-hidden shadow-2xl shadow-primary/10 ring-1 ring-black/5 group">
                    {/* Background Glow */}
                    <div className="absolute inset-0 bg-primary/5 blur-xl pointer-events-none" />

                    {/* Image */}
                    {previewUrl ? (
                        <img
                            src={previewUrl}
                            alt="Cleaned Jewelry"
                            className="w-full h-full object-contain transition-transform duration-700 group-hover:scale-105"
                        />
                    ) : (
                        <div className="w-full h-full flex items-center justify-center bg-gray-100 text-gray-400">
                            <span className="material-icons-outlined text-4xl animate-pulse">image</span>
                        </div>
                    )}

                    {/* Floating Tag */}
                    <div className="absolute top-4 right-4 px-3 py-1.5 rounded-full bg-white/30 backdrop-blur-md border border-white/40 flex items-center gap-1.5 shadow-lg">
                        <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
                        <span className="text-xs font-medium text-white drop-shadow-sm tracking-wide">Live Preview</span>
                    </div>
                </div>

                {/* 3. Product Details */}
                <div className="space-y-3">
                    <label className="text-sm font-semibold text-gray-400 uppercase tracking-wider ml-1">Product Details</label>
                    <div className="space-y-2">
                        <input
                            type="text"
                            value={detalhes}
                            onChange={(e) => setDetalhes(e.target.value)}
                            className="w-full p-4 bg-white rounded-xl text-gray-800 font-medium placeholder-gray-300 focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all shadow-sm"
                            placeholder="Product Name (e.g. Gold Ring)"
                        />
                        <div className="relative">
                            <input
                                type="text"
                                value={preco}
                                onChange={(e) => setPreco(e.target.value)}
                                className="w-full p-4 pl-12 bg-white rounded-xl text-gray-800 font-bold placeholder-gray-300 focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all shadow-sm"
                                placeholder="R$ 0,00"
                            />
                            <span className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 material-icons-outlined">payments</span>
                        </div>
                    </div>
                </div>

                {/* 4. Select Format */}
                <div className="space-y-3">
                    <label className="text-sm font-semibold text-gray-400 uppercase tracking-wider ml-1">Select Format</label>
                    <div className="grid grid-cols-4 gap-3">
                        {[
                            { id: 'orig', label: 'Orig', icon: 'crop_free' },
                            { id: '1:1', label: '1:1', icon: 'crop_square' },
                            { id: 'story', label: 'Story', icon: 'smartphone' },
                            { id: '4:5', label: '4:5', icon: 'crop_portrait' }
                        ].map((fmt) => (
                            <button
                                key={fmt.id}
                                onClick={() => setFormato(fmt.id)}
                                className={`flex flex-col items-center justify-center py-4 rounded-xl transition-all duration-300 ${formato === fmt.id
                                    ? 'bg-primary text-white shadow-lg shadow-primary/30 scale-105'
                                    : 'bg-white text-gray-400 hover:bg-gray-50'
                                    }`}
                            >
                                <span className="material-icons-outlined text-xl mb-1">{fmt.icon}</span>
                                <span className="text-xs font-medium">{fmt.label}</span>
                            </button>
                        ))}
                    </div>
                </div>

                {/* 5. Toggles */}
                <div className="space-y-3">
                    <label className="text-sm font-semibold text-gray-400 uppercase tracking-wider ml-1">Display Options</label>
                    <div className="grid grid-cols-2 gap-4">
                        {/* Show Price Toggle */}
                        <div className="bg-white p-4 rounded-2xl flex items-center justify-between shadow-sm">
                            <div className="flex flex-col">
                                <span className="material-icons-outlined text-gray-400 mb-1">payments</span>
                                <span className="text-sm font-semibold text-gray-700">Show Price</span>
                            </div>
                            <label className="relative inline-flex items-center cursor-pointer">
                                <input
                                    type="checkbox"
                                    className="sr-only peer"
                                    checked={mostrarPreco}
                                    onChange={(e) => setMostrarPreco(e.target.checked)}
                                />
                                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                            </label>
                        </div>

                        {/* Installments Toggle */}
                        <div className="bg-white p-4 rounded-2xl flex items-center justify-between shadow-sm">
                            <div className="flex flex-col">
                                <span className="material-icons-outlined text-gray-400 mb-1">calendar_month</span>
                                <span className="text-sm font-semibold text-gray-700">Installments</span>
                            </div>
                            <label className="relative inline-flex items-center cursor-pointer">
                                <input
                                    type="checkbox"
                                    className="sr-only peer"
                                    checked={mostrarParcelas}
                                    onChange={(e) => setMostrarParcelas(e.target.checked)}
                                />
                                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                            </label>
                        </div>
                    </div>
                </div>

                {/* Spacer for floating button */}
                <div className="h-12" />
            </div>

            {/* 6. Botão Flutuante Inferior */}
            <div className="fixed bottom-0 left-0 right-0 p-6 bg-gradient-to-t from-background-light via-background-light/95 to-transparent z-50">
                <button
                    onClick={handleGerarArte}
                    className="w-full max-w-md mx-auto bg-primary hover:bg-primary-dark text-white font-bold py-4 rounded-xl shadow-xl shadow-primary/25 flex items-center justify-center gap-2 transform transition-all active:scale-95 group"
                >
                    <span className="material-icons-outlined animate-pulse">auto_fix_normal</span>
                    <span className="tracking-wide">GENERATE LUXURY ART</span>
                </button>
            </div>
        </div>
    );
};

export default StyleSettings;
