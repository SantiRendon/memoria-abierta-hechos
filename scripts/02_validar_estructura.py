"""
02_validar_estructura.py
========================
Propósito:
    Verificar la calidad, integridad y cumplimiento del esquema de los datos crudos
    descargados (tanto casos como víctimas) según las reglas definidas en
    'config/columnas_requeridas.yaml'.

Uso:
    python scripts/02_validar_estructura.py --hecho reclutamiento_niños
    python scripts/02_validar_estructura.py --hecho violencia_sexual
"""

import os
import sys
import argparse
from pathlib import Path
import pandas as pd
import yaml

# Rutas de configuración
RUTA_CONFIG_COLUMNAS = Path("config/columnas_requeridas.yaml")


def cargar_reglas():
    """Carga las especificaciones de columnas esperadas."""
    print("[INFO] Cargando reglas de validación de esquema...")
    with open(RUTA_CONFIG_COLUMNAS, "r", encoding="utf-8") as f:
        reglas = yaml.safe_load(f)
    return reglas


def validar_archivo(ruta_csv, esquema_esperado, nombre_dataset="Dataset"):
    """
    Realiza chequeos de calidad sobre un archivo CSV crudo:
    1. Existencia del archivo.
    2. Columnas obligatorias presentes.
    3. Porcentaje de valores nulos por columna.
    4. Duplicados en claves principales.
    """
    print(f"\n[VALIDACIÓN] Analizando: {nombre_dataset} ({ruta_csv.name})")

    if not ruta_csv.exists():
        print(f"  [ALERTA] El archivo no existe aún: {ruta_csv}")
        # TODO: Retornar False o lanzar advertencia según modo de ejecución
        return False

    # TODO: Leer archivo con pandas (manejar encoding utf-8 o latin1 si aplica)
    # df = pd.read_csv(ruta_csv, encoding='utf-8', low_memory=False)
    # print(f"  -> Total filas leídas: {len(df)}")

    # TODO: Validar presencia de columnas obligatorias
    # cols_faltantes = [c for c in esquema_esperado['columnas_obligatorias'] if c not in df.columns]
    # if cols_faltantes:
    #     print(f"  [ERROR] Faltan columnas obligatorias: {cols_faltantes}")
    # else:
    #     print("  [OK] Todas las columnas obligatorias están presentes.")

    # TODO: Validar porcentaje de valores nulos
    # nulos = df.isnull().mean() * 100
    # print("  [INFO] Reporte de valores nulos:")
    # for col, pct in nulos.items():
    #     if pct > 0:
    #         print(f"     - {col}: {pct:.1f}% nulos")

    # TODO: Verificar unicidad en identificadores primarios (id_caso / id_victima)
    # duplicados = df['id_caso'].duplicated().sum()
    # print(f"  [INFO] Registros duplicados detectados: {duplicados}")

    print("  [TODO] Lógica de validación pendiente de ejecución.")
    return True


def resolver_archivo_raw(carpeta_raw, prefijo, hecho):
    """
    Busca dinámicamente el archivo crudo más reciente en las subcarpetas
    'json/' y 'csv/' respetando el versionado de fecha yyyy-mm-dd.
    """
    # 1. Buscar en subcarpeta json/ (archivo más reciente por nombre/fecha)
    carpeta_json = carpeta_raw / "json"
    if carpeta_json.exists():
        archivos_json = sorted(list(carpeta_json.glob(f"{prefijo}_{hecho}_raw_*.json")), reverse=True)
        if archivos_json:
            return archivos_json[0]
            
    # 2. Buscar en subcarpeta csv/ (archivo más reciente por nombre/fecha)
    carpeta_csv = carpeta_raw / "csv"
    if carpeta_csv.exists():
        archivos_csv = sorted(list(carpeta_csv.glob(f"{prefijo}_{hecho}_raw_*.csv")), reverse=True)
        if archivos_csv:
            return archivos_csv[0]
            
    # 3. Respaldo en carpeta raíz de datos crudos
    for ext in ["json", "csv"]:
        candidatos = sorted(list(carpeta_raw.glob(f"{prefijo}_{hecho}_raw*.{ext}")), reverse=True)
        if candidatos:
            return candidatos[0]
            
    return carpeta_raw / "json" / f"{prefijo}_{hecho}_raw.json"


def main():
    parser = argparse.ArgumentParser(description="Validador de estructura y calidad de datos")
    parser.add_argument(
        "--hecho",
        type=str,
        required=True,
        choices=["reclutamiento_niños", "violencia_sexual"],
        help="Nombre del hecho victimizante a validar"
    )
    args = parser.parse_args()
    hecho = args.hecho

    print("=" * 70)
    print(f"[ETAPA 02] VALIDACIÓN DE ESTRUCTURA - HECHO: {hecho.upper()}")
    print("=" * 70)

    reglas = cargar_reglas()
    carpeta_data_raw = Path(f"hechos/{hecho}/data/raw")

    # Archivos a inspeccionar (detección dinámica de .json o .csv)
    archivo_casos = resolver_archivo_raw(carpeta_data_raw, "casos", hecho)
    archivo_victimas = resolver_archivo_raw(carpeta_data_raw, "victimas", hecho)

    # 1. Validar casos
    validar_archivo(archivo_casos, reglas["esquema_casos"], nombre_dataset="Nivel Casos")

    # 2. Validar víctimas
    validar_archivo(archivo_victimas, reglas["esquema_victimas"], nombre_dataset="Nivel Víctimas")

    print("\n[INFO] Proceso de validación finalizado.")


if __name__ == "__main__":
    main()

