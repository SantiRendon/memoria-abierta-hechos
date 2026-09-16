# Hecho Victimizante: Reclutamiento y Utilización de Niños, Niñas y Adolescentes

## 1. Definición y Alcance
El reclutamiento y utilización ilícita de menores de 18 años por parte de actores armados ilegales (guerrillas, paramilitares y grupos armados organizados residuales) constituye una de las más graves violaciones al Derecho Internacional Humanitario en Colombia.

## 2. Estructura Local
- `data/raw/`: Respaldos en CSV crudos descargados desde la API Socrata (casos y víctimas).
- `data/processed/`: Archivo consolidado tras cruzar `id_caso` y normalizar nombres de municipios y códigos DANE.
- `data/features/`: Conjunto de datos tabulares con variables rezagadas (*lags*) por municipio y año listos para modelado predictivo.
- `notebooks/`: Espacio para análisis exploratorio, pirámides etarias y mapas de calor.
- `modelos/`: Almacén del estimador predictivo (`.joblib`).
- `reports/`: Exportaciones de métricas y gráficos para informes analíticos.

## 3. Variables Críticas en este Hecho
- `edad`: Distribución entre niñez (0-11 años) y adolescencia (12-17 años).
- `sexo`: Diferencias de roles impuestos al interior del grupo armado.
- `etnia`: Especial vulnerabilidad en resguardos indígenas y consejos comunitarios.
- `c_digo_dane_de_municipio`: Localización geoespacial de zonas de captación.

