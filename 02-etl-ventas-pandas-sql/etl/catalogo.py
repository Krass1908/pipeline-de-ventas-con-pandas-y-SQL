"""Catálogos de referencia y utilidades para normalizar texto."""

from __future__ import annotations

import unicodedata

import pandas as pd

# producto -> (categoría, precio base en pesos)
CATALOGO: dict[str, tuple[str, float]] = {
    "Laptop": ("Tecnología", 14500.0),
    "Monitor": ("Tecnología", 3200.0),
    "Teclado": ("Tecnología", 600.0),
    "Mouse": ("Tecnología", 250.0),
    "Escritorio": ("Muebles", 3500.0),
    "Silla ergonómica": ("Muebles", 2800.0),
    "Mochila": ("Accesorios", 520.0),
    "Audífonos": ("Accesorios", 800.0),
    "Cuaderno": ("Papelería", 45.0),
    "Pluma": ("Papelería", 12.0),
}

# ciudad canónica -> variantes con las que suele escribirse
CIUDADES: dict[str, list[str]] = {
    "Ciudad de México": ["CDMX", "cdmx", "Ciudad de Mexico", "ciudad de méxico"],
    "Guadalajara": ["GDL", "guadalajara", "Guadalajara "],
    "Monterrey": ["MTY", "monterrey", " Monterrey"],
    "Puebla": ["puebla", "PUEBLA"],
    "Querétaro": ["Queretaro", "queretaro", "QRO"],
    "Mérida": ["Merida", "merida", "MID"],
}

METODOS_PAGO = ("Efectivo", "Tarjeta", "Transferencia")


def clave(texto) -> str | None:
    """Minúsculas, sin acentos ni espacios sobrantes. Devuelve None si no hay texto."""
    if pd.isna(texto):
        return None
    descompuesto = unicodedata.normalize("NFKD", str(texto).strip().lower())
    sin_acentos = "".join(c for c in descompuesto if not unicodedata.combining(c))
    return sin_acentos or None


ALIAS_PRODUCTO = {clave(producto): producto for producto in CATALOGO}
ALIAS_PAGO = {clave(metodo): metodo for metodo in METODOS_PAGO}
ALIAS_CIUDAD: dict[str | None, str] = {}
for _canonica, _variantes in CIUDADES.items():
    ALIAS_CIUDAD[clave(_canonica)] = _canonica
    for _variante in _variantes:
        ALIAS_CIUDAD[clave(_variante)] = _canonica
