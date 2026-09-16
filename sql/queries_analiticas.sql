-- ==============================================================================
-- CONSULTAS ANALÍTICAS Y VISTAS PARA EXPLORACIÓN Y POWER BI
-- Base de datos: memoria_historica
-- ==============================================================================

USE memoria_historica;

-- ------------------------------------------------------------------------------
-- 1. Top 10 municipios más afectados por tipo de hecho victimizante
-- ------------------------------------------------------------------------------
SELECT 
    m.departamento,
    m.municipio,
    c.tipo_hecho,
    COUNT(DISTINCT c.id_caso) AS total_casos,
    SUM(c.total_victimas) AS total_victimas
FROM hechos_casos c
JOIN dim_municipio m ON c.codigo_dane = m.codigo_dane
GROUP BY m.departamento, m.municipio, c.tipo_hecho
ORDER BY total_victimas DESC
LIMIT 10;

-- ------------------------------------------------------------------------------
-- 2. Evolución temporal de víctimas por año y hecho (Serie Temporal)
-- ------------------------------------------------------------------------------
SELECT 
    c.anio,
    c.tipo_hecho,
    COUNT(DISTINCT c.id_caso) AS numero_casos,
    SUM(c.total_victimas) AS numero_victimas,
    ROUND(SUM(c.total_victimas) / COUNT(DISTINCT c.id_caso), 2) AS promedio_victimas_por_caso
FROM hechos_casos c
GROUP BY c.anio, c.tipo_hecho
ORDER BY c.anio ASC, c.tipo_hecho;

-- ------------------------------------------------------------------------------
-- 3. Participación por Presunto Responsable (Distribución macro)
-- ------------------------------------------------------------------------------
SELECT 
    COALESCE(r.categoria_macro, 'NO DETERMINADO') AS presunto_responsable,
    c.tipo_hecho,
    COUNT(DISTINCT c.id_caso) AS total_casos,
    SUM(c.total_victimas) AS total_victimas,
    ROUND(SUM(c.total_victimas) * 100.0 / SUM(SUM(c.total_victimas)) OVER(PARTITION BY c.tipo_hecho), 2) AS porcentaje_victimas
FROM hechos_casos c
LEFT JOIN dim_responsable r ON c.id_responsable = r.id_responsable
GROUP BY r.categoria_macro, c.tipo_hecho
ORDER BY total_victimas DESC;

-- ------------------------------------------------------------------------------
-- 4. Caracterización de Enfoque Diferencial (Sexo y Rango de Edad)
-- ------------------------------------------------------------------------------
SELECT 
    v.tipo_hecho,
    COALESCE(v.sexo, 'SIN INFORMACIÓN') AS sexo,
    COALESCE(v.rango_edad, 'SIN INFORMACIÓN') AS rango_edad,
    COUNT(v.id_victima) AS total_personas
FROM hechos_victimas v
GROUP BY v.tipo_hecho, v.sexo, v.rango_edad
ORDER BY v.tipo_hecho, total_personas DESC;

-- ------------------------------------------------------------------------------
-- 5. Consulta optimizada para Modelo Tabular en Power BI
-- ------------------------------------------------------------------------------
CREATE OR REPLACE VIEW vista_powerbi_hechos AS
SELECT 
    c.id_caso,
    c.tipo_hecho,
    c.anio,
    c.mes,
    c.codigo_dane,
    m.municipio,
    m.departamento,
    m.region,
    m.latitud,
    m.longitud,
    c.modalidad,
    COALESCE(r.categoria_macro, 'NO IDENTIFICADO') AS actor_responsable,
    c.total_victimas
FROM hechos_casos c
LEFT JOIN dim_municipio m ON c.codigo_dane = m.codigo_dane
LEFT JOIN dim_responsable r ON c.id_responsable = r.id_responsable;

