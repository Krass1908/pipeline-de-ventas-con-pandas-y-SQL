"""Transformación: limpia y estandariza las ventas crudas con pandas."""

from __future__ import annotations

import pandas as pd

from .catalogo import ALIAS_CIUDAD, ALIAS_PAGO, ALIAS_PRODUCTO, CATALOGO, clave

COLUMNAS_FINALES = [
    "id_venta",
    "fecha",
    "mes",
    "ciudad",
    "producto",
    "categoria",
    "cantidad",
    "precio_unitario",
    "total",
    "metodo_pago",
]

# Motivos por los que una fila se descarta (en el orden en que se aplican)
MOTIVOS_DESCARTE = (
    "id_invalido",
    "duplicados",
    "fecha_invalida",
    "producto_desconocido",
    "cantidad_invalida",
    "precio_atipico",
)

ETIQUETAS_MOTIVO = {
    "id_invalido": "ID inválido",
    "duplicados": "duplicados",
    "fecha_invalida": "fecha inválida",
    "producto_desconocido": "producto desconocido",
    "cantidad_invalida": "cantidad inválida",
    "precio_atipico": "precio atípico",
}

# Un precio se considera atípico si es más de 5 veces mayor (o menor) que la
# mediana de su producto.
UMBRAL_ATIPICO = 5


def _a_numero(serie: pd.Series) -> pd.Series:
    """Texto -> float. Quita "$", comas y espacios; lo que no se pueda leer queda en NaN."""
    texto = serie.astype("string").str.replace(r"[^\d.\-]", "", regex=True)
    return pd.to_numeric(texto, errors="coerce").astype("float64")


def limpiar(crudo: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int]]:
    """Devuelve (ventas limpias, reporte de calidad).

    El reporte indica cuántas filas se descartaron por cada motivo, cuántos
    precios se imputaron y cuántas filas quedaron.
    """
    df = crudo.copy()
    reporte: dict[str, int] = {"filas_iniciales": len(df)}

    def descartar(motivo: str, invalidas: pd.Series) -> None:
        nonlocal df
        reporte[motivo] = int(invalidas.sum())
        df = df.loc[~invalidas].copy()

    # 1. Identificador y duplicados (nos quedamos con la primera aparición)
    df["id_venta"] = _a_numero(df["id_venta"])
    descartar("id_invalido", df["id_venta"].isna())
    df["id_venta"] = df["id_venta"].astype("int64")
    descartar("duplicados", df.duplicated(subset="id_venta", keep="first"))

    # 2. Fechas: acepta AAAA-MM-DD y DD/MM/AAAA; descarta las imposibles (31/02)
    texto = df["fecha"].astype("string").str.strip()
    iso = pd.to_datetime(texto, format="%Y-%m-%d", errors="coerce")
    latino = pd.to_datetime(texto, format="%d/%m/%Y", errors="coerce")
    df["fecha"] = iso.fillna(latino)
    descartar("fecha_invalida", df["fecha"].isna())

    # 3. Producto: unifica mayúsculas, espacios y acentos contra el catálogo
    df["producto"] = df["producto"].map(lambda v: ALIAS_PRODUCTO.get(clave(v)))
    descartar("producto_desconocido", df["producto"].isna())

    # 4. Cantidad: debe ser un entero positivo
    cantidad = _a_numero(df["cantidad"])
    df["cantidad"] = cantidad
    descartar("cantidad_invalida", cantidad.isna() | (cantidad <= 0) | (cantidad % 1 != 0))
    df["cantidad"] = df["cantidad"].astype("int64")

    # 5. Precio: detecta errores de captura (x10, x100) y completa los faltantes
    precio = _a_numero(df["precio_unitario"]).where(lambda s: s > 0)  # <= 0 se trata como faltante
    mediana = precio.groupby(df["producto"]).transform("median")
    atipico = precio.notna() & (
        (precio > mediana * UMBRAL_ATIPICO) | (precio < mediana / UMBRAL_ATIPICO)
    )
    df["precio_unitario"] = precio
    descartar("precio_atipico", atipico)

    reporte["precios_imputados"] = int(df["precio_unitario"].isna().sum())
    mediana = df.groupby("producto")["precio_unitario"].transform("median")
    precio_catalogo = df["producto"].map(lambda p: CATALOGO[p][1])
    df["precio_unitario"] = df["precio_unitario"].fillna(mediana).fillna(precio_catalogo).round(2)

    # 6. Ciudad y método de pago estandarizados; lo que falta queda como "Sin dato"
    df["ciudad"] = df["ciudad"].map(lambda v: ALIAS_CIUDAD.get(clave(v), "Sin dato"))
    df["metodo_pago"] = df["metodo_pago"].map(lambda v: ALIAS_PAGO.get(clave(v), "Sin dato"))

    # 7. La categoría se deriva del catálogo (así nunca queda vacía ni inconsistente)
    df["categoria"] = df["producto"].map(lambda p: CATALOGO[p][0])

    # 8. Columnas derivadas
    df["total"] = (df["cantidad"] * df["precio_unitario"]).round(2)
    df["mes"] = df["fecha"].dt.strftime("%Y-%m")
    df["fecha"] = df["fecha"].dt.strftime("%Y-%m-%d")

    limpio = df[COLUMNAS_FINALES].sort_values("id_venta").reset_index(drop=True)
    reporte["filas_finales"] = len(limpio)
    return limpio, reporte
