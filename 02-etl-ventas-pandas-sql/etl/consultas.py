"""Ejecuta las consultas SQL de sql/consultas.sql y las devuelve como DataFrames."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

import pandas as pd

RUTA_SQL = Path(__file__).resolve().parent.parent / "sql" / "consultas.sql"


def cargar_consultas(ruta: Path = RUTA_SQL) -> dict[str, str]:
    """Lee el archivo .sql y devuelve {nombre: consulta}."""
    consultas: dict[str, str] = {}
    nombre: str | None = None
    lineas: list[str] = []
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        if linea.startswith("-- name:"):
            if nombre:
                consultas[nombre] = "\n".join(lineas).strip()
            nombre = linea.split(":", 1)[1].strip()
            lineas = []
        elif nombre is not None:
            lineas.append(linea)
    if nombre:
        consultas[nombre] = "\n".join(lineas).strip()
    return consultas


def ejecutar(ruta_db: str | Path, nombre: str) -> pd.DataFrame:
    """Corre la consulta `nombre` contra la base de datos y devuelve el resultado."""
    consultas = cargar_consultas()
    if nombre not in consultas:
        raise KeyError(f"No existe la consulta '{nombre}'. Disponibles: {', '.join(consultas)}")
    with closing(sqlite3.connect(ruta_db)) as conexion:
        return pd.read_sql_query(consultas[nombre], conexion)
