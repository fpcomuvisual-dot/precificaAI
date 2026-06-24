import { initializeApp } from 'firebase/app';
import { getFirestore } from 'firebase/firestore';
import { getStorage } from 'firebase/storage';

const firebaseConfig = {
  apiKey: "AIzaSyBi63NsMa55eOkPamaS7wlT6C9hWQKHSps",
  authDomain: "precificaai-vivi-9b5f6.firebaseapp.com",
  projectId: "precificaai-vivi-9b5f6",
  storageBucket: "precificaai-vivi-9b5f6.firebasestorage.app",
  messagingSenderId: "139370645736",
  appId: "1:139370645736:web:1c32b62fe712470e4b615d",
};

const app = initializeApp(firebaseConfig);
export const db = getFirestore(app);
export const storage = getStorage(app);
