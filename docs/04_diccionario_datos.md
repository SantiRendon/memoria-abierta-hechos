# Diccionario de Datos

Este documento define las variables y campos extraídos de las APIs de Datos Abiertos del Centro Nacional de Memoria Histórica (CNMH) para los endpoints de **Casos** y **Víctimas**.

---

## 1. Campos Comunes y Nivel Casos

| Nombre de Columna | Tipo de Dato | Nullable | Descripción | Ejemplo de Valor | Notas |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id_caso` | `VARCHAR(50)` / `BIGINT` | No | Identificador único del evento o hecho victimizante. | `"104251"` | Clave primaria a nivel caso. |
| `id_caso_relacionado` | `VARCHAR(50)` | Sí | Identificador de otro caso vinculado o conexo. | `"104250"` | Relación entre hechos múltiples. |
| `a_o` | `INT` | No | Año en el que ocurrió el hecho victimizante. | `2002` | Rango histórico analizado (1958-actual). |
| `mes` | `INT` / `VARCHAR(20)` | Sí | Mes del hecho (numérico o texto según API). | `5` o `"MAYO"` | Puede requerir estandarización a número. |
| `d_a` | `INT` | Sí | Día de ocurrencia del hecho victimizante. | `14` | Puede ser nulo en hechos con fecha indeterminada. |
| `c_digo_dane_de_municipio`| `VARCHAR(10)` | No | Código DANE oficial del municipio (5 dígitos). | `"05001"` | Fundamental para joins y mapas geoespaciales. |
| `municipio` | `VARCHAR(100)` | No | Nombre oficial del municipio colombiano. | `"MEDELLÍN"` | Estandarizado a mayúsculas sin tildes erróneas. |
| `departamento` | `VARCHAR(100)` | No | Nombre del departamento colombiano. | `"ANTIOQUIA"` | Nivel de agregación político-administrativa. |
| `regi_n` | `VARCHAR(100)` | Sí | Región geográfica o de análisis del CNMH. | `"ANDINA"` / `"URABÁ"` | Clasificación territorial contextual. |
| `modalidad` | `VARCHAR(150)` | Sí | Forma específica en que se perpetró el hecho. | `"RECLUTAMIENTO FORZADO"` | Categoría detallada de la violencia. |
| `presunto_responsable` | `VARCHAR(150)` | Sí | Grupo armado macro presuntamente responsable. | `"GUERRILLAS"` / `"PARAMILITARES"` | Categoría para análisis de responsabilidad. |
| `descripci_n_presunto` | `TEXT` | Sí | Detalle o facción específica del presunto autor. | `"FARC-EP FRENTE 5"` | Información cualitativa descriptiva. |
| `total_de_v_ctimas_del_caso`| `INT` | No | Cantidad de personas afectadas en el caso. | `3` | Métrica numérica para cuantificación de daño. |
| `latitud_longitud` | `VARCHAR(100)` | Sí | Coordenadas geográficas (lat, lon) o Point. | `"(6.25184, -75.56359)"` | Parseable en `latitud` y `longitud` float. |

---

## 2. Campos Nivel Víctimas (Desagregado)

| Nombre de Columna | Tipo de Dato | Nullable | Descripción | Ejemplo de Valor | Notas |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id_victima` | `VARCHAR(50)` / `BIGINT` | No | Identificador único del registro individual. | `"V-88231"` | Clave primaria a nivel víctima. |
| `id_caso` | `VARCHAR(50)` | No | Clave foránea que asocia a la víctima con el caso. | `"104251"` | Utilizada para el cruce en `03_unificar_datos.py`. |
| `sexo` | `VARCHAR(20)` | Sí | Sexo biológico o de identidad de la víctima. | `"MUJER"` / `"HOMBRE"` | Variable clave de enfoque diferencial. |
| `genero` | `VARCHAR(50)` | Sí | Identidad u orientación de género si está registrada. | `"LGBTIQ+"` / `"HETEROSEXUAL"` | Crucial en análisis de violencia sexual. |
| `etnia` | `VARCHAR(80)` | Sí | Pertenencia étnica autorreconocida. | `"INDÍGENA"` / `"AFROCOLOMBIANO"` | Enfoque diferencial étnico. |
| `edad` | `INT` | Sí | Edad estimada de la víctima al momento del hecho. | `14` | Crítico para menores de edad reclutados. |
| `rango_edad` | `VARCHAR(50)` | Sí | Grupo etario consolidado. | `"0-14 AÑOS"` / `"15-17 AÑOS"` | Categorización para tabulación rápida. |
| `ocupacion` | `VARCHAR(120)` | Sí | Actividad u ocupación laboral de la víctima. | `"ESTUDIANTE"` / `"CAMPESINO"` | Caracterización socioeconómica. |

---

## 3. Variables Derivadas / Calculadas (Feature Engineering)

Variables generadas durante la etapa `04_crear_features.py`:

| Nombre de Columna | Tipo de Dato | Descripción | Método de Cálculo |
| :--- | :--- | :--- | :--- |
| `fecha_caso` | `DATE` | Fecha unificada estimada del hecho. | Construida a partir de `a_o`, `mes` (o 1), `d_a` (o 1). |
| `victimas_lag_1` | `INT` | Total de víctimas en el municipio el año anterior. | Desplazamiento temporal `shift(1)` por `codigo_dane`. |
| `promedio_victimas_3y` | `FLOAT` | Media móvil de víctimas en los últimos 3 años. | `rolling(window=3).mean()`. |
| `alerta_alto_riesgo` | `TINYINT` | Indicador binario (1/0) de alta probabilidad de evento. | Umbral percentil 75 de intensidad histórica. |

