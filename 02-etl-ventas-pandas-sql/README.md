# 📊 Pipeline ETL de ventas con pandas y SQL

Pipeline de datos completo en Python: genera un archivo de ventas con los problemas típicos de datos reales, lo **limpia con pandas**, lo **carga a SQLite** con restricciones de integridad y lo analiza con **consultas SQL** (funciones de ventana incluidas). Al final produce un reporte en Markdown con gráfico.

!\[Python](https://img.shields.io/badge/python-3.10%2B-blue)
!\[pandas](https://img.shields.io/badge/pandas-2.2%2B-150458)
!\[SQLite](https://img.shields.io/badge/SQLite-3-003B57)

## Flujo

```
generar\_datos ──► ventas\_crudas.csv ──► limpieza (pandas) ──► ventas\_limpias.csv
                                                  │
                                                  ▼
                         reporte.md + gráfico ◄── consultas SQL ◄── SQLite (ventas.db)
```

## Problemas de calidad que resuelve

|Problema en los datos crudos|Qué hace el pipeline|
|-|-|
|Filas duplicadas|Conserva la primera aparición de cada `id\_venta`|
|`laptop`, `LAPTOP`, `" Laptop "`, `audifonos`|Normaliza contra un catálogo (sin acentos, mayúsculas ni espacios)|
|`CDMX`, `Ciudad de Mexico`, `GDL`, `Queretaro`|Unifica ciudades; las faltantes quedan como `Sin dato`|
|Fechas `2025-03-10` y `10/03/2025`, y fechas imposibles (`31/02`)|Parsea ambos formatos y descarta las inválidas|
|Precios como texto: `$1,250.00`|Convierte a número|
|Precios faltantes|Los imputa con la **mediana de su producto**|
|Errores de captura (precio ×10 o ×100)|Detecta atípicos (> 5× la mediana del producto) y los descarta|
|Cantidades faltantes, cero o negativas|Descarta la fila|

Cada ejecución devuelve un reporte de calidad que cuadra: `filas recibidas − descartadas = filas cargadas`.

## Cómo ejecutarlo

```bash
git clone https://github.com/Krass1908/etl-ventas-pandas-sql.git
cd etl-ventas-pandas-sql
python -m venv .venv \&\& source .venv/bin/activate   # en Windows: .venv\\Scripts\\activate
pip install -r requirements.txt

python -m etl                          # 5000 ventas, semilla 42, resultados en ./output
python -m etl --filas 20000 --semilla 7 --salida resultados
```

Genera en `output/`:

|Archivo|Contenido|
|-|-|
|`ventas\_crudas.csv`|Datos de entrada con errores|
|`ventas\_limpias.csv`|Datos ya limpios y estandarizados|
|`ventas.db`|Base SQLite con la tabla `ventas` (índices y restricciones `CHECK`)|
|`reporte.md`|Reporte con KPIs, calidad de datos y tablas|
|`ingresos\_por\_mes.png`|Gráfico de ingresos mensuales|

### Ejemplo de resultado (configuración por defecto)

```
Filas recibidas: 5150
  descartadas por duplicados: 150
  descartadas por fecha inválida: 18
  descartadas por producto desconocido: 26
  descartadas por cantidad inválida: 132
  descartadas por precio atípico: 12
  precios imputados: 154
Filas cargadas a SQLite: 4812
```

Del reporte: ingresos totales de **$27,370,970.47**, ticket promedio de **$5,688.07**, y noviembre y diciembre como los meses más fuertes (+58.4% en noviembre contra octubre).

## Consultas SQL

Están en [`sql/consultas.sql`](sql/consultas.sql) y también se pueden correr a mano:

```bash
sqlite3 output/ventas.db < sql/consultas.sql
```

Ejemplo con `LAG()` para el crecimiento contra el mes anterior:

```sql
WITH mensual AS (
    SELECT mes, SUM(total) AS ingresos FROM ventas GROUP BY mes
)
SELECT mes,
       ROUND(ingresos, 2) AS ingresos,
       ROUND(100.0 \* (ingresos - LAG(ingresos) OVER (ORDER BY mes))
                   / LAG(ingresos) OVER (ORDER BY mes), 1) AS crecimiento\_pct
FROM mensual;
```

Incluye también `RANK() OVER (PARTITION BY ...)` para el producto líder por categoría y `SUM(...) OVER ()` para la participación por ciudad.

## Pruebas

```bash
pytest
```

28 pruebas que cubren cada regla de limpieza, la integridad de la base, que las consultas sumen igual que los datos originales y que el pipeline completo funcione de punta a punta.

## Estructura

```
etl/
├── catalogo.py       # productos, ciudades y utilidad de normalización
├── generar\_datos.py  # datos crudos con errores inyectados (reproducible con semilla)
├── limpieza.py       # transformación con pandas + reporte de calidad
├── carga.py          # esquema SQLite y carga
├── consultas.py      # lee sql/consultas.sql y ejecuta cada consulta
├── reporte.py        # reporte Markdown y gráfico con matplotlib
├── pipeline.py       # orquesta todo el flujo
└── \_\_main\_\_.py       # python -m etl
sql/consultas.sql
tests/
```

## Conceptos que practica este proyecto

* ETL: extracción, transformación y carga.
* Limpieza de datos con pandas: parseo de fechas y números, normalización de texto, duplicados, valores atípicos, imputación.
* Diseño de tablas con claves, índices y restricciones.
* SQL analítico: `GROUP BY`, CTE, funciones de ventana (`LAG`, `RANK`, `SUM OVER`).
* Pruebas automáticas sobre transformaciones de datos.

## Ideas para ampliarlo

* Leer de un CSV real en lugar de generarlo.
* Pasar de SQLite a PostgreSQL.
* Programar la ejecución diaria (cron, Airflow o GitHub Actions).
* Dashboard con Streamlit.

