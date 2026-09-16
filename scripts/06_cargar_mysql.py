"""
06_cargar_mysql.py
==================
Propósito:
    Conectar a la base de datos MySQL, insertar las dimensiones y cargar
    los registros de hechos y víctimas procesados para su consumo en Power BI.

Uso:
    python scripts/06_cargar_mysql.py --hecho reclutamiento_niños
    python scripts/06_cargar_mysql.py --hecho violencia_sexual
"""

import os
import sys
import argparse
from pathlib import Path
import pandas as pd
import mysql.connector
from dotenv import load_dotenv

# Cargar credenciales desde .env
load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "memoria_historica")


def obtener_conexion():
    """Establece conexión con el servidor MySQL."""
    print(f"[CONEXIÓN] Conectando a MySQL ({DB_HOST}:{DB_PORT}/{DB_NAME})...")
    # TODO: Manejar excepciones de conexión (ej. credenciales inválidas o servidor apagado)
    # try:
    #     conexion = mysql.connector.connect(
    #         host=DB_HOST,
    #         port=DB_PORT,
    #         user=DB_USER,
    #         password=DB_PASSWORD,
    #         database=DB_NAME
    #     )
    #     print("  [OK] Conexión establecida exitosamente.")
    #     return conexion
    # except mysql.connector.Error as err:
    #     print(f"  [ERROR] Falló la conexión: {err}")
    #     return None
    return None


def cargar_a_mysql(ruta_datos_procesados, hecho):
    """
    Inserta o actualiza datos en las tablas:
    - dim_municipio
    - dim_responsable
    - hechos_casos
    - hechos_victimas
    """
    print(f"[CARGA A BD] Preparando datos para el hecho: {hecho}")

    if not ruta_datos_procesados.exists():
        print(f"  [ALERTA] Archivo procesado no encontrado: {ruta_datos_procesados}")
        return False

    conexion = obtener_conexion()
    if not conexion:
        print("  [TODO] Conexión a MySQL deshabilitada en modo placeholder.")
        return False

    # TODO: 1. Leer dataset unificado
    # df = pd.read_csv(ruta_datos_procesados)

    # TODO: 2. Poblar tabla dim_municipio (INSERT IGNORE / ON DUPLICATE KEY UPDATE)
    # cursor = conexion.cursor()
    # sql_municipio = '''
    #     INSERT INTO dim_municipio (codigo_dane, municipio, departamento, region)
    #     VALUES (%s, %s, %s, %s)
    #     ON DUPLICATE KEY UPDATE municipio=VALUES(municipio)
    # '''
    # cursor.executemany(sql_municipio, datos_municipios)

    # TODO: 3. Poblar tabla dim_responsable
    # sql_responsable = '''
    #     INSERT IGNORE INTO dim_responsable (categoria_macro, descripcion_detalle)
    #     VALUES (%s, %s)
    # '''

    # TODO: 4. Insertar en tabla hechos_casos
    # sql_casos = '''
    #     INSERT INTO hechos_casos (id_caso, tipo_hecho, anio, mes, dia, codigo_dane, modalidad, total_victimas)
    #     VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    #     ON DUPLICATE KEY UPDATE total_victimas=VALUES(total_victimas)
    # '''

    # TODO: 5. Confirmar transacción (commit)
    # conexion.commit()
    # cursor.close()
    # conexion.close()
    # print("[ÉXITO] Carga masiva en MySQL finalizada.")

    return True


def main():
    parser = argparse.ArgumentParser(description="Cargador de datos analíticos a MySQL")
    parser.add_argument(
        "--hecho",
        type=str,
        required=True,
        choices=["reclutamiento_niños", "violencia_sexual"],
        help="Nombre del hecho victimizante a cargar"
    )
    args = parser.parse_args()
    hecho = args.hecho

    print("=" * 70)
    print(f"[ETAPA 06] CARGA A BASE DE DATOS MYSQL - HECHO: {hecho.upper()}")
    print("=" * 70)

    carpeta_processed = Path(f"hechos/{hecho}/data/processed")
    ruta_procesado = carpeta_processed / f"{hecho}_unificado.csv"

    cargar_a_mysql(ruta_procesado, hecho)


if __name__ == "__main__":
    main()

