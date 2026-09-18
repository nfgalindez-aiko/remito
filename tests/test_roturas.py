from __future__ import annotations

from pathlib import Path

import pytest

from remito.roturas import LAS_DOCE, Defensa, por_defensa
from remito.validacion import revisar

TODAS = pytest.mark.parametrize("rotura", LAS_DOCE, ids=lambda r: r.nombre)


class TestElCatalogo:
    def test_son_doce(self) -> None:
        assert len(LAS_DOCE) == 12
        assert len({r.nombre for r in LAS_DOCE}) == 12

    @TODAS
    def test_explica_que_paso_en_el_mostrador(self, rotura) -> None:
        assert len(rotura.que_paso) > 30, rotura.nombre
        assert "error" not in rotura.que_paso.lower(), (
            f"{rotura.nombre}: decir 'error' no explica nada. Va lo que le pasó al papel."
        )

    @TODAS
    def test_la_verdad_siempre_cierra(self, rotura) -> None:
        """El papel nunca está mal. Lo que está mal es la lectura, o la foto. Si la verdad
        de una rotura no cerrara, el caso probaría otra cosa de la que dice probar."""
        assert revisar(rotura.armar().verdad).aprobado, rotura.nombre


class TestLasQueAgarraLaAritmetica:
    ARITMETICAS = pytest.mark.parametrize(
        "rotura", por_defensa(Defensa.ARITMETICA), ids=lambda r: r.nombre
    )

    @ARITMETICAS
    def test_la_lectura_no_se_aprueba(self, rotura) -> None:
        caso = rotura.armar()
        assert caso.lectura is not None
        assert not revisar(caso.lectura).aprobado, f"{rotura.nombre} pasó sin que nadie la frene"

    @ARITMETICAS
    def test_la_agarra_el_chequeo_que_dice_el_catalogo(self, rotura) -> None:
        """Si la agarra otro chequeo que el que dice la tabla, la tabla miente. Y la tabla
        es lo que se lee para entender hasta dónde llega la validación."""
        vetos = {d.chequeo for d in revisar(rotura.armar().lectura).vetos}
        assert rotura.chequeo in vetos, (
            f"{rotura.nombre}: el catálogo dice {rotura.chequeo.value}, "
            f"la frenaron {sorted(c.value for c in vetos)}"
        )


class TestLasQueLaAritmeticaNoPuedeVer:
    """La parte incómoda. Es la razón por la que la tabla vale más que las doce roturas."""

    SIN_ARITMETICA = pytest.mark.parametrize(
        "rotura",
        por_defensa(Defensa.EL_EXTRACTOR) + por_defensa(Defensa.NINGUNA),
        ids=lambda r: r.nombre,
    )

    @SIN_ARITMETICA
    def test_o_no_hay_nada_que_leer_o_lo_leido_pasa_los_chequeos(self, rotura) -> None:
        """Las dos formas de que la aritmética no sirva.

        O no hay lectura posible —la foto está movida, no es un comprobante—, o la lectura
        salió consistente consigo misma porque el que leyó armó el pie con lo que vio. En
        el segundo caso los cuatro chequeos dan bien sobre algo que está mal.
        """
        caso = rotura.armar()
        if caso.lectura is None:
            return
        assert revisar(caso.lectura).aprobado, (
            f"{rotura.nombre}: si la aritmética la frena, está mal clasificada"
        )

    @SIN_ARITMETICA
    def test_pero_lo_que_entraria_no_es_lo_que_dice_el_papel(self, rotura) -> None:
        """El daño, dicho sin vueltas: la lectura pasa y difiere de la verdad.

        `dos_papeles_en_la_misma_foto` es la excepción y por eso está aparte: lo que se
        leyó es correcto. Lo que se perdió es el otro papel, que nunca llegó a leerse, y
        sobre un documento que nadie leyó no hay chequeo posible.
        """
        caso = rotura.armar()
        if caso.lectura is None or rotura.defensa is Defensa.NINGUNA:
            return
        assert caso.lectura != caso.verdad, rotura.nombre
        faltantes = len(caso.verdad.lineas) - len(caso.lectura.lineas)
        distinta_plata = caso.lectura.pie.subtotal != caso.verdad.pie.subtotal
        assert faltantes > 0 or distinta_plata, rotura.nombre

    @SIN_ARITMETICA
    def test_traen_su_imagen(self, rotura) -> None:
        imagen = rotura.armar().imagen
        assert imagen is not None, rotura.nombre
        assert imagen.size[0] > 100 and imagen.size[1] > 100


class TestHastaDondeLlegaLaTesis:
    def test_el_reparto_suma_doce_y_hay_al_menos_una_sin_defensa(self) -> None:
        """No se afirma un reparto concreto acá a propósito.

        Un número escrito a mano en un assert se desactualiza y hay que corregirlo; peor,
        invita a reclasificar una rotura para que el número cierre. Lo que impide mentir
        con la clasificación son los tests de arriba, que verifican rotura por rotura que
        la etiqueta sea cierta. Acá sólo se exige que no falte ninguna y que el catálogo
        no se quede sin admitir al menos un caso sin defensa.
        """
        reparto = {d: len(por_defensa(d)) for d in Defensa}
        assert sum(reparto.values()) == 12
        assert reparto[Defensa.NINGUNA] >= 1, (
            "un catálogo de roturas donde todo tiene defensa es un folleto"
        )

    def test_lo_que_no_tiene_defensa_esta_escrito_en_limites(self) -> None:
        """Una rotura sin defensa que no esté en LIMITES.md es una mentira por omisión."""
        limites = (Path(__file__).resolve().parents[1] / "LIMITES.md").read_text(
            encoding="utf-8"
        ).lower()
        for r in por_defensa(Defensa.NINGUNA):
            assert "dos papeles" in limites or "dos facturas" in limites, (
                f"{r.nombre} no tiene defensa y no está en LIMITES.md"
            )
