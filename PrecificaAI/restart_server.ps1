# Script de Restart do Servidor PrecificaAI
# Garante que o servidor seja reiniciado corretamente

Write-Host "🔄 Reiniciando PrecificaAI Server..." -ForegroundColor Cyan

# 1. Matar todos os processos Python do PrecificaAI
Write-Host "1️⃣ Finalizando processos antigos..." -ForegroundColor Yellow
$procs = Get-Process python -ErrorAction SilentlyContinue | Where-Object {$_.Path -like "*PrecificaAI*"}
if ($procs) {
    $procs | Stop-Process -Force
    Write-Host "   ✅ $($procs.Count) processo(s) finalizado(s)" -ForegroundColor Green
} else {
    Write-Host "   ℹ️ Nenhum processo rodando" -ForegroundColor Gray
}

# 2. Liberar porta 8000
Write-Host "2️⃣ Liberando porta 8000..." -ForegroundColor Yellow
$conn = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($conn) {
    $pid = $conn.OwningProcess | Select-Object -First 1
    Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
    Write-Host "   ✅ Porta 8000 liberada (PID: $pid)" -ForegroundColor Green
} else {
    Write-Host "   ✅ Porta 8000 já está livre" -ForegroundColor Green
}

# 3. Aguardar liberação
Write-Host "3️⃣ Aguardando 3 segundos..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

# 4. Iniciar servidor
Write-Host "4️⃣ Iniciando servidor..." -ForegroundColor Yellow
cd "x:\Dev\TEXTOJOIA\Antigravity\PrecificaAI"
.\.venv\Scripts\python.exe server.py

Write-Host "✅ Servidor iniciado!" -ForegroundColor Green
