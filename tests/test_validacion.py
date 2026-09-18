from __future__ import annotations

import dataclasses
from datetime import date

from remito.comprobante import Linea
from remito.plata import Centavos
from remito.validacion import (
    Chequeo,
    DesvioConocido,
    Gravedad,
    revisar,
    tolerancia_linea,
)


class TestLaFacturaReal:
    def test_se_aprueba(self, p01) -> None:
        """La factura A 0026-00183517 de P01 es legítima y tiene que entrar."""
        assert revisar(p01).aprobado

    def test_pero_avisa_que_el_total_no_cierra(self, p01) -> None:
        """38.068,23 + 609,09 + 7.994,33 = 46.671,65 y el papel dice 46.671,64.

        Este es el test que existe para que nadie vuelva a convertir el aviso en veto.
        Si alguien lo hace, este test se pone en rojo y le explica por qué.
        """
        avisos = [d for d in revisar(p01).descuadres if d.chequeo is Chequeo.TOTAL]
        assert len(avisos) == 1
        assert avisos[0].gravedad is Gravedad.AVISO
        assert avisos[0].diferencia_centavos == 1

    def test_el_subtotal_cierra_exacto(self, p01) -> None:
        assert not [d for d in revisar(p01).descuadres if d.chequeo is Chequeo.SUBTOTAL]

    def test_las_unidades_cierran(self, p01) -> None:
        assert sum(l.cantidad for l in p01.lineas) == p01.pie.unidades == 26
        assert not [d for d in revisar(p01).descuadres if d.chequeo is Chequeo.UNIDADES]

    def test_las_lineas_que_no_dan_exactas_igual_pasan(self, p01) -> None:
        """Cuatro de las seis líneas tienen precio × cantidad ≠ subtotal, por 1 o 2 centavos,
        porque el precio impreso está redondeado. Ninguna es un descuadre."""
        desajustadas = [
            l for l in p01.lineas if l.precio_unitario * l.cantidad != l.subtotal
        ]
        assert len(desajustadas) == 4
        assert not [d for d in revisar(p01).descuadres if d.chequeo is Chequeo.LINEA]


class TestLineaTapadaPorLaSegundaHoja:
    """El modo de falla que motivó el proyecto: la foto no muestra todas las líneas."""

    def test_falta_una_linea_entera(self, p01) -> None:
        mocho = dataclasses.replace(p01, lineas=p01.lineas[:-1])
        veredicto = revisar(mocho)
        assert not veredicto.aprobado
        chequeos = {d.chequeo for d in veredicto.vetos}
        assert Chequeo.SUBTOTAL in chequeos
        assert Chequeo.UNIDADES in chequeos

    def test_la_linea_tapada_tenia_subtotal_cero(self, p01) -> None:
        """Acá está la razón de mantener los dos vetos aunque parezcan el mismo.

        Una línea de subtotal cero —una bonificación, un producto de regalo— no mueve la
        suma de plata, así que el veto del subtotal no la ve. El de unidades sí. Sin el
        segundo, esa mercadería nunca entra al stock y nadie se entera.
        """
        regalo = Linea("9999", "PROMO SIN CARGO", 2, Centavos(0), Centavos(0))
        con_regalo = dataclasses.replace(
            p01,
            lineas=p01.lineas + (regalo,),
            pie=dataclasses.replace(p01.pie, unidades=28),
        )
        completo = revisar(con_regalo)
        assert completo.aprobado

        sin_el_regalo = dataclasses.replace(
            con_regalo, lineas=con_regalo.lineas[:-1]
        )
        veredicto = revisar(sin_el_regalo)
        assert not veredicto.aprobado
        assert {d.chequeo for d in veredicto.vetos} == {Chequeo.UNIDADES}

    def test_sin_ninguna_linea(self, p01) -> None:
        veredicto = revisar(dataclasses.replace(p01, lineas=()))
        assert not veredicto.aprobado


class TestElOcrSeComeLaComa:
    def test_un_precio_cien_veces_mas_grande_no_entra(self, p01) -> None:
        """"737,61" leído como "73761" da $73.761 en vez de $737,61.

        El parser no puede distinguirlo: "$ 73761" es un importe perfectamente válido.
        Lo agarra la aritmética, que es de lo que se trata todo esto.
        """
        rota = dataclasses.replace(
            p01.lineas[0], precio_unitario=Centavos(7376100), subtotal=Centavos(36880500)
        )
        veredicto = revisar(dataclasses.replace(p01, lineas=(rota,) + p01.lineas[1:]))
        assert not veredicto.aprobado
        assert Chequeo.SUBTOTAL in {d.chequeo for d in veredicto.vetos}


class TestToleranciaDeLinea:
    def test_la_formula(self) -> None:
        assert tolerancia_linea(1) == 2
        assert tolerancia_linea(3) == 3
        assert tolerancia_linea(5) == 4

    def test_cubre_lo_observado_en_p01(self, p01) -> None:
        """El peor desvío medido en la factura real fue de 2 centavos, en una línea de 5
        unidades. La tolerancia para q=5 es 4."""
        peor = max(
            abs(l.subtotal - l.precio_unitario * l.cantidad) for l in p01.lineas
        )
        assert peor == 2
        assert peor < tolerancia_linea(5)

    def test_un_centavo_de_mas_y_no_pasa(self, p01) -> None:
        linea = p01.lineas[0]  # q=5, tolerancia 4
        rota = dataclasses.replace(linea, subtotal=Centavos(linea.subtotal + 5))
        veredicto = revisar(dataclasses.replace(p01, lineas=(rota,) + p01.lineas[1:]))
        assert Chequeo.LINEA in {d.chequeo for d in veredicto.vetos}


class TestMañasDelProveedor:
    """R8 del ESTADO, idea de Nicolás: un desvío legítimo se confirma una vez y se anota."""

    def _maña_de_p01(self) -> DesvioConocido:
        return DesvioConocido(
            proveedor="P01",
            chequeo=Chequeo.TOTAL,
            tolerancia_centavos=1,
            confirmado_por="Nicolás",
            fecha=date(2026, 9, 18),
            nota="redondea el total un centavo para abajo, siempre",
        )

    def test_el_aviso_queda_marcado_como_maña_conocida(self, p01) -> None:
        veredicto = revisar(p01, (self._maña_de_p01(),))
        aviso = next(d for d in veredicto.descuadres if d.chequeo is Chequeo.TOTAL)
        assert "maña conocida de P01" in aviso.detalle
        assert "Nicolás" in aviso.detalle and "2026-09-18" in aviso.detalle

    def test_la_maña_es_de_un_proveedor_y_no_afloja_a_los_demas(self, p01) -> None:
        """Lo que hace que esto sea una decisión y no una tolerancia global."""
        otro = dataclasses.replace(p01, proveedor="P02")
        aviso = next(
            d
            for d in revisar(otro, (self._maña_de_p01(),)).descuadres
            if d.chequeo is Chequeo.TOTAL
        )
        assert "maña conocida" not in aviso.detalle

    def test_una_maña_de_un_chequeo_no_afloja_otro(self, p01) -> None:
        mocho = dataclasses.replace(p01, lineas=p01.lineas[:-1])
        veredicto = revisar(mocho, (self._maña_de_p01(),))
        assert not veredicto.aprobado

    def test_un_desvio_mas_grande_que_la_maña_sigue_frenando(self, p01) -> None:
        """La maña de P01 es de un centavo. Dos centavos es otra cosa y frena."""
        maña = self._maña_de_p01()
        peor = dataclasses.replace(
            p01, pie=dataclasses.replace(p01.pie, total=Centavos(p01.pie.total - 50))
        )
        aviso = next(
            d for d in revisar(peor, (maña,)).descuadres if d.chequeo is Chequeo.TOTAL
        )
        assert "maña conocida" not in aviso.detalle


class TestIdempotencia:
    def test_la_misma_factura_da_la_misma_clave(self, p01) -> None:
        """Dos fotos del mismo papel tienen que chocar contra el mismo UNIQUE."""
        otra_foto = dataclasses.replace(p01, hoja="1/1")
        assert p01.id_unico == otra_foto.id_unico
        assert p01.id_unico == "P01|A|0026|00183517"

    def test_un_numero_distinto_es_otra_factura(self, p01) -> None:
        assert p01.id_unico != dataclasses.replace(p01, numero="00183518").id_unico
