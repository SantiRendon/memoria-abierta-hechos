"""
01_extraer_api.py
=================
Propósito:
    Descargar de forma automatizada y dinámica los datos históricos desde la API
    de Datos Abiertos de Colombia (datos.gov.co / Socrata) para un hecho victimizante
    específico (tanto para 'casos' como para 'víctimas').

    Dinamismo de Formato:
    - Analiza dinámicamente si la URL configurada termina en '.json' o '.csv'.
    - Permite alternar extensiones entre JSON y CSV directamente desde el CLI (--formato).
    - Guarda los archivos crudos en 'data/raw/' tanto en su formato nativo (.json / .csv)
      como en formato complementario para total interoperabilidad.

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
                      carpeta_salida=None, nombre_base=None, formato_solicitado="auto"):
    """
    Descarga el dataset desde la API de datos abiertos gestionando dinámicamente
    formatos JSON y CSV, guardando el archivo nativo según la URL y un espejo
    para máxima compatibilidad.
    """
    url_efectiva, formato = ajustar_url_segun_formato(url_endpoint, formato_solicitado)
    
    print(f"\n[INFO] Conectando a la API:")
    print(f"       URL: {url_efectiva}")
    print(f"  [FORMATO DETECTADO] {formato.upper()}")

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
            
            # Caso A: Endpoints de consulta directa (/query.json)
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
        # GUARDADO EN DISCO DINÁMICO (JSON Y CSV)
        # ======================================================================
        if df_resultado is not None and not df_resultado.empty:
            tiempo_total = time.time() - inicio_tiempo
            print(f"  [ÉXITO] Descarga completada en {tiempo_total:.2f}s.")
            print(f"          Registros: {len(df_resultado):,}")
            print(f"          Columnas:  {len(df_resultado.columns)}")

            if carpeta_salida and nombre_base:
                carpeta_salida.mkdir(parents=True, exist_ok=True)
                
                ruta_json = carpeta_salida / f"{nombre_base}.json"
                ruta_csv = carpeta_salida / f"{nombre_base}.csv"

                # 1. Guardar archivo JSON
                if datos_json_raw is not None:
                    with open(ruta_json, "w", encoding="utf-8") as f:
                        json.dump(datos_json_raw, f, ensure_ascii=False, indent=2)
                else:
                    # Si vino en CSV, exportar también a JSON para tener ambos disponibles
                    df_resultado.to_json(ruta_json, orient="records", force_ascii=False, indent=2)
                print(f"  [GUARDADO JSON] {ruta_json}")

                # 2. Guardar archivo CSV
                df_resultado.to_csv(ruta_csv, index=False, encoding="utf-8")
                print(f"  [GUARDADO CSV]  {ruta_csv}")

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
        description="Extractor dinámico de datos de Memoria Histórica (JSON y CSV)"
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
        help="Formato solicitado: 'auto' (según la URL en YAML), 'json' o 'csv'"
    )
    args = parser.parse_args()
    hecho = args.hecho
    formato_solicitado = args.formato

    print("=" * 70)
    print(f"[ETAPA 01] EXTRACCIÓN DINÁMICA DE DATOS API - HECHO: {hecho.upper()}")
    print(f"Modo de formato: {formato_solicitado.upper()}")
    print("=" * 70)

    config = cargar_config()
    if hecho not in config.get("hechos", {}):
        print(f"[ERROR] El hecho '{hecho}' no existe en {RUTA_CONFIG_API}", file=sys.stderr)
        sys.exit(1)

    info_hecho = config["hechos"][hecho]
    carpeta_data_raw = Path(f"hechos/{hecho}/data/raw")

    limite_lote = config.get("api_general", {}).get("limite_por_pagina", 5000)
    timeout = config.get("api_general", {}).get("timeout_segundos", 120)

    # 1. Extracción Nivel Casos
    print("\n" + "-" * 55)
    print("--- 1. Extrayendo Nivel Casos ---")
    print("-" * 55)
    url_casos = info_hecho["casos"]["url_completa"]
    descargar_dataset(
        url_endpoint=url_casos,
        app_token=SODATA_APP_TOKEN,
        limite_por_lote=limite_lote,
        timeout=timeout,
        carpeta_salida=carpeta_data_raw,
        nombre_base=f"casos_{hecho}_raw",
        formato_solicitado=formato_solicitado
    )

    # 2. Extracción Nivel Víctimas
    print("\n" + "-" * 55)
    print("--- 2. Extrayendo Nivel Víctimas ---")
    print("-" * 55)
    url_victimas = info_hecho["victimas"]["url_completa"]
    descargar_dataset(
        url_endpoint=url_victimas,
        app_token=SODATA_APP_TOKEN,
        limite_por_lote=limite_lote,
        timeout=timeout,
        carpeta_salida=carpeta_data_raw,
        nombre_base=f"victimas_{hecho}_raw",
        formato_solicitado=formato_solicitado
    )

    print("\n" + "=" * 70)
    print(f"[INFO] Proceso de extracción dinámico completado para: {hecho}")
    print("=" * 70)


if __name__ == "__main__":
    main()
