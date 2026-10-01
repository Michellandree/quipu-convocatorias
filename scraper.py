"""
Scraper de Convocatorias CAS para El Quipu PE - v2.0
=====================================================
Con detección exacta de:
- URL específica de cada convocatoria (campo 'url')
- Dominio real de cada entidad (desde enlace_entidad + mapa)
"""

import os
import json
import sys
import requests
from datetime import datetime
from urllib.parse import urlparse


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
# La API devuelve el campo "url" con el path exacto.
# Solo hay que agregar el dominio base.
# ============================================================
def obtener_url_convocatoria(c):
    url = c.get('url', '')
    if url:
        url = url.strip()
        if url.startswith('/'):
            return BASE_URL + url
        if url.startswith('http'):
            return url
    # Fallback: página general de la entidad
    return c.get('enlace_entidad', 'https://www.gob.pe/convocatorias-de-trabajo')


# ============================================================
# ✅ DOMINIO REAL DE LA ENTIDAD
# Estrategia:
# 1. Extraer del subdominio de enlace_entidad (ej: practicantes.anin.gob.pe → anin.gob.pe)
# 2. Extraer de la ruta de gob.pe (ej: gob.pe/ositran → ositran.gob.pe)
# 3. Buscar en el mapa de entidades conocidas
# ============================================================
MAPA_ENTIDADES = {
    # Ministerios
    'minsa': 'minsa.gob.pe', 'mef': 'mef.gob.pe', 'minedu': 'minedu.gob.pe',
    'mininter': 'mininter.gob.pe', 'mindef': 'mindef.gob.pe',
    'minjus': 'minjus.gob.pe', 'mtpe': 'trabajo.gob.pe',
    'produce': 'produce.gob.pe', 'minem': 'minem.gob.pe',
    'mtc': 'mtc.gob.pe', 'vivienda': 'vivienda.gob.pe',
    'mimp': 'mimp.gob.pe', 'minam': 'minam.gob.pe',
    'cultura': 'cultura.gob.pe', 'midis': 'midis.gob.pe',
    'rree': 'rree.gob.pe', 'mincetur': 'mincetur.gob.pe',
    'midagri': 'midagri.gob.pe', 'pcm': 'gob.pe',
    
    # Organismos autónomos
    'sunat': 'sunat.gob.pe', 'sunarp': 'sunarp.gob.pe',
    'reniec': 'reniec.gob.pe', 'onpe': 'onpe.gob.pe',
    'jne': 'jne.gob.pe', 'contraloria': 'contraloria.gob.pe',
    'servir': 'servir.gob.pe', 'sbs': 'sbs.gob.pe',
    'bcrp': 'bcrp.gob.pe', 'sbn': 'sbn.gob.pe',
    'senasa': 'senasa.gob.pe', 'oefa': 'oefa.gob.pe',
    'sernanp': 'sernanp.gob.pe', 'senamhi': 'senamhi.gob.pe',
    'inei': 'inei.gob.pe', 'indeci': 'indeci.gob.pe',
    'cenepred': 'cenepred.gob.pe', 'ipd': 'ipd.gob.pe',
    'inacal': 'inacal.gob.pe', 'promperu': 'promperu.gob.pe',
    'proinversion': 'proinversion.gob.pe',
    
    # Poderes del Estado
    'poder judicial': 'pj.gob.pe', 'congreso': 'congreso.gob.pe',
    'fiscalia': 'mpfn.gob.pe', 'ministerio publico': 'mpfn.gob.pe',
    'defensoria': 'defensoria.gob.pe', 'tribunal constitucional': 'tc.gob.pe',
    
    # Bancos
    'banco de la nacion': 'bn.com.pe', 'agrobanco': 'agrobanco.com.pe',
    'cofide': 'cofide.com.pe', 'fonafe': 'fonafe.gob.pe',
    
    # Infraestructura y transporte
    'autoridad nacional de infraestructura': 'anin.gob.pe',
    'anin': 'anin.gob.pe',
    'ositran': 'ositran.gob.pe',
    'sutran': 'sutran.gob.pe',
    'osiptel': 'osiptel.gob.pe',
    'osinergmin': 'osinergmin.gob.pe',
    'osce': 'osce.gob.pe',
    'oefa': 'oefa.gob.pe',
    
    # Otros
    'essalud': 'essalud.gob.pe', 'senati': 'senati.edu.pe',
    'pronabec': 'pronabec.gob.pe', 'sencico': 'sencico.gob.pe',
    'sunedu': 'sunedu.gob.pe', 'indecopi': 'indecopi.gob.pe',
    'perupetro': 'perupetro.com.pe', 'petroperu': 'petroperu.com.pe',
    'sedapal': 'sedapal.com.pe', 'pronied': 'pronied.gob.pe',
    'cofopri': 'cofopri.gob.pe', 'onp': 'onp.gob.pe',
    'migraciones': 'migraciones.gob.pe', 'ana': 'ana.gob.pe',
    'igp': 'igp.gob.pe', 'imarpe': 'imarpe.gob.pe',
    'sanipes': 'sanipes.gob.pe', 'digesa': 'digesa.minsa.gob.pe',
}


def extraer_dominio(c):
    """Extrae el dominio principal de la entidad."""
    entidad_lower = (c.get('entidad') or '').lower()
    
    # 1. Buscar en el mapa por nombre de entidad (más confiable)
    for clave, dominio in sorted(MAPA_ENTIDADES.items(), key=lambda x: -len(x[0])):
        if clave in entidad_lower:
            return dominio
    
    # 2. Extraer del enlace_entidad
    enlace = c.get('enlace_entidad', '')
    if enlace:
        try:
            if not enlace.startswith(('http://', 'https://')):
                enlace = 'https://' + enlace
            parsed = urlparse(enlace)
            hostname = (parsed.hostname or '').lower()
            
            # Caso 1: subdominio.gob.pe (ej: practicantes.anin.gob.pe)
            if hostname.endswith('.gob.pe') and hostname.count('.') >= 2:
                partes = hostname.split('.')
                # Tomar los últimos 3: ej [practicantes, anin, gob, pe] → anin.gob.pe
                if len(partes) >= 3 and partes[-2] == 'gob' and partes[-1] == 'pe':
                    return '.'.join(partes[-3:])
            
            # Caso 2: www.gob.pe/ositran (extraer de la ruta)
            if hostname in ('www.gob.pe', 'gob.pe'):
                path = parsed.path or ''
                partes_path = [p for p in path.split('/') if p]
                if 'institucion' in partes_path:
                    idx = partes_path.index('institucion')
                    if idx + 1 < len(partes_path):
                        slug = partes_path[idx + 1]
                        return f'{slug}.gob.pe'
            
            # Caso 3: dominio propio (ej: bn.com.pe, petroperu.com.pe)
            if hostname and '.' in hostname and 'gob.pe' not in hostname:
                return hostname.replace('www.', '')
        except Exception:
            pass
    
    return None


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
print(f"\n🔄 Transformando...")

convocatorias = []
con_dominio = 0

for c in resultados:
    entidad = c.get('entidad', 'Entidad Pública')
    url_conv = obtener_url_convocatoria(c)
    dominio = extraer_dominio(c)
    
    if dominio:
        con_dominio += 1
    
    region = c.get('departamento', 'Nacional')
    if region and len(region) > 30:
        region = region[:30]
    
    convocatorias.append({
        'codigo': c.get('numero_convocatoria', 'CAS'),
        'entidad': entidad,
        'dominio': dominio or '',
        'titulo': c.get('puesto', 'Puesto no especificado'),
        'descripcion': f"Convocatoria CAS publicada por {entidad}. {c.get('vacantes', 1)} vacante(s) disponible(s).",
        'region': region,
        'nivel': mapear_nivel(c.get('puesto', '')),
        'sueldoMin': c.get('remuneracion', 0) or 0,
        'sueldoMax': c.get('remuneracion', 0) or 0,
        'vacantes': c.get('vacantes', 1) or 1,
        'publicacion': c.get('fecha_inicio', ''),
        'cierre': c.get('fecha_fin', ''),
        'url': url_conv,
        'vigente': c.get('vigente', True)
    })

print(f"✅ {len(convocatorias)} transformadas")
print(f"🎯 Con dominio detectado: {con_dominio}")
print(f"⚪ Sin dominio: {len(convocatorias) - con_dominio}")

print(f"\n📋 Muestra de URLs y dominios:")
for c in convocatorias[:5]:
    print(f"   [{c['dominio'] or 'SIN DOMINIO'}] {c['entidad'][:30]}")
    print(f"      → {c['url'][:90]}")


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
