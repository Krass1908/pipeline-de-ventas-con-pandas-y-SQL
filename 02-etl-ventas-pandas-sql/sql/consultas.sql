-- Consultas analíticas sobre la tabla `ventas`.
-- Cada bloque empieza con "-- name: <nombre>" y lo ejecuta etl/consultas.py.
-- También puedes correrlas a mano:  sqlite3 output/ventas.db < sql/consultas.sql

-- name: kpis
SELECT COUNT(*)                    AS ventas,
       ROUND(SUM(total), 2)        AS ingresos,
       ROUND(AVG(total), 2)        AS ticket_promedio,
       COUNT(DISTINCT producto)    AS productos
FROM ventas;

-- name: ingresos_por_mes
SELECT mes,
       COUNT(*)                AS ventas,
       ROUND(SUM(total), 2)    AS ingresos,
       ROUND(AVG(total), 2)    AS ticket_promedio
FROM ventas
GROUP BY mes
ORDER BY mes;

-- name: crecimiento_mensual
-- LAG() compara cada mes contra el anterior.
WITH mensual AS (
    SELECT mes, SUM(total) AS ingresos
    FROM ventas
    GROUP BY mes
)
SELECT mes,
       ROUND(ingresos, 2) AS ingresos,
       ROUND(100.0 * (ingresos - LAG(ingresos) OVER (ORDER BY mes))
                   / LAG(ingresos) OVER (ORDER BY mes), 1) AS crecimiento_pct
FROM mensual
ORDER BY mes;

-- name: top_productos
SELECT producto,
       SUM(cantidad)        AS unidades,
       ROUND(SUM(total), 2) AS ingresos
FROM ventas
GROUP BY producto
ORDER BY ingresos DESC
LIMIT 5;

-- name: ingresos_por_ciudad
-- SUM(...) OVER () calcula el total general para sacar la participación.
SELECT ciudad,
       COUNT(*)             AS ventas,
       ROUND(SUM(total), 2) AS ingresos,
       ROUND(100.0 * SUM(total) / SUM(SUM(total)) OVER (), 1) AS participacion_pct
FROM ventas
GROUP BY ciudad
ORDER BY ingresos DESC;

-- name: producto_lider_por_categoria
-- RANK() numera los productos dentro de cada categoría; nos quedamos con el #1.
WITH ranking AS (
    SELECT categoria,
           producto,
           SUM(total) AS ingresos,
           RANK() OVER (PARTITION BY categoria ORDER BY SUM(total) DESC) AS posicion
    FROM ventas
    GROUP BY categoria, producto
)
SELECT categoria, producto, ROUND(ingresos, 2) AS ingresos
FROM ranking
WHERE posicion = 1
ORDER BY ingresos DESC;

-- name: metodos_pago
SELECT metodo_pago,
       COUNT(*)             AS ventas,
       ROUND(SUM(total), 2) AS ingresos
FROM ventas
GROUP BY metodo_pago
ORDER BY ventas DESC;
