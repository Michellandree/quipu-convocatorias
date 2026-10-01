"""
Scraper de Convocatorias CAS para El Quipu PE - v4.1
=====================================================
✅ Maneja valores None/null correctamente
✅ URL hacia la FUENTE OFICIAL (enlace_entidad)
✅ Fallback robusto
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
    resultados = data.get('resultados', []) or []
    print(f"✅ {len(resultados)} convocatorias recibidas")
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)


# ============================================================
# TRANSFORMAR
# ============================================================
print(f"\n🔄 Transformando...")

convocatorias = []
con_oficial = 0
con_api = 0
sin_url = 0

for c in resultados:
    entidad = (c.get('entidad') or 'Entidad Pública').strip()
    
    # 🎯 ESTRATEGIA DE URL EN CASCADA:
    # 1. enlace_entidad (fuente oficial - página de la entidad)
    # 2. url (convocatoria específica en el agregador)
    # 3. Fallback genérico
    
    url_oficial = (c.get('enlace_entidad') or '').strip()
    
    if url_oficial and url_oficial.startswith(('http://', 'https://')):
        # ✅ Tenemos enlace oficial
        url_final = url_oficial
        con_oficial += 1
        origen = 'oficial'
    else:
        # Fallback: usar el campo url de la API
        url_api = (c.get('url') or '').strip()
        
        if url_api.startswith('/'):
            url_final = 'https://convocatoriasestado.pe' + url_api
            con_api += 1
            origen = 'api'
        elif url_api.startswith('http'):
            url_final = url_api
            con_api += 1
            origen = 'api'
        else:
            url_final = 'https://www.gob.pe/convocatorias-de-trabajo'
            sin_url += 1
            origen = 'fallback'
    
    region = (c.get('departamento') or 'Nacional').strip()
    if len(region) > 30:
        region = region[:30]
    
    puesto = (c.get('puesto') or 'Puesto no especificado').strip()
    
    convocatorias.append({
        'codigo': c.get('numero_convocatoria') or 'CAS',
        'entidad': entidad,
        'titulo': puesto,
        'descripcion': f"Convocatoria publicada por {entidad}. {c.get('vacantes', 1)} vacante(s) disponible(s).",
        'region': region,
        'nivel': mapear_nivel(puesto),
        'sueldoMin': c.get('remuneracion') or 0,
        'sueldoMax': c.get('remuneracion') or 0,
        'vacantes': c.get('vacantes') or 1,
        'publicacion': c.get('fecha_inicio') or '',
        'cierre': c.get('fecha_fin') or '',
        'url': url_final,
        'vigente': c.get('vigente', True)
    })

print(f"✅ {len(convocatorias)} convocatorias transformadas")
print(f"🎯 Con enlace oficial (fuente .gob.pe): {con_oficial}")
print(f"🔗 Con URL de la API: {con_api}")
print(f"⚠️  Sin URL (fallback): {sin_url}")

print(f"\n📋 Muestra de URLs finales:")
print(f"{'='*70}")
for c in convocatorias[:5]:
    print(f"   {c['entidad'][:38]}")
    print(f"   → {c['url']}")
    print()


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

print(f"💾 {OUTPUT_FILE} guardado")
print(f"✅ ¡Listo!\n")
