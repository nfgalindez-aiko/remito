from __future__ import annotations

import pytest

from remito.plata import (
    ImporteInvalido,
    comparar_costo_unitario,
    formatear,
    iva,
    parse_importe,
)


class TestParseImporte:
    @pytest.mark.parametrize(
        "texto, esperado",
        [
            ("$ 737,61", 73761),
            ("$ 3.688,05", 368805),
            ("$ 46.671,64", 4667164),
            ("$ 0,00", 0),
            ("1.981,74", 198174),
            ("609,09", 60909),
        ],
    )
    def test_formato_argentino(self, texto: str, esperado: int) -> None:
        assert parse_importe(texto) == esperado

    def test_el_mismo_papel_trae_dos_formatos(self) -> None:
        """La factura P01 imprime el TOTAL con coma decimal y el IVA con punto decimal.

        No es un error de transcripción: está así en el papel. Cualquier parser que
        asuma "el punto es de miles" convierte 7994.33 en 799.433 pesos, cien veces
        más, y después ese número cierra contra nada.
        """
        assert parse_importe("$ 46.671,64") == 4667164
        assert parse_importe("7994.33") == 799433

    @pytest.mark.parametrize(
        "texto, esperado",
        [
            ("38.068", 3806800),  # tres dígitos después del punto: son miles
            ("1.234.567", 123456700),
            ("7994.3", 799430),  # uno o dos dígitos: es decimal
        ],
    )
    def test_cuando_solo_hay_puntos_deciden_los_digitos(
        self, texto: str, esperado: int
    ) -> None:
        assert parse_importe(texto) == esperado

    def test_formato_yanqui_tambien_entra(self) -> None:
        """Con los dos separadores presentes manda el último. Ningún proveedor del kiosco
        factura así, pero la regla sale gratis y no adivina."""
        assert parse_importe("1,234.56") == 123456

    def test_sin_separador_son_pesos_enteros(self) -> None:
        assert parse_importe("$ 1000") == 100000

    @pytest.mark.parametrize("texto", ["", "   ", "$", "abc", "1.2.3", "3.68.8,05"])
    def test_lo_que_no_se_puede_leer_no_se_adivina(self, texto: str) -> None:
        with pytest.raises(ImporteInvalido):
            parse_importe(texto)

    def test_grupo_de_miles_mal_formado_no_pasa(self) -> None:
        """El OCR sobre una foto torcida mueve los puntos. "3.68.8,05" tiene un grupo de
        dos dígitos: no es un número argentino válido y no se parsea a 3.688,05 "porque
        se entiende". Un importe plausible e inventado es peor que un error."""
        with pytest.raises(ImporteInvalido):
            parse_importe("3.68.8,05")

    def test_la_factura_entera_se_parsea_igual_a_su_etiqueta(self, datos_p01) -> None:
        """Cada importe impreso del fixture tiene al lado su valor en centavos, puesto a
        mano. Esto compara las dos columnas."""
        for linea in datos_p01["lineas"]:
            assert parse_importe(linea["precio_unitario_impreso"]) == linea["precio_unitario"]
            assert parse_importe(linea["subtotal_impreso"]) == linea["subtotal"]
        pie = datos_p01["pie"]
        for campo in (
            "subtotal",
            "otros_descuentos",
            "percepcion_iva",
            "percepcion_iibb",
            "impuestos_internos",
            "iva",
            "total",
        ):
            assert parse_importe(pie[f"{campo}_impreso"]) == pie[campo], campo

    def test_todo_lo_que_devuelve_es_int(self) -> None:
        """Si alguna vez entra un float por acá, se lleva puesto el resto del proyecto."""
        for texto in ("$ 46.671,64", "7994.33", "$ 0,00", "38.068"):
            assert type(parse_importe(texto)) is int


class TestFormatear:
    @pytest.mark.parametrize(
        "centavos, esperado",
        [(4667164, "46.671,64"), (0, "0,00"), (5, "0,05"), (100000000, "1.000.000,00")],
    )
    def test_formatear(self, centavos: int, esperado: str) -> None:
        assert formatear(centavos) == esperado

    def test_ida_y_vuelta(self) -> None:
        for centavos in (0, 5, 73761, 4667164, 123456700):
            assert parse_importe(formatear(centavos)) == centavos


class TestIva:
    def test_contra_el_papel(self) -> None:
        """P01: neto 38.068,23, IVA impreso 7.994,33."""
        assert iva(3806823) == 799433

    def test_el_caso_donde_el_float_se_equivoca(self) -> None:
        """Medido el 18/09/2026: sobre los 19.999.900 netos posibles de $1 a $200.000,
        147.239 (el 0,736%) dan un IVA distinto en float que en enteros. Este es el
        primero de la lista.

        En float: round(3.50 * 0.21, 2) == 0.73, porque 0.735 no existe exacto en binario
        y cae apenas por debajo. La respuesta correcta es 0,74.
        """
        assert iva(350) == 74
        assert round(3.50 * 0.21, 2) == 0.73  # lo que haría un programa con floats

    @pytest.mark.parametrize("neto", [350, 450, 650, 750, 850, 950])
    def test_los_otros_cinco_casos_medidos(self, neto: int) -> None:
        por_float = round(round((neto / 100) * 0.21, 2) * 100)
        assert iva(neto) == por_float + 1

    def test_redondeo_half_up_no_bancario(self) -> None:
        """Python redondea 0,5 al par más cercano; AFIP no. 2,675 va a 2,68, no a 2,67."""
        assert iva(1274) == 268  # 1274 * 0,21 = 267,54 -> 268
        assert round(12.74 * 0.21, 2) == 2.68


class TestCompararCostoUnitario:
    def test_precio_impreso_igual_pero_costo_distinto(self) -> None:
        """Las dos líneas imprimirían el mismo precio unitario, 1.981,74, y sin embargo
        una cuesta más que la otra.

        5.945,21 / 3 = 1.981,7367 -> imprime 1.981,74
        5.945,22 / 3 = 1.981,7400 -> imprime 1.981,74

        Un sistema que compare precios impresos dice "no aumentó". Uno que compare
        subtotales cruzados dice la verdad. Por eso no se divide nunca.
        """
        assert comparar_costo_unitario(594521, 3, 594522, 3) == -1

    def test_cantidades_distintas(self) -> None:
        """Mismo producto, una vez por 3 unidades y otra por 5, al mismo costo real."""
        assert comparar_costo_unitario(300, 3, 500, 5) == 0
        assert comparar_costo_unitario(300, 3, 501, 5) == -1

    def test_contra_las_lineas_reales_de_p01(self, datos_p01) -> None:
        por_codigo = {l["codigo"]: l for l in datos_p01["lineas"]}
        kokis_a, kokis_b = por_codigo["15004"], por_codigo["15001"]
        # Dos productos distintos al mismo precio: el membrillito y el cañoncito.
        assert (
            comparar_costo_unitario(
                kokis_a["subtotal"], kokis_a["cantidad"],
                kokis_b["subtotal"], kokis_b["cantidad"],
            )
            == 0
        )
        jorgito, rhodesia = por_codigo["1825"], por_codigo["3398"]
        assert (
            comparar_costo_unitario(
                jorgito["subtotal"], jorgito["cantidad"],
                rhodesia["subtotal"], rhodesia["cantidad"],
            )
            == -1
        )

    def test_cantidad_cero_no_se_deja_pasar(self) -> None:
        with pytest.raises(ValueError):
            comparar_costo_unitario(100, 0, 100, 1)


class TestLoQueNoSePuedeSaberNoSeElige:
    """`ImporteAmbiguo` existía documentado y sin levantarse nunca.

    Lo encontró la consolidación del 18/09/2026: una clase con un docstring que decía "se
    levanta en vez de elegir" mientras el código elegía igual. Es la misma falta que un
    README que promete lo que no hay, pero adentro del código, donde nadie la ve hasta que
    la busca.
    """

    def test_una_coma_con_tres_digitos_no_se_adivina(self) -> None:
        """"1,234" es 1234 en formato yanqui y 1,234 en argentino. Mil veces distinto."""
        from remito.plata import ImporteAmbiguo

        with pytest.raises(ImporteAmbiguo):
            parse_importe("1,234")

    def test_pero_un_punto_con_tres_digitos_si(self) -> None:
        """Acá sí se sabe: así está impreso el SUB-TOTAL en la factura de P01."""
        assert parse_importe("38.068") == 3806800

    def test_la_coma_con_dos_digitos_es_decimal_y_no_tiene_nada_de_ambiguo(self) -> None:
        assert parse_importe("1,23") == 123

    def test_con_los_dos_separadores_no_hay_ambiguedad(self) -> None:
        """El último manda, y eso resuelve el caso sin adivinar."""
        assert parse_importe("1.234,56") == 123456
        assert parse_importe("1,234.56") == 123456

    def test_ambiguo_es_distinto_de_invalido(self) -> None:
        """Quien llame tiene que poder distinguir "esto no es un número" de "esto es un
        número y no sé cuál": el segundo caso se le puede preguntar a un humano."""
        from remito.plata import ImporteAmbiguo, ImporteInvalido

        assert issubclass(ImporteAmbiguo, ValueError)
        assert not issubclass(ImporteAmbiguo, ImporteInvalido)


class TestUnaSolaFormaDeRedondear:
    def test_las_cuatro_cuentas_que_estaban_sueltas_dan_lo_mismo(self) -> None:
        """Antes de consolidar, este redondeo estaba escrito de cuatro formas distintas en
        cuatro archivos. Este test fija que la única que quedó hace lo que hacían las cuatro."""
        from remito.plata import redondear

        assert redondear(3806823 * 210, 1000) == (3806823 * 210 + 500) // 1000
        assert redondear(6225922 * 16, 1000) == (6225922 * 16 * 2 + 1000) // 2000
        assert redondear(594521, 3) == (594521 * 2 + 3) // (3 * 2)

    def test_redondea_para_arriba_en_el_medio_como_AFIP(self) -> None:
        from remito.plata import redondear

        assert redondear(5, 2) == 3  # 2,5 -> 3, no 2 como el redondeo al par de Python
        assert redondear(7, 2) == 4
        assert round(2.5) == 2  # lo que haría Python, para que se vea la diferencia

    def test_no_acepta_negativos_en_vez_de_hacer_cualquier_cosa(self) -> None:
        from remito.plata import redondear

        with pytest.raises(ValueError):
            redondear(-100, 3)
        with pytest.raises(ValueError):
            redondear(100, 0)
