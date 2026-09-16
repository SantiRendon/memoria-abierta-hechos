# Flujo del Pipeline de Datos (ETL y Machine Learning)

Este documento detalla la arquitectura operativa del pipeline, describiendo las entradas, transformaciones y salidas de cada uno de los scripts que componen el flujo de datos.

---

## 1. Diagrama de Flujo General

```text
                     [ Portal datos.gov.co ]
                               │
            ┌──────────────────┴──────────────────┐
            ▼                                     ▼
   (Endpoint Casos)                     (Endpoint Víctimas)
            │                                     │
            └──────────────────┬──────────────────┘
                               ▼
                   [ 01_extraer_api.py ]
                               │
             ┌─────────────────┴─────────────────┐
             ▼                                   ▼
  hechos/{h}/data/raw/                hechos/{h}/data/raw/
      casos.csv                           victimas.csv
             │                                   │
             └─────────────────┬─────────────────┘
                               ▼
               [ 02_validar_estructura.py ]
            (Valida esquema, nulos, consistencia)
                               │
                               ▼
                   [ 03_unificar_datos.py ]
          (Une casos y víctimas por id_caso + DANE)
                               │
                               ▼
                  hechos/{h}/data/processed/
                        hechos_unificados.csv
                               │
             ┌─────────────────┴─────────────────┐
             ▼                                   ▼
   [ 04_crear_features.py ]             [ 06_cargar_mysql.py ]
             │                                   │
             ▼                                   ▼
  hechos/{h}/data/features/               Base de Datos MySQL
     dataset_modelo.csv                   (Tablas analíticas)
             │                                   │
             ▼                                   ▼
  [ 05_entrenar_modelo.py ]                [ Power BI Dashboard ]
             │
             ▼
  hechos/{h}/modelos/
     modelo_riesgo.joblib
```

---

## 2. Descripción Paso a Paso de los Scripts

### Script `01_extraer_api.py`
- **Propósito:** Conectarse al API de datos abiertos de Colombia (`datos.gov.co`) y descargar los registros históricos correspondientes al hecho victimizante seleccionado.
- **Entrada:**
  - Configuración de URLs y parámetros en `config/api_endpoints.yaml`.
  - Token de acceso en `.env` (si existe).
  - Parámetro `--hecho` (ej. `reclutamiento_niños` o `violencia_sexual`).
- **Procesamiento:**
  - Realiza peticiones HTTP GET paginadas (`$limit` y `$offset`) hasta agotar registros.
  - Informa el avance por lotes en la consola.
- **Salida:**
  - `hechos/{hecho}/data/raw/casos_raw.csv`
  - `hechos/{hecho}/data/raw/victimas_raw.csv`

---

### Script `02_validar_estructura.py`
- **Propósito:** Validar la calidad y conformidad del esquema de datos antes de iniciar transformaciones complejas.
- **Entrada:** Archivos crudos en `hechos/{hecho}/data/raw/` y reglas en `config/columnas_requeridas.yaml`.
- **Procesamiento:**
  - Verifica presencia de columnas mandatorias (`id_caso`, `a_o`, `municipio`, etc.).
  - Analiza porcentajes de nulos y duplicados.
  - Valida tipos de datos (numéricos, fechas, texto).
- **Salida:**
  - Log en consola y reporte opcional de calidad en `hechos/{hecho}/reports/calidad_datos.txt`.

---

### Script `03_unificar_datos.py`
- **Propósito:** Realizar el cruce relacional entre el nivel agregado (Casos) y el nivel desagregado (Víctimas).
- **Entrada:**
  - `casos_raw.csv` y `victimas_raw.csv`.
- **Procesamiento:**
  - Estandarización de códigos DANE a 5 dígitos (2 departamento + 3 municipio).
  - Normalización de nombres de municipios y departamentos (mayúsculas, tildes).
  - `merge` / unión relacional a través de `id_caso`.
  - Imputación o marcado de valores faltantes conocidos.
- **Salida:**
  - `hechos/{hecho}/data/processed/datos_unificados.csv`

---

### Script `04_crear_features.py`
- **Propósito:** Construir variables calculadas (ingeniería de variables / feature engineering) para el modelo de Machine Learning.
- **Entrada:**
  - `datos_unificados.csv`.
- **Procesamiento:**
  - Agregaciones espaciotemporales: conteo de víctimas por municipio/año, ventanas móviles (lag de 1, 2 y 3 años).
  - Variables de contexto: diversidad de presuntos actores responsables, tasa de cambio interanual.
  - Codificación categórica (Target Encoding o One-Hot Encoding).
- **Salida:**
  - `hechos/{hecho}/data/features/features_entrenamiento.csv`

---

### Script `05_entrenar_modelo.py`
- **Propósito:** Entrenar, evaluar y serializar un modelo predictivo (ej. estimación del nivel de riesgo o número de casos por municipio).
- **Entrada:**
  - `features_entrenamiento.csv`.
- **Procesamiento:**
  - División temporal o estratificada en Train/Test (respetando la cronología temporal de los datos).
  - Entrenamiento del modelo base (Random Forest, Gradient Boosting o Regresión Ridge).
  - Cálculo de métricas: RMSE, MAE, R² (para regresión) o F1-score, ROC-AUC (para clasificación de alerta alta/media/baja).
  - Serialización de artefactos con `joblib`.
- **Salida:**
  - `hechos/{hecho}/modelos/modelo_predictivo.joblib`
  - `hechos/{hecho}/reports/metricas_modelo.json`

---

### Script `06_cargar_mysql.py`
- **Propósito:** Poblar el esquema de base de datos relacional en MySQL con las dimensiones y tablas de hechos procesadas.
- **Entrada:**
  - `datos_unificados.csv`.
  - Credenciales en `.env`.
- **Procesamiento:**
  - Conexión a MySQL mediante `mysql-connector-python`.
  - Carga masiva o por lotes (`INSERT ... ON DUPLICATE KEY UPDATE` o inserción limpia).
  - Poblado de `dim_municipio`, `dim_tiempo`, `dim_responsable`, `hechos_casos`, `hechos_victimas`.
- **Salida:**
  - Tablas actualizadas y listas en la base de datos `memoria_historica`.

---

### Script `07_ejecutar_todos.py`
- **Propósito:** Orquestar de forma secuencial los scripts `01` al `06` para un hecho determinado o para todos los hechos configurados.
- **Entrada:** Parámetro `--hecho` o `--todos`.
- **Procesamiento:**
  - Ejecuta cada script verificando códigos de retorno exitosos (`exit code 0`).
  - Mide tiempos de ejecución de cada fase.
  - Detiene el flujo si alguna etapa crítica falla.
- **Salida:**
  - Registro consolidado en consola y en `logs/ejecucion_pipeline.log`.

