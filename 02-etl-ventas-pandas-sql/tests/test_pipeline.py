from etl.generar_datos import generar_ventas_crudas
from etl.pipeline import ejecutar_pipeline


def test_pipeline_completo_genera_todos_los_archivos(tmp_path):
    resultado = ejecutar_pipeline(filas=300, semilla=7, salida=tmp_path / "out")

    for ruta in resultado["archivos"].values():
        assert ruta.exists() and ruta.stat().st_size > 0

    assert resultado["filas_cargadas"] == resultado["reporte_limpieza"]["filas_finales"]
    contenido = resultado["archivos"]["reporte"].read_text(encoding="utf-8")
    assert "# Reporte de ventas 2025" in contenido
    assert "## Top 5 productos por ingresos" in contenido


def test_misma_semilla_produce_los_mismos_datos():
    assert generar_ventas_crudas(100, 3).equals(generar_ventas_crudas(100, 3))
    assert not generar_ventas_crudas(100, 3).equals(generar_ventas_crudas(100, 4))


def test_los_datos_generados_realmente_vienen_sucios():
    crudo = generar_ventas_crudas(1000, 42)
    assert crudo["id_venta"].duplicated().any()
    assert crudo["precio_unitario"].isna().any()
    assert crudo["precio_unitario"].str.startswith("$", na=False).any()
    assert crudo["producto"].nunique() > 10  # variantes de mayúsculas, espacios, acentos
