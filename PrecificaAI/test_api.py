import requests
import base64
import json

# Testar a API diretamente
url = "http://localhost:8000/api/health"
response = requests.get(url)
print("Health check:", response.json())

# Criar um payload de teste simples
# (você precisaria adicionar uma imagem real em base64 aqui)
print("\nServidor está respondendo corretamente!")
print("Agentes:", response.json()['agentes'])
