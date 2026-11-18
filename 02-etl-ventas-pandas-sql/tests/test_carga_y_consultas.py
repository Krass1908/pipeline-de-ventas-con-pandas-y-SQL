import sqlite3
from contextlib import closing

import pytest

from etl.carga import cargar_sqlite
from etl.consultas import cargar_consultas, ejecutar
from etl.generar_datos import generar_ventas_crudas
from etl.limpieza import limpiar


@pytest.fixture
def base(tmp_path):
    limpio, _ = limpiar(generar_ventas_crudas(filas=600, semilla=11))
    ruta = tmp_path / "ventas.db"
    cargar_sqlite(limpio, ruta)
    return ruta, limpio


def test_carga_todas_las_filas(tmp_path):
    limpio, _ = limpiar(generar_ventas_crudas(filas=300, semilla=5))
    assert cargar_sqlite(limpio, tmp_path / "x.db") == len(limpio)


def test_recargar_no_duplica_datos(base):
    ruta, limpio = base
    assert cargar_sqlite(limpio, ruta) == len(limpio)


def test_la_base_rechaza_datos_invalidos(base):
    ruta, _ = base
    with closing(sqlite3.connect(ruta)) as con:
        with pytest.raises(sqlite3.IntegrityError):
            con.execute(
                "INSERT INTO ventas VALUES (999999, '2025-01-01', '2025-01', 'Puebla', "
                "'Mouse', 'Tecnología', 0, 250, 0, 'Efectivo')"
            )


def test_todas_las_consultas_devuelven_resultados(base):
    ruta, _ = base
    nombres = cargar_consultas()
    assert len(nombres) >= 7
    for nombre in nombres:
        assert not ejecutar(ruta, nombre).empty, nombre


def test_ingresos_por_mes_suman_el_total_general(base):
    ruta, limpio = base
    por_mes = ejecutar(ruta, "ingresos_por_mes")
    assert por_mes["ingresos"].sum() == pytest.approx(limpio["total"].sum(), abs=0.5)
    assert por_mes["ventas"].sum() == len(limpio)


def test_participacion_por_ciudad_suma_cien(base):
    ruta, _ = base
    assert ejecutar(ruta, "ingresos_por_ciudad")["participacion_pct"].sum() == pytest.approx(
        100, abs=0.5
    )


def test_crecimiento_del_primer_mes_es_nulo(base):
    ruta, _ = base
    crecimiento = ejecutar(ruta, "crecimiento_mensual")
    assert crecimiento["crecimiento_pct"].isna().iloc[0]
    assert crecimiento["crecimiento_pct"].iloc[1:].notna().all()


def test_producto_lider_es_uno_por_categoria(base):
    ruta, _ = base
    lideres = ejecutar(ruta, "producto_lider_por_categoria")
    assert lideres["categoria"].is_unique


def test_consulta_inexistente_da_error_claro(base):
    ruta, _ = base
    with pytest.raises(KeyError, match="No existe la consulta"):
        ejecutar(ruta, "no_existe")
