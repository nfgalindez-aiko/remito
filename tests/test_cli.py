from __future__ import annotations

import pytest

from remito.cli import armar_casos, main
from remito.validacion import Chequeo, Gravedad


class TestLaDemo:
    def test_corre_y_sale_bien(self, capsys) -> None:
        assert main(["demo"]) == 0
        assert "APROBADO" in capsys.readouterr().out

    def test_la_factura_real_entra_y_las_rotas_no(self) -> None:
        aprobados = [titulo for titulo, _, v, _ in armar_casos() if v.aprobado]
        assert len(aprobados) == 2  # la factura como vino, y la misma con la maña

    def test_cada_caso_rechazado_explica_por_que(self) -> None:
        """Una demo que dice que no sin decir el motivo no muestra nada."""
        for titulo, _, v, _ in armar_casos():
            if not v.aprobado:
                assert v.vetos, titulo
                for veto in v.vetos:
                    assert len(veto.detalle) > 20, titulo

    def test_el_encabezado_cuenta_los_casos_que_hay(self, capsys) -> None:
        """R10: el número del texto sale del dato, no de la memoria del que escribió.

        Si alguien agrega o saca un caso, el encabezado se corrige solo. Este test existe
        porque el mismo error de conteo ya se cometió tres veces en este repo.
        """
        main(["demo"])
        rechazados = sum(1 for _, _, v, _ in armar_casos() if not v.aprobado)
        assert f"y {rechazados} formas de romperla" in capsys.readouterr().out

    def test_los_vetos_aparecen_marcados_como_veto(self, capsys) -> None:
        main(["demo"])
        salida = capsys.readouterr().out
        assert "veto" in salida and "aviso" in salida


class TestRevisarArchivo:
    def test_devuelve_cero_con_la_factura_real(self, capsys) -> None:
        from remito.cli import DATOS

        assert main(["revisar", str(DATOS / "p01-2026-09-17.json")]) == 0

    def test_codigo_de_salida_distinto_de_cero_si_no_aprueba(self, tmp_path, capsys) -> None:
        """El código de salida es lo que usa un script para saber si algo entró o no.
        Devolver siempre cero convierte el veto en un adorno."""
        from remito.cli import DATOS
        import json

        datos = json.loads((DATOS / "p01-2026-09-17.json").read_text(encoding="utf-8"))
        datos["lineas"].pop()
        roto = tmp_path / "roto.json"
        roto.write_text(json.dumps(datos), encoding="utf-8")
        assert main(["revisar", str(roto)]) == 1


class TestSinArgumentos:
    def test_sin_comando_no_revienta_feo(self) -> None:
        with pytest.raises(SystemExit):
            main([])
