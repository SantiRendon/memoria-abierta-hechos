"""
02_1_validar_integridad.py
==========================
Propósito:
    Validar la integridad referencial (Clave Primaria PK - Clave Foránea FK)
    y la coherencia de métricas cuantitativas entre las tablas de Casos y Víctimas
    antes de proceder al cruce y consolidación en el script 03.

    Validaciones Específicas:
    1. Integridad Referencial PK-FK:
       - Detección de casos sin víctimas (huérfanos en Casos).
       - Detección de víctimas sin caso asignado (huérfanos en Víctimas).
    2. Consistencia Numérica de Víctimas:
       - Compara 'total_de_v_ctimas_del_caso' declarado contra el conteo real
         de filas individuales en la tabla de Víctimas para cada id_caso.
       - Clasifica y almacena en arrays los casos discrepantes:
         * MAYOR_EN_CASO: El caso declara más víctimas que las filas individuales existentes.
         * MENOR_EN_CASO: Hay más víctimas individuales registradas que el total declarado.
    3. Coherencia Cruzada de Atributos:
       - Valida que el año (a_o) y el municipio (c_digo_dane_de_municipio) coincidan
         entre el caso padre y sus víctimas hijas.
    4. Generación de Reporte de Auditoría:
       - Exporta un reporte detallado en JSON con los arrays de discrepancias en 'reports/'.

Uso:
    python scripts/02_1_validar_integridad.py --hecho reclutamiento_niños
    python scripts/02_1_validar_integridad.py --hecho reclutamiento_niños --formato csv
    python scripts/02_1_validar_integridad.py --hecho violencia_sexual --formato json
"""

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path
import pandas as pd


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


def cargar_datos(ruta_archivo):
    """Carga un archivo crudo en DataFrame según su extensión (.json o .csv)."""
    if ruta_archivo.suffix.lower() == ".json":
        return pd.read_json(ruta_archivo)
    elif ruta_archivo.suffix.lower() == ".csv":
        return pd.read_csv(ruta_archivo, low_memory=False)
    else:
        raise ValueError(f"Extensión no soportada: {ruta_archivo.suffix}")


def validar_integridad_relacional(df_casos, df_victimas, hecho):
    """
    Ejecuta todas las validaciones cruzadas entre Casos y Víctimas.
    """
    print("=" * 75)
    print(f">>> AUDITORÍA RELACIONAL PK-FK Y CONSISTENCIA NUMÉRICA: {hecho.upper()}")
    print("=" * 75)

    # --------------------------------------------------------------------------
    # 0. Preparación de Claves Primarias y Foráneas
    # --------------------------------------------------------------------------
    # Convertir identificadores a strings limpios sin decimales (.0)
    df_casos_proc = df_casos.copy()
    df_victimas_proc = df_victimas.copy()

    df_casos_proc["id_caso_clean"] = df_casos_proc["id_caso"].astype(str).str.split(".").str[0].str.strip()
    df_victimas_proc["id_caso_clean"] = df_victimas_proc["id_caso"].astype(str).str.split(".").str[0].str.strip()

    set_pk_casos = set(df_casos_proc["id_caso_clean"])
    set_fk_victimas = set(df_victimas_proc["id_caso_clean"])

    total_casos = len(df_casos_proc)
    total_victimas = len(df_victimas_proc)
    casos_unicos = df_casos_proc["id_caso_clean"].nunique()

    print(f"[ESTADÍSTICAS BÁSICAS]")
    print(f"  - Total registros en Casos:     {total_casos:,}")
    print(f"  - Total casos únicos (PK):      {casos_unicos:,}")
    print(f"  - Total registros en Víctimas:  {total_victimas:,}")

    # --------------------------------------------------------------------------
    # 1. Integridad Referencial: Huérfanos en PK y FK
    # --------------------------------------------------------------------------
    print("\n--- 1. Integridad Referencial (Relación Casos <-> Víctimas) ---")
    
    # Casos que no tienen ninguna víctima registrada
    huerfanos_casos = sorted(list(set_pk_casos - set_fk_victimas))
    # Víctimas cuyo caso no existe en la tabla de Casos
    huerfanos_victimas = sorted(list(set_fk_victimas - set_pk_casos))

    if not huerfanos_casos:
        print("  [OK] Todos los Casos tienen al menos una víctima registrada (0 huérfanos).")
    else:
        print(f"  [ALERTA] Se detectaron {len(huerfanos_casos):,} Casos sin víctimas asociadas:")
        print(f"           Muestra de IDs: {huerfanos_casos[:10]}")

    if not huerfanos_victimas:
        print("  [OK] Todas las Víctimas están asociadas a un Caso existente (0 huérfanas).")
    else:
        print(f"  [CRÍTICO] Se detectaron {len(huerfanos_victimas):,} Víctimas cuyo id_caso NO existe en Casos:")
        print(f"            Muestra de IDs: {huerfanos_victimas[:10]}")

    # --------------------------------------------------------------------------
    # 2. Consistencia Numérica de Víctimas (Declaradas vs Contadas)
    # --------------------------------------------------------------------------
    print("\n--- 2. Consistencia Numérica: Total Declarado vs Víctimas Contadas ---")

    # Contar víctimas reales por cada caso
    conteo_real = df_victimas_proc.groupby("id_caso_clean").size().rename("victimas_reales")

    # Extraer columna total_de_v_ctimas_del_caso y convertir a número
    df_casos_proc["victimas_declaradas"] = pd.to_numeric(
        df_casos_proc.get("total_de_v_ctimas_del_caso", 0), errors="coerce"
    ).fillna(0).astype(int)

    # Unir casos con su conteo real
    df_comparacion = df_casos_proc[["id_caso_clean", "victimas_declaradas"]].merge(
        conteo_real, left_on="id_caso_clean", right_index=True, how="left"
    ).fillna({"victimas_reales": 0})
    df_comparacion["victimas_reales"] = df_comparacion["victimas_reales"].astype(int)

    # Calcular diferencias
    df_comparacion["diferencia"] = df_comparacion["victimas_declaradas"] - df_comparacion["victimas_reales"]

    # Casos que coinciden exactamente
    df_coincidentes = df_comparacion[df_comparacion["diferencia"] == 0]
    # Casos donde el caso declara más víctimas que las registradas
    df_mayor_en_caso = df_comparacion[df_comparacion["diferencia"] > 0]
    # Casos donde hay más víctimas registradas que las que declara el caso
    df_menor_en_caso = df_comparacion[df_comparacion["diferencia"] < 0]

    cant_coincidentes = len(df_coincidentes)
    cant_mayor = len(df_mayor_en_caso)
    cant_menor = len(df_menor_en_caso)

    pct_coincidencia = (cant_coincidentes / casos_unicos) * 100 if casos_unicos > 0 else 0
    print(f"  - Casos con conteo exacto:               {cant_coincidentes:,} ({pct_coincidencia:.2f}%)")
    print(f"  - Casos con MAYOR número declarado:      {cant_mayor:,}")
    print(f"  - Casos con MENOR número declarado:      {cant_menor:,}")

    # Guardar en arrays detallados
    array_mayor_en_caso = []
    for _, fila in df_mayor_en_caso.iterrows():
        array_mayor_en_caso.append({
            "id_caso": fila["id_caso_clean"],
            "declarado_en_caso": int(fila["victimas_declaradas"]),
            "contadas_en_victimas": int(fila["victimas_reales"]),
            "diferencia": int(fila["diferencia"]),
            "tipo": "MAYOR_EN_CASO",
            "descripcion": f"El caso declara {int(fila['victimas_declaradas'])} víctimas pero solo hay {int(fila['victimas_reales'])} registradas."
        })

    array_menor_en_caso = []
    for _, fila in df_menor_en_caso.iterrows():
        array_menor_en_caso.append({
            "id_caso": fila["id_caso_clean"],
            "declarado_en_caso": int(fila["victimas_declaradas"]),
            "contadas_en_victimas": int(fila["victimas_reales"]),
            "diferencia": int(abs(fila["diferencia"])),
            "tipo": "MENOR_EN_CASO",
            "descripcion": f"Hay {int(fila['victimas_reales'])} víctimas registradas pero el caso solo declara {int(fila['victimas_declaradas'])}."
        })

    if cant_mayor > 0:
        print(f"\n  [EJEMPLOS MAYOR_EN_CASO] (Muestra primeros 3):")
        for item in array_mayor_en_caso[:3]:
            print(f"     -> ID {item['id_caso']}: declara {item['declarado_en_caso']} vs {item['contadas_en_victimas']} en víctimas (dif: +{item['diferencia']})")

    if cant_menor > 0:
        print(f"\n  [EJEMPLOS MENOR_EN_CASO] (Muestra primeros 3):")
        for item in array_menor_en_caso[:3]:
            print(f"     -> ID {item['id_caso']}: declara {item['declarado_en_caso']} vs {item['contadas_en_victimas']} en víctimas (dif: -{item['diferencia']})")

    # --------------------------------------------------------------------------
    # 3. Coherencia Espacial y Temporal Cruzada
    # --------------------------------------------------------------------------
    print("\n--- 3. Coherencia de Atributos Cruzados (Espacio y Tiempo) ---")
    
    # Evaluar si año y DANE coinciden entre el caso y la víctima
    cols_evaluar = []
    if "a_o" in df_casos_proc.columns and "a_o" in df_victimas_proc.columns:
        cols_evaluar.append("a_o")
    if "c_digo_dane_de_municipio" in df_casos_proc.columns and "c_digo_dane_de_municipio" in df_victimas_proc.columns:
        cols_evaluar.append("c_digo_dane_de_municipio")

    discrepancias_atributos = {}
    if cols_evaluar:
        # Cruce interno para validar consistencia
        df_cruce_test = df_victimas_proc[["id_caso_clean"] + cols_evaluar].merge(
            df_casos_proc[["id_caso_clean"] + cols_evaluar],
            on="id_caso_clean",
            suffixes=("_vic", "_caso")
        )

        for c in cols_evaluar:
            # Comparar como strings normalizados
            diferentes = (
                df_cruce_test[f"{c}_vic"].astype(str).str.strip().str.upper() !=
                df_cruce_test[f"{c}_caso"].astype(str).str.strip().str.upper()
            ).sum()
            discrepancias_atributos[c] = int(diferentes)
            if diferentes == 0:
                print(f"  [OK] Campo '{c}' es 100% consistente entre Casos y Víctimas vinculados.")
            else:
                print(f"  [ALERTA] Campo '{c}' tiene {diferentes:,} registros con discrepancias entre Caso y Víctima.")

    # --------------------------------------------------------------------------
    # 4. Dictamen Final
    # --------------------------------------------------------------------------
    es_aprobado = len(huerfanos_victimas) == 0
    print("\n" + "-" * 75)
    if es_aprobado and (cant_mayor == 0 and cant_menor == 0):
        print(">>> DICTAMEN: [APROBADO PERFECTO] Integridad relacional y numérica al 100%.")
    elif es_aprobado:
        print(">>> DICTAMEN: [APROBADO CON OBSERVACIONES] Integridad PK-FK intacta.")
        print(f"              Existen discrepancias numéricas documentadas ({cant_mayor + cant_menor:,} casos).")
    else:
        print(">>> DICTAMEN: [REVISIÓN CRÍTICA] Existen víctimas huérfanas sin caso correspondiente.")
    print("-" * 75)

    resultados = {
        "hecho": hecho,
        "fecha_auditoria": datetime.now().strftime("%Y-%m-%d"),
        "estadisticas_generales": {
            "total_casos_registros": total_casos,
            "total_casos_unicos_pk": casos_unicos,
            "total_victimas_registros": total_victimas,
            "porcentaje_coincidencia_conteo": round(pct_coincidencia, 2)
        },
        "integridad_pk_fk": {
            "casos_sin_victimas_count": len(huerfanos_casos),
            "victimas_sin_caso_count": len(huerfanos_victimas),
            "casos_sin_victimas_ids": huerfanos_casos[:100],  # Top 100 para no inflar el json
            "victimas_sin_caso_ids": huerfanos_victimas[:100]
        },
        "discrepancias_conteo_victimas": {
            "total_coincidentes": cant_coincidentes,
            "total_mayor_en_caso": cant_mayor,
            "total_menor_en_caso": cant_menor,
            "array_mayor_en_caso": array_mayor_en_caso,
            "array_menor_en_caso": array_menor_en_caso
        },
        "coherencia_atributos_cruzados": discrepancias_atributos,
        "es_aprobado": es_aprobado
    }
    return resultados


def guardar_reporte(hecho, formato, resultados):
    """Guarda el reporte en hechos/{hecho}/reports/."""
    carpeta_reportes = Path(f"hechos/{hecho}/reports")
    carpeta_reportes.mkdir(parents=True, exist_ok=True)
    
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    ruta_salida = carpeta_reportes / f"integridad_relacional_{hecho}_{formato}_{fecha_hoy}.json"
    
    with open(ruta_salida, "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)
        
    print(f"\n[REPORTES] Reporte detallado de integridad guardado en:")
    print(f"           {ruta_salida}")


def main():
    parser = argparse.ArgumentParser(
        description="Validador de Integridad Relacional (PK-FK) y Consistencia Numérica de Víctimas"
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
        help="Formato de los datos a auditar: 'auto', 'json' o 'csv'"
    )
    parser.add_argument(
        "--fecha",
        type=str,
        default=None,
        help="Fecha específica a auditar (yyyy-mm-dd)"
    )
    args = parser.parse_args()
    hecho = args.hecho
    formato = args.formato
    fecha = args.fecha

    print("=" * 75)
    print(f"[ETAPA 02.1] VALIDACIÓN DE INTEGRIDAD RELACIONAL - HECHO: {hecho.upper()}")
    print(f"Modo de formato: {formato.upper()}")
    if fecha:
        print(f"Fecha filtrada:  {fecha}")
    print("=" * 75)

    carpeta_data_raw = Path(f"hechos/{hecho}/data/raw")

    # Localizar archivos
    archivo_casos = resolver_archivo_raw(carpeta_data_raw, "casos", hecho, formato=formato, fecha=fecha)
    archivo_victimas = resolver_archivo_raw(carpeta_data_raw, "victimas", hecho, formato=formato, fecha=fecha)

    if not archivo_casos or not archivo_casos.exists():
        print(f"[ERROR] No se encontró archivo crudo de Casos en {carpeta_data_raw}", file=sys.stderr)
        sys.exit(1)
        
    if not archivo_victimas or not archivo_victimas.exists():
        print(f"[ERROR] No se encontró archivo crudo de Víctimas en {carpeta_data_raw}", file=sys.stderr)
        sys.exit(1)

    formato_detectado = archivo_casos.suffix.replace(".", "").lower()
    print(f"\n[ARCHIVOS LOCALIZADOS ({formato_detectado.upper()})]")
    print(f"  - Casos:    {archivo_casos.name} ({archivo_casos.parent.name}/)")
    print(f"  - Víctimas: {archivo_victimas.name} ({archivo_victimas.parent.name}/)")

    # Cargar DataFrames
    df_casos = cargar_datos(archivo_casos)
    df_victimas = cargar_datos(archivo_victimas)

    # Ejecutar validación
    resultados = validar_integridad_relacional(df_casos, df_victimas, hecho)

    # Guardar reporte
    guardar_reporte(hecho, formato_detectado, resultados)

    print("\n" + "=" * 75)
    print(f"[INFO] Auditoría relacional completada para: {hecho} ({formato_detectado.upper()})")
    print("=" * 75)


if __name__ == "__main__":
    main()

