"""Genera un CSV de ventas "sucio", como el que llegaría de sistemas reales.

Los problemas se inyectan a propósito (con una semilla fija para que sea
reproducible) y son los que luego resuelve `limpieza.py`:

- filas duplicadas
- nombres de producto/ciudad/método de pago escritos de varias formas
- fechas en dos formatos (y alguna imposible, como 31/02)
- precios como texto con símbolo "$", faltantes o con errores de captura (x10, x100)
- cantidades faltantes, cero o negativas
"""

from __future__ import annotations

import random
from datetime import date

import pandas as pd

from .catalogo import CATALOGO, CIUDADES, METODOS_PAGO, clave

COLUMNAS_CRUDAS = [
    "id_venta",
    "fecha",
    "ciudad",
    "producto",
    "categoria",
    "cantidad",
    "precio_unitario",
    "metodo_pago",
]

# Más ventas en noviembre y diciembre (temporada alta)
PESOS_MES = [8, 7, 8, 8, 9, 8, 9, 9, 8, 10, 14, 15]
PROPORCION_DUPLICADOS = 0.03


def _ensuciar(rng, id_venta, fecha, ciudad, producto, categoria, cantidad, precio, metodo):
    """Devuelve una fila con texto "sucio" a partir de valores correctos."""
    # producto
    nombre = producto
    r = rng.random()
    if r < 0.005:
        nombre = "Producto desconocido"
    elif r < 0.30:
        nombre = rng.choice([producto.upper(), producto.lower(), f"  {producto} ", clave(producto)])

    # ciudad
    ciudad_txt = ciudad
    r = rng.random()
    if r < 0.02:
        ciudad_txt = None
    elif r < 0.32:
        ciudad_txt = rng.choice(CIUDADES[ciudad])

    # fecha
    r = rng.random()
    if r < 0.005:
        fecha_txt = "31/02/2025"
    elif r < 0.30:
        fecha_txt = fecha.strftime("%d/%m/%Y")
    else:
        fecha_txt = fecha.isoformat()

    # precio
    r = rng.random()
    if r < 0.03:
        precio_txt = None
    elif r < 0.035:
        precio_txt = f"{precio * rng.choice([10, 100]):.2f}"  # error de captura
    elif r < 0.25:
        precio_txt = f"${precio:,.2f}"
    else:
        precio_txt = f"{precio:.2f}"

    # cantidad
    r = rng.random()
    if r < 0.02:
        cantidad_txt = None
    elif r < 0.03:
        cantidad_txt = rng.choice(["0", "-1", "-3"])
    else:
        cantidad_txt = str(cantidad)

    # método de pago
    r = rng.random()
    if r < 0.02:
        metodo_txt = None
    elif r < 0.40:
        metodo_txt = rng.choice([metodo.lower(), metodo.upper()])
    else:
        metodo_txt = metodo

    return {
        "id_venta": str(id_venta),
        "fecha": fecha_txt,
        "ciudad": ciudad_txt,
        "producto": nombre,
        "categoria": None if rng.random() < 0.05 else categoria,
        "cantidad": cantidad_txt,
        "precio_unitario": precio_txt,
        "metodo_pago": metodo_txt,
    }


def generar_ventas_crudas(filas: int = 5000, semilla: int = 42) -> pd.DataFrame:
    """Crea `filas` ventas de 2025 con datos sucios. Misma semilla = mismo resultado."""
    rng = random.Random(semilla)
    productos = list(CATALOGO)
    ciudades = list(CIUDADES)
    registros = []

    for id_venta in range(1, filas + 1):
        producto = rng.choice(productos)
        categoria, precio_base = CATALOGO[producto]
        mes = rng.choices(range(1, 13), weights=PESOS_MES)[0]
        fecha = date(2025, mes, rng.randint(1, 28))
        cantidad = rng.randint(1, 3) if precio_base > 2000 else rng.randint(1, 8)
        precio = round(precio_base * rng.uniform(0.9, 1.1), 2)
        registros.append(
            _ensuciar(
                rng,
                id_venta,
                fecha,
                rng.choice(ciudades),
                producto,
                categoria,
                cantidad,
                precio,
                rng.choice(METODOS_PAGO),
            )
        )

    registros.extend(rng.choice(registros) for _ in range(int(filas * PROPORCION_DUPLICADOS)))
    rng.shuffle(registros)
    return pd.DataFrame(registros, columns=COLUMNAS_CRUDAS)
