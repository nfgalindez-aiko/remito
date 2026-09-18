from __future__ import annotations

import pytest

from remito.plata import iva
from remito.sintetico import (
    caso_con_senal,
    caso_fuga,
    caso_linea_tapada,
    caso_sin_senal,
    degradar,
    dibujar,
    generar,
)
from remito.validacion import Chequeo, Gravedad, revisar


class TestLaAritmeticaDelGenerado:
    """Si los comprobantes inventados fueran más prolijos que los de verdad, certificarían
    un medidor que después falla con el primer papel del kiosco."""

    @pytest.mark.parametrize("semilla", range(30))
    def test_siempre_se_aprueba(self, semilla: int) -> None:
        assert revisar(generar(semilla)).aprobado

    @pytest.mark.parametrize("semilla", range(30))
    def test_las_lineas_suman_el_subtotal_exacto(self, semilla: int) -> None:
        c = generar(semilla)
        assert sum(l.subtotal for l in c.lineas) == c.pie.subtotal

    @pytest.mark.parametrize("semilla", range(30))
    def test_el_iva_es_el_21_del_neto(self, semilla: int) -> None:
        c = generar(semilla)
        assert c.pie.iva == iva(c.pie.subtotal)

    def test_reproduce_el_redondeo_del_precio_impreso(self) -> None:
        """Sobre treinta comprobantes tiene que aparecer el fenómeno de P01: líneas
        donde precio impreso × cantidad no da el subtotal impreso."""
        desajustadas = sum(
            1
            for semilla in range(30)
            for l in generar(semilla).lineas
            if l.precio_unitario * l.cantidad != l.subtotal
        )
        assert desajustadas > 0

    def test_ninguna_linea_desajustada_pasa_la_tolerancia(self) -> None:
        """El desajuste que genera tiene que ser del tamaño del real, no más grande."""
        for semilla in range(30):
            assert not [
                d for d in revisar(generar(semilla)).descuadres
                if d.chequeo is Chequeo.LINEA
            ]

    def test_es_determinista(self) -> None:
        assert generar(7) == generar(7)
        assert generar(7) != generar(8)


class TestLaMañaDeP01:
    def test_con_maña_el_total_no_cierra_pero_igual_aprueba(self) -> None:
        c = generar(11, maña_total_centavos=1)
        veredicto = revisar(c)
        assert veredicto.aprobado
        aviso = next(d for d in veredicto.descuadres if d.chequeo is Chequeo.TOTAL)
        assert aviso.gravedad is Gravedad.AVISO
        assert aviso.diferencia_centavos == 1

    def test_sin_maña_cierra_perfecto(self) -> None:
        assert not [
            d for d in revisar(generar(11)).descuadres if d.chequeo is Chequeo.TOTAL
        ]


class TestLosTresCasosDeCertificacion:
    """CRITERIOS.md sección 7. Por ahora comprueban que los casos se generan y que la
    verdad que llevan adentro es coherente; cuando exista el extractor, se le exige a él."""

    def test_con_senal(self) -> None:
        caso = caso_con_senal()
        assert revisar(caso.comprobante).aprobado
        assert caso.imagen.size[0] > 1000

    def test_con_senal_no_lleva_nada_tapado(self) -> None:
        """Si le taparan líneas, la verdad no estaría en la imagen y el caso no
        certificaría nada. Es el mismo dibujo degradado, sin la hoja encima."""
        caso = caso_con_senal(1)
        assert caso.imagen.tobytes() == degradar(dibujar(generar(1)), 1).tobytes()

    def test_linea_tapada_lo_correcto_es_no_aprobar(self) -> None:
        """La foto de Nicolás. Lo que se mide acá no es extraer bien: es darse cuenta."""
        caso = caso_linea_tapada()
        assert revisar(caso.comprobante).aprobado  # el papel entero sí cierra
        assert caso.imagen.tobytes() != degradar(
            dibujar(caso.comprobante), 4
        ).tobytes()

    def test_sin_senal(self) -> None:
        assert caso_sin_senal().size == (900, 700)

    def test_fuga_la_imagen_pierde_el_pie_pero_la_verdad_lo_conserva(self) -> None:
        """La verdad sigue teniendo el total; la imagen no. Esa diferencia es justamente
        lo que mide si el sistema inventa."""
        caso = caso_fuga()
        assert caso.comprobante.pie.total > 0
        entera = degradar(dibujar(caso.comprobante), 3)
        assert caso.imagen.height < entera.height

    def test_la_hoja_superpuesta_tapa_algo(self) -> None:
        c = generar(5)
        limpia = degradar(dibujar(c), 5)
        tapada = degradar(dibujar(c), 5, hoja_superpuesta=True)
        assert limpia.size == tapada.size
        assert limpia.tobytes() != tapada.tobytes()

    def test_degradar_es_determinista(self) -> None:
        c = generar(9)
        assert degradar(dibujar(c), 4).tobytes() == degradar(dibujar(c), 4).tobytes()
