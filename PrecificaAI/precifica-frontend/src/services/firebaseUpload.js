import { db, storage } from './firebase';
import { doc, setDoc, serverTimestamp } from 'firebase/firestore';
import { ref, uploadString, getDownloadURL } from 'firebase/storage';

export async function uploadLote(sessionId, nomeLote, artes, onProgress) {
  const resultado = { sucesso: 0, falha: 0 };

  const sessaoRef = doc(db, 'sessoes', sessionId);
  await setDoc(sessaoRef, {
    nome: nomeLote,
    vendedora: 'vivi',
    created_at: serverTimestamp(),
    total_artes: artes.length,
    artes: [],
  });

  const artesMetadata = [];

  for (let i = 0; i < artes.length; i++) {
    try {
      const arte = artes[i];
      const fileName = `${arte.nome.replace(/\s+/g, '_')}_${Date.now()}.jpg`;
      const storagePath = `sessoes/${sessionId}/${fileName}`;

      const storageRef = ref(storage, storagePath);
      const base64Data = arte.dataURL.split(',')[1];
      await uploadString(storageRef, base64Data, 'base64', {
        contentType: 'image/jpeg',
      });

      const downloadURL = await getDownloadURL(storageRef);

      artesMetadata.push({
        nome: arte.nome,
        preco: arte.preco,
        parcelas: arte.parcelas,
        storage_path: storagePath,
        storage_url: downloadURL,
      });

      resultado.sucesso++;
    } catch (err) {
      console.error(`Erro upload arte ${i}:`, err);
      resultado.falha++;
    }

    if (onProgress) onProgress(i + 1, artes.length);
  }

  await setDoc(sessaoRef, { artes: artesMetadata }, { merge: true });

  return resultado;
}
