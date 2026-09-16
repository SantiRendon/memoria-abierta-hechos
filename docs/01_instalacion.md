# Guía de Instalación y Configuración del Entorno

Esta guía describe paso a paso cómo preparar tu estación de trabajo en Windows para ejecutar el pipeline de datos, almacenar los registros en MySQL y conectarlos a Power BI.

---

## 1. Requisitos Previos

Antes de comenzar, asegúrate de tener instalados los siguientes componentes en tu sistema:

1. **Python 3.10 o superior**
   - Descárgalo desde [python.org](https://www.python.org/downloads/).
   - *Importante:* Al instalar, marca la casilla **"Add Python to PATH"**.
   - Verifica en PowerShell o CMD ejecutando:
     ```powershell
     python --version
     pip --version
     ```

2. **MySQL Server 8.0 o superior & MySQL Workbench**
   - Puedes instalar la distribución comunitaria: [MySQL Community Server](https://dev.mysql.com/downloads/mysql/).
   - Anota el usuario administrador (por defecto `root`), el puerto (`3306`) y la contraseña elegida.

3. **Power BI Desktop**
   - Descárgalo desde Microsoft Store o [Power BI](https://powerbi.microsoft.com/es-es/desktop/).
   - Permite conectar directamente con MySQL mediante el conector nativo o ODBC.

4. **Git**
   - Para el control de versiones de código y documentación.

---

## 2. Preparación del Entorno Virtual de Python

Trabajar en un entorno virtual aislado evita conflictos de versiones entre dependencias del sistema y del proyecto.

### Paso 2.1: Abrir la terminal en la raíz del proyecto
Abre PowerShell o tu terminal integrada en el editor:
```powershell
cd c:\Users\Santiago\Desktop\memoria-abierta-hechos
```

### Paso 2.2: Crear el entorno virtual (`venv`)
Ejecuta:
```powershell
python -m venv venv
```

### Paso 2.3: Activar el entorno virtual
En Windows PowerShell:
```powershell
.\venv\Scripts\Activate.ps1
```
*(Nota: Si recibes un error de permisos sobre ejecución de scripts en PowerShell, ejecuta primero `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` y vuelve a activar).*

Si usas el Símbolo del Sistema (CMD tradicional):
```cmd
venv\Scripts\activate.bat
```
Sabrás que está activo porque aparecerá `(venv)` al inicio de la línea de comandos.

### Paso 2.4: Actualizar pip e instalar dependencias
Con el entorno virtual activo:
```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

---

## 3. Configuración de Variables de Entorno

El proyecto almacena credenciales y rutas en un archivo `.env` local que **no** se sube al repositorio Git.

1. Duplica la plantilla `.env.example`:
   ```powershell
   copy .env.example .env
   ```

2. Abre `.env` con tu editor y configura tus valores:
   ```env
   ENVIRONMENT=development

   # Credenciales de MySQL
   DB_HOST=localhost
   DB_PORT=3306
   DB_USER=root
   DB_PASSWORD=tu_clave_de_mysql
   DB_NAME=memoria_historica

   # Token opcional de Datos Abiertos Colombia
   SODATA_APP_TOKEN=

   # Logging
   LOG_LEVEL=INFO
   LOG_DIR=logs
   ```

---

## 4. Configuración de la Base de Datos MySQL

1. Abre **MySQL Workbench** o la consola de MySQL.
2. Abre y ejecuta el script de inicialización DDL ubicado en:
   ```text
   sql/schema.sql
   ```
3. Esto creará la base de datos `memoria_historica` y sus tablas asociadas (`dim_municipio`, `dim_tiempo`, `dim_responsable`, `hechos_casos`, `hechos_victimas`).

---

## 5. Verificación de la Instalación

Crea un script temporal o prueba interactiva en Python para verificar que todos los componentes responden correctamente:

```powershell
python -c "import pandas, numpy, requests, sklearn, mysql.connector, yaml, dotenv; print('¡Todas las dependencias están correctamente instaladas!')"
```

Si no se genera ningún error y se imprime el mensaje afirmativo, tu entorno está 100% listo para ejecutar el pipeline.

