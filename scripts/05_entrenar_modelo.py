"""
05_entrenar_modelo.py
=====================
Propósito:
    Entrenar un modelo de Machine Learning (ej. Random Forest) para predecir
    el nivel de riesgo o volumen de hechos por municipio, evaluar métricas
    y serializar el modelo final con Joblib en 'modelos/'.

Uso:
    python scripts/05_entrenar_modelo.py --hecho reclutamiento_niños
    python scripts/05_entrenar_modelo.py --hecho violencia_sexual
"""

import os
import sys
import argparse
import json
from pathlib import Path
import pandas as pd
import joblib

# Importaciones de Scikit-Learn
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, f1_score, accuracy_score


def entrenar(ruta_features_csv, ruta_salida_modelo, ruta_salida_reporte):
    """
    Entrena el modelo predictivo base, evalúa sobre test set y serializa el artefacto.
    """
    print(f"[ENTRENAMIENTO ML] Leyendo matriz de características: {ruta_features_csv.name}")

    if not ruta_features_csv.exists():
        print(f"  [ALERTA] Archivo de features no encontrado: {ruta_features_csv}")
        return None

    # TODO: Cargar dataset de entrenamiento
    # df = pd.read_csv(ruta_features_csv)

    # TODO: 1. Seleccionar variables predictoras (X) y variable objetivo (y)
    # columnas_predictoras = ['victimas_lag1', 'victimas_lag2', 'media_movil_3y']
    # X = df[columnas_predictoras].fillna(0)
    # y = df['target_alerta_riesgo']

    # TODO: 2. División temporal o aleatoria estratificada (Train / Test)
    # X_train, X_test, y_train, y_test = train_test_split(
    #     X, y, test_size=0.20, random_state=42, stratify=y
    # )

    # TODO: 3. Ajustar el modelo de Machine Learning
    # print("  [INFO] Entrenando clasificador Random Forest...")
    # modelo = RandomForestClassifier(n_estimators=100, max_depth=6, random_state=42)
    # modelo.fit(X_train, y_train)

    # TODO: 4. Evaluación de métricas
    # y_pred = modelo.predict(X_test)
    # f1 = f1_score(y_test, y_pred, average='weighted')
    # acc = accuracy_score(y_test, y_pred)
    # print(f"  [MÉTRICAS] Accuracy: {acc:.4f} | F1-Score: {f1:.4f}")

    # TODO: 5. Serializar modelo en formato .joblib
    # ruta_salida_modelo.parent.mkdir(parents=True, exist_ok=True)
    # joblib.dump(modelo, ruta_salida_modelo)
    # print(f"[ÉXITO] Modelo serializado en: {ruta_salida_modelo}")

    # TODO: 6. Guardar métricas en JSON
    # ruta_salida_reporte.parent.mkdir(parents=True, exist_ok=True)
    # with open(ruta_salida_reporte, 'w', encoding='utf-8') as f:
    #     json.dump({'accuracy': acc, 'f1_weighted': f1}, f, indent=4)

    print("  [TODO] Lógica de entrenamiento y evaluación pendiente de implementación.")
    return None


def main():
    parser = argparse.ArgumentParser(description="Entrenador de modelo de Machine Learning")
    parser.add_argument(
        "--hecho",
        type=str,
        required=True,
        choices=["reclutamiento_niños", "violencia_sexual"],
        help="Nombre del hecho victimizante a modelar"
    )
    args = parser.parse_args()
    hecho = args.hecho

    print("=" * 70)
    print(f"[ETAPA 05] ENTRENAMIENTO DE MODELO - HECHO: {hecho.upper()}")
    print("=" * 70)

    carpeta_features = Path(f"hechos/{hecho}/data/features")
    carpeta_modelos = Path(f"hechos/{hecho}/modelos")
    carpeta_reports = Path(f"hechos/{hecho}/reports")

    carpeta_modelos.mkdir(parents=True, exist_ok=True)
    carpeta_reports.mkdir(parents=True, exist_ok=True)

    ruta_features = carpeta_features / f"features_{hecho}.csv"
    ruta_modelo = carpeta_modelos / f"modelo_{hecho}_riesgo.joblib"
    ruta_reporte = carpeta_reports / f"metricas_modelo_{hecho}.json"

    entrenar(ruta_features, ruta_modelo, ruta_reporte)


if __name__ == "__main__":
    main()

