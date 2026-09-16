"""
04_crear_features.py
====================
Propósito:
    Generar el conjunto de variables explicativas (features) espaciotemporales,
    tasas de variación, variables rezagadas (lags) y la variable objetivo
    para el entrenamiento de modelos de Machine Learning.

Uso:
    python scripts/04_crear_features.py --hecho reclutamiento_niños
    python scripts/04_crear_features.py --hecho violencia_sexual
"""

import os
import sys
import argparse
from pathlib import Path
import pandas as pd
import numpy as np
import yaml


def construir_features(ruta_datos_procesados, ruta_salida_features):
    """
    Construye la matriz de características a nivel Municipio-Año.
    """
    print(f"[INGENIERÍA DE FEATURES] Procesando: {ruta_datos_procesados.name}")

    if not ruta_datos_procesados.exists():
        print(f"  [ALERTA] Archivo procesado no encontrado: {ruta_datos_procesados}")
        return None

    # TODO: Cargar datos unificados
    # df = pd.read_csv(ruta_datos_procesados)

    # TODO: 1. Agrupar por Municipio y Año para calcular la intensidad histórica
    # df_panel = df.groupby(['c_digo_dane_de_municipio', 'municipio', 'departamento', 'a_o']).agg(
    #     total_casos=('id_caso', 'nunique'),
    #     total_victimas=('total_de_v_ctimas_del_caso', 'sum')
    # ).reset_index()

    # TODO: 2. Crear variables rezagadas (Lags temporales de 1 y 2 años)
    # df_panel = df_panel.sort_values(by=['c_digo_dane_de_municipio', 'a_o'])
    # df_panel['victimas_lag1'] = df_panel.groupby('c_digo_dane_de_municipio')['total_victimas'].shift(1).fillna(0)
    # df_panel['victimas_lag2'] = df_panel.groupby('c_digo_dane_de_municipio')['total_victimas'].shift(2).fillna(0)

    # TODO: 3. Media móvil de los últimos 3 años (tendencia de riesgo persistente)
    # df_panel['media_movil_3y'] = df_panel.groupby('c_digo_dane_de_municipio')['total_victimas'].transform(
    #     lambda s: s.rolling(window=3, min_periods=1).mean()
    # )

    # TODO: 4. Definir variable objetivo (Target)
    # Ejemplo clasificación: 1 si el año tuvo más de X víctimas (Alerta Alta), 0 en caso contrario
    # umbral = 3
    # df_panel['target_alerta_riesgo'] = (df_panel['total_victimas'] >= umbral).astype(int)

    # TODO: Guardar dataset con features
    # ruta_salida_features.parent.mkdir(parents=True, exist_ok=True)
    # df_panel.to_csv(ruta_salida_features, index=False, encoding='utf-8')
    # print(f"[ÉXITO] Matriz de características guardada en: {ruta_salida_features}")

    print("  [TODO] Lógica de feature engineering pendiente de implementación.")
    return None


def main():
    parser = argparse.ArgumentParser(description="Generador de features para Machine Learning")
    parser.add_argument(
        "--hecho",
        type=str,
        required=True,
        choices=["reclutamiento_niños", "violencia_sexual"],
        help="Nombre del hecho victimizante"
    )
    args = parser.parse_args()
    hecho = args.hecho

    print("=" * 70)
    print(f"[ETAPA 04] CREACIÓN DE FEATURES - HECHO: {hecho.upper()}")
    print("=" * 70)

    carpeta_processed = Path(f"hechos/{hecho}/data/processed")
    carpeta_features = Path(f"hechos/{hecho}/data/features")
    carpeta_features.mkdir(parents=True, exist_ok=True)

    ruta_procesado = carpeta_processed / f"{hecho}_unificado.csv"
    ruta_features = carpeta_features / f"features_{hecho}.csv"

    construir_features(ruta_procesado, ruta_features)


if __name__ == "__main__":
    main()

