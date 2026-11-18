import pandas as pd
import pytest

from etl.generar_datos import generar_ventas_crudas
from etl.limpieza import MOTIVOS_DESCARTE, limpiar


def fila(**cambios):
    """Una venta cruda válida; cada prueba modifica solo lo que quiere probar."""
    base = {
        "id_venta": "1",
        "fecha": "2025-03-10",
        "ciudad": "CDMX",
        "producto": "Laptop",
        "categoria": "Tecnología",
        "cantidad": "2",
        "precio_unitario": "14500.00",
        "metodo_pago": "Tarjeta",
    }
    base.update(cambios)
    return base


def crudo(*filas):
    return pd.DataFrame(list(filas))


def laptops_normales(desde=100, cuantas=5):
    """Varias ventas normales de laptop para que la mediana del producto sea confiable."""
    return [fila(id_venta=str(desde + i)) for i in range(cuantas)]


# ------------------------------------------------------------ estandarización
def test_normaliza_texto_y_deriva_la_categoria():
    limpio, _ = limpiar(
        crudo(fila(producto="  laptop ", ciudad="cdmx", metodo_pago="TARJETA", categoria=None))
    )
    registro = limpio.iloc[0]
    assert registro["producto"] == "Laptop"
    assert registro["ciudad"] == "Ciudad de México"
    assert registro["metodo_pago"] == "Tarjeta"
    assert registro["categoria"] == "Tecnología"


def test_acepta_los_dos_formatos_de_fecha():
    limpio, _ = limpiar(
        crudo(fila(id_venta="1", fecha="2025-03-10"), fila(id_venta="2", fecha="10/03/2025"))
    )
    assert list(limpio["fecha"]) == ["2025-03-10", "2025-03-10"]
    assert list(limpio["mes"]) == ["2025-03", "2025-03"]


def test_precio_con_simbolo_y_comas_se_convierte_a_numero():
    limpio, _ = limpiar(crudo(fila(precio_unitario="$14,500.00")))
    assert limpio.iloc[0]["precio_unitario"] == 14500.0
    assert limpio.iloc[0]["total"] == 29000.0


def test_ciudad_desconocida_o_faltante_queda_como_sin_dato():
    limpio, _ = limpiar(
        crudo(fila(id_venta="1", ciudad="Narnia"), fila(id_venta="2", ciudad=None))
    )
    assert list(limpio["ciudad"]) == ["Sin dato", "Sin dato"]


# ------------------------------------------------------------------ descartes
def test_descarta_duplicados_por_id():
    limpio, reporte = limpiar(crudo(fila(), fila()))
    assert len(limpio) == 1
    assert reporte["duplicados"] == 1


def test_descarta_fechas_imposibles():
    limpio, reporte = limpiar(crudo(fila(id_venta="1", fecha="31/02/2025"), fila(id_venta="2")))
    assert list(limpio["id_venta"]) == [2]
    assert reporte["fecha_invalida"] == 1


def test_descarta_productos_desconocidos():
    limpio, reporte = limpiar(crudo(fila(id_venta="1", producto="Zapatos"), fila(id_venta="2")))
    assert list(limpio["id_venta"]) == [2]
    assert reporte["producto_desconocido"] == 1


@pytest.mark.parametrize("cantidad", ["0", "-1", "abc", None, "1.5"])
def test_descarta_cantidades_invalidas(cantidad):
    limpio, reporte = limpiar(crudo(fila(id_venta="1", cantidad=cantidad), fila(id_venta="2")))
    assert list(limpio["id_venta"]) == [2]
    assert reporte["cantidad_invalida"] == 1


def test_descarta_precios_atipicos():
    filas = [*laptops_normales(), fila(id_venta="1", precio_unitario="145000.00")]
    limpio, reporte = limpiar(crudo(*filas))
    assert 1 not in set(limpio["id_venta"])
    assert reporte["precio_atipico"] == 1
    assert len(limpio) == 5


# ----------------------------------------------------------------- imputación
def test_imputa_precio_faltante_con_la_mediana_del_producto():
    filas = [*laptops_normales(), fila(id_venta="1", precio_unitario=None)]
    limpio, reporte = limpiar(crudo(*filas))
    assert limpio.loc[limpio["id_venta"] == 1, "precio_unitario"].iloc[0] == 14500.0
    assert reporte["precios_imputados"] == 1


def test_sin_precios_de_referencia_usa_el_precio_del_catalogo():
    limpio, _ = limpiar(crudo(fila(producto="Mouse", precio_unitario=None)))
    assert limpio.iloc[0]["precio_unitario"] == 250.0


# ------------------------------------------------------------ propiedades
def test_el_reporte_cuadra_y_los_datos_son_consistentes():
    limpio, reporte = limpiar(generar_ventas_crudas(filas=800, semilla=1))
    descartadas = sum(reporte[m] for m in MOTIVOS_DESCARTE)
    assert reporte["filas_iniciales"] - descartadas == reporte["filas_finales"] == len(limpio)
    assert limpio["id_venta"].is_unique
    assert not limpio.isna().any().any()
    assert ((limpio["cantidad"] * limpio["precio_unitario"]).round(2) == limpio["total"]).all()
    assert (limpio["cantidad"] > 0).all() and (limpio["precio_unitario"] > 0).all()
