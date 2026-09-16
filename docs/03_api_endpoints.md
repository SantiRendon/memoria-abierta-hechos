# Documentación de APIs y Endpoints (Portal Datos Abiertos Colombia)

Este documento detalla el funcionamiento técnico del API del portal [datos.gov.co](https://www.datos.gov.co), basado en la tecnología Socrata Open Data API (SODA).

---

## 1. URL Base y Formato

Todos los conjuntos de datos en datos.gov.co exponen endpoints REST compatibles con formato JSON, CSV y GeoJSON:

- **Endpoint JSON estándar:**
  ```text
  https://www.datos.gov.co/resource/{dataset_id}.json
  ```
  *(Donde `{dataset_id}` es una clave alfanumérica única de 4 caracteres, un guion, y 4 caracteres, por ejemplo `abcd-1234`).*

---

## 2. Parámetros de Consulta (SoQL - Socrata Query Language)

La API permite filtrar, paginar y ordenar datos mediante parámetros en la URL tipo SoQL:

| Parámetro | Propósito | Ejemplo |
| :--- | :--- | :--- |
| `$limit` | Número máximo de registros a retornar (máx. 50,000; por defecto 1,000). | `$limit=5000` |
| `$offset` | Desplazamiento o índice de inicio (clave para paginación). | `$offset=5000` |
| `$where` | Filtro condicional booleano (similar a SQL WHERE). | `$where=a_o >= 2000 AND departamento = 'ANTIOQUIA'` |
| `$order` | Campo y dirección de ordenamiento. | `$order=a_o ASC, id_caso ASC` |
| `$select` | Columnas específicas a retornar (reduce ancho de banda). | `$select=id_caso, a_o, municipio, total_de_v_ctimas_del_caso` |

---

## 3. Autenticación y Límites de Tasa (Rate Limiting)

- **Consultas anónimas:** Permitidas para datos públicos. Sin embargo, Socrata aplica un límite estricto de peticiones por hora por dirección IP pública.
- **Consultas autenticadas (App Token):** Recomendado. Para obtenerlo:
  1. Inicia sesión en [datos.gov.co](https://www.datos.gov.co).
  2. Ve a Configuración de desarrollador (*Developer Settings*).
  3. Crea un "App Token".
  4. Envía este token en la cabecera HTTP:
     ```http
     X-App-Token: TU_APP_TOKEN
     ```

---

## 4. Ejemplo Práctico en Python con `requests`

```python
import os
import requests
from dotenv import load_dotenv

load_dotenv()

dataset_id = "xxxx-xxxx"  # Reemplazar con el ID del hecho
base_url = f"https://www.datos.gov.co/resource/{dataset_id}.json"

headers = {}
app_token = os.getenv("SODATA_APP_TOKEN")
if app_token:
    headers["X-App-Token"] = app_token

params = {
    "$limit": 5000,
    "$offset": 0,
    "$order": ":id"
}

response = requests.get(base_url, headers=headers, params=params, timeout=30)

if response.status_code == 200:
    registros = response.json()
    print(f"Descargados exitosamente {len(registros)} registros.")
else:
    print(f"Error {response.status_code}: {response.text}")
```

---

## 5. Estrategia de Paginación para Datasets Extensos

Para descargar la totalidad de un hecho histórico (que puede superar los 20,000 a 100,000 registros), el pipeline utiliza un bucle de paginación:

```python
todos_los_registros = []
limite = 5000
offset = 0

while True:
    params = {
        "$limit": limite,
        "$offset": offset,
        "$order": ":id"
    }
    resp = requests.get(base_url, headers=headers, params=params)
    data = resp.json()
    
    if not data:
        break  # Se han obtenido todos los registros
        
    todos_los_registros.extend(data)
    print(f"Progreso: {len(todos_los_registros)} registros acumulados...")
    
    if len(data) < limite:
        break  # Última página
        
    offset += limite
```

---

## 6. Manejo de Errores Comunes

- **HTTP 404:** Identificador de dataset inválido o dataset retirado.
- **HTTP 429 (Too Many Requests):** Límite de tasa excedido; requiere pausar unos minutos o configurar un `SODATA_APP_TOKEN`.
- **HTTP 500/504 (Server Error / Gateway Timeout):** La consulta es demasiado pesada; reduce el valor de `$limit` (ej. de 50,000 a 5,000).

