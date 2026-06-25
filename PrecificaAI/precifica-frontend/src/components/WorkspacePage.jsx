import React, { useState, useRef } from 'react';
import { Capacitor } from '@capacitor/core';
import { Camera, CameraResultType, CameraSource } from '@capacitor/camera';
import { Filesystem, Directory } from '@capacitor/filesystem';
import { Share } from '@capacitor/share';
import { gerarArteDataURL } from '../utils/renderArteFinal';
import { uploadLote } from '../services/firebaseUpload';
import BatchItemCard from './upload/BatchItemCard';
import BatchGalleryScreen from './upload/BatchGalleryScreen';

function gerarNomeLoteDefault() {
    const now = new Date();
    const dd = String(now.getDate()).padStart(2, '0');
    const mm = String(now.getMonth() + 1).padStart(2, '0');
    const hh = String(now.getHours()).padStart(2, '0');
    const min = String(now.getMinutes()).padStart(2, '0');
    return `lote-${dd}${mm}-${hh}${min}`;
}

function formatarPreco(input) {
    let limpo = input.replace(/[^\d.,'‘’]/g, '');
    limpo = limpo.replace(/[,'‘’]/g, '.');
    const valor = parseFloat(limpo);
    if (isNaN(valor) || valor <= 0) return input;
    return `R$ ${valor.toFixed(2).replace('.', ',')}`;
}

function calcularTextoParcelas(precoString) {
    const limpo = precoString.replace(/[^\d,]/g, '').replace(',', '.');
    const valor = parseFloat(limpo);
    if (isNaN(valor) || valor <= 0) return '';
    const parcela = (valor / 10).toFixed(2).replace('.', ',');
    return `10x R$ ${parcela}`;
}

const WorkspacePage = () => {
    const [step, setStep] = useState('upload'); // 'upload' | 'loading' | 'decisao_pinos' | 'editando_pinos' | 'text_input' | 'style_settings'
    const [modoAtual, setModoAtual] = useState('batch'); // 'batch' | 'batch_result'
    const [filaBatch, setFilaBatch] = useState([]);
    const [batchResultados, setBatchResultados] = useState([]);
    const [imagemOriginal, setImagemOriginal] = useState(null);
    const [imagemLimpaBase64, setImagemLimpaBase64] = useState(null);
    const [boxes, setBoxes] = useState([]);
    const [valoresPinos, setValoresPinos] = useState({});
    const [camposIniciais, setCamposIniciais] = useState(null); // {nome, preco, parcelas} vindos do NLP (T-NLP-001)
    const [showNomeLoteModal, setShowNomeLoteModal] = useState(false);
    const [nomeLote, setNomeLote] = useState('');
    const [sessionId, setSessionId] = useState('');
    const [uploadStatus, setUploadStatus] = useState(null); // null | 'enviando' | 'concluido' | 'erro'
    const [uploadProgress, setUploadProgress] = useState('');
    const fileInputRef = useRef(null);
    const [apiBase, setApiBase] = useState(() => {
        return localStorage.getItem('API_BASE') || 'https://precifica-api-356056496893.us-central1.run.app';
    });
    const [showSettings, setShowSettings] = useState(false);
    const [tempApiBase, setTempApiBase] = useState(apiBase);
    const handleFileUpload = async (event) => {
        const file = event.target.files[0];
        if (!file) return;

        setImagemOriginal(file);
        await processarImagem(file);
    };

    const triggerPhotoSelection = async () => {
        if (Capacitor.isNativePlatform()) {
            try {
                const image = await Camera.getPhoto({
                    quality: 95,
                    allowEditing: false,
                    resultType: CameraResultType.Uri,
                    source: CameraSource.Prompt
                });

                const response = await fetch(image.webPath);
                const blob = await response.blob();
                const file = new File([blob], 'foto_joia_' + Date.now() + '.jpg', { type: blob.type || 'image/jpeg' });

                setImagemOriginal(file);
                await processarImagem(file);
            } catch (err) {
                console.log('Photo selection cancelled or failed:', err);
            }
        } else {
            fileInputRef.current?.click();
        }
    };

    const handleBatchFilesSelected = (e) => {
        const files = Array.from(e.target.files || []);
        if (files.length === 0) return;
        const novosItens = files.map((file, i) => ({
            id: `batch-${Date.now()}-${i}`,
            webPath: URL.createObjectURL(file),
            file,
            nome: '',
            preco: '',
            status: 'pendente',
        }));
        setFilaBatch(prev => [...prev, ...novosItens]);
        setModoAtual('batch');
    };

    const abrirCamera = async () => {
        try {
            const photo = await Camera.getPhoto({
                quality: 90,
                resultType: CameraResultType.Uri,
                source: CameraSource.Camera,
            });
            const response = await fetch(photo.webPath);
            const blob = await response.blob();
            const file = new File([blob], `camera_${Date.now()}.jpg`, { type: 'image/jpeg' });
            const novoItem = {
                id: `batch-${Date.now()}`,
                webPath: photo.webPath,
                file,
                nome: '',
                preco: '',
                status: 'pendente',
            };
            setFilaBatch(prev => [...prev, novoItem]);
        } catch (err) {
            if (!String(err).toLowerCase().includes('cancel')) {
                console.error('Erro câmera:', err);
            }
        }
    };

    const abrirSeletorMultiplo = () => {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = 'image/*';
        input.multiple = true;
        input.onchange = handleBatchFilesSelected;
        input.click();
    };

    const handleRemoverBatchItem = (id) => {
        setFilaBatch(prev => prev.filter(item => item.id !== id));
    };

    const handleUpdateBatchNome = (id, novoNome) => {
        setFilaBatch(prev => prev.map(item => item.id === id ? { ...item, nome: novoNome } : item));
    };

    const handleUpdateBatchPreco = (id, novoPreco) => {
        setFilaBatch(prev => prev.map(item => item.id === id ? { ...item, preco: novoPreco } : item));
    };

    const handleAbrirModalNomeLote = () => {
        setNomeLote(gerarNomeLoteDefault());
        setSessionId(crypto.randomUUID());
        setShowNomeLoteModal(true);
    };

    const handleConfirmarNomeLote = () => {
        setShowNomeLoteModal(false);
        handleProcessarBatch();
    };

    const handleProcessarBatch = async () => {
        const resultados = [];
        const artesParaUpload = [];
        for (const item of filaBatch) {
            setFilaBatch(prev => prev.map(i => i.id === item.id ? { ...i, status: 'processando' } : i));
            try {
                const dataUrl = await new Promise((resolve, reject) => {
                    const reader = new FileReader();
                    reader.onload = () => resolve(reader.result);
                    reader.onerror = reject;
                    reader.readAsDataURL(item.file);
                });
                const base64 = dataUrl.split(',')[1];
                const precoFormatado = formatarPreco(item.preco);
                const parcelas = calcularTextoParcelas(precoFormatado);
                const dataURL = await gerarArteDataURL({
                    imagemBase64: base64,
                    detalhes: item.nome,
                    preco: precoFormatado,
                    parcelas,
                    formato: 'story',
                    mostrarPreco: true,
                    mostrarParcelas: true,
                });
                let savedUri = null;
                if (Capacitor.isNativePlatform()) {
                    try {
                        const ts = Date.now();
                        const saved = await Filesystem.writeFile({
                            path: `PrecificaAI/${nomeLote}/${item.nome.replace(/\s+/g, '_')}_${ts}.jpg`,
                            data: dataURL.split(',')[1],
                            directory: Directory.Documents,
                            recursive: true,
                        });
                        savedUri = saved.uri;
                    } catch (fsErr) {
                        console.warn('Filesystem.writeFile falhou:', fsErr);
                    }
                }
                resultados.push({ id: item.id, nome: item.nome, dataURL, uri: savedUri, status: 'concluido' });
                artesParaUpload.push({ nome: item.nome, preco: precoFormatado, parcelas, dataURL });
                setFilaBatch(prev => prev.map(i => i.id === item.id ? { ...i, status: 'concluido' } : i));
            } catch (err) {
                console.error(`Erro ao processar ${item.nome}:`, err);
                resultados.push({ id: item.id, nome: item.nome, dataURL: null, uri: null, status: 'erro' });
                setFilaBatch(prev => prev.map(i => i.id === item.id ? { ...i, status: 'erro' } : i));
            }
        }
        setBatchResultados(resultados);
        setModoAtual('batch_result');

        // Upload Firebase — fire-and-forget
        if (artesParaUpload.length > 0) {
            try {
                setUploadStatus('enviando');
                const resultado = await uploadLote(
                    sessionId,
                    nomeLote,
                    artesParaUpload,
                    (current, total) => setUploadProgress(`${current}/${total}`)
                );
                setUploadStatus('concluido');
                console.log('Upload Firebase:', resultado);
            } catch (err) {
                console.error('Erro upload Firebase:', err);
                setUploadStatus('erro');
            }
        }
    };

    const processarImagem = async (file) => {
        const base64 = await new Promise((resolve) => {
            const reader = new FileReader();
            reader.onload = () => resolve(reader.result.split(',')[1]);
            reader.readAsDataURL(file);
        });
        setImagemLimpaBase64(base64);
        setBoxes([]);
        setStep('text_input');
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

    // --- Tela de texto (NLP / T-NLP-001) ---
    const handleConfirmarTexto = (campos) => {
        setCamposIniciais(campos);
        setStep('style_settings');
    };

    const handlePularTexto = () => {
        setCamposIniciais(null); // rota antiga: StyleSettings com valores padrão
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
            else setStep('text_input');
        } else if (step === 'editando_pinos') {
            setStep('decisao_pinos');
        } else if (step === 'decisao_pinos') {
            setStep('upload');
        }
    };


    // --- RENDERS ---

    if (modoAtual === 'batch_result') {
        return (
            <BatchGalleryScreen
                resultados={batchResultados}
                uploadStatus={uploadStatus}
                uploadProgress={uploadProgress}
                onVoltar={() => setModoAtual('batch')}
                onNovaLeva={() => {
                    setFilaBatch([]);
                    setBatchResultados([]);
                    setUploadStatus(null);
                    setUploadProgress('');
                    setModoAtual('inicial');
                }}
            />
        );
    }

    if (modoAtual === 'batch') {
        return (
            <div className="min-h-screen bg-background-light flex flex-col animate-fade-in pb-24">
                {/* Header Fixo */}
                <header className="sticky top-0 z-30 bg-white/80 backdrop-blur-md border-b border-gray-100 shadow-sm px-6 py-4">
                    <h1 className="text-2xl font-bold text-gray-900">
                        Precifica<span className="text-primary">.AI</span>
                    </h1>
                    <p className="text-sm text-gray-400 mt-1">
                        {filaBatch.length} {filaBatch.length === 1 ? 'peça' : 'peças'}
                    </p>
                </header>

                {/* Grid de Fotos */}
                <main className="flex-1 p-6">
                    {filaBatch.length === 0 ? (
                        <div className="flex flex-col items-center gap-6 py-20">
                            <span className="material-icons-outlined text-6xl text-gray-200">add_photo_alternate</span>
                            <p className="text-gray-400 text-center">
                                Tire fotos ou selecione da galeria<br/>para começar a precificar
                            </p>
                            <div className="flex gap-3">
                                <button
                                    onClick={abrirCamera}
                                    className="flex items-center gap-2 px-5 py-3 bg-primary text-white font-bold rounded-2xl shadow-lg active:scale-95 transition-all"
                                >
                                    <span className="material-icons-outlined">photo_camera</span>
                                    Câmera
                                </button>
                                <button
                                    onClick={abrirSeletorMultiplo}
                                    className="flex items-center gap-2 px-5 py-3 bg-white border-2 border-gray-200 text-gray-700 font-bold rounded-2xl active:scale-95 transition-all"
                                >
                                    <span className="material-icons-outlined">photo_library</span>
                                    Galeria
                                </button>
                            </div>
                        </div>
                    ) : (
                        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                            {filaBatch.map((item, index) => (
                                <BatchItemCard
                                    key={item.id}
                                    item={item}
                                    index={index}
                                    onUpdateNome={handleUpdateBatchNome}
                                    onUpdatePreco={handleUpdateBatchPreco}
                                    onRemove={handleRemoverBatchItem}
                                />
                            ))}

                            {/* Adicionar mais — câmera e galeria */}
                            <div className="flex flex-col gap-2 justify-center min-h-[120px]">
                                <button
                                    onClick={abrirCamera}
                                    className="flex items-center justify-center gap-2 border-2 border-dashed border-gray-200 hover:border-primary/50 bg-white/50 hover:bg-primary/5 rounded-xl p-3 transition-colors group"
                                >
                                    <span className="material-icons-outlined text-gray-400 group-hover:text-primary transition-colors">photo_camera</span>
                                    <span className="text-sm font-medium text-gray-500 group-hover:text-primary transition-colors">Câmera</span>
                                </button>
                                <button
                                    onClick={abrirSeletorMultiplo}
                                    className="flex items-center justify-center gap-2 border-2 border-dashed border-gray-200 hover:border-primary/50 bg-white/50 hover:bg-primary/5 rounded-xl p-3 transition-colors group"
                                >
                                    <span className="material-icons-outlined text-gray-400 group-hover:text-primary transition-colors">photo_library</span>
                                    <span className="text-sm font-medium text-gray-500 group-hover:text-primary transition-colors">Galeria</span>
                                </button>
                            </div>
                        </div>
                    )}
                </main>

                <footer className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-100 p-4 shadow-[0_-10px_30px_rgba(0,0,0,0.05)] z-30">
                    {(() => {
                        const prontas = filaBatch.length > 0 && filaBatch.every(i => i.nome.trim() && i.preco.trim());
                        return (
                            <div className="max-w-4xl mx-auto flex justify-center">
                                <button
                                    onClick={prontas ? handleAbrirModalNomeLote : undefined}
                                    disabled={!prontas}
                                    className={`w-full sm:w-auto px-8 py-4 font-bold rounded-2xl flex items-center justify-center gap-2 transition-all ${
                                        prontas
                                            ? 'bg-primary hover:bg-primary-dark text-white shadow-lg shadow-primary/25 active:scale-95'
                                            : 'bg-gray-200 text-gray-400 cursor-not-allowed shadow-inner'
                                    }`}
                                >
                                    <span className="material-icons-outlined">auto_awesome</span>
                                    {prontas ? `Processar Todas (${filaBatch.length})` : 'Preencha nome e preço'}
                                </button>
                            </div>
                        );
                    })()}
                </footer>

                {/* Modal Nome do Lote */}
                {showNomeLoteModal && (
                    <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/50 backdrop-blur-sm">
                        <div className="bg-white rounded-t-3xl p-6 w-full max-w-md shadow-2xl space-y-4 pb-8">
                            <h3 className="text-lg font-bold text-gray-900">Nome do lote</h3>
                            <input
                                type="text"
                                value={nomeLote}
                                onChange={(e) => setNomeLote(e.target.value)}
                                autoFocus
                                className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-gray-800 font-medium focus:outline-none focus:border-primary"
                                placeholder="ex: lote-2406-0920"
                            />
                            <button
                                onClick={handleConfirmarNomeLote}
                                className="w-full py-4 bg-primary text-white font-bold rounded-2xl shadow-lg active:scale-95 transition-all flex items-center justify-center gap-2"
                            >
                                <span className="material-icons-outlined">auto_awesome</span>
                                Processar
                            </button>
                        </div>
                    </div>
                )}
            </div>
        );
    }

};

export default WorkspacePage;
