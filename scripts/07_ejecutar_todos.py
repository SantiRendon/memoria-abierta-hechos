"""
07_ejecutar_todos.py
====================
Propósito:
    Orquestador principal del pipeline. Ejecuta de manera secuencial los scripts
    01 al 06 para un hecho victimizante específico o para todos los hechos configurados,
    monitoreando tiempos de ejecución y deteniendo el flujo ante posibles fallos.

Uso:
    python scripts/07_ejecutar_todos.py --hecho reclutamiento_niños
    python scripts/07_ejecutar_todos.py --hecho violencia_sexual
    python scripts/07_ejecutar_todos.py --todos
"""

import sys
import subprocess
import argparse
import time
from pathlib import Path

# Lista de scripts que conforman el pipeline secuencial
PIPELINE_SCRIPTS = [
    ("01_extraer_api.py", "Descarga de datos crudos desde API"),
    ("02_validar_estructura.py", "Validación de calidad y esquema"),
    ("02_1_validar_integridad.py", "Validación de integridad referencial PK-FK y consistencia numérica"),
    ("03_unificar_datos.py", "Cruce y normalización de casos y víctimas"),
    ("04_crear_features.py", "Ingeniería de variables para ML"),
    ("05_entrenar_modelo.py", "Entrenamiento y evaluación de modelo"),
    ("06_cargar_mysql.py", "Carga analítica a base de datos MySQL"),
]


def ejecutar_script(script_nombre, hecho):
    """Ejecuta un script secundario pasando el parámetro --hecho."""
    ruta_script = Path("scripts") / script_nombre
    comando = [sys.executable, str(ruta_script), "--hecho", hecho]

    print(f"\n>>> [ORQUESTADOR] Iniciando: {script_nombre} ...")
    inicio = time.time()

    # TODO: Configurar registro de salida en archivo de logs (logs/ejecucion_pipeline.log)
    try:
        resultado = subprocess.run(comando, check=True)
        duracion = time.time() - inicio
        print(f">>> [OK] {script_nombre} completado en {duracion:.2f}s")
        return True
    except subprocess.CalledProcessError as e:
        print(f">>> [FALLA] Error al ejecutar {script_nombre} (Código {e.returncode})", file=sys.stderr)
        # TODO: Decidir si detener todo el pipeline o continuar según severidad
        return False


def ejecutar_pipeline_hecho(hecho):
    """Ejecuta todos los pasos del pipeline para un hecho determinado."""
    print("=" * 75)
    print(f"INICIANDO PIPELINE COMPLETO PARA: {hecho.upper()}")
    print("=" * 75)

    tiempo_total_inicio = time.time()

    for script, descripcion in PIPELINE_SCRIPTS:
        print(f"\n[FASE] {descripcion}")
        exito = ejecutar_script(script, hecho)
        if not exito:
            print(f"\n[INTERRUPCIÓN] El pipeline se detuvo por error en: {script}", file=sys.stderr)
            return False

    tiempo_total = time.time() - tiempo_total_inicio
    print("\n" + "=" * 75)
    print(f"PIPELINE FINALIZADO CON ÉXITO PARA: {hecho.upper()}")
    print(f"Tiempo total transcurrido: {tiempo_total:.2f}s")
    print("=" * 75)
    return True


def main():
    parser = argparse.ArgumentParser(description="Orquestador general del pipeline analítico")
    parser.add_argument(
        "--hecho",
        type=str,
        choices=["reclutamiento_niños", "violencia_sexual"],
        help="Hecho victimizante específico a procesar"
    )
    parser.add_argument(
        "--todos",
        action="store_true",
        help="Ejecutar el pipeline para todos los hechos soportados"
    )
    args = parser.parse_args()

    if not args.hecho and not args.todos:
        parser.print_help()
        print("\n[ALERTA] Debes especificar --hecho <nombre> o la opción --todos.")
        sys.exit(1)

    hechos_a_procesar = []
    if args.todos:
        hechos_a_procesar = ["reclutamiento_niños", "violencia_sexual"]
    else:
        hechos_a_procesar = [args.hecho]

    for hecho in hechos_a_procesar:
        exito = ejecutar_pipeline_hecho(hecho)
        if not exito:
            sys.exit(1)


if __name__ == "__main__":
    main()

