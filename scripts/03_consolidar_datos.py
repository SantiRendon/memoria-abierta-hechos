"""
03_consolidar_datos.py
======================
Propósito:
    Limpiar, normalizar y consolidar en una única tabla analítica los datos de
    Casos y Víctimas correspondientes a un hecho victimizante.
    
    Cada registro en el dataset consolidado representa una víctima individual,
    enriquecida con la totalidad de los atributos y variables de contexto del caso
    al que pertenece (modalidad, presunto responsable, simultaneidades, etc.).

Formatos Soportados:
    - Entrada: Permite elegir consolidar desde archivos crudos en formato CSV o JSON.
               (Opciones: 'auto', 'csv', 'json').
    - Salida:  Permite elegir exportar el resultado consolidado a CSV, JSON o ambos.
               (Opciones: 'csv', 'json', 'ambos').

Estandarizaciones Realizadas:
    1. Eliminación de metadatos del sistema Socrata (:id, :created_at, etc.).
    2. Homogeneización de Claves (id_caso e id_persona) sin decimales.
    3. Estandarización de Códigos DANE a 5 dígitos oficiales con ceros a la izquierda (ej. '05001').
    4. Extracción de coordenadas numéricas separadas ('latitud' y 'longitud') a partir del objeto Point GeoJSON.
    5. Normalización de campos de texto (eliminación de espacios en blanco).
    6. Cruce relacional limpio sin duplicación de columnas transversales (_x, _y).
    7. Inclusión de columnas de trazabilidad: 'hecho_victimizante' y 'fecha_consolidacion'.

Uso:
    python scripts/03_consolidar_datos.py --hecho reclutamiento_niños
    python scripts/03_consolidar_datos.py --hecho reclutamiento_niños --formato-entrada csv --formato-salida ambos
    python scripts/03_consolidar_datos.py --hecho violencia_sexual --formato-entrada json --formato-salida json
    python scripts/03_consolidar_datos.py --hecho violencia_sexual --formato-salida csv --fecha 2026-09-17
"""

import os
import sys
import ast
import json
import argparse
from datetime import datetime
from pathlib import Path
import pandas as pd
import numpy as np


def resolver_archivo_raw(carpeta_raw, prefijo, hecho, formato="auto", fecha=None):
    """
    Busca dinámicamente el archivo crudo en las subcarpetas 'json/' y 'csv/'
    según el formato solicitado (auto, json, csv) y fecha opcional.
    """
    formato = formato.lower().strip()
    patron_fecha = f"_{fecha}" if fecha else "_*"

    # 1. Modo explícito JSON
    if formato == "json":
        carpeta_json = carpeta_raw / "json"
        if carpeta_json.exists():
            archivos = sorted(list(carpeta_json.glob(f"{prefijo}_{hecho}_raw{patron_fecha}.json")), reverse=True)
            if archivos:
                return archivos[0]
        archivos_raiz = sorted(list(carpeta_raw.glob(f"{prefijo}_{hecho}_raw*.json")), reverse=True)
        return archivos_raiz[0] if archivos_raiz else None

    # 2. Modo explícito CSV
    elif formato == "csv":
        carpeta_csv = carpeta_raw / "csv"
        if carpeta_csv.exists():
            archivos = sorted(list(carpeta_csv.glob(f"{prefijo}_{hecho}_raw{patron_fecha}.csv")), reverse=True)
            if archivos:
                return archivos[0]
        archivos_raiz = sorted(list(carpeta_raw.glob(f"{prefijo}_{hecho}_raw*.csv")), reverse=True)
        return archivos_raiz[0] if archivos_raiz else None

    # 3. Modo 'auto': busca el archivo más reciente entre json/ y csv/
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


def cargar_datos_crudos(ruta_archivo):
    """Carga un archivo crudo según su extensión (.json o .csv)."""
    extension = ruta_archivo.suffix.lower()
    if extension == ".json":
        return pd.read_json(ruta_archivo)
    elif extension == ".csv":
        return pd.read_csv(ruta_archivo, low_memory=False)
    else:
        raise ValueError(f"Extensión no soportada: {extension}")


def extraer_coordenadas(val):
    """
    Parsea de forma segura el campo 'latitud_longitud' (formato GeoJSON Point)
    y retorna la tupla (latitud, longitud) como números flotantes.
    En GeoJSON Point el estándar es coordinates: [longitud, latitud].
    """
    if pd.isna(val) or val is None or val == "":
        return None, None
    try:
        if isinstance(val, dict):
            coords = val.get("coordinates")
        elif isinstance(val, str):
            val_clean = val.strip()
            if "coordinates" in val_clean:
                parsed = ast.literal_eval(val_clean)
                coords = parsed.get("coordinates") if isinstance(parsed, dict) else None
            else:
                coords = None
        else:
            coords = None

        if coords and len(coords) >= 2:
            lon = float(coords[0])
            lat = float(coords[1])
            return lat, lon
    except Exception:
        pass
    return None, None


def estandarizar_codigo_dane(serie):
    """
    Estandariza códigos DANE a strings oficiales de 5 dígitos con ceros a la izquierda.
    Ejemplos: 5001 -> '05001', 76001 -> '76001', 0 -> '00000'.
    """
    def formatear_dane(v):
        if pd.isna(v) or v is None or str(v).strip().lower() in ["", "nan", "none"]:
            return "00000"
        limpio = str(v).split(".")[0].strip()
        if limpio.isdigit():
            return limpio.zfill(5)
        return limpio

    return serie.apply(formatear_dane)


def limpiar_y_estandarizar(df, hecho):
    """
    Aplica limpieza técnica y de negocio a los datos de Casos o Víctimas:
    - Remueve columnas del sistema Socrata (:id, :created_at, etc.).
    - Limpia identificadores numéricos.
    - Estandariza DANE y extrae coordenadas geográficas.
    - Recorta espacios en blanco en campos de texto.
    """
    df_clean = df.copy()

    # 1. Descartar metadatos de sistema Socrata
    cols_sistema = [c for c in df_clean.columns if c.startswith(":")]
    if cols_sistema:
        df_clean = df_clean.drop(columns=cols_sistema)

    # 2. Homogeneizar 'id_caso'
    if "id_caso" in df_clean.columns:
        df_clean["id_caso"] = (
            df_clean["id_caso"]
            .astype(str)
            .str.split(".")
            .str[0]
            .str.strip()
        )

    # 3. Homogeneizar 'id_persona' si está presente
    if "id_persona" in df_clean.columns:
        df_clean["id_persona"] = (
            df_clean["id_persona"]
            .astype(str)
            .str.split(".")
            .str[0]
            .str.strip()
        )

    # 4. Estandarizar código DANE
    if "c_digo_dane_de_municipio" in df_clean.columns:
        df_clean["c_digo_dane_de_municipio"] = estandarizar_codigo_dane(df_clean["c_digo_dane_de_municipio"])

    # 5. Estandarizar año, mes y día a valores enteros limpios
    for col_temporal in ["a_o", "mes", "d_a"]:
        if col_temporal in df_clean.columns:
            df_clean[col_temporal] = pd.to_numeric(df_clean[col_temporal], errors="coerce").fillna(0).astype(int)

    # 6. Extraer latitud y longitud numéricas
    if "latitud_longitud" in df_clean.columns:
        coords = df_clean["latitud_longitud"].apply(extraer_coordenadas)
        df_clean["latitud"] = [c[0] for c in coords]
        df_clean["longitud"] = [c[1] for c in coords]

    # 7. Normalizar strings de texto (quitar espacios sobrantes)
    cols_texto = df_clean.select_dtypes(include=["object", "string", str]).columns
    for c in cols_texto:
        if c not in ["latitud_longitud"]:
            df_clean[c] = df_clean[c].apply(lambda x: x.strip() if isinstance(x, str) else x)

    return df_clean


def consolidar_hecho(hecho, formato_entrada="auto", formato_salida="csv", fecha=None):
    """
    Ejecuta el pipeline completo de consolidación para un hecho victimizante:
    Localización -> Carga -> Limpieza -> Merge Relacional -> Enriquecimiento -> Exportación.
    """
    print("=" * 75)
    print(f"[ETAPA 03] CONSOLIDACIÓN DE DATOS - HECHO: {hecho.upper()}")
    print(f"Modo Entrada:  {formato_entrada.upper()}")
    print(f"Modo Salida:   {formato_salida.upper()}")
    if fecha:
        print(f"Fecha filtro:  {fecha}")
    print("=" * 75)

    carpeta_raw = Path(f"hechos/{hecho}/data/raw")
    carpeta_processed = Path(f"hechos/{hecho}/data/processed")
    carpeta_processed_csv = carpeta_processed / "csv"
    carpeta_processed_json = carpeta_processed / "json"

    carpeta_processed_csv.mkdir(parents=True, exist_ok=True)
    carpeta_processed_json.mkdir(parents=True, exist_ok=True)

    # 1. Localizar archivos crudos de Casos y Víctimas
    archivo_casos = resolver_archivo_raw(carpeta_raw, "casos", hecho, formato=formato_entrada, fecha=fecha)
    archivo_victimas = resolver_archivo_raw(carpeta_raw, "victimas", hecho, formato=formato_entrada, fecha=fecha)

    if not archivo_casos or not archivo_casos.exists():
        print(f"[ERROR] No se localizó archivo crudo de Casos en {carpeta_raw}", file=sys.stderr)
        sys.exit(1)

    if not archivo_victimas or not archivo_victimas.exists():
        print(f"[ERROR] No se localizó archivo crudo de Víctimas en {carpeta_raw}", file=sys.stderr)
        sys.exit(1)

    formato_in_detectado = archivo_casos.suffix.replace(".", "").lower()
    print(f"\n[ARCHIVOS DE ENTRADA LOCALIZADOS ({formato_in_detectado.upper()})]")
    print(f"  - Casos:    {archivo_casos.name} ({archivo_casos.parent.name}/)")
    print(f"  - Víctimas: {archivo_victimas.name} ({archivo_victimas.parent.name}/)")

    # 2. Cargar datos
    print("\n[PROCESAMIENTO] Cargando conjuntos de datos crudos...")
    df_casos = cargar_datos_crudos(archivo_casos)
    df_victimas = cargar_datos_crudos(archivo_victimas)

    print(f"  -> Filas leídas en Casos:     {len(df_casos):,} registros")
    print(f"  -> Filas leídas en Víctimas:  {len(df_victimas):,} registros")

    # 3. Limpieza y estandarización individual
    print("\n[PROCESAMIENTO] Estandarizando claves, campos DANE y coordenadas...")
    df_casos_clean = limpiar_y_estandarizar(df_casos, hecho)
    df_victimas_clean = limpiar_y_estandarizar(df_victimas, hecho)

    # 4. Preparación para Merge Relacional (Evitar colisión de columnas transversales)
    # Las columnas comunes como departamento, municipio, a_o, d_a, mes, latitud_longitud, etc.,
    # ya están en víctimas y son idénticas. Mantenemos las de víctimas y solo incorporamos
    # de casos los atributos exclusivos del evento (modalidad, presunto responsable, etc.).
    columnas_duplicadas = [
        col for col in df_casos_clean.columns
        if col in df_victimas_clean.columns and col != "id_caso"
    ]
    df_casos_para_merge = df_casos_clean.drop(columns=columnas_duplicadas)

    print("\n[PROCESAMIENTO] Ejecutando merge relacional Casos -> Víctimas por 'id_caso'...")
    df_consolidado = pd.merge(
        df_victimas_clean,
        df_casos_para_merge,
        on="id_caso",
        how="left"
    )

    # 5. Agregar variables de trazabilidad analítica
    df_consolidado["hecho_victimizante"] = hecho
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    df_consolidado["fecha_consolidacion"] = fecha_hoy

    total_filas = len(df_consolidado)
    total_columnas = len(df_consolidado.columns)

    print(f"\n[ESTADÍSTICAS DEL DATASET CONSOLIDADO]")
    print(f"  - Total registros consolidados (víctimas): {total_filas:,}")
    print(f"  - Total columnas finales:                 {total_columnas}")
    print(f"  - Víctimas con georreferenciación lat/lon: {df_consolidado['latitud'].notna().sum():,} "
          f"({(df_consolidado['latitud'].notna().sum() / total_filas) * 100:.1f}%)")

    # 6. Exportación en formatos solicitados
    rutas_generadas = []

    # Determinar qué formatos generar
    generar_csv = formato_salida in ["csv", "ambos"]
    generar_json = formato_salida in ["json", "ambos"]

    # Determinar fecha para nombre de archivo (prioridad: argumento --fecha -> fecha en nombre crudo -> fecha de hoy)
    import re
    match_fecha_crudo = re.search(r"(\d{4}-\d{2}-\d{2})", archivo_casos.name)
    tag_fecha = fecha if fecha else (match_fecha_crudo.group(1) if match_fecha_crudo else fecha_hoy)

    # Exportación a CSV
    if generar_csv:
        ruta_csv_versionada = carpeta_processed_csv / f"{hecho}_consolidado_{tag_fecha}.csv"
        ruta_csv_canonico = carpeta_processed / f"{hecho}_consolidado.csv"

        df_consolidado.to_csv(ruta_csv_versionada, index=False, encoding="utf-8")
        df_consolidado.to_csv(ruta_csv_canonico, index=False, encoding="utf-8")
        rutas_generadas.append(ruta_csv_versionada)
        rutas_generadas.append(ruta_csv_canonico)

    # Exportación a JSON
    if generar_json:
        ruta_json_versionada = carpeta_processed_json / f"{hecho}_consolidado_{tag_fecha}.json"
        ruta_json_canonico = carpeta_processed / f"{hecho}_consolidado.json"

        df_consolidado.to_json(ruta_json_versionada, orient="records", force_ascii=False, indent=2)
        df_consolidado.to_json(ruta_json_canonico, orient="records", force_ascii=False, indent=2)
        rutas_generadas.append(ruta_json_versionada)
        rutas_generadas.append(ruta_json_canonico)

    print("\n" + "=" * 75)
    print("[ÉXITO] Archivos consolidados exportados:")
    for r in rutas_generadas:
        tam_mb = r.stat().st_size / (1024 * 1024)
        print(f"  -> {r} ({tam_mb:.2f} MB)")
    print("=" * 75)

    return df_consolidado


def main():
    parser = argparse.ArgumentParser(
        description="Consolidador de datos de Casos y Víctimas a nivel individual enriquecido"
    )
    parser.add_argument(
        "--hecho",
        type=str,
        required=True,
        choices=["reclutamiento_niños", "violencia_sexual"],
        help="Nombre del hecho victimizante a consolidar"
    )
    parser.add_argument(
        "--formato-entrada",
        "--formato",
        dest="formato_entrada",
        type=str,
        choices=["auto", "json", "csv"],
        default="auto",
        help="Formato del archivo crudo de entrada a procesar: 'auto', 'json' o 'csv' (por defecto: 'auto')"
    )
    parser.add_argument(
        "--formato-salida",
        dest="formato_salida",
        type=str,
        choices=["csv", "json", "ambos"],
        default="csv",
        help="Formato de salida del dataset consolidado: 'csv', 'json' o 'ambos' (por defecto: 'csv')"
    )
    parser.add_argument(
        "--fecha",
        type=str,
        default=None,
        help="Fecha específica de los datos a consolidar en formato yyyy-mm-dd (por defecto: la más reciente)"
    )
    args = parser.parse_args()

    consolidar_hecho(
        hecho=args.hecho,
        formato_entrada=args.formato_entrada,
        formato_salida=args.formato_salida,
        fecha=args.fecha
    )


if __name__ == "__main__":
    main()
