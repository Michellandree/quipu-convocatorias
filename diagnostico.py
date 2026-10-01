"""
DIAGNÓSTICO - Ver exactamente qué datos devuelve la API
para identificar el campo correcto de la URL y del dominio.
"""

import os
import json
import requests

API_KEY = os.environ.get('API_KEY')
API_URL = 'https://convocatoriasestado.pe/api/v1/convocatorias/'

headers = {
    'Authorization': f'Bearer {API_KEY}',
    'Accept': 'application/json'
}

params = {'vigentes': 'true', 'por_pagina': '3'}

print("=" * 70)
print("🔍 DIAGNÓSTICO DE LA API")
print("=" * 70)

r = requests.get(API_URL, params=params, headers=headers, timeout=30)
print(f"\n📡 Status: {r.status_code}")
print(f"\n📄 Respuesta (primeras 5 convocatorias):\n")

data = r.json()
resultados = data.get('resultados', [])

for i, conv in enumerate(resultados[:5], 1):
    print(f"\n{'='*70}")
    print(f"CONVOCATORIA #{i}")
    print(f"{'='*70}")
    print(json.dumps(conv, indent=2, ensure_ascii=False))
    print()

# Guardar el resultado completo
with open('diagnostico.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("\n✅ Guardado en diagnostico.json")
