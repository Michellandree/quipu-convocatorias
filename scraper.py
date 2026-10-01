"""
Scraper de Convocatorias CAS para El Quipu PE - v3.0
=====================================================
URL específica correcta + sin logos (para diseño limpio)
"""

import os
import json
import sys
import requests
from datetime import datetime


API_KEY = os.environ.get('API_KEY')
API_URL = 'https://convocatoriasestado.pe/api/v1/convocatorias/'
BASE_URL = 'https://convocatoriasestado.pe'
OUTPUT_FILE = 'convocatorias.json'

if not API_KEY:
    print("❌ ERROR: Falta API_KEY")
    sys.exit(1)

print(f"🔑 API Key: {API_KEY[:15]}...")


# ============================================================
# ✅ URL ESPECÍFICA DE LA CONVOCATORIA
# ============================================================
def obtener_url_convocatoria(c):
    """
    Construye la URL exacta de la convocatoria.
    La API devuelve: "url": "/convocatoria/18840-practicante-profesional/"
    Resultado: "https://convocatoriasestado.pe/convocatoria/18840-practicante-profesional/"
    """
    url = c.get('url', '')
    
    if url:
        url = url.strip()
        # Path relativo → agregar dominio base
        if url.startswith('/'):
            url_final = BASE_URL + url
            print(f"   ✅ URL construida: {url_final[:80]}")
            return url_final
        # URL absoluta → devolver tal cual
        if url.startswith('http'):
            return url
    
    # Fallback: enlace de la entidad (página general)
    print(f"   ⚠️ Sin campo 'url', usando enlace_entidad")
    return c.get('enlace_entidad', 'https://www.gob.pe/convocatorias-de-trabajo')


# ============================================================
# MAPEO DE NIVEL
# ============================================================
def mapear_nivel(texto):
    t = (texto or '').lower()
    if any(x in t for x in ['titulad', 'universitari', 'profesional', 'ingenier',
                            'abogad', 'médic', 'medic', 'contador', 'arquitect',
                            'licenciad', 'doctor', 'químic', 'biólog', 'psicólog',
                            'derecho', 'practicante profesional']):
        return 'titulado'
    if 'bachiller' in t:
        return 'bachiller'
    if any(x in t for x in ['técnic', 'tecnic', 'enfermer', 'obstetr', 'laborator', 'egresad']):
        return 'tecnico'
    if any(x in t for x in ['secundari', 'oficio', 'chofer', 'conductor', 'vigilan', 'auxiliar']):
        return 'secundaria'
    return 'titulado'


# ============================================================
# CONSULTAR LA API
# ============================================================
print(f"\n📡 Consultando la API...")

params = {'vigentes': 'true', 'por_pagina': '100'}
headers = {'Authorization': f'Bearer {API_KEY}', 'Accept': 'application/json'}

try:
    response = requests.get(API_URL, params=params, headers=headers, timeout=30)
    response.raise_for_status()
    data = response.json()
    resultados = data.get('resultados', [])
    print(f"✅ {len(resultados)} convocatorias recibidas")
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)


# ============================================================
# TRANSFORMAR
# ============================================================
print(f"\n🔄 Transformando primeras 3 para verificar URLs:")
print(f"{'='*70}")

convocatorias = []

for i, c in enumerate(resultados):
    entidad = c.get('entidad', 'Entidad Pública')
    
    # Mostrar las primeras 3 URLs para verificar
    if i < 3:
        print(f"\n#{i+1} {entidad[:40]}")
        print(f"   url (API): {c.get('url', 'NO TIENE')}")
    
    url_conv = obtener_url_convocatoria(c)
    
    region = c.get('departamento', 'Nacional')
    if region and len(region) > 30:
        region = region[:30]
    
    convocatorias.append({
        'codigo': c.get('numero_convocatoria', 'CAS'),
        'entidad': entidad,
        'titulo': c.get('puesto', 'Puesto no especificado'),
        'descripcion': f"Convocatoria publicada por {entidad}. {c.get('vacantes', 1)} vacante(s) disponible(s).",
        'region': region,
        'nivel': mapear_nivel(c.get('puesto', '')),
        'sueldoMin': c.get('remuneracion', 0) or 0,
        'sueldoMax': c.get('remuneracion', 0) or 0,
        'vacantes': c.get('vacantes', 1) or 1,
        'publicacion': c.get('fecha_inicio', ''),
        'cierre': c.get('fecha_fin', ''),
        'url': url_conv,  # ← URL específica
        'vigente': c.get('vigente', True)
    })

print(f"\n{'='*70}")
print(f"✅ {len(convocatorias)} convocatorias transformadas")

# Verificar URLs guardadas
print(f"\n📋 Muestra de URLs guardadas:")
for c in convocatorias[:3]:
    print(f"   {c['url']}")


# ============================================================
# GUARDAR
# ============================================================
output = {
    'actualizado': datetime.now().isoformat(),
    'fuente': 'convocatoriasestado.pe',
    'total': len(convocatorias),
    'convocatorias': convocatorias
}

with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"\n💾 {OUTPUT_FILE} guardado con URLs específicas")
print(f"✅ ¡Listo!\n")
