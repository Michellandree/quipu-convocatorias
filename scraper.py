"""
Scraper de Convocatorias CAS para El Quipu PE - v4.0
=====================================================
✅ URL hacia la FUENTE OFICIAL (enlace_entidad)
✅ Sin logos (diseño limpio)
"""

import os
import json
import sys
import requests
from datetime import datetime


API_KEY = os.environ.get('API_KEY')
API_URL = 'https://convocatoriasestado.pe/api/v1/convocatorias/'
OUTPUT_FILE = 'convocatorias.json'

if not API_KEY:
    print("❌ ERROR: Falta API_KEY")
    sys.exit(1)

print(f"🔑 API Key: {API_KEY[:15]}...")


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
# TRANSFORMAR — USA enlace_entidad COMO URL PRINCIPAL
# ============================================================
print(f"\n🔄 Transformando...")

convocatorias = []
con_oficial = 0
sin_oficial = 0

for c in resultados:
    entidad = c.get('entidad', 'Entidad Pública')
    
    # 🎯 PRIORIDAD: enlace_entidad (fuente oficial)
    url_oficial = c.get('enlace_entidad', '').strip()
    
    # Fallback: si no hay enlace_entidad, usar el url de la API
    if not url_oficial:
        url_api = c.get('url', '')
        if url_api.startswith('/'):
            url_oficial = 'https://convocatoriasestado.pe' + url_api
        elif url_api.startswith('http'):
            url_oficial = url_api
        else:
            url_oficial = 'https://www.gob.pe/convocatorias-de-trabajo'
        sin_oficial += 1
    else:
        con_oficial += 1
    
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
        'url': url_oficial,  # ← URL OFICIAL DE LA ENTIDAD
        'vigente': c.get('vigente', True)
    })

print(f"✅ {len(convocatorias)} transformadas")
print(f"🎯 Con enlace oficial: {con_oficial}")
print(f"⚠️  Sin enlace oficial (fallback): {sin_oficial}")

print(f"\n📋 Muestra de URLs (deben ir a .gob.pe de cada entidad):")
print(f"{'='*70}")
for c in convocatorias[:5]:
    print(f"   {c['entidad'][:35]}")
    print(f"   → {c['url']}")


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

print(f"\n💾 {OUTPUT_FILE} guardado")
print(f"✅ ¡Listo!\n")
