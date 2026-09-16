# Hecho Victimizante: Violencia Sexual

## 1. Definición y Alcance
La violencia sexual en el conflicto armado colombiano ha sido utilizada sistemáticamente como arma de guerra, mecanismo de terror, control social y castigo colectivo contra las comunidades, con una desproporcionada afectación sobre mujeres, niñas y personas con identidades de género y orientaciones sexuales diversas (LGBTIQ+).

## 2. Estructura Local
- `data/raw/`: Respaldos en CSV crudos descargados desde la API Socrata (casos y víctimas).
- `data/processed/`: Consolidado tras estandarización de municipios, codificación de género y cruce con el nivel agregado.
- `data/features/`: Dataset analítico con tasas de ocurrencia y variables de persistencia territorial.
- `notebooks/`: Análisis exploratorio enfocado en tipologías, perfiles de víctimas e impunidad.
- `modelos/`: Modelo clasificador de riesgo municipal.
- `reports/`: Gráficos de tendencias temporales y mapas departamentales.

## 3. Variables Críticas en este Hecho
- `modalidad`: Agresiones, violaciones, esclavitud sexual u otras conductas tipificadas.
- `sexo` y `genero`: Enfoque diferencial de género.
- `presunto_responsable`: Caracterización de actores (bloques paramilitares, frentes guerrilleros, etc.).
- `subregistro`: Consideración metodológica fundamental para la interpretación de resultados.

