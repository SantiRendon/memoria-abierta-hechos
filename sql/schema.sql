-- ==============================================================================
-- ESQUEMA RELACIONAL Y DIMENSIONAL: MEMORIA HISTÓRICA
-- Motor: MySQL 8.0+
-- Optimizado para analítica y conexiones directas desde Power BI
-- ==============================================================================

CREATE DATABASE IF NOT EXISTS memoria_historica
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE memoria_historica;

-- ------------------------------------------------------------------------------
-- 1. Dimensión Geográfica (Municipios de Colombia)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_municipio (
    codigo_dane VARCHAR(10) PRIMARY KEY,
    municipio VARCHAR(100) NOT NULL,
    departamento VARCHAR(100) NOT NULL,
    region VARCHAR(100) NULL,
    latitud DECIMAL(10, 7) NULL,
    longitud DECIMAL(10, 7) NULL,
    INDEX idx_departamento (departamento),
    INDEX idx_region (region)
) ENGINE=InnoDB;

-- ------------------------------------------------------------------------------
-- 2. Dimensión de Presuntos Responsables / Actores Armados
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_responsable (
    id_responsable INT AUTO_INCREMENT PRIMARY KEY,
    categoria_macro VARCHAR(150) NOT NULL,
    descripcion_detalle VARCHAR(255) NULL,
    UNIQUE KEY uk_responsable (categoria_macro, descripcion_detalle(100)),
    INDEX idx_categoria (categoria_macro)
) ENGINE=InnoDB;

-- ------------------------------------------------------------------------------
-- 3. Tabla de Hechos: Nivel Casos (Eventos Agregados)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS hechos_casos (
    id_caso VARCHAR(50) PRIMARY KEY,
    id_caso_relacionado VARCHAR(50) NULL,
    tipo_hecho VARCHAR(80) NOT NULL,
    anio INT NOT NULL,
    mes VARCHAR(20) NULL,
    dia VARCHAR(10) NULL,
    codigo_dane VARCHAR(10) NOT NULL,
    modalidad VARCHAR(150) NULL,
    id_responsable INT NULL,
    total_victimas INT NOT NULL DEFAULT 1,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_tipo_hecho (tipo_hecho),
    INDEX idx_anio (anio),
    INDEX idx_codigo_dane (codigo_dane),
    INDEX idx_responsable (id_responsable),
    
    CONSTRAINT fk_casos_municipio
        FOREIGN KEY (codigo_dane) REFERENCES dim_municipio (codigo_dane)
        ON UPDATE CASCADE ON DELETE RESTRICT,
        
    CONSTRAINT fk_casos_responsable
        FOREIGN KEY (id_responsable) REFERENCES dim_responsable (id_responsable)
        ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB;

-- ------------------------------------------------------------------------------
-- 4. Tabla de Hechos: Nivel Víctimas (Desagregación Individual)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS hechos_victimas (
    id_victima VARCHAR(50) PRIMARY KEY,
    id_caso VARCHAR(50) NOT NULL,
    tipo_hecho VARCHAR(80) NOT NULL,
    sexo VARCHAR(30) NULL,
    genero VARCHAR(50) NULL,
    etnia VARCHAR(80) NULL,
    edad INT NULL,
    rango_edad VARCHAR(50) NULL,
    ocupacion VARCHAR(120) NULL,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_victima_caso (id_caso),
    INDEX idx_victima_sexo (sexo),
    INDEX idx_victima_etnia (etnia),
    INDEX idx_victima_rango_edad (rango_edad),
    
    CONSTRAINT fk_victimas_caso
        FOREIGN KEY (id_caso) REFERENCES hechos_casos (id_caso)
        ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB;

