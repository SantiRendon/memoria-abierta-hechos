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
             [ 02_1_validar_integridad.py ]
        (Auditoría PK-FK, huérfanos y total_de_v_ctimas)
                                │
                                ▼
                    [ 03_consolidar_datos.py ]
          (Cruce relacional, normalización DANE y GeoJSON)
                                │
                                ▼
                 hechos/{h}/data/processed/{csv,json}/
                       {h}_consolidado.{csv,json}
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
  - Opciones de `--formato` (`auto`, `json`, `csv`).
- **Procesamiento:**
  - Detección automática del formato según terminación del endpoint.
  - Peticiones paginadas (`$limit` y `$offset`) hasta agotar registros.
  - Notificación de progreso por lotes en consola.
- **Salida:**
  - `hechos/{hecho}/data/raw/{json,csv}/casos_{hecho}_raw_yyyy-mm-dd.{json,csv}`
  - `hechos/{hecho}/data/raw/{json,csv}/victimas_{hecho}_raw_yyyy-mm-dd.{json,csv}`

---

### Script `02_validar_estructura.py`
- **Propósito:** Validar la calidad y conformidad del esquema de datos antes de iniciar transformaciones complejas.
- **Entrada:** Archivos crudos en `hechos/{hecho}/data/raw/` y reglas modulares en `config/esquema_datos.yaml` / `config/columnas_requeridas.yaml`.
- **Procesamiento:**
  - Selección de formato (`--formato auto|json|csv`).
  - Verifica presencia de columnas transversales obligatorias (`id_caso`, `a_o`, `municipio`, etc.) y específicas por hecho.
  - Filtra metadatos de Socrata (`:id`, `:created_at`).
  - Analiza porcentajes de nulos y cardinalidad/unicidad.
- **Salida:**
  - Log en consola con dictamen claro.
  - Reporte JSON de calidad en `hechos/{hecho}/reports/calidad_datos_{hecho}_{formato}_{fecha}.json`.

---

### Script `02_1_validar_integridad.py`
- **Propósito:** Auditar la integridad relacional referencial (PK-FK) y la coherencia cuantitativa de víctimas entre las tablas de Casos y Víctimas.
- **Entrada:** Archivos crudos de Casos y Víctimas de un hecho específico.
- **Procesamiento:**
  - **Integridad PK-FK:** Detección de casos huérfanos (sin víctimas) y víctimas huérfanas (sin caso existente en tabla casos).
  - **Consistencia Numérica:** Compara el valor numérico declarado en `total_de_v_ctimas_del_caso` contra el conteo real de registros asociados en Víctimas.
  - **Clasificación de Discrepancias:** Guarda arrays de casos discrepantes identificando `MAYOR_EN_CASO` (declara más de las que hay) y `MENOR_EN_CASO` (hay más registros que los declarados).
  - **Consistencia Espacio-Temporal:** Verifica coherencia de `a_o` y `c_digo_dane_de_municipio` entre caso y víctimas vinculadas.
- **Salida:**
  - Dictamen en consola (`APROBADO PERFECTO`, `APROBADO CON OBSERVACIONES` o `REVISIÓN CRÍTICA`).
  - Reporte JSON detallado en `hechos/{hecho}/reports/integridad_relacional_{hecho}_{formato}_{fecha}.json`.

---

### Script `03_consolidar_datos.py`
- **Propósito:** Limpiar, homogeneizar y consolidar en una tabla analítica unificada a nivel de víctima los registros de Casos y Víctimas, integrando variables contextuales del evento.
- **Entrada:**
  - Parámetro `--hecho` (`reclutamiento_niños`, `violencia_sexual`).
  - Parámetro `--formato-entrada` (`auto`, `json`, `csv`): permite escoger procesar los crudos CSV o JSON.
  - Parámetro `--fecha`: snapshot específico (opcional).
- **Procesamiento:**
  - Filtrado de columnas de metadatos Socrata (`:id`, `:created_at`, etc.).
  - Normalización de llaves `id_caso` e `id_persona` (sin decimales ni espacios).
  - Estandarización de códigos DANE a 5 dígitos (`zfill(5)`).
  - Extracción de coordenadas numéricas (`latitud`, `longitud`) a partir de geometrías GeoJSON Point.
  - Merge relacional `left` por `id_caso` sin colisión de columnas transversales.
  - Trazabilidad con `hecho_victimizante` y `fecha_consolidacion`.
- **Salida:**
  - Parámetro `--formato-salida` (`csv`, `json`, `ambos`).
  - `hechos/{hecho}/data/processed/csv/{hecho}_consolidado_{fecha}.csv`
  - `hechos/{hecho}/data/processed/json/{hecho}_consolidado_{fecha}.json`
  - Enlaces directos canónicos: `hechos/{hecho}/data/processed/{hecho}_consolidado.{csv,json}`

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

