"""
Scraper de convocatorias CAS para El Quipu PE.
Corre en GitHub Actions todos los días.
Genera convocatorias.json que la web lee.
"""

import os
import json
import requests
from datetime import datetime

# Configuración
API_KEY = os.environ.get('API_KEY')
API_URL = 'https://convocatoriasestado.pe/api/v1/convocatorias/'

if not API_KEY:
    raise ValueError("❌ Falta la API_KEY en las variables de entorno")

print(f"🔑 API Key: {API_KEY[:15]}...")
print(f"📡 Consultando la API...")

# Consultar la API
params = {
    'vigentes': 'true',
    'por_pagina': '100'
}

headers = {
    'Authorization': f'Bearer {API_KEY}',
    'Accept': 'application/json'
}

try:
    r = requests.get(API_URL, params=params, headers=headers, timeout=30)
    r.raise_for_status()
    data = r.json()
    print(f"✅ Respuesta recibida: {data.get('total', 0)} convocatorias en total")
except Exception as e:
    print(f"❌ Error: {e}")
    raise

# Transformar al formato que usa la web
def mapear_nivel(texto):
    t = (texto or '').lower()
    if any(x in t for x in ['titulad', 'universitari', 'profesional', 'ingenier', 'abogad', 'médic', 'contador', 'arquitect']):
        return 'titulado'
    if 'bachiller' in t:
        return 'bachiller'
    if any(x in t for x in ['técnic', 'tecnico', 'enfermer']):
        return 'tecnico'
    return 'secundaria'

resultados = data.get('resultados', [])

convocatorias = []
for c in resultados:
    entidad = c.get('entidad', 'Entidad Pública')
    slug = ''.join(ch for ch in entidad.lower() if ch.isalnum())[:30]
    
    convocatorias.append({
        'codigo': c.get('numero_convocatoria', 'CAS'),
        'entidad': entidad,
        'logoUrl': f'https://www.google.com/s2/favicons?domain={slug}.gob.pe&sz=128',
        'titulo': c.get('puesto', 'Puesto no especificado'),
        'descripcion': f"Convocatoria CAS publicada por {entidad}. {c.get('vacantes', 1)} vacante(s) disponible(s).",
        'region': c.get('departamento', 'Nacional'),
        'nivel': mapear_nivel(c.get('puesto', '')),
        'sueldoMin': c.get('remuneracion', 0),
        'sueldoMax': c.get('remuneracion', 0),
        'vacantes': c.get('vacantes', 1),
        'publicacion': c.get('fecha_inicio', ''),
        'cierre': c.get('fecha_fin', ''),
        'url': c.get('enlace_entidad', f'https://www.gob.pe'),
        'vigente': c.get('vigente', True)
    })

# Guardar JSON con metadata
salida = {
    'actualizado': datetime.now().isoformat(),
    'total': len(convocatorias),
    'convocatorias': convocatorias
}

with open('convocatorias.json', 'w', encoding='utf-8') as f:
    json.dump(salida, f, ensure_ascii=False, indent=2)

print(f"✅ {len(convocatorias)} convocatorias guardadas en convocatorias.json")
