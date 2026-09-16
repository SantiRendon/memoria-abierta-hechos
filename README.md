# Memoria Histórica Predictiva (Memoria Abierta Hechos)

Sistema integral de extracción, procesamiento, análisis y modelado predictivo a partir de los datos abiertos del **Centro Nacional de Memoria Histórica (CNMH)** de Colombia publicados en el portal nacional [datos.gov.co](https://www.datos.gov.co).

Este proyecto procesa inicialmente dos hechos victimizantes de alto impacto en el conflicto armado colombiano:
1. **Reclutamiento y Utilización de Niños, Niñas y Adolescentes**
2. **Violencia Sexual**

---

## Objetivos del Proyecto

- **Monitoreo Histórico y Analítico:**
  - Ingestar y unificar los datos a nivel agregado (**Casos**) e individual (**Víctimas**).
  - Limpiar, estructurar y cargar un modelo relacional en **MySQL** optimizado para visualización e inteligencia de negocios con **Power BI**.
  - Responder preguntas analíticas sobre concentración territorial (municipios/departamentos), líneas de tiempo y presuntos actores responsables.

- **Analítica Predictiva:**
  - Generar variables geo-espaciales, temporales y de dinámica de conflicto.
  - Entrenar modelos de Machine Learning (clasificación / regresión) para estimar riesgo territorial, severidad o tipología de hechos a nivel municipal.
  - Generar alertas tempranas e insumos cuantitativos para investigación y formulación de políticas públicas.

---

## Estructura del Proyecto

```text
memoria-abierta-hechos/
│
├── hechos/
│   ├── reclutamiento_niños/
│   │   ├── data/
│   │   │   ├── raw/                 # Datos crudos extraídos de la API
│   │   │   ├── processed/           # Datos limpios y unificados
│   │   │   └── features/            # Conjuntos de variables para ML
│   │   ├── notebooks/               # Análisis exploratorio (EDA)
│   │   ├── modelos/                 # Modelos entrenados (.joblib)
│   │   ├── reports/                 # Figuras, métricas y reportes
│   │   ├── config.yaml              # Parámetros propios del hecho
│   │   └── README.md                # Contexto y particularidades
│   │
│   └── violencia_sexual/
│       └── (misma estructura modular)
│
├── scripts/
│   ├── 01_extraer_api.py            # Descarga paginada desde datos.gov.co
│   ├── 02_validar_estructura.py      # Control de calidad y esquema
│   ├── 03_unificar_datos.py         # Cruce entre Casos y Víctimas
│   ├── 04_crear_features.py         # Ingeniería de características
│   ├── 05_entrenar_modelo.py        # Modelado predictivo (Scikit-Learn)
│   ├── 06_cargar_mysql.py           # Persistencia en base de datos relacional
│   └── 07_ejecutar_todos.py         # Orquestador del pipeline completo
│
├── sql/
│   ├── schema.sql                   # DDL de tablas dimensionales y hechos
│   └── queries_analiticas.sql       # Consultas SQL analíticas
│
├── config/
│   ├── api_endpoints.yaml           # Endpoints SODA y parámetros
│   ├── columnas_requeridas.yaml     # Reglas de validación de datos
│   └── config_global.yaml           # Rutas, logs y base de datos
│
├── docs/
│   ├── 01_instalacion.md            # Guía detallada de instalación
│   ├── 02_flujo_pipeline.md         # Documentación técnica del pipeline
│   ├── 03_api_endpoints.md         # Documentación de APIs y SoQL
│   ├── 04_diccionario_datos.md      # Diccionario de campos
│   └── 05_preguntas_analisis.md     # Preguntas de negocio e hipótesis
│
├── logs/                            # Registro de eventos de ejecución
├── reports/                         # Reportes consolidados
├── tests/                           # Pruebas de integración y datos
│
├── requirements.txt                 # Dependencias de Python
├── .env.example                     # Plantilla de credenciales
├── .gitignore                       # Exclusiones de control de versiones
├── README.md                        # Documento principal
└── setup_project.py                 # Script de inicialización
```

---

## Flujo del Pipeline de Datos

```text
[ API datos.gov.co ] (Casos y Víctimas)
         │
         ▼
[ 01_extraer_api.py ] ──────> Guarda CSVs en data/raw/
         │
         ▼
[ 02_validar_estructura.py ] ─> Verifica columnas requeridas y tipos
         │
         ▼
[ 03_unificar_datos.py ] ────> Cruza Casos + Víctimas por id_caso ──> data/processed/
         │
         ├───> [ 04_crear_features.py ] ──> data/features/
         │             │
         │             ▼
         │     [ 05_entrenar_modelo.py ] ─> Guarda modelo en modelos/
         │
         ▼
[ 06_cargar_mysql.py ] ──────> Carga en MySQL (schema dimensional)
         │
         ▼
[ Dashboard Power BI ] <───── Conexión directa a MySQL
```

---

## Stack Tecnológico

- **Lenguaje:** Python 3.10+
- **Procesamiento de Datos:** `pandas`, `numpy`
- **Extracción:** `requests` (API Socrata / SODA)
- **Machine Learning:** `scikit-learn`, `joblib`
- **Almacenamiento:** MySQL Server
- **Visualización:** Power BI, `matplotlib`, `seaborn`
- **Configuración:** `pyyaml`, `python-dotenv`

---

## Guía de Instalación Rápida

1. **Clonar o abrir el repositorio en tu terminal:**
   ```bash
   cd c:\Users\Santiago\Desktop\memoria-abierta-hechos
   ```

2. **Crear y activar un entorno virtual de Python:**
   ```bash
   python -m venv venv
   # En Windows PowerShell:
   .\venv\Scripts\Activate.ps1
   # O en CMD:
   .\venv\Scripts\activate.bat
   ```

3. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar credenciales:**
   ```bash
   copy .env.example .env
   ```
   Edita `.env` con tus contraseñas locales de MySQL y tu token de datos abiertos.

5. **Inicializar estructura física:**
   ```bash
   python setup_project.py
   ```

---

## Guía de Uso del Pipeline

Puedes ejecutar cada etapa individualmente para monitorear el progreso paso a paso:

```bash
# 1. Extracción desde API
python scripts/01_extraer_api.py --hecho reclutamiento_niños

# 2. Validación de calidad
python scripts/02_validar_estructura.py --hecho reclutamiento_niños

# 3. Cruce y unificación
python scripts/03_unificar_datos.py --hecho reclutamiento_niños

# 4. Ingeniería de variables para ML
python scripts/04_crear_features.py --hecho reclutamiento_niños

# 5. Entrenamiento de modelo predictivo
python scripts/05_entrenar_modelo.py --hecho reclutamiento_niños

# 6. Carga a MySQL
python scripts/06_cargar_mysql.py --hecho reclutamiento_niños
```

O ejecutar el orquestador global para procesar el flujo completo:
```bash
python scripts/07_ejecutar_todos.py --hecho reclutamiento_niños
```

---

## Documentación Detallada

Para más detalles, consulta la carpeta `docs/`:
- [Guía de Instalación y Requisitos](docs/01_instalacion.md)
- [Flujo Detallado del Pipeline](docs/02_flujo_pipeline.md)
- [Documentación de APIs y Endpoints](docs/03_api_endpoints.md)
- [Diccionario de Datos](docs/04_diccionario_datos.md)
- [Preguntas de Negocio e Hipótesis de Investigación](docs/05_preguntas_analisis.md)

---

## Créditos y Licencia

- **Fuente de Datos:** Centro Nacional de Memoria Histórica (CNMH) y Portal Nacional de Datos Abiertos de Colombia ([datos.gov.co](https://www.datos.gov.co)).
- **Autor / Analista:** Santi Rendon
- **Licencia:** MIT License (Ver archivo [LICENSE](LICENSE)).

