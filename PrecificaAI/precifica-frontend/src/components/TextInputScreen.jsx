import React, { useState } from 'react';
import { processarTexto } from '../services/api';

/**
 * Tela de entrada de texto com IA (T-NLP-001).
 * A vendedora descreve a peça numa frase ("aneu de rodiu 10x 2") e o
 * Agente 02 (Groq Llama) estrutura em nome / preço / parcelas.
 *
 * Props:
 *   imagemLimpaBase64 - foto já processada (PNG base64) para destaque
 *   apiBase           - endereço do backend (paridade com tratar-imagem)
 *   onConfirmar(campos) - segue pro StyleSettings com {nome, preco, parcelas}
 *   onPular()         - rota antiga: StyleSettings com campos vazios/padrão
 *   onVoltar()        - volta pro upload
 */
const TextInputScreen = ({ imagemLimpaBase64, apiBase, onConfirmar, onPular, onVoltar }) => {
    const [texto, setTexto] = useState('');
    const [loading, setLoading] = useState(false);
    const [erro, setErro] = useState('');
    const [resultado, setResultado] = useState(null); // { nome, preco, parcelas }

    const handleProcessar = async () => {
        const limpo = texto.trim();
        if (!limpo) {
            setErro('Digite a descrição da peça antes de processar.');
            return;
        }
        setLoading(true);
        setErro('');
        setResultado(null);
        try {
            const dados = await processarTexto(limpo, apiBase);
            setResultado({
                nome: dados.nome || '',
                preco: dados.preco || '',
                parcelas: dados.parcelas || '',
            });
        } catch (e) {
            setErro(e.message || 'Não foi possível interpretar o texto. Tente novamente.');
        } finally {
            setLoading(false);
        }
    };

    const handleRefazer = () => {
        setResultado(null);
        setErro('');
    };

    const handleContinuar = () => {
        if (resultado) onConfirmar(resultado);
    };

    return (
        <div className="min-h-screen bg-background-light flex flex-col animate-fade-in pb-28">
            {/* Navbar */}
            <nav className="sticky top-0 z-30 flex items-center justify-between px-6 py-4 bg-background-light/80 backdrop-blur-md border-b border-gray-100/50">
                <button
                    onClick={onVoltar}
                    className="w-10 h-10 flex items-center justify-center rounded-full bg-white shadow-sm hover:bg-gray-50 transition-colors"
                    title="Voltar"
                >
                    <span className="material-icons-outlined text-gray-600">chevron_left</span>
                </button>
                <h1 className="text-lg font-semibold tracking-tight text-gray-900">Descreva a peça</h1>
                <div className="w-10" />
            </nav>

            <main className="flex-1 px-6 pt-6 space-y-6 max-w-md mx-auto w-full">
                {/* Foto em destaque */}
                {imagemLimpaBase64 && (
                    <div className="relative w-full aspect-square rounded-3xl overflow-hidden shadow-xl shadow-primary/10 ring-1 ring-black/5 bg-white">
                        <img
                            src={`data:image/png;base64,${imagemLimpaBase64}`}
                            alt="Peça processada"
                            className="w-full h-full object-contain"
                        />
                    </div>
                )}

                {!resultado && (
                    <>
                        <div className="space-y-3">
                            <label className="text-sm font-semibold text-gray-400 uppercase tracking-wider ml-1">
                                Descreva em uma frase
                            </label>
                            <textarea
                                data-testid="texto-input"
                                value={texto}
                                onChange={(e) => setTexto(e.target.value)}
                                rows={3}
                                placeholder='Ex: "aneu de rodiu 10x 2" ou "colar ouro 18k 350"'
                                className="w-full p-4 bg-white rounded-2xl text-gray-800 font-medium placeholder-gray-300 focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all shadow-sm resize-none"
                            />
                            <p className="text-xs text-gray-400 leading-relaxed ml-1">
                                A IA entende gíria, abreviação e parcelas. Você confere antes de continuar.
                            </p>
                        </div>

                        {erro && (
                            <div
                                data-testid="erro-msg"
                                className="p-4 bg-red-50 text-red-600 rounded-xl text-sm font-medium animate-fade-in border border-red-100"
                            >
                                {erro}
                            </div>
                        )}

                        <button
                            data-testid="processar-btn"
                            onClick={handleProcessar}
                            disabled={loading}
                            className="w-full bg-primary hover:bg-primary-dark disabled:opacity-60 disabled:cursor-not-allowed text-white font-bold py-4 rounded-2xl shadow-xl shadow-primary/25 flex items-center justify-center gap-2 transform transition-all active:scale-95"
                        >
                            {loading ? (
                                <>
                                    <span className="animate-spin rounded-full h-5 w-5 border-t-2 border-b-2 border-white" />
                                    <span className="tracking-wide">Processando...</span>
                                </>
                            ) : (
                                <>
                                    <span className="material-icons-outlined animate-pulse">auto_awesome</span>
                                    <span className="tracking-wide">Processar com IA</span>
                                </>
                            )}
                        </button>

                        <button
                            data-testid="pular-btn"
                            onClick={onPular}
                            className="w-full text-sm font-semibold text-gray-500 hover:text-primary py-2 transition-colors"
                        >
                            Pular, preencher na mão
                        </button>
                    </>
                )}

                {resultado && (
                    <div className="space-y-4 animate-fade-in">
                        <label className="text-sm font-semibold text-gray-400 uppercase tracking-wider ml-1">
                            Confira os dados extraídos
                        </label>

                        <div className="space-y-3">
                            <CampoExtraido
                                testid="campo-nome"
                                icon="label"
                                rotulo="Nome"
                                valor={resultado.nome || '—'}
                            />
                            <CampoExtraido
                                testid="campo-preco"
                                icon="payments"
                                rotulo="Preço"
                                valor={resultado.preco || '—'}
                            />
                            <CampoExtraido
                                testid="campo-parcelas"
                                icon="calendar_month"
                                rotulo="Parcelas"
                                valor={resultado.parcelas || 'Sem parcelamento'}
                            />
                        </div>

                        <div className="flex gap-3 pt-2">
                            <button
                                data-testid="refazer-btn"
                                onClick={handleRefazer}
                                className="flex-1 py-4 bg-white border-2 border-gray-200 hover:border-primary/40 text-gray-600 font-semibold rounded-2xl transition-all active:scale-95"
                            >
                                Refazer
                            </button>
                            <button
                                data-testid="continuar-btn"
                                onClick={handleContinuar}
                                className="flex-1 py-4 bg-primary hover:bg-primary-dark text-white font-bold rounded-2xl shadow-lg shadow-primary/30 transition-all active:scale-95 flex items-center justify-center gap-2"
                            >
                                Continuar
                                <span className="material-icons-outlined">arrow_forward</span>
                            </button>
                        </div>
                    </div>
                )}
            </main>
        </div>
    );
};

const CampoExtraido = ({ testid, icon, rotulo, valor }) => (
    <div className="bg-white p-4 rounded-2xl flex items-center gap-4 shadow-sm">
        <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center text-primary shrink-0">
            <span className="material-icons-outlined text-xl">{icon}</span>
        </div>
        <div className="min-w-0">
            <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">{rotulo}</p>
            <p data-testid={testid} className="text-gray-900 font-bold truncate">{valor}</p>
        </div>
    </div>
);

export default TextInputScreen;
