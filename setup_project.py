"""
setup_project.py
================
Script de scaffolding para inicializar la estructura de carpetas y archivos base
del proyecto de análisis y predicción de Memoria Histórica de Colombia.

Uso:
    python setup_project.py
"""

from pathlib import Path
import sys

# Definición de la estructura de directorios
DIRECTORIOS = [
    # Hecho: Reclutamiento de Niños y Niñas
    Path("hechos/reclutamiento_niños/data/raw"),
    Path("hechos/reclutamiento_niños/data/raw/json"),
    Path("hechos/reclutamiento_niños/data/raw/csv"),
    Path("hechos/reclutamiento_niños/data/processed"),
    Path("hechos/reclutamiento_niños/data/features"),
    Path("hechos/reclutamiento_niños/notebooks"),
    Path("hechos/reclutamiento_niños/modelos"),
    Path("hechos/reclutamiento_niños/reports"),
    
    # Hecho: Violencia Sexual
    Path("hechos/violencia_sexual/data/raw"),
    Path("hechos/violencia_sexual/data/raw/json"),
    Path("hechos/violencia_sexual/data/raw/csv"),
    Path("hechos/violencia_sexual/data/processed"),
    Path("hechos/violencia_sexual/data/features"),
    Path("hechos/violencia_sexual/notebooks"),
    Path("hechos/violencia_sexual/modelos"),
    Path("hechos/violencia_sexual/reports"),
    
    # Módulos y utilidades generales
    Path("scripts"),
    Path("sql"),
    Path("config"),
    Path("docs"),
    Path("logs"),
    Path("reports"),
    Path("tests"),
]

# Definición de archivos base (placeholders vacíos si no existen)
ARCHIVOS_BASE = [
    # Configuración y contexto por hecho
    Path("hechos/reclutamiento_niños/config.yaml"),
    Path("hechos/reclutamiento_niños/README.md"),
    Path("hechos/violencia_sexual/config.yaml"),
    Path("hechos/violencia_sexual/README.md"),
    
    # Scripts del pipeline
    Path("scripts/01_extraer_api.py"),
    Path("scripts/02_validar_estructura.py"),
    Path("scripts/03_unificar_datos.py"),
    Path("scripts/04_crear_features.py"),
    Path("scripts/05_entrenar_modelo.py"),
    Path("scripts/06_cargar_mysql.py"),
    Path("scripts/07_ejecutar_todos.py"),
    
    # Scripts SQL
    Path("sql/schema.sql"),
    Path("sql/queries_analiticas.sql"),
    
    # Archivos de configuración
    Path("config/api_endpoints.yaml"),
    Path("config/columnas_requeridas.yaml"),
    Path("config/config_global.yaml"),
    
    # Documentación técnica y funcional
    Path("docs/01_instalacion.md"),
    Path("docs/02_flujo_pipeline.md"),
    Path("docs/03_api_endpoints.md"),
    Path("docs/04_diccionario_datos.md"),
    Path("docs/05_preguntas_analisis.md"),
    
    # Raíz del proyecto
    Path("requirements.txt"),
    Path(".env.example"),
    Path(".gitignore"),
    Path("README.md"),
]


def crear_estructura():
    print("=" * 70)
    print("INICIALIZACIÓN DEL PROYECTO: MEMORIA HISTÓRICA PREDICTIVA")
    print("=" * 70)
    
    # 1. Crear directorios
    print("\n[PASO 1/2] Creando carpetas del proyecto...")
    carpetas_creadas = 0
    for dir_path in DIRECTORIOS:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"  [DIR CREADA]  {dir_path}")
            carpetas_creadas += 1
        else:
            print(f"  [DIR EXISTE]  {dir_path}")
            
    # 2. Crear archivos placeholders si no existen
    print("\n[PASO 2/2] Creando archivos base (placeholders)...")
    archivos_creados = 0
    for file_path in ARCHIVOS_BASE:
        # Asegurar directorio padre
        file_path.parent.mkdir(parents=True, exist_ok=True)
        if not file_path.exists():
            file_path.touch()
            print(f"  [FILE CREADO] {file_path}")
            archivos_creados += 1
        else:
            print(f"  [FILE EXISTE] {file_path}")
            
    print("\n" + "=" * 70)
    print(f"ESTRUCTURA COMPLETADA EXITOSAMENTE")
    print(f"-> Nuevas carpetas: {carpetas_creadas}")
    print(f"-> Nuevos archivos: {archivos_creados}")
    print("=" * 70)


if __name__ == "__main__":
    try:
        crear_estructura()
    except Exception as e:
        print(f"\n[ERROR] Ocurrió una falla al crear la estructura: {e}", file=sys.stderr)
        sys.exit(1)

