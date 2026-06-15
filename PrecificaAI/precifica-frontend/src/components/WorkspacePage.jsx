import React, { useState, useRef } from 'react';
import StyleSettings from './StyleSettings';
import ModalPinos from './ModalPinos'; // Assuming this component exists or will exist
import { gerarEBaixarArte } from '../utils/renderArteFinal';

const WorkspacePage = () => {
    const [step, setStep] = useState('upload'); // 'upload' | 'loading' | 'decisao_pinos' | 'editando_pinos' | 'style_settings'
    const [imagemOriginal, setImagemOriginal] = useState(null);
    const [imagemLimpaBase64, setImagemLimpaBase64] = useState(null);
    const [boxes, setBoxes] = useState([]);
    const [valoresPinos, setValoresPinos] = useState({});
    const fileInputRef = useRef(null);
    const [error, setError] = useState('');

    const handleFileUpload = async (event) => {
        const file = event.target.files[0];
        if (!file) return;

        setImagemOriginal(file);
        await processarImagem(file);
    };

    const processarImagem = async (file) => {
        setStep('loading');
        setError('');

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('http://localhost:8000/api/tratar-imagem', {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                throw new Error('Falha no processamento da imagem');
            }

            const data = await response.json();

            if (data.success) {
                setImagemLimpaBase64(data.image_base64);
                setBoxes(data.boxes || []);

                // Lógica de Roteamento Inteligente
                if (data.boxes && data.boxes.length > 1) {
                    setStep('decisao_pinos');
                } else {
                    setStep('style_settings');
                }
            } else {
                throw new Error(data.message || 'Erro desconhecido na API');
            }
        } catch (err) {
            console.error('Erro ao processar imagem:', err);
            setError('Ocorreu um erro ao limpar a imagem. Tente novamente.');
            setStep('upload');
        }
    };

    const handleDecisaoPinos = (usarPinos) => {
        if (usarPinos) {
            setStep('editando_pinos');
        } else {
            setStep('style_settings');
        }
    };

    const handleSalvarPinos = (novosValores) => {
        setValoresPinos(novosValores);
        setStep('style_settings');
    };

    const handleGerarArteFinal = async (configuracoes) => {
        try {
            // Optional: Loading feedback could be added here
            console.log('Gerando Arte Final com:', {
                imagemLimpaBase64,
                boxes,
                valoresPinos,
                configuracoes
            });

            await gerarEBaixarArte({
                imagemBase64: imagemLimpaBase64,
                detalhes: configuracoes.detalhes,
                formato: configuracoes.formato,
                mostrarPreco: configuracoes.mostrarPreco,
                valoresPinos: valoresPinos,
                boxes: boxes
            });

            // Success feedback
            alert("✨ Arte de luxo gerada e baixada com sucesso!");

            // Optional: Logic to reset or continue could be here
        } catch (error) {
            console.error("Erro ao renderizar o Canvas:", error);
            alert("Ops! Houve um problema ao gerar a sua imagem final.");
        }
    };

    const handleVoltar = () => {
        // Simple logic to go back step by step or reset
        if (step === 'style_settings') {
            if (boxes.length > 1) setStep('decisao_pinos');
            else setStep('upload');
        } else if (step === 'editando_pinos') {
            setStep('decisao_pinos');
        } else if (step === 'decisao_pinos') {
            setStep('upload');
        }
    };


    // --- RENDERS ---

    if (step === 'loading') {
        return (
            <div className="min-h-screen bg-background-light flex flex-col items-center justify-center p-6">
                <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-primary shadow-lg shadow-primary/30"></div>
                <p className="mt-6 text-gray-600 font-medium text-lg animate-pulse">
                    A inteligência artificial está limpando a imagem...
                </p>
            </div>
        );
    }

    if (step === 'decisao_pinos') {
        return (
            <div className="min-h-screen bg-background-light flex flex-col items-center justify-center p-6 relative">
                {/* Background Image Preview */}
                <div className="absolute inset-0 z-0 opacity-20 blur-sm pointer-events-none">
                    <img
                        src={`data:image/png;base64,${imagemLimpaBase64}`}
                        alt="Background Preview"
                        className="w-full h-full object-cover"
                    />
                </div>

                <div className="bg-white/90 backdrop-blur-md p-8 rounded-3xl shadow-xl shadow-primary/10 max-w-md w-full text-center z-10 border border-white/50">
                    <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-4">
                        <span className="material-icons-outlined text-3xl text-primary">sell</span>
                    </div>
                    <h2 className="text-2xl font-display font-bold text-gray-800 mb-2">
                        Múltiplos preços detectados!
                    </h2>
                    <p className="text-gray-500 mb-8">
                        Encontramos {boxes.length} áreas de preço antigo nesta foto. Como você gostaria de prosseguir?
                    </p>

                    <div className="space-y-3">
                        <button
                            onClick={() => handleDecisaoPinos(true)}
                            className="w-full py-4 bg-primary hover:bg-primary-dark text-white font-semibold rounded-2xl shadow-lg shadow-primary/30 transition-all transform active:scale-95 flex items-center justify-center gap-2"
                        >
                            <span className="material-icons-outlined">push_pin</span>
                            Inserir valores separados (Usar Pinos) ✨
                        </button>
                        <button
                            onClick={() => handleDecisaoPinos(false)}
                            className="w-full py-4 bg-transparent border-2 border-gray-200 hover:border-primary/50 text-gray-600 font-semibold rounded-2xl transition-all hover:bg-gray-50 active:scale-95"
                        >
                            Pular, vou colocar só um valor
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    if (step === 'editando_pinos') {
        // Placeholder for ModalPinos integration
        // Assuming ModalPinos takes these props based on the prompt description for flow, 
        // but strict prop interface might vary. 
        // For now, rendering a placeholder if ModalPinos isn't ready, or the authentic component if it was.
        // Since I need to assume it's imported, I will render it.
        // If ModalPinos is not yet created, this will fail. 
        // I will create a dummy ModalPinos internally or assume it is handled by the user's codebase.
        // Given the instruction "assuma que já está importado", I will use it.
        return (
            <ModalPinos
                imagemBase64={imagemLimpaBase64}
                boxes={boxes}
                onClose={() => setStep('decisao_pinos')} // Or style_settings depending on UX preference, logical to go back
                onSave={handleSalvarPinos}
            />
        );
    }

    if (step === 'style_settings') {
        return (
            <StyleSettings
                imagemLimpaBase64={imagemLimpaBase64}
                onVoltar={handleVoltar}
                onGerarArte={handleGerarArteFinal}
            />
        );
    }

    // Default: Upload Step
    return (
        <div className="min-h-screen bg-background-light p-6 flex flex-col items-center justify-center">
            <div className="max-w-md w-full text-center space-y-8">

                <div className="space-y-2">
                    <h1 className="text-3xl font-display font-bold text-gray-900">
                        Nova Arte <span className="text-primary">Premium</span>
                    </h1>
                    <p className="text-gray-500">
                        Carregue a foto da joia para começar a mágica.
                    </p>
                </div>

                <div
                    onClick={() => fileInputRef.current?.click()}
                    className="border-3 border-dashed border-gray-200 hover:border-primary/50 bg-white hover:bg-gray-50 rounded-3xl p-12 cursor-pointer transition-all duration-300 group shadow-sm hover:shadow-md"
                >
                    <div className="w-20 h-20 bg-primary/5 rounded-full flex items-center justify-center mx-auto mb-6 group-hover:bg-primary/10 transition-colors">
                        <span className="material-icons-outlined text-4xl text-primary/80 group-hover:text-primary transition-colors">add_a_photo</span>
                    </div>
                    <p className="text-lg font-medium text-gray-700 group-hover:text-gray-900">
                        Toque para enviar foto
                    </p>
                    <p className="text-sm text-gray-400 mt-2">
                        Suporta JPG e PNG
                    </p>
                    <input
                        type="file"
                        ref={fileInputRef}
                        onChange={handleFileUpload}
                        accept="image/*"
                        className="hidden"
                    />
                </div>

                {error && (
                    <div className="p-4 bg-red-50 text-red-600 rounded-xl text-sm font-medium animate-fade-in border border-red-100">
                        {error}
                    </div>
                )}
            </div>
        </div>
    );
};

export default WorkspacePage;
