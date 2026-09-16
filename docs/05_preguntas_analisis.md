# Preguntas de Negocio, Hipótesis y Criterios de Éxito

Este documento orienta los análisis exploratorios, tableros analíticos en Power BI y experimentos predictivos de Machine Learning en el marco de la Memoria Histórica y el conflicto armado.

---

## 1. Preguntas de Negocio y Análisis

### Dimensión Temporal y Tendencias
1. ¿Cuáles fueron los periodos de mayor intensificación del **Reclutamiento de Niños y Niñas** y de la **Violencia Sexual** en Colombia?
2. ¿Existen hitos históricos (ej. desmovilizaciones, diálogos de paz, ofensivas militares) que marcaron quiebres estadísticos en la ocurrencia de estos hechos?
3. ¿Cuál es el comportamiento de estacionalidad (meses con picos recurrentes) a lo largo de las décadas?

### Dimensión Espacial y Territorial
4. ¿Cuáles son los 10 municipios con mayor número acumulado de casos y víctimas para cada hecho?
5. ¿Existen corredores geográficos o clusters territoriales donde ambos hechos victimizantes coexisten intensamente?
6. ¿Cómo se relaciona la presencia de economías ilícitas o zonas de frontera con el riesgo de reclutamiento de menores?

### Dimensión de Presuntos Responsables y Modalidades
7. ¿Qué proporción de los hechos se atribuye a grupos paramilitares, guerrillas, agentes estatales o grupos no determinados?
8. ¿Cómo cambió la participación de los distintos actores armados a lo largo del tiempo?
9. ¿Cuáles son las modalidades más frecuentes de violencia sexual y reclutamiento según la región?

### Dimensión de Enfoque Diferencial
10. ¿Cuál es la distribución por sexo y edad en las víctimas de reclutamiento?
11. ¿En qué medida las mujeres y las comunidades étnicas (indígenas y afrocolombianas) se han visto desproporcionadamente afectadas por la violencia sexual?

---

## 2. Hipótesis Iniciales de Investigación

- **Hipótesis 1 (Inercia Espaciotemporal):** Los municipios que sufrieron reclutamiento forzado o violencia sexual en el año \( t-1 \) tienen una probabilidad significativamente mayor de registrar hechos en el año \( t \).
- **Hipótesis 2 (Concentración Geográfica):** Menos del 15% de los municipios del país concentran más del 65% del total de víctimas registradas.
- **Hipótesis 3 (Divergencia de Perfil por Hecho):** Mientras que la violencia sexual presenta una victimización predominantemente femenina y subregistro crónico, el reclutamiento infantil presenta una composición etaria concentrada en adolescentes de 12 a 17 años con dinámicas de coacción comunitaria.

---

## 3. Métricas Clave (KPIs)

### Para Monitoreo y Power BI
- **Total Casos Registrados:** Conteo absoluto de hechos únicos (`COUNT(DISTINCT id_caso)`).
- **Total Víctimas:** Suma agregada de personas afectadas (`SUM(total_de_v_ctimas_del_caso)`).
- **Promedio de Víctimas por Evento:** `Total Víctimas / Total Casos`.
- **Tasa de Crecimiento Interanual (%):** \(\frac{\text{Víctimas}_t - \text{Víctimas}_{t-1}}{\text{Víctimas}_{t-1}} \times 100\).
- **Índice de Concentración Territorial (Herfindahl o Top-10 Share):** Porcentaje de víctimas que representan los 10 municipios más golpeados respecto al total nacional.

### Para Modelos Predictivos
- **F1-Score / ROC-AUC (Clasificación de Alto Riesgo Municipal):** Capacidad del modelo para identificar correctamente municipios en riesgo sin disparar excesivos falsos positivos.
- **MAE / RMSE (Regresión de Víctimas Esperadas):** Error medio absoluto en la cantidad de víctimas proyectadas por año/municipio.

---

## 4. Criterios de Éxito del Proyecto

1. **Integridad del Pipeline:** Capacidad de actualizar y re-ejecutar el pipeline de punta a punta (extracción, validación, transformación, carga a MySQL) sin intervención manual.
2. **Calidad de Datos:** Menos del 2% de registros descartados por inconsistencias críticas de claves o fechas.
3. **Utilidad para Toma de Decisiones:** Tableros interactivos en Power BI que permitan a un investigador filtrar por municipio, año o actor armado en menos de 2 segundos.
4. **Desempeño del Modelo:** Superar a un modelo base ingenuo (naive baseline como persistencia temporal del año anterior) en al menos un 15% en métrica F1-score o reducción de RMSE.

