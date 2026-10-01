"""
Scraper de Convocatorias CAS para El Quipu PE
=============================================
Consulta la API y genera convocatorias.json con el DOMINIO REAL
de cada entidad para mostrar sus logos correctamente.
"""

import os
import json
import sys
import requests
from datetime import datetime
from urllib.parse import urlparse


# ============================================================
# CONFIGURACIÓN
# ============================================================
API_KEY = os.environ.get('API_KEY')
API_URL = 'https://convocatoriasestado.pe/api/v1/convocatorias/'
OUTPUT_FILE = 'convocatorias.json'

if not API_KEY:
    print("❌ ERROR: Falta la variable de entorno API_KEY")
    sys.exit(1)

print(f"🔑 API Key detectada: {API_KEY[:15]}...")


# ============================================================
# UTILIDADES
# ============================================================
def extraer_dominio(url):
    """Extrae el dominio principal de una URL."""
    if not url or not isinstance(url, str):
        return None
    try:
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        parsed = urlparse(url)
        hostname = parsed.hostname or ''
        # Quitar "www." del inicio
        if hostname.startswith('www.'):
            hostname = hostname[4:]
        return hostname or None
    except Exception:
        return None


def mapear_nivel(texto):
    """Detecta el nivel educativo desde el nombre del puesto."""
    t = (texto or '').lower()
    
    if any(x in t for x in [
        'titulad', 'universitari', 'profesional', 'ingenier',
        'abogad', 'médic', 'medic', 'contador', 'arquitect',
        'licenciad', 'doctor', 'químic', 'quimic', 'biólog',
        'psicólog', 'psicolog'
    ]):
        return 'titulado'
    if 'bachiller' in t:
        return 'bachiller'
    if any(x in t for x in [
        'técnic', 'tecnic', 'enfermer', 'obstetr', 'laborator',
        'asistente técnico', 'egresad'
    ]):
        return 'tecnico'
    if any(x in t for x in [
        'secundari', 'oficio', 'chofer', 'conductor', 'vigilan',
        'auxiliar', 'limpieza', 'operario'
    ]):
        return 'secundaria'
    return 'titulado'


# ============================================================
# MAPA DE DOMINIOS CONOCIDOS
# Muchas veces "enlace_entidad" no tiene el dominio directo,
# así que tenemos un mapa de las entidades más comunes.
# ============================================================
DOMINIOS_CONOCIDOS = {
    # Ministerios
    'minsa': 'minsa.gob.pe',
    'mef': 'mef.gob.pe',
    'minedu': 'minedu.gob.pe',
    'mininter': 'gob.pe',
    'mindef': 'gob.pe',
    'minjus': 'minjus.gob.pe',
    'mtpe': 'gob.pe',
    'produce': 'produce.gob.pe',
    'minem': 'minem.gob.pe',
    'mtc': 'mtc.gob.pe',
    'vivienda': 'gob.pe',
    'mimp': 'mimp.gob.pe',
    'minam': 'minam.gob.pe',
    'cultura': 'gob.pe',
    'midis': 'midis.gob.pe',
    'rree': 'rree.gob.pe',
    'mincetur': 'mincetur.gob.pe',
    'midagri': 'midagri.gob.pe',
    'pcm': 'gob.pe',
    
    # Organismos
    'sunat': 'sunat.gob.pe',
    'sunarp': 'sunarp.gob.pe',
    'reniec': 'reniec.gob.pe',
    'onpe': 'onpe.gob.pe',
    'jne': 'jne.gob.pe',
    'onpe': 'onpe.gob.pe',
    'contraloria': 'contraloria.gob.pe',
    'servir': 'servir.gob.pe',
    'sbs': 'sbs.gob.pe',
    'bcrp': 'bcrp.gob.pe',
    'sbn': 'sbn.gob.pe',
    'senasa': 'senasa.gob.pe',
    'oefa': 'oefa.gob.pe',
    'sernanp': 'sernanp.gob.pe',
    'senamhi': 'senamhi.gob.pe',
    'inei': 'inei.gob.pe',
    'indeci': 'indeci.gob.pe',
    'cenepred': 'cenepred.gob.pe',
    'ipd': 'ipd.gob.pe',
    'inacal': 'inacal.gob.pe',
    'promperu': 'promperu.gob.pe',
    'proinversion': 'proinversion.gob.pe',
    
    # Poderes
    'poder judicial': 'pj.gob.pe',
    'pj': 'pj.gob.pe',
    'congreso': 'congreso.gob.pe',
    'ministerio publico': 'mpfn.gob.pe',
    'fiscalia': 'mpfn.gob.pe',
    'defensoria': 'defensoria.gob.pe',
    'tribunal constitucional': 'tc.gob.pe',
    
    # Bancos y otros
    'banco de la nacion': 'bn.com.pe',
    'bn': 'bn.com.pe',
    'agrobanco': 'agrobanco.com.pe',
    'cofide': 'cofide.com.pe',
    'fonafe': 'fonafe.gob.pe',
    
    # Otros conocidos
    'essalud': 'essalud.gob.pe',
    'senati': 'senati.edu.pe',
    'pronabec': 'pronabec.gob.pe',
    'sencico': 'sencico.gob.pe',
    'sunedu': 'sunedu.gob.pe',
    'osinergmin': 'osinergmin.gob.pe',
    'osiptel': 'osiptel.gob.pe',
    'osce': 'osce.gob.pe',
    'indecopi': 'indecopi.gob.pe',
    'perupetro': 'perupetro.com.pe',
    'petroperu': 'petroperu.com.pe',
    'enapu': 'enapu.com.pe',
    'sedapal': 'sedapal.com.pe',
    'luz del sur': 'luzdelsur.com.pe',
    'enel': 'enel.pe',
    'electroperu': 'electroperu.com.pe',
}


def buscar_dominio(entidad, url_enlace):
    """
    Busca el dominio de una entidad siguiendo este orden:
    1. Extraer de la URL del enlace (si existe)
    2. Buscar en el diccionario de dominios conocidos
    3. Devolver None si no se encuentra
    """
    # 1. Intentar extraer de la URL real
    dominio = extraer_dominio(url_enlace)
    if dominio and '.gob.pe' in dominio or (dominio and '.com.pe' in dominio):
        return dominio
    
    # 2. Buscar en el diccionario
    entidad_lower = (entidad or '').lower()
    for clave, dom in DOMINIOS_CONOCIDOS.items():
        if clave in entidad_lower:
            return dom
    
    # 3. Si la URL tiene algún dominio válido, usarlo
    if dominio:
        return dominio
    
    return None


# ============================================================
# CONSULTAR LA API
# ============================================================
print(f"\n📡 Consultando la API...")

params = {'vigentes': 'true', 'por_pagina': '100'}
headers = {
    'Authorization': f'Bearer {API_KEY}',
    'Accept': 'application/json'
}

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
# TRANSFORMAR DATOS
# ============================================================
print(f"\n🔄 Transformando datos...")

convocatorias = []
con_logo = 0
sin_logo = 0

for c in resultados:
    entidad = c.get('entidad', 'Entidad Pública')
    url_enlace = c.get('enlace_entidad') or c.get('url') or ''
    
    # Buscar el dominio
    dominio = buscar_dominio(entidad, url_enlace)
    
    # Generar URL del logo
    logo_url = ''
    if dominio:
        logo_url = f'https://www.google.com/s2/favicons?domain={dominio}&sz=128'
        con_logo += 1
    else:
        sin_logo += 1
    
    region = c.get('departamento', 'Nacional')
    if region and len(region) > 30:
        region = region[:30]
    
    convocatorias.append({
        'codigo': c.get('numero_convocatoria', 'CAS'),
        'entidad': entidad,
        'logoUrl': logo_url,
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
        'url': url_enlace or 'https://www.gob.pe',
        'vigente': c.get('vigente', True)
    })

print(f"✅ {len(convocatorias)} convocatorias transformadas")
print(f"   🎨 Con logo: {con_logo}")
print(f"   ⚪ Sin logo: {sin_logo}")


# ============================================================
# GUARDAR JSON
# ============================================================
output = {
    'actualizado': datetime.now().isoformat(),
    'fuente': 'convocatoriasestado.pe',
    'total': len(convocatorias),
    'convocatorias': convocatorias
}

with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"\n💾 Guardado: {OUTPUT_FILE}")
print(f"✅ ¡Todo listo!\n")
