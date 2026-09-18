"""
03_unificar_datos.py
====================
Propósito:
    Limpiar, normalizar y unificar los datos de Casos y Víctimas mediante su
    clave común (id_caso). Genera el dataset maestro en 'data/processed/'.

Uso:
    python scripts/03_unificar_datos.py --hecho reclutamiento_niños
    python scripts/03_unificar_datos.py --hecho violencia_sexual
"""

import os
import sys
import argparse
from pathlib import Path
import pandas as pd
import numpy as np


def limpiar_y_estandarizar(df):
    """
    Estandariza formatos comunes:
    - Código DANE a string de 5 dígitos (con ceros a la izquierda si aplica).
    - Nombres de departamentos y municipios a mayúsculas limpias.
    - Manejo de fechas numéricas (año, mes, día).
    """
    print("  [INFO] Estandarizando campos geográficos y temporales...")
    # TODO: Asegurar que el código DANE tenga 5 caracteres (ej. zfill(5))
    # if 'c_digo_dane_de_municipio' in df.columns:
    #     df['c_digo_dane_de_municipio'] = df['c_digo_dane_de_municipio'].astype(str).str.split('.').str[0].str.zfill(5)
    
    # TODO: Convertir nombres a mayúsculas y retirar espacios sobrantes
    # for col in ['municipio', 'departamento', 'modalidad', 'presunto_responsable']:
    #     if col in df.columns:
    #         df[col] = df[col].astype(str).str.strip().str.upper()
            
    return df


def unificar(ruta_casos_csv, ruta_victimas_csv, ruta_salida_csv):
    """Realiza el merge relacional entre casos y víctimas."""
    print(f"[PROCESAMIENTO] Cruzando casos y víctimas...")
    
    # TODO: Validar existencia de archivos
    if not ruta_casos_csv.exists() or not ruta_victimas_csv.exists():
        print("  [ALERTA] Archivos crudos no disponibles para el cruce.")
        return None

    # TODO: Cargar DataFrames
    # df_casos = pd.read_csv(ruta_casos_csv)
    # df_victimas = pd.read_csv(ruta_victimas_csv)

    # TODO: Limpieza individual previa
    # df_casos = limpiar_y_estandarizar(df_casos)
    # df_victimas = limpiar_y_estandarizar(df_victimas)

    # TODO: Realizar merge (left join o outer join según enfoque)
    # df_unificado = pd.merge(
    #     df_casos,
    #     df_victimas,
    #     on='id_caso',
    #     how='left',
    #     suffixes=('_caso', '_victima')
    # )
    # print(f"  -> Total registros consolidados: {len(df_unificado)}")

    # TODO: Guardar en ruta procesada
    # ruta_salida_csv.parent.mkdir(parents=True, exist_ok=True)
    # df_unificado.to_csv(ruta_salida_csv, index=False, encoding='utf-8')
    # print(f"[ÉXITO] Archivo procesado guardado en: {ruta_salida_csv}")

    print("  [TODO] Lógica de unificación pendiente de implementación.")
    return None


def resolver_archivo_raw(carpeta_raw, prefijo, hecho, formato="auto", fecha=None):
    """
    Busca dinámicamente el archivo crudo en las subcarpetas 'json/' y 'csv/'
    según el formato solicitado (auto, json, csv) y fecha opcional.
    """
    formato = formato.lower().strip()
    patron_fecha = f"_{fecha}" if fecha else "_*"
    
    # 1. Si se solicita explícitamente JSON
    if formato == "json":
        carpeta_json = carpeta_raw / "json"
        if carpeta_json.exists():
            archivos = sorted(list(carpeta_json.glob(f"{prefijo}_{hecho}_raw{patron_fecha}.json")), reverse=True)
            if archivos:
                return archivos[0]
        archivos_raiz = sorted(list(carpeta_raw.glob(f"{prefijo}_{hecho}_raw*.json")), reverse=True)
        return archivos_raiz[0] if archivos_raiz else None

    # 2. Si se solicita explícitamente CSV
    elif formato == "csv":
        carpeta_csv = carpeta_raw / "csv"
        if carpeta_csv.exists():
            archivos = sorted(list(carpeta_csv.glob(f"{prefijo}_{hecho}_raw{patron_fecha}.csv")), reverse=True)
            if archivos:
                return archivos[0]
        archivos_raiz = sorted(list(carpeta_raw.glob(f"{prefijo}_{hecho}_raw*.csv")), reverse=True)
        return archivos_raiz[0] if archivos_raiz else None

    # 3. Modo 'auto': buscar el más reciente entre json/ y csv/
    else:
        candidatos = []
        carpeta_json = carpeta_raw / "json"
        if carpeta_json.exists():
            candidatos.extend(carpeta_json.glob(f"{prefijo}_{hecho}_raw{patron_fecha}.json"))
            
        carpeta_csv = carpeta_raw / "csv"
        if carpeta_csv.exists():
            candidatos.extend(carpeta_csv.glob(f"{prefijo}_{hecho}_raw{patron_fecha}.csv"))

        candidatos.extend(carpeta_raw.glob(f"{prefijo}_{hecho}_raw*.json"))
        candidatos.extend(carpeta_raw.glob(f"{prefijo}_{hecho}_raw*.csv"))

        if candidatos:
            return sorted(candidatos, reverse=True)[0]

    return None


def main():
    parser = argparse.ArgumentParser(description="Unificador de datos de casos y víctimas")
    parser.add_argument(
        "--hecho",
        type=str,
        required=True,
        choices=["reclutamiento_niños", "violencia_sexual"],
        help="Nombre del hecho victimizante a unificar"
    )
    parser.add_argument(
        "--formato",
        type=str,
        choices=["auto", "json", "csv"],
        default="auto",
        help="Formato de archivo a utilizar: 'auto' (más reciente), 'json' o 'csv'"
    )
    parser.add_argument(
        "--fecha",
        type=str,
        default=None,
        help="Fecha específica a unificar en formato yyyy-mm-dd (por defecto: la más reciente)"
    )
    args = parser.parse_args()
    hecho = args.hecho
    formato = args.formato
    fecha = args.fecha

    print("=" * 70)
    print(f"[ETAPA 03] UNIFICACIÓN DE DATOS - HECHO: {hecho.upper()}")
    print(f"Modo de formato: {formato.upper()}")
    if fecha:
        print(f"Fecha filtrada:  {fecha}")
    print("=" * 70)

    carpeta_raw = Path(f"hechos/{hecho}/data/raw")
    carpeta_processed = Path(f"hechos/{hecho}/data/processed")
    carpeta_processed.mkdir(parents=True, exist_ok=True)

    ruta_casos = resolver_archivo_raw(carpeta_raw, "casos", hecho, formato=formato, fecha=fecha)
    ruta_victimas = resolver_archivo_raw(carpeta_raw, "victimas", hecho, formato=formato, fecha=fecha)
    ruta_salida = carpeta_processed / f"{hecho}_unificado.csv"

    unificar(ruta_casos, ruta_victimas, ruta_salida)


if __name__ == "__main__":
    main()

