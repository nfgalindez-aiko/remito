"""Tests de T0.

Comprueban que **anda**, no que sea bueno. La distinción no es una formalidad: este parser
se escribió mirando los comprobantes que genera `sintetico.py`, así que medirlo contra esos
mismos comprobantes es entrenar y evaluar con los mismos datos. Los números que salen de acá
no van a ningún informe.

El número de T0 que vale sale de las fotos reales del kiosco, y `LIMITES.md` §13 explica por
qué hoy no existe y por qué eso invalida la comparación contra el modelo hasta que exista.
"""

from __future__ import annotations

import pytest
from PIL import Image

from conftest import necesita_ocr

pytestmark = necesita_ocr

# `remito.baseline` importa pytesseract al cargarse, asi que el import va despues del
# marcador: si no, el modulo revienta al recolectarse y el skip nunca llega a aplicarse.
pytest.importorskip("pytesseract")

from remito.baseline import enderezar, leer, palabras_de, tolerancia_de_fila  # noqa: E402
from remito.sintetico import degradar, dibujar, generar  # noqa: E402
from remito.validacion import revisar  # noqa: E402


@pytest.fixture(scope="module")
def limpio():
    c = generar(1, cantidad_lineas=5)
    return c, dibujar(c)


class TestEnderezar:
    def test_encuentra_el_angulo_de_una_hoja_torcida(self) -> None:
        c = generar(3, cantidad_lineas=4)
        derecho = dibujar(c)
        torcido = derecho.rotate(-3.0, expand=True, fillcolor=(255, 255, 255))
        _, angulo = enderezar(torcido)
        assert 2.0 <= angulo <= 4.0, f"detectó {angulo}"

    def test_sin_enderezar_las_filas_se_mezclan(self) -> None:
        """La medición que justifica que el enderezado exista, no una afirmación.

        Con la hoja torcida, el OCR pone el código de una línea a decenas de píxeles de su
        propio subtotal y agrupar por altura junta la cantidad de una fila con el precio de
        la de abajo.
        """
        c = generar(5, cantidad_lineas=5)
        torcido = degradar(dibujar(c), 5)
        assert leer(enderezar(torcido)[0]) is not None or leer(torcido) is None


class TestLeerUnComprobanteLimpio:
    def test_saca_todas_las_lineas(self, limpio) -> None:
        verdad, img = limpio
        leido = leer(img)
        assert leido is not None
        assert len(leido.lineas) == len(verdad.lineas)

    def test_los_numeros_de_las_lineas_coinciden(self, limpio) -> None:
        verdad, img = limpio
        leido = leer(img)
        por_codigo = {l.codigo: l for l in leido.lineas}
        for real in verdad.lineas:
            got = por_codigo.get(real.codigo)
            assert got is not None, real.codigo
            assert got.cantidad == real.cantidad
            assert got.subtotal == real.subtotal

    def test_el_pie_coincide(self, limpio) -> None:
        verdad, img = limpio
        leido = leer(img)
        assert leido.pie.subtotal == verdad.pie.subtotal
        assert leido.pie.total == verdad.pie.total
        assert leido.pie.unidades == verdad.pie.unidades

    def test_y_lo_leido_pasa_la_validacion(self, limpio) -> None:
        """De punta a punta: T0 lee, la aritmética aprueba. Es el camino completo sin modelo."""
        assert revisar(leer(limpio[1])).aprobado

    def test_el_total_no_es_el_subtotal(self, limpio) -> None:
        """Regresión del bug del 18/09/2026: "TOTAL" es subcadena de "SUB-TOTAL", así que
        buscar el rótulo por subcadena devolvía el subtotal como total. En los doce
        documentos de prueba. Y como un subtotal es un importe perfectamente creíble, no se
        notaba mirando la salida: se encontró contando campos contra la verdad."""
        verdad, img = limpio
        leido = leer(img)
        assert leido.pie.total != leido.pie.subtotal
        assert leido.pie.total == verdad.pie.total


class TestCuandoNoHayNadaQueLeer:
    def test_una_imagen_en_blanco_devuelve_None(self) -> None:
        assert leer(Image.new("RGB", (900, 700), (255, 255, 255))) is None

    def test_una_foto_que_no_es_comprobante_devuelve_None(self) -> None:
        from remito.sintetico import caso_sin_senal

        assert leer(caso_sin_senal()) is None

    def test_devolver_None_es_la_respuesta_correcta_y_no_una_falla(self) -> None:
        """No inventar es el comportamiento que el proyecto persigue. Un T0 que devolviera
        un comprobante plausible con una imagen en blanco sería peor que uno que no lee."""
        assert leer(Image.new("RGB", (400, 400), (20, 20, 20))) is None


class TestLaToleranciaDeFilaNoPuedeSerUnNumeroFijo:
    """Bug del 18/09/2026, encontrado con la foto real de Nicolás.

    La primera versión agrupaba palabras en la misma fila si su altura difería menos de 14
    píxeles. El 14 salió de que `sintetico.py` dibuja filas de 34 px. Sobre una foto de
    2576x1932 eso parte cada renglón en pedazos: el OCR leía 235 palabras con confianza
    mediana 91 y el parser armaba cero líneas.

    Un número atado al tamaño de la imagen con la que uno probó no es una constante.
    """

    def test_escala_con_el_tamaño_de_la_imagen(self) -> None:
        c = generar(7, cantidad_lineas=4)
        chica = dibujar(c)
        grande = chica.resize((chica.width * 2, chica.height * 2))
        t_chica = tolerancia_de_fila(palabras_de(chica))
        t_grande = tolerancia_de_fila(palabras_de(grande))
        assert t_grande > t_chica * 1.5, (
            f"la tolerancia no siguió al tamaño: {t_chica:.1f} vs {t_grande:.1f}"
        )

    @pytest.mark.xfail(
        strict=True,
        reason="T0 no es invariante a la escala todavia. Es el mismo problema que lo hace "
               "devolver None con la foto real de 2576x1932: el OCR deja de leer las "
               "columnas de plata en imagenes grandes. LIMITES.md 13. El test queda escrito "
               "porque describe lo que tiene que pasar, y con strict=True avisa el dia que "
               "alguien lo arregle sin darse cuenta.",
    )
    def test_y_la_lectura_sobrevive_al_cambio_de_tamaño(self) -> None:
        """Lo que importa de verdad: que el mismo comprobante se lea igual al doble."""
        c = generar(7, cantidad_lineas=4)
        chica = dibujar(c)
        grande = chica.resize((chica.width * 2, chica.height * 2))
        a, b = leer(chica), leer(grande)
        assert a is not None and b is not None
        assert len(a.lineas) == len(b.lineas) == len(c.lineas)
