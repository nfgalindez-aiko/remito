from __future__ import annotations

import sqlite3
from concurrent.futures import ThreadPoolExecutor
from datetime import date

import pytest

from remito.base import (
    Carga,
    aumento_de,
    aumentos,
    cargar,
    conectar,
    desvios_de,
    guardar_desvio,
    historial,
)
from remito.comprobante import Comprobante, Linea, PieDeComprobante
from remito.plata import Centavos
from remito.validacion import Chequeo, DesvioConocido, Veredicto, revisar

import dataclasses


@pytest.fixture
def conn():
    c = conectar()
    yield c
    c.close()


@pytest.fixture
def archivo(tmp_path):
    return tmp_path / "remito.sqlite"


def compra(codigo: str, cantidad: int, subtotal: int, numero: str, fecha: str) -> Comprobante:
    """Un comprobante de una línea, para armar historiales de precio."""
    return Comprobante(
        proveedor="P01", tipo="A", punto_venta="0026", numero=numero,
        fecha=date.fromisoformat(fecha),
        # El precio unitario se redondea half-up, como lo imprime el papel, no con
        # división entera: si no, el test de abajo compararía un redondeo que no existe.
        lineas=(Linea(codigo, "KOKIS MEMBRILLITO 500 G", cantidad,
                      Centavos((subtotal * 2 + cantidad) // (cantidad * 2)),
                      Centavos(subtotal)),),
        pie=PieDeComprobante(subtotal=Centavos(subtotal), total=Centavos(subtotal),
                             unidades=cantidad),
    )


class TestIdempotencia:
    """Requisito 4 de PLAN.md, pedido por 7 de los 9 evaluadores."""

    def test_la_segunda_vez_dice_que_ya_estaba(self, conn, p01) -> None:
        v = revisar(p01)
        assert cargar(conn, p01, v) is Carga.NUEVO
        assert cargar(conn, p01, v) is Carga.YA_ESTABA

    def test_y_no_duplica_las_lineas(self, conn, p01) -> None:
        v = revisar(p01)
        cargar(conn, p01, v)
        cargar(conn, p01, v)
        assert conn.execute("SELECT count(*) FROM comprobante").fetchone()[0] == 1
        assert conn.execute("SELECT count(*) FROM linea").fetchone()[0] == len(p01.lineas)

    def test_doce_hilos_cargando_la_misma_factura_a_la_vez(self, archivo, p01) -> None:
        """El caso que un `if ya existe` no cubre.

        Preguntar y después insertar deja una ventana entre las dos cosas. Doce hilos que
        preguntan al mismo tiempo reciben todos "no existe" y todos insertan. Acá la
        unicidad la hace la clave primaria, así que gana exactamente uno.

        Honestidad sobre lo que este test prueba y lo que no: SQLite serializa a los
        escritores, así que esto demuestra que la restricción se cumple, no que el sistema
        aguante contención de verdad. Con Postgres el test sería el mismo y la prueba más
        fuerte; por qué no hay Postgres está en docs/adr/0001.
        """
        conectar(archivo).close()  # crea el esquema una vez
        v = revisar(p01)

        def intentar(_: int) -> Carga:
            c = conectar(archivo)
            try:
                return cargar(c, p01, v)
            finally:
                c.close()

        with ThreadPoolExecutor(max_workers=12) as pool:
            resultados = list(pool.map(intentar, range(12)))

        assert resultados.count(Carga.NUEVO) == 1
        assert resultados.count(Carga.YA_ESTABA) == 11

        c = conectar(archivo)
        assert c.execute("SELECT count(*) FROM comprobante").fetchone()[0] == 1
        assert c.execute("SELECT count(*) FROM linea").fetchone()[0] == len(p01.lineas)
        c.close()

    def test_otro_numero_es_otra_factura(self, conn, p01) -> None:
        v = revisar(p01)
        cargar(conn, p01, v)
        assert cargar(conn, dataclasses.replace(p01, numero="00183518"), v) is Carga.NUEVO


class TestLaBaseNoDejaEntrarFloats:
    def test_el_check_rechaza_un_subtotal_decimal(self, conn, p01) -> None:
        """SQLite tiene afinidad de tipos, no tipos: en una columna INTEGER entra un 1.5.
        El CHECK de typeof es lo único que lo impide."""
        rota = dataclasses.replace(
            p01, lineas=(dataclasses.replace(p01.lineas[0], subtotal=Centavos(3688.05)),)
        )
        with pytest.raises(sqlite3.IntegrityError):
            cargar(conn, rota, revisar(p01))

    def test_y_si_falla_una_linea_no_queda_el_comprobante(self, conn, p01) -> None:
        """La transacción es todo o nada. Un comprobante sin sus líneas en la base es peor
        que ninguno: parece cargado y no tiene la mercadería."""
        rota = dataclasses.replace(
            p01,
            lineas=p01.lineas[:2] + (dataclasses.replace(p01.lineas[2], subtotal=Centavos(1.5)),),
        )
        with pytest.raises(sqlite3.IntegrityError):
            cargar(conn, rota, revisar(p01))
        assert conn.execute("SELECT count(*) FROM comprobante").fetchone()[0] == 0
        assert conn.execute("SELECT count(*) FROM linea").fetchone()[0] == 0


class TestClavesForaneas:
    def test_estan_encendidas(self, conn) -> None:
        """En SQLite vienen apagadas por defecto y por conexión. Sin el PRAGMA, REFERENCES
        es un comentario: se pueden meter líneas de un comprobante que no existe."""
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO linea VALUES ('no-existe', 0, 'X', 'X', 1, 100, 100)"
            )


class TestHistorialDePrecios:
    def test_lo_que_esta_a_revision_no_entra_al_historial(self, conn, p01) -> None:
        """El motivo por el que el estado existe.

        Un comprobante en la cola de revisión todavía no es un hecho. Si sus números
        entraran al historial, un precio mal leído se volvería una alerta de aumento que
        nunca pasó, y lo único que este sistema tiene para ofrecer es que sus avisos sean
        ciertos.
        """
        mocho = dataclasses.replace(p01, lineas=p01.lineas[:-1])
        veredicto = revisar(mocho)
        assert not veredicto.aprobado
        cargar(conn, mocho, veredicto)
        assert historial(conn, "P01", "1825") == []

    def test_ordena_de_la_mas_vieja_a_la_mas_nueva(self, conn) -> None:
        for numero, fecha in [("2", "2026-08-01"), ("1", "2026-06-01"), ("3", "2026-09-01")]:
            c = compra("15004", 3, 594521, numero, fecha)
            cargar(conn, c, revisar(c))
        assert [x.fecha.isoformat() for x in historial(conn, "P01", "15004")] == [
            "2026-06-01", "2026-08-01", "2026-09-01"
        ]


class TestAumento:
    def test_un_aumento_del_diez_por_ciento(self, conn) -> None:
        for c in (compra("15004", 3, 594521, "1", "2026-06-01"),
                  compra("15004", 5, 1090000, "2", "2026-09-01")):
            cargar(conn, c, revisar(c))
        a = aumento_de(conn, "P01", "15004")
        assert a is not None
        assert a.porcentaje == "10,00%"

    def test_si_bajo_no_avisa(self, conn) -> None:
        for c in (compra("15004", 3, 600000, "1", "2026-06-01"),
                  compra("15004", 3, 594521, "2", "2026-09-01")):
            cargar(conn, c, revisar(c))
        assert aumento_de(conn, "P01", "15004") is None

    def test_con_una_sola_compra_no_hay_con_que_comparar(self, conn) -> None:
        c = compra("15004", 3, 594521, "1", "2026-06-01")
        cargar(conn, c, revisar(c))
        assert aumento_de(conn, "P01", "15004") is None

    def test_el_precio_impreso_no_alcanza_para_verlo(self, conn) -> None:
        """Las dos compras imprimirían el mismo precio unitario: $ 1.981,74.

        5.945,21 / 3 = 1.981,7367
        5.945,22 / 3 = 1.981,7400

        Un sistema que compare precios impresos dice que no aumentó. Éste ve que sí.
        Es chiquito —un tercio de centavo— y ése es justamente el punto: la diferencia
        existe y el redondeo la borra.
        """
        for c in (compra("15004", 3, 594521, "1", "2026-06-01"),
                  compra("15004", 3, 594522, "2", "2026-09-01")):
            cargar(conn, c, revisar(c))
        impresos = conn.execute("SELECT DISTINCT precio_unitario FROM linea").fetchall()
        assert impresos == [(198174,)], "las dos compras imprimen el mismo precio unitario"
        assert aumento_de(conn, "P01", "15004") is not None

    def test_la_lista_sale_ordenada_del_que_mas_aumento(self, conn) -> None:
        datos = [("A", 100000, 150000), ("B", 100000, 110000), ("C", 100000, 300000)]
        for i, (codigo, viejo, nuevo) in enumerate(datos):
            for j, (monto, fecha) in enumerate([(viejo, "2026-06-01"), (nuevo, "2026-09-01")]):
                c = compra(codigo, 1, monto, f"{i}{j}", fecha)
                cargar(conn, c, revisar(c))
        assert [a.codigo for a in aumentos(conn, "P01")] == ["C", "A", "B"]


class TestDesviosConocidos:
    def _maña(self) -> DesvioConocido:
        return DesvioConocido("P01", Chequeo.TOTAL, 1, "Nicolás", date(2026, 9, 18),
                              "redondea el total un centavo para abajo")

    def test_se_guarda_y_se_lee_igual(self, conn) -> None:
        guardar_desvio(conn, self._maña())
        assert desvios_de(conn, "P01") == (self._maña(),)

    def test_no_se_le_dan_a_otro_proveedor(self, conn) -> None:
        guardar_desvio(conn, self._maña())
        assert desvios_de(conn, "P02") == ()

    def test_confirmarlo_de_nuevo_lo_actualiza_en_vez_de_duplicarlo(self, conn) -> None:
        guardar_desvio(conn, self._maña())
        guardar_desvio(conn, dataclasses.replace(self._maña(), tolerancia_centavos=2,
                                                 confirmado_por="Nicolás (revisado)"))
        desvios = desvios_de(conn, "P01")
        assert len(desvios) == 1
        assert desvios[0].tolerancia_centavos == 2

    def test_la_maña_guardada_sirve_para_aprobar(self, conn, p01) -> None:
        """El circuito completo: frena, el humano confirma, queda guardado, deja de frenar."""
        guardar_desvio(conn, self._maña())
        veredicto = revisar(p01, desvios_de(conn, "P01"))
        aviso = next(d for d in veredicto.descuadres if d.chequeo is Chequeo.TOTAL)
        assert "maña conocida" in aviso.detalle
