import argparse

from .limpieza import ETIQUETAS_MOTIVO, MOTIVOS_DESCARTE
from .pipeline import ejecutar_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="python -m etl",
        description="Pipeline ETL de ventas: genera datos sucios, los limpia, "
        "los carga a SQLite y produce un reporte.",
    )
    parser.add_argument("--filas", type=int, default=5000, help="Ventas a generar (5000).")
    parser.add_argument("--semilla", type=int, default=42, help="Semilla aleatoria (42).")
    parser.add_argument("--salida", default="output", help="Carpeta de salida (output).")
    args = parser.parse_args()

    resultado = ejecutar_pipeline(args.filas, args.semilla, args.salida)
    r = resultado["reporte_limpieza"]

    print(f"Filas recibidas: {r['filas_iniciales']}")
    for motivo in MOTIVOS_DESCARTE:
        print(f"  descartadas por {ETIQUETAS_MOTIVO[motivo]}: {r[motivo]}")
    print(f"  precios imputados: {r['precios_imputados']}")
    print(f"Filas cargadas a SQLite: {resultado['filas_cargadas']}")
    print("Archivos generados:")
    for nombre, ruta in resultado["archivos"].items():
        print(f"  {nombre:<14} {ruta}")


if __name__ == "__main__":
    main()
