"""Carga: guarda las ventas limpias en una base de datos SQLite."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

import pandas as pd

ESQUEMA = """
DROP TABLE IF EXISTS ventas;

CREATE TABLE ventas (
    id_venta        INTEGER PRIMARY KEY,
    fecha           TEXT    NOT NULL,
    mes             TEXT    NOT NULL,
    ciudad          TEXT    NOT NULL,
    producto        TEXT    NOT NULL,
    categoria       TEXT    NOT NULL,
    cantidad        INTEGER NOT NULL CHECK (cantidad > 0),
    precio_unitario REAL    NOT NULL CHECK (precio_unitario > 0),
    total           REAL    NOT NULL CHECK (total > 0),
    metodo_pago     TEXT    NOT NULL
);

CREATE INDEX idx_ventas_mes      ON ventas (mes);
CREATE INDEX idx_ventas_ciudad   ON ventas (ciudad);
CREATE INDEX idx_ventas_producto ON ventas (producto);
"""


def cargar_sqlite(ventas: pd.DataFrame, ruta_db: str | Path) -> int:
    """Recrea la tabla `ventas` y la llena. Devuelve cuántas filas se cargaron."""
    ruta_db = Path(ruta_db)
    ruta_db.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(ruta_db)) as conexion:
        conexion.executescript(ESQUEMA)
        ventas.to_sql("ventas", conexion, if_exists="append", index=False)
        conexion.commit()
        return conexion.execute("SELECT COUNT(*) FROM ventas").fetchone()[0]
