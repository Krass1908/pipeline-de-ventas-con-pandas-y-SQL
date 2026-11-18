"""Orquesta el flujo completo: generar -> extraer -> transformar -> cargar -> reportar."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .carga import cargar_sqlite
from .generar_datos import generar_ventas_crudas
from .limpieza import limpiar
from .reporte import generar_reporte


def ejecutar_pipeline(filas: int = 5000, semilla: int = 42, salida: str | Path = "output") -> dict:
    """Corre todo el pipeline y devuelve un resumen con las rutas y el reporte de calidad."""
    salida = Path(salida)
    salida.mkdir(parents=True, exist_ok=True)

    # 0. Datos de entrada (en un caso real vendrían de otro sistema)
    ruta_crudo = salida / "ventas_crudas.csv"
    generar_ventas_crudas(filas, semilla).to_csv(ruta_crudo, index=False)

    # 1. Extract
    crudo = pd.read_csv(ruta_crudo, dtype=str)

    # 2. Transform
    limpio, reporte_limpieza = limpiar(crudo)
    ruta_limpio = salida / "ventas_limpias.csv"
    limpio.to_csv(ruta_limpio, index=False)

    # 3. Load
    ruta_db = salida / "ventas.db"
    filas_cargadas = cargar_sqlite(limpio, ruta_db)

    # 4. Reporte
    archivos = generar_reporte(ruta_db, salida, reporte_limpieza)

    return {
        "reporte_limpieza": reporte_limpieza,
        "filas_cargadas": filas_cargadas,
        "archivos": {
            "crudo": ruta_crudo,
            "limpio": ruta_limpio,
            "base_de_datos": ruta_db,
            **archivos,
        },
    }
