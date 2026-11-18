"""Genera el reporte en Markdown y el gráfico de ingresos mensuales."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # sin ventana: funciona en servidores y en CI
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from .consultas import ejecutar  # noqa: E402
from .limpieza import ETIQUETAS_MOTIVO, MOTIVOS_DESCARTE  # noqa: E402


def _moneda(valor) -> str:
    return f"${valor:,.2f}"


def _entero(valor) -> str:
    return f"{int(valor):,}"


def _porcentaje(valor) -> str:
    return "—" if pd.isna(valor) else f"{valor:+.1f}%"


def _participacion(valor) -> str:
    return f"{valor:.1f}%"


def tabla_markdown(df: pd.DataFrame, formatos: dict | None = None) -> str:
    """Convierte un DataFrame en una tabla Markdown (sin depender de `tabulate`)."""
    formatos = formatos or {}
    lineas = [
        "| " + " | ".join(df.columns) + " |",
        "|" + "|".join("---" for _ in df.columns) + "|",
    ]
    for _, fila in df.iterrows():
        celdas = [formatos.get(col, str)(fila[col]) for col in df.columns]
        lineas.append("| " + " | ".join(celdas) + " |")
    return "\n".join(lineas)


def graficar_ingresos_mensuales(ruta_db: str | Path, destino: str | Path) -> Path:
    datos = ejecutar(ruta_db, "ingresos_por_mes")
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.bar(datos["mes"], datos["ingresos"] / 1000, color="#2f6fdb")
    ax.set_title("Ingresos por mes (2025)")
    ax.set_ylabel("Miles de pesos")
    ax.tick_params(axis="x", rotation=45)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(destino, dpi=150)
    plt.close(fig)
    return Path(destino)


def generar_reporte(
    ruta_db: str | Path, carpeta: str | Path, reporte_limpieza: dict[str, int]
) -> dict[str, Path]:
    """Escribe reporte.md y ingresos_por_mes.png en `carpeta`."""
    carpeta = Path(carpeta)
    grafico = graficar_ingresos_mensuales(ruta_db, carpeta / "ingresos_por_mes.png")

    kpis = ejecutar(ruta_db, "kpis").iloc[0]
    calidad = pd.DataFrame(
        [("Filas recibidas", reporte_limpieza["filas_iniciales"])]
        + [(f"Descartadas: {ETIQUETAS_MOTIVO[m]}", reporte_limpieza[m]) for m in MOTIVOS_DESCARTE]
        + [
            ("Precios faltantes imputados", reporte_limpieza["precios_imputados"]),
            ("Filas cargadas a la base", reporte_limpieza["filas_finales"]),
        ],
        columns=["Concepto", "Filas"],
    )

    secciones = [
        "# Reporte de ventas 2025",
        "## Resumen",
        f"- **Ventas:** {_entero(kpis['ventas'])}\n"
        f"- **Ingresos:** {_moneda(kpis['ingresos'])}\n"
        f"- **Ticket promedio:** {_moneda(kpis['ticket_promedio'])}\n"
        f"- **Productos distintos:** {_entero(kpis['productos'])}",
        "## Calidad de los datos",
        tabla_markdown(calidad, {"Filas": _entero}),
        "## Ingresos por mes",
        f"![Ingresos por mes]({grafico.name})",
        tabla_markdown(
            ejecutar(ruta_db, "ingresos_por_mes"),
            {"ventas": _entero, "ingresos": _moneda, "ticket_promedio": _moneda},
        ),
        "## Crecimiento contra el mes anterior",
        tabla_markdown(
            ejecutar(ruta_db, "crecimiento_mensual"),
            {"ingresos": _moneda, "crecimiento_pct": _porcentaje},
        ),
        "## Top 5 productos por ingresos",
        tabla_markdown(
            ejecutar(ruta_db, "top_productos"), {"unidades": _entero, "ingresos": _moneda}
        ),
        "## Ingresos por ciudad",
        tabla_markdown(
            ejecutar(ruta_db, "ingresos_por_ciudad"),
            {"ventas": _entero, "ingresos": _moneda, "participacion_pct": _participacion},
        ),
        "## Producto líder por categoría",
        tabla_markdown(ejecutar(ruta_db, "producto_lider_por_categoria"), {"ingresos": _moneda}),
        "## Métodos de pago",
        tabla_markdown(
            ejecutar(ruta_db, "metodos_pago"), {"ventas": _entero, "ingresos": _moneda}
        ),
    ]
    ruta_md = carpeta / "reporte.md"
    ruta_md.write_text("\n\n".join(secciones) + "\n", encoding="utf-8")
    return {"reporte": ruta_md, "grafico": grafico}
