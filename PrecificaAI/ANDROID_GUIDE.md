# 📱 PrecificaAI - Guia Android

## ✅ Configuração Completa!

O projeto Android foi criado em:
```
x:\Dev\TEXTOJOIA\Antigravity\PrecificaAI\precifica-frontend\android
```

## 🚀 Como Rodar no Android Studio

### 1. **Android Studio Deve Estar Abrindo**
   - Se não abriu automaticamente, abra manualmente:
   - File → Open → Selecione a pasta `android`

### 2. **Aguarde o Gradle Sync**
   - O Android Studio vai sincronizar as dependências
   - Isso pode levar alguns minutos na primeira vez

### 3. **Conecte seu Dispositivo ou Emulador**
   - **Dispositivo Físico:** Conecte via USB e ative "Depuração USB"
   - **Emulador:** Crie um AVD (Android Virtual Device) no Android Studio

### 4. **Execute o App**
   - Clique no botão ▶️ (Run) no Android Studio
   - Ou pressione `Shift + F10`

---

## ⚙️ Configuração Importante: API Backend

**ATENÇÃO:** O app precisa se conectar ao backend Python!

### Opção 1: Backend Local (Mesmo PC)
Se o backend está rodando no mesmo PC:

1. Edite `src/services/api.js`:
```javascript
// Para emulador Android
const API_BASE = "http://10.0.2.2:8000";

// Para dispositivo físico na mesma rede
const API_BASE = "http://SEU_IP_LOCAL:8000";
```

2. Rebuild:
```bash
npm run build
npx cap sync android
```

### Opção 2: Backend em Servidor
Se o backend está em um servidor:
```javascript
const API_BASE = "https://seu-servidor.com";
```

---

## 📝 Comandos Úteis

### Rebuild do Frontend
```bash
cd x:\Dev\TEXTOJOIA\Antigravity\PrecificaAI\precifica-frontend
npm run build
npx cap sync android
```

### Reabrir no Android Studio
```bash
npx cap open android
```

### Ver Logs do App
```bash
npx cap run android -l
```

---

## 🔧 Troubleshooting

### Erro de Gradle
- Certifique-se que o JDK 17 está instalado
- Android Studio → File → Project Structure → SDK Location

### App não conecta ao backend
- Verifique se o backend está rodando
- Teste a URL no navegador do celular
- Verifique firewall/antivírus

### Rebuild Completo
```bash
cd android
./gradlew clean
cd ..
npm run build
npx cap sync android
```

---

## 📦 Gerar APK para Distribuição

### Debug APK (para testes)
No Android Studio:
- Build → Build Bundle(s) / APK(s) → Build APK(s)
- APK estará em: `android/app/build/outputs/apk/debug/`

### Release APK (produção)
1. Crie uma keystore:
```bash
keytool -genkey -v -keystore precificaai.keystore -alias precificaai -keyalg RSA -keysize 2048 -validity 10000
```

2. Configure em `android/app/build.gradle`

3. Build → Generate Signed Bundle / APK

---

## 🎯 Status Atual

✅ Capacitor instalado
✅ Plataforma Android adicionada
✅ Projeto sincronizado
✅ Android Studio abrindo
✅ Pronto para rodar!

**Próximo passo:** Aguarde o Gradle sync terminar e clique em ▶️ Run!
