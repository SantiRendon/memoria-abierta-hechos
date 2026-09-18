"""
02_validar_estructura.py
========================
Propósito:
    Auditar la calidad, integridad y cumplimiento del contrato de datos de los
    archivos crudos descargados (Casos y Víctimas) contra el esquema centralizado
    'config/esquema_datos.yaml'.

    Capacidades de Validación:
    - Selección de formato: Permite escoger auditar archivos JSON o CSV mediante --formato.
    - Selección temporal: Permite validar una fecha específica con --fecha o la más reciente por defecto.
    - Validación dinámica por hecho victimizante (soporta esquemas distintos por hecho).
    - Verificación de columnas obligatorias y opcionales.
    - Detección de columnas adicionales/inesperadas que envíe la API.
    - Chequeo de valores nulos en campos críticos (permite_nulos: false).
    - Verificación de unicidad en identificadores primarios (id_caso).
    - Generación de reporte de calidad en 'reports/'.

Uso:
    python scripts/02_validar_estructura.py --hecho reclutamiento_niños
    python scripts/02_validar_estructura.py --hecho reclutamiento_niños --formato json
    python scripts/02_validar_estructura.py --hecho reclutamiento_niños --formato csv
    python scripts/02_validar_estructura.py --hecho violencia_sexual --formato json
    python scripts/02_validar_estructura.py --hecho violencia_sexual --formato csv
"""

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path
import pandas as pd
import yaml

# Rutas de configuración
RUTA_CONFIG_ESQUEMA = Path("config/esquema_datos.yaml")
RUTA_CONFIG_FALLBACK = Path("config/columnas_requeridas.yaml")


def cargar_esquema():
    """Carga el catálogo de esquemas y reglas de validación."""
    ruta = RUTA_CONFIG_ESQUEMA if RUTA_CONFIG_ESQUEMA.exists() else RUTA_CONFIG_FALLBACK
    if not ruta.exists():
        print(f"[ERROR] No se encontró el archivo de esquema en: {ruta}", file=sys.stderr)
        sys.exit(1)
        
    print(f"[INFO] Cargando esquema de validación desde: {ruta.name}")
    with open(ruta, "r", encoding="utf-8") as f:
        esquema = yaml.safe_load(f)
    return esquema


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
        # Respaldo en la raíz si fue descargado con nombre antiguo
        archivos_raiz = sorted(list(carpeta_raw.glob(f"{prefijo}_{hecho}_raw*.json")), reverse=True)
        return archivos_raiz[0] if archivos_raiz else None

    # 2. Si se solicita explícitamente CSV
    elif formato == "csv":
        carpeta_csv = carpeta_raw / "csv"
        if carpeta_csv.exists():
            archivos = sorted(list(carpeta_csv.glob(f"{prefijo}_{hecho}_raw{patron_fecha}.csv")), reverse=True)
            if archivos:
                return archivos[0]
        # Respaldo en la raíz si fue descargado con nombre antiguo
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

        # Respaldo en carpeta raíz de datos crudos
        candidatos.extend(carpeta_raw.glob(f"{prefijo}_{hecho}_raw*.json"))
        candidatos.extend(carpeta_raw.glob(f"{prefijo}_{hecho}_raw*.csv"))

        if candidatos:
            return sorted(candidatos, reverse=True)[0]

    return None


def cargar_datos(ruta_archivo):
    """Carga un archivo en memoria según su extensión (.json o .csv)."""
    if ruta_archivo.suffix.lower() == ".json":
        return pd.read_json(ruta_archivo)
    elif ruta_archivo.suffix.lower() == ".csv":
        return pd.read_csv(ruta_archivo, low_memory=False)
    else:
        raise ValueError(f"Extensión no soportada: {ruta_archivo.suffix}")


def validar_dataset(df, esquema_nivel, metadatos_sistema, nombre_dataset="Dataset"):
    """
    Ejecuta la auditoría completa de calidad sobre el DataFrame contra su esquema.
    Retorna un diccionario con métricas y estado final (True/False).
    """
    print("=" * 70)
    print(f">>> AUDITORÍA DE CALIDAD: {nombre_dataset.upper()}")
    print("=" * 70)

    total_filas, total_cols = df.shape
    print(f"[DIMENSIONES] Filas: {total_filas:,} | Columnas totales recibidas: {total_cols}")

    # Separar metadatos del sistema (:id, :version, etc.) de las columnas de negocio
    cols_sistema = [c for c in df.columns if c in metadatos_sistema or c.startswith(":")]
    cols_negocio = [c for c in df.columns if c not in cols_sistema]
    print(f"  -> Columnas de negocio detectadas: {len(cols_negocio)}")
    if cols_sistema:
        print(f"  -> Metadatos de plataforma Socrata filtrados: {len(cols_sistema)} columnas")

    # Columnas definidas en el contrato YAML
    diccionario_esquema = esquema_nivel.get("columnas", {})
    cols_esperadas = list(diccionario_esquema.keys())
    
    cols_obligatorias = [k for k, v in diccionario_esquema.items() if v.get("requerido", False)]
    cols_opcionales = [k for k, v in diccionario_esquema.items() if not v.get("requerido", False)]

    # --------------------------------------------------------------------------
    # 1. Validación de Columnas Obligatorias
    # --------------------------------------------------------------------------
    print("\n--- 1. Validación de Presencia de Columnas Obligatorias ---")
    faltantes_obligatorias = [c for c in cols_obligatorias if c not in df.columns]
    
    if not faltantes_obligatorias:
        print(f"  [OK] 100% de las columnas obligatorias están presentes ({len(cols_obligatorias)}/{len(cols_obligatorias)}).")
    else:
        print(f"  [CRÍTICO] Faltan {len(faltantes_obligatorias)} columnas OBLIGATORIAS:")
        for col in faltantes_obligatorias:
            nombre_legible = diccionario_esquema[col].get("nombre_columna", col)
            print(f"     [X] {col} ('{nombre_legible}')")

    # --------------------------------------------------------------------------
    # 2. Validación de Columnas Opcionales y Extra
    # --------------------------------------------------------------------------
    print("\n--- 2. Validación de Columnas Opcionales y No Registradas ---")
    faltantes_opcionales = [c for c in cols_opcionales if c not in df.columns]
    extras_no_registradas = [c for c in cols_negocio if c not in cols_esperadas]

    if not faltantes_opcionales:
        print(f"  [OK] Todas las columnas opcionales están presentes ({len(cols_opcionales)}/{len(cols_opcionales)}).")
    else:
        print(f"  [AVISO] {len(faltantes_opcionales)} columnas opcionales no vienen en este dataset:")
        for col in faltantes_opcionales:
            nombre_legible = diccionario_esquema[col].get("nombre_columna", col)
            print(f"     [-] {col} ('{nombre_legible}')")

    if extras_no_registradas:
        print(f"  [AVISO] Se detectaron {len(extras_no_registradas)} columnas extras no contempladas en el YAML:")
        for col in extras_no_registradas:
            print(f"     [+] {col}")
    else:
        print("  [OK] No se detectaron columnas desconocidas fuera del esquema.")

    # --------------------------------------------------------------------------
    # 3. Integridad de Valores Nulos en Campos Críticos
    # --------------------------------------------------------------------------
    print("\n--- 3. Integridad de Valores Nulos ---")
    cols_sin_nulos = [k for k, v in diccionario_esquema.items() if not v.get("permite_nulos", True)]
    infracciones_nulos = {}

    for col in cols_sin_nulos:
        if col in df.columns:
            cant_nulos = df[col].isnull().sum()
            if cant_nulos > 0:
                pct = (cant_nulos / total_filas) * 100
                infracciones_nulos[col] = (cant_nulos, pct)

    if not infracciones_nulos:
        print(f"  [OK] Todos los campos de no-nulidad estricta están limpios (0 nulos).")
    else:
        print(f"  [ALERTA] Se hallaron valores nulos en campos no permitidos:")
        for col, (cant, pct) in infracciones_nulos.items():
            print(f"     - {col}: {cant:,} registros nulos ({pct:.2f}%)")

    # --------------------------------------------------------------------------
    # 4. Chequeo de Identificadores y Unicidad
    # --------------------------------------------------------------------------
    print("\n--- 4. Unicidad de Identificadores ---")
    if "id_caso" in df.columns:
        casos_unicos = df["id_caso"].nunique()
        duplicados = df["id_caso"].duplicated().sum()
        if "casos" in nombre_dataset.lower():
            if duplicados == 0:
                print(f"  [OK] id_caso es 100% único ({casos_unicos:,} casos distintos sin duplicados).")
            else:
                print(f"  [ALERTA] Se detectaron {duplicados:,} filas duplicadas en id_caso a nivel Casos.")
        else:
            promedio_victimas = total_filas / casos_unicos if casos_unicos > 0 else 0
            print(f"  [INFO] Total casos vinculados: {casos_unicos:,} (Promedio: {promedio_victimas:.2f} víctimas/caso).")

    if "id_persona" in df.columns:
        personas_unicas = df["id_persona"].nunique()
        print(f"  [INFO] Total personas identificadas: {personas_unicas:,}")

    # --------------------------------------------------------------------------
    # 5. Dictamen Final de Validación
    # --------------------------------------------------------------------------
    es_valido = len(faltantes_obligatorias) == 0 and len(infracciones_nulos) == 0
    print("\n" + "-" * 70)
    if es_valido:
        print(f">>> DICTAMEN: [APROBADO] El dataset cumple con los requisitos del esquema.")
    else:
        print(f">>> DICTAMEN: [REVISIÓN REQUERIDA] Hay inconsistencias obligatorias que deben subsanarse.")
    print("-" * 70)

    resultado = {
        "dataset": nombre_dataset,
        "filas": total_filas,
        "columnas_negocio": len(cols_negocio),
        "faltantes_obligatorias": faltantes_obligatorias,
        "faltantes_opcionales": faltantes_opcionales,
        "extras_no_registradas": extras_no_registradas,
        "infracciones_nulos": infracciones_nulos,
        "es_valido": es_valido
    }
    return resultado


def guardar_reporte(hecho, formato_auditado, resultados_casos, resultados_victimas):
    """Guarda un reporte estructurado en reports/."""
    carpeta_reportes = Path(f"hechos/{hecho}/reports")
    carpeta_reportes.mkdir(parents=True, exist_ok=True)
    
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    ruta_reporte = carpeta_reportes / f"calidad_datos_{hecho}_{formato_auditado}_{fecha_hoy}.json"
    
    reporte_consolidado = {
        "hecho": hecho,
        "formato_auditado": formato_auditado,
        "fecha_auditoria": fecha_hoy,
        "casos": resultados_casos,
        "victimas": resultados_victimas,
        "aprobacion_global": resultados_casos.get("es_valido", False) and resultados_victimas.get("es_valido", False)
    }
    
    with open(ruta_reporte, "w", encoding="utf-8") as f:
        json.dump(reporte_consolidado, f, ensure_ascii=False, indent=2)
    print(f"\n[REPORTES] Reporte de auditoría guardado en:")
    print(f"           {ruta_reporte}")


def main():
    parser = argparse.ArgumentParser(
        description="Auditor y validador de estructura de datos de Memoria Histórica"
    )
    parser.add_argument(
        "--hecho",
        type=str,
        required=True,
        choices=["reclutamiento_niños", "violencia_sexual"],
        help="Nombre del hecho victimizante a auditar"
    )
    parser.add_argument(
        "--formato",
        type=str,
        choices=["auto", "json", "csv"],
        default="auto",
        help="Formato de archivo a auditar: 'auto' (más reciente), 'json' o 'csv'"
    )
    parser.add_argument(
        "--fecha",
        type=str,
        default=None,
        help="Fecha específica a auditar en formato yyyy-mm-dd (por defecto: la más reciente)"
    )
    args = parser.parse_args()
    hecho = args.hecho
    formato = args.formato
    fecha = args.fecha

    print("=" * 75)
    print(f"[ETAPA 02] VALIDACIÓN DE ESTRUCTURA Y CALIDAD - HECHO: {hecho.upper()}")
    print(f"Modo de formato seleccionado: {formato.upper()}")
    if fecha:
        print(f"Fecha filtrada:               {fecha}")
    print("=" * 75)

    esquema_general = cargar_esquema()
    if hecho not in esquema_general.get("hechos", {}):
        print(f"[ERROR] El hecho '{hecho}' no está configurado en el archivo de esquema.", file=sys.stderr)
        sys.exit(1)

    esquema_hecho = esquema_general["hechos"][hecho]
    metadatos_sistema = esquema_general.get("metadatos_sistema", [])
    carpeta_data_raw = Path(f"hechos/{hecho}/data/raw")

    # 1. Localizar y cargar Casos
    archivo_casos = resolver_archivo_raw(carpeta_data_raw, "casos", hecho, formato=formato, fecha=fecha)
    if not archivo_casos or not archivo_casos.exists():
        print(f"[ERROR] No se encontró archivo crudo de Casos ({formato.upper()}) para '{hecho}' en {carpeta_data_raw}", file=sys.stderr)
        sys.exit(1)
        
    formato_detectado = archivo_casos.suffix.replace(".", "").lower()
    print(f"\n[ARCHIVO] Cargando Casos ({formato_detectado.upper()}): {archivo_casos.name} ({archivo_casos.parent.name}/)")
    df_casos = cargar_datos(archivo_casos)
    res_casos = validar_dataset(
        df=df_casos,
        esquema_nivel=esquema_hecho["casos"],
        metadatos_sistema=metadatos_sistema,
        nombre_dataset=f"Casos ({formato_detectado.upper()}) - {hecho}"
    )

    # 2. Localizar y cargar Víctimas
    archivo_victimas = resolver_archivo_raw(carpeta_data_raw, "victimas", hecho, formato=formato, fecha=fecha)
    if not archivo_victimas or not archivo_victimas.exists():
        print(f"[ERROR] No se encontró archivo crudo de Víctimas ({formato.upper()}) para '{hecho}' en {carpeta_data_raw}", file=sys.stderr)
        sys.exit(1)

    formato_vic_detectado = archivo_victimas.suffix.replace(".", "").lower()
    print(f"\n[ARCHIVO] Cargando Víctimas ({formato_vic_detectado.upper()}): {archivo_victimas.name} ({archivo_victimas.parent.name}/)")
    df_victimas = cargar_datos(archivo_victimas)
    res_victimas = validar_dataset(
        df=df_victimas,
        esquema_nivel=esquema_hecho["victimas"],
        metadatos_sistema=metadatos_sistema,
        nombre_dataset=f"Víctimas ({formato_vic_detectado.upper()}) - {hecho}"
    )

    # Guardar reporte de auditoría
    guardar_reporte(hecho, formato_detectado, res_casos, res_victimas)

    print("\n" + "=" * 75)
    print(f"[INFO] Proceso de validación finalizado para: {hecho} ({formato_detectado.upper()})")
    print("=" * 75)


if __name__ == "__main__":
    main()
