"""
01_extraer_api.py
=================
Propósito:
    Descargar de forma automatizada y versionada los datos históricos desde la API
    de Datos Abiertos de Colombia (datos.gov.co / Socrata) para un hecho victimizante
    específico (tanto para 'casos' como para 'víctimas').

    Buenas Prácticas Implementadas:
    - Control temporal de descarga: incorpora la fecha de extracción (formato yyyy-mm-dd)
      en el nombre de los archivos para trazabilidad histórica.
    - Organización por formato: almacena archivos en subcarpetas dedicadas 'data/raw/json/'
      y 'data/raw/csv/', facilitando la distinción entre tipos de datos.
    - Dinamismo de formato: detecta si la URL es .json o .csv y permite alternar
      mediante el parámetro --formato.

Uso:
    python scripts/01_extraer_api.py --hecho reclutamiento_niños
    python scripts/01_extraer_api.py --hecho reclutamiento_niños --formato json
    python scripts/01_extraer_api.py --hecho reclutamiento_niños --formato csv
    python scripts/01_extraer_api.py --hecho violencia_sexual
"""

import os
import sys
import io
import json
import argparse
import time
from datetime import datetime
from pathlib import Path
import requests
import pandas as pd
import yaml
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# Constantes y Rutas
RUTA_CONFIG_API = Path("config/api_endpoints.yaml")
RUTA_CONFIG_GLOBAL = Path("config/config_global.yaml")
SODATA_APP_TOKEN = os.getenv("SODATA_APP_TOKEN", "")


def cargar_config():
    """Carga los parámetros de configuración de endpoints desde YAML."""
    print("[INFO] Cargando configuración de endpoints desde config/api_endpoints.yaml...")
    if not RUTA_CONFIG_API.exists():
        print(f"[ERROR] No se encontró el archivo de configuración: {RUTA_CONFIG_API}", file=sys.stderr)
        sys.exit(1)
        
    with open(RUTA_CONFIG_API, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    return config


def detectar_formato(url_endpoint):
    """
    Detecta si una URL apunta a .json o .csv basándose en la terminación de su ruta.
    """
    url_limpia = url_endpoint.split("?")[0].strip().lower()
    if url_limpia.endswith(".csv"):
        return "csv"
    elif url_limpia.endswith(".json"):
        return "json"
    else:
        return "json"


def ajustar_url_segun_formato(url_endpoint, formato_deseado="auto"):
    """
    Si el usuario solicita un formato explícito (json o csv), adapta dinámicamente
    la extensión final de la URL ya que en datos.gov.co la base es idéntica.
    Si formato_deseado es 'auto', respeta la extensión configurada en la URL.
    """
    formato_actual = detectar_formato(url_endpoint)
    if formato_deseado == "auto" or not formato_deseado:
        return url_endpoint, formato_actual

    formato_deseado = formato_deseado.lower().strip()
    partes = url_endpoint.split("?")
    url_base = partes[0]
    query_params = f"?{partes[1]}" if len(partes) > 1 else ""

    if formato_deseado == "csv" and url_base.lower().endswith(".json"):
        nueva_url = url_base[:-5] + ".csv" + query_params
        return nueva_url, "csv"
    elif formato_deseado == "json" and url_base.lower().endswith(".csv"):
        nueva_url = url_base[:-4] + ".json" + query_params
        return nueva_url, "json"
    else:
        return url_endpoint, formato_actual


def descargar_dataset(url_endpoint, app_token="", limite_por_lote=5000, timeout=120,
                      carpeta_data_raw=None, prefijo="casos", hecho="hecho",
                      fecha_descarga=None, formato_solicitado="auto"):
    """
    Descarga el dataset desde la API de datos abiertos.
    - Crea subcarpetas dedicadas 'data/raw/json/' y 'data/raw/csv/'.
    - Nombra los archivos con el estándar: {prefijo}_{hecho}_raw_{yyyy-mm-dd}.{ext}
    - Notifica si ya existía una descarga previa con esa misma fecha.
    """
    if fecha_descarga is None:
        fecha_descarga = datetime.now().strftime("%Y-%m-%d")

    url_efectiva, formato = ajustar_url_segun_formato(url_endpoint, formato_solicitado)
    
    # Subcarpetas organizadas por formato
    carpeta_json = carpeta_data_raw / "json"
    carpeta_csv = carpeta_data_raw / "csv"
    carpeta_json.mkdir(parents=True, exist_ok=True)
    carpeta_csv.mkdir(parents=True, exist_ok=True)

    # Nombres de archivo estandarizados con fecha yyyy-mm-dd
    nombre_archivo_json = f"{prefijo}_{hecho}_raw_{fecha_descarga}.json"
    nombre_archivo_csv = f"{prefijo}_{hecho}_raw_{fecha_descarga}.csv"
    ruta_salida_json = carpeta_json / nombre_archivo_json
    ruta_salida_csv = carpeta_csv / nombre_archivo_csv

    print(f"\n[INFO] Conectando a la API ({prefijo.upper()}):")
    print(f"       URL: {url_efectiva}")
    print(f"  [FORMATO DETECTADO] {formato.upper()}")
    print(f"  [FECHA DESCARGA]    {fecha_descarga}")

    if ruta_salida_json.exists() or ruta_salida_csv.exists():
        print(f"  [AVISO TEMPORAL] Ya existe un registro descargado el {fecha_descarga}.")
        print("                   Se actualizará el archivo con los datos más recientes de la API.")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) MemoriaHistoricaPredictiva/1.0"
    }
    
    if app_token and app_token.strip():
        headers["X-App-Token"] = app_token.strip()
        print("  [SEGURIDAD] Utilizando X-App-Token configurado.")
    else:
        print("  [AVISO] Conexión pública (sin token).")

    df_resultado = None
    datos_json_raw = None
    inicio_tiempo = time.time()

    try:
        # ======================================================================
        # RAMA 1: DESCARGA EN FORMATO JSON
        # ======================================================================
        if formato == "json":
            url_limpia = url_efectiva.split("?")[0].lower()
            
            # Caso A: Endpoints directos de consulta (/query.json)
            if "query.json" in url_limpia:
                print("  [DESCARGA JSON] Solicitando exportación JSON directa...")
                respuesta = requests.get(url_efectiva, headers=headers, timeout=timeout)
                
                if respuesta.status_code != 200:
                    print(f"  [ERROR] Código HTTP {respuesta.status_code}: {respuesta.text[:300]}", file=sys.stderr)
                    return None

                print("  [PROCESANDO] Parseando JSON recibido...")
                datos_json_raw = respuesta.json()
                if isinstance(datos_json_raw, list):
                    df_resultado = pd.DataFrame(datos_json_raw)
                elif isinstance(datos_json_raw, dict) and "data" in datos_json_raw:
                    df_resultado = pd.DataFrame(datos_json_raw["data"])
                else:
                    df_resultado = pd.DataFrame([datos_json_raw])

            # Caso B: Endpoint paginado tradicional SODA (/resource/xxxx-xxxx.json)
            else:
                print("  [PAGINACIÓN JSON] Descargando por lotes ($limit / $offset)...")
                registros_acumulados = []
                offset = 0

                while True:
                    params = {
                        "$limit": limite_por_lote,
                        "$offset": offset,
                        "$order": ":id"
                    }
                    resp = requests.get(url_efectiva, headers=headers, params=params, timeout=timeout)
                    if resp.status_code != 200:
                        print(f"  [ERROR] Falló lote offset={offset} (HTTP {resp.status_code})", file=sys.stderr)
                        break

                    lote = resp.json()
                    if not lote:
                        break

                    registros_acumulados.extend(lote)
                    print(f"  -> {len(registros_acumulados):,} registros acumulados...")

                    if len(lote) < limite_por_lote:
                        break
                    offset += limite_por_lote

                datos_json_raw = registros_acumulados
                if registros_acumulados:
                    df_resultado = pd.DataFrame(registros_acumulados)

        # ======================================================================
        # RAMA 2: DESCARGA EN FORMATO CSV
        # ======================================================================
        elif formato == "csv":
            print("  [DESCARGA CSV] Solicitando archivo CSV desde la API...")
            respuesta = requests.get(url_efectiva, headers=headers, timeout=timeout)
            
            if respuesta.status_code != 200:
                print(f"  [ERROR] Código HTTP {respuesta.status_code}: {respuesta.text[:300]}", file=sys.stderr)
                return None

            print("  [PROCESANDO] Parseando contenido CSV...")
            texto_csv = respuesta.text
            df_resultado = pd.read_csv(io.StringIO(texto_csv), low_memory=False)

        # ======================================================================
        # GUARDADO EN SUBCARPETAS DEDICADAS (JSON Y CSV)
        # ======================================================================
        if df_resultado is not None and not df_resultado.empty:
            tiempo_total = time.time() - inicio_tiempo
            print(f"  [ÉXITO] Descarga completada en {tiempo_total:.2f}s.")
            print(f"          Registros: {len(df_resultado):,}")
            print(f"          Columnas:  {len(df_resultado.columns)}")

            # 1. Guardar en carpeta json/
            if datos_json_raw is not None:
                with open(ruta_salida_json, "w", encoding="utf-8") as f:
                    json.dump(datos_json_raw, f, ensure_ascii=False, indent=2)
            else:
                df_resultado.to_json(ruta_salida_json, orient="records", force_ascii=False, indent=2)
            print(f"  [GUARDADO JSON] {ruta_salida_json}")

            # 2. Guardar en carpeta csv/
            df_resultado.to_csv(ruta_salida_csv, index=False, encoding="utf-8")
            print(f"  [GUARDADO CSV]  {ruta_salida_csv}")

            return df_resultado
        else:
            print("  [ALERTA] La API no retornó registros.", file=sys.stderr)
            return None

    except requests.exceptions.Timeout:
        print("  [ERROR] Tiempo de espera agotado (Timeout).", file=sys.stderr)
        return None
    except requests.exceptions.RequestException as e:
        print(f"  [ERROR] Error de conexión: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"  [ERROR] Excepción inesperada: {e}", file=sys.stderr)
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Extractor de datos de Memoria Histórica con versionado por fecha y subcarpetas"
    )
    parser.add_argument(
        "--hecho",
        type=str,
        required=True,
        choices=["reclutamiento_niños", "violencia_sexual"],
        help="Nombre del hecho victimizante a extraer"
    )
    parser.add_argument(
        "--formato",
        type=str,
        choices=["auto", "json", "csv"],
        default="auto",
        help="Formato solicitado: 'auto' (según URL en YAML), 'json' o 'csv'"
    )
    parser.add_argument(
        "--fecha",
        type=str,
        default=None,
        help="Fecha de la extracción en formato yyyy-mm-dd (por defecto: hoy)"
    )
    args = parser.parse_args()
    hecho = args.hecho
    formato_solicitado = args.formato
    
    # Fecha de descarga (yyyy-mm-dd)
    fecha_descarga = args.fecha if args.fecha else datetime.now().strftime("%Y-%m-%d")

    print("=" * 75)
    print(f"[ETAPA 01] EXTRACCIÓN DE DATOS API - HECHO: {hecho.upper()}")
    print(f"Fecha de descarga registrada: {fecha_descarga}")
    print(f"Modo de formato:              {formato_solicitado.upper()}")
    print("=" * 75)

    config = cargar_config()
    if hecho not in config.get("hechos", {}):
        print(f"[ERROR] El hecho '{hecho}' no existe en {RUTA_CONFIG_API}", file=sys.stderr)
        sys.exit(1)

    info_hecho = config["hechos"][hecho]
    carpeta_data_raw = Path(f"hechos/{hecho}/data/raw")

    limite_lote = config.get("api_general", {}).get("limite_por_pagina", 5000)
    timeout = config.get("api_general", {}).get("timeout_segundos", 120)

    # 1. Extracción Nivel Casos
    print("\n" + "-" * 60)
    print("--- 1. Extrayendo Nivel Casos ---")
    print("-" * 60)
    url_casos = info_hecho["casos"]["url_completa"]
    descargar_dataset(
        url_endpoint=url_casos,
        app_token=SODATA_APP_TOKEN,
        limite_por_lote=limite_lote,
        timeout=timeout,
        carpeta_data_raw=carpeta_data_raw,
        prefijo="casos",
        hecho=hecho,
        fecha_descarga=fecha_descarga,
        formato_solicitado=formato_solicitado
    )

    # 2. Extracción Nivel Víctimas
    print("\n" + "-" * 60)
    print("--- 2. Extrayendo Nivel Víctimas ---")
    print("-" * 60)
    url_victimas = info_hecho["victimas"]["url_completa"]
    descargar_dataset(
        url_endpoint=url_victimas,
        app_token=SODATA_APP_TOKEN,
        limite_por_lote=limite_lote,
        timeout=timeout,
        carpeta_data_raw=carpeta_data_raw,
        prefijo="victimas",
        hecho=hecho,
        fecha_descarga=fecha_descarga,
        formato_solicitado=formato_solicitado
    )

    print("\n" + "=" * 75)
    print(f"[INFO] Extracción finalizada exitosamente para: {hecho} ({fecha_descarga})")
    print("=" * 75)


if __name__ == "__main__":
    main()
