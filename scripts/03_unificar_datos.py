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


def resolver_archivo_raw(carpeta_raw, prefijo, hecho):
    """Busca dinámicamente si el archivo crudo está en formato .json o .csv."""
    archivo_json = carpeta_raw / f"{prefijo}_{hecho}_raw.json"
    if archivo_json.exists():
        return archivo_json
    archivo_csv = carpeta_raw / f"{prefijo}_{hecho}_raw.csv"
    if archivo_csv.exists():
        return archivo_csv
    return archivo_json


def main():
    parser = argparse.ArgumentParser(description="Unificador de datos de casos y víctimas")
    parser.add_argument(
        "--hecho",
        type=str,
        required=True,
        choices=["reclutamiento_niños", "violencia_sexual"],
        help="Nombre del hecho victimizante a unificar"
    )
    args = parser.parse_args()
    hecho = args.hecho

    print("=" * 70)
    print(f"[ETAPA 03] UNIFICACIÓN DE DATOS - HECHO: {hecho.upper()}")
    print("=" * 70)

    carpeta_raw = Path(f"hechos/{hecho}/data/raw")
    carpeta_processed = Path(f"hechos/{hecho}/data/processed")
    carpeta_processed.mkdir(parents=True, exist_ok=True)

    ruta_casos = resolver_archivo_raw(carpeta_raw, "casos", hecho)
    ruta_victimas = resolver_archivo_raw(carpeta_raw, "victimas", hecho)
    ruta_salida = carpeta_processed / f"{hecho}_unificado.csv"

    unificar(ruta_casos, ruta_victimas, ruta_salida)


if __name__ == "__main__":
    main()

