import { Capacitor } from '@capacitor/core';
import { Share } from '@capacitor/share';

export default function BatchGalleryScreen({ resultados, uploadStatus, uploadProgress, onVoltar, onNovaLeva }) {
    const concluidas = resultados.filter(r => r.status === 'concluido');
    const erros = resultados.filter(r => r.status === 'erro');
    const isNative = Capacitor.isNativePlatform();

    const compartilharItem = async (item) => {
        if (!isNative || !item.uri) return;
        try {
            await Share.share({ title: item.nome, url: item.uri, dialogTitle: 'Compartilhar arte' });
        } catch (err) {
            console.warn('Share falhou:', err);
        }
    };

    const salvarTodasNaGaleria = () => {
        const count = concluidas.filter(r => r.uri).length;
        alert(`✅ ${count} artes salvas em Documents/PrecificaAI`);
    };

    return (
        <div className="min-h-screen bg-background-light flex flex-col pb-44">
            <header className="sticky top-0 z-30 bg-white/80 backdrop-blur-md border-b border-gray-100 shadow-sm px-6 py-4">
                <h1 className="text-xl font-display font-bold text-gray-900">Artes Geradas</h1>
                <p className="text-sm text-gray-500">
                    {concluidas.length}/{resultados.length} concluídas
                    {erros.length > 0 && ` · ${erros.length} com erro`}
                </p>
            </header>

            <main className="flex-1 p-4 grid grid-cols-2 gap-4">
                {resultados.map((item) => (
                    <div key={item.id} className="flex flex-col rounded-xl overflow-hidden shadow-md bg-white">
                        <div className="relative aspect-[9/16]">
                            {item.dataURL ? (
                                <img src={item.dataURL} alt={item.nome} className="w-full h-full object-cover" />
                            ) : (
                                <div className="w-full h-full bg-red-50 flex items-center justify-center">
                                    <span className="material-icons-outlined text-red-300 text-3xl">broken_image</span>
                                </div>
                            )}
                        </div>
                        <div className="p-2 space-y-1.5">
                            <p className="text-xs font-semibold text-gray-700 truncate">{item.nome}</p>
                            {item.status === 'concluido' && isNative && (
                                <button
                                    onClick={() => compartilharItem(item)}
                                    className="w-full text-xs py-1.5 bg-primary text-white rounded-lg font-semibold flex items-center justify-center gap-1 active:opacity-80"
                                >
                                    <span className="material-icons-outlined" style={{ fontSize: 14 }}>share</span>
                                    Compartilhar
                                </button>
                            )}
                            {item.status === 'erro' && (
                                <p className="text-xs text-red-400 font-medium">Erro ao gerar</p>
                            )}
                        </div>
                    </div>
                ))}
            </main>

            <footer className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-100 p-4 shadow-lg z-30 space-y-2">
                {uploadStatus === 'enviando' && (
                    <div className="w-full py-2 px-4 bg-blue-50 border border-blue-100 rounded-xl text-sm text-blue-700 font-medium flex items-center gap-2">
                        <span className="material-icons-outlined text-base animate-spin">sync</span>
                        Enviando para o catálogo... {uploadProgress}
                    </div>
                )}
                {uploadStatus === 'concluido' && (
                    <div className="w-full py-2 px-4 bg-green-50 border border-green-100 rounded-xl text-sm text-green-700 font-medium flex items-center gap-2">
                        <span className="material-icons-outlined text-base">cloud_done</span>
                        {concluidas.length} artes salvas no catálogo
                    </div>
                )}
                {uploadStatus === 'erro' && (
                    <div className="w-full py-2 px-4 bg-amber-50 border border-amber-100 rounded-xl text-sm text-amber-700 font-medium flex items-center gap-2">
                        <span className="material-icons-outlined text-base">warning</span>
                        Erro ao enviar. Artes salvas localmente.
                    </div>
                )}
                {concluidas.length > 0 && isNative && (
                    <button
                        onClick={salvarTodasNaGaleria}
                        className="w-full py-3 bg-primary hover:bg-primary-dark text-white font-bold rounded-2xl shadow-md flex items-center justify-center gap-2 active:scale-95 transition-all"
                    >
                        <span className="material-icons-outlined">save_alt</span>
                        Salvar Todas na Galeria ({concluidas.length})
                    </button>
                )}
                <button
                    onClick={onNovaLeva}
                    className="w-full py-3 bg-white border-2 border-gray-200 text-gray-700 font-bold rounded-2xl flex items-center justify-center gap-2 active:scale-95 transition-all"
                >
                    <span className="material-icons-outlined">add_photo_alternate</span>
                    Novo Lote
                </button>
                <button
                    onClick={onVoltar}
                    className="w-full py-2 text-gray-400 text-sm font-medium"
                >
                    Voltar ao lote atual
                </button>
            </footer>
        </div>
    );
}
