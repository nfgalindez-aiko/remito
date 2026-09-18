from __future__ import annotations

import json
import re
from datetime import datetime, timezone

import pytest

from remito.bitacora import (
    Bitacora,
    DatoQueNoVaEnLaBitacora,
    hilo_de,
    leer,
    nuevo_id,
)


class TestElIdentificador:
    def test_empieza_con_el_dia(self) -> None:
        assert nuevo_id(datetime(2026, 9, 18, tzinfo=timezone.utc)).startswith("0918-")

    def test_no_lleva_caracteres_que_se_copian_mal(self) -> None:
        """Alguien lo va a anotar en el margen del papel y después tipearlo.

        O y 0, I y l y 1 son las que se confunden a mano. Sacarlas cuesta un poco de
        espacio de combinaciones y ahorra un llamado por teléfono.
        """
        sufijos = "".join(nuevo_id().split("-")[1] for _ in range(500))
        confusos = set(sufijos) & set("o0il1")
        assert not confusos, f"salieron caracteres que se copian mal: {sorted(confusos)}"

    def test_se_puede_decir_por_telefono(self) -> None:
        assert re.fullmatch(r"\d{4}-[a-z2-9]{4}", nuevo_id())

    def test_dos_seguidos_no_son_iguales(self) -> None:
        assert len({nuevo_id() for _ in range(200)}) > 190


class TestNoEntranDatosPersonales:
    def test_un_cuit_con_guiones_no_entra(self, tmp_path) -> None:
        b = Bitacora(tmp_path / "b.jsonl")
        with pytest.raises(DatoQueNoVaEnLaBitacora):
            b.escribir("0918-aaaa", "prueba", {"quien": "CUIT 33-65197123-9"})

    def test_un_cuit_sin_guiones_tampoco(self, tmp_path) -> None:
        b = Bitacora(tmp_path / "b.jsonl")
        with pytest.raises(DatoQueNoVaEnLaBitacora):
            b.escribir("0918-aaaa", "prueba", {"quien": "33651971239"})

    def test_ni_escondido_adentro_de_una_lista(self, tmp_path) -> None:
        """Los datos personales se cuelan por los campos que nadie mira, como una lista de
        motivos de rechazo armada con texto del documento."""
        b = Bitacora(tmp_path / "b.jsonl")
        with pytest.raises(DatoQueNoVaEnLaBitacora):
            b.escribir("0918-aaaa", "prueba", {"motivos": ["todo bien", "23-37388418-9"]})

    def test_los_importes_si_entran(self, tmp_path) -> None:
        """La plata tiene que estar: sin los números la bitácora no contesta nada."""
        b = Bitacora(tmp_path / "b.jsonl")
        b.escribir("0918-aaaa", "revisado", {"subtotal": 3806823, "unidades": 26})
        assert leer(b.ruta)[0]["subtotal"] == 3806823


class TestElHiloDeUnComprobante:
    def test_todas_las_anotaciones_llevan_el_mismo_id(self, tmp_path) -> None:
        b = Bitacora(tmp_path / "b.jsonl")
        with b.comprobante() as s:
            s.anotar("leido", lineas=6)
            s.anotar("revisado", aprobado=False)
        ids = {a["id"] for a in leer(b.ruta)}
        assert len(ids) == 1
        assert [a["evento"] for a in leer(b.ruta)] == [
            "abierto", "leido", "revisado", "cerrado"
        ]

    def test_si_revienta_queda_escrito_que_reventó(self, tmp_path) -> None:
        """Un comprobante cuyo último evento es "abierto" y nada más es indistinguible de
        uno que nunca se procesó. Con esto se distingue."""
        b = Bitacora(tmp_path / "b.jsonl")
        with pytest.raises(ZeroDivisionError):
            with b.comprobante() as s:
                s.anotar("leido")
                1 // 0
        eventos = [a["evento"] for a in leer(b.ruta)]
        assert "reventó" in eventos
        assert eventos[-1] == "cerrado"
        anotacion = next(a for a in leer(b.ruta) if a["evento"] == "reventó")
        assert anotacion["error"] == "ZeroDivisionError"

    def test_hilo_de_separa_un_comprobante_de_los_demas(self, tmp_path) -> None:
        """La pregunta real: "esta factura quedó en revisión, ¿por qué?". Con la bitácora
        de un mes mezclada, hay que poder sacar una sola."""
        b = Bitacora(tmp_path / "b.jsonl")
        with b.comprobante("0918-aaaa") as s:
            s.anotar("a_revision", motivos=["las líneas suman 31.952,99"])
        with b.comprobante("0918-bbbb") as s:
            s.anotar("cargado")
        hilo = hilo_de(b.ruta, "0918-aaaa")
        assert {a["evento"] for a in hilo} == {"abierto", "a_revision", "cerrado"}
        assert "31.952,99" in hilo[1]["motivos"][0]


class TestElArchivo:
    def test_una_linea_json_por_evento(self, tmp_path) -> None:
        b = Bitacora(tmp_path / "b.jsonl")
        with b.comprobante():
            pass
        for linea in (tmp_path / "b.jsonl").read_text(encoding="utf-8").splitlines():
            assert json.loads(linea)["ts"]

    def test_no_pisa_lo_que_ya_habia(self, tmp_path) -> None:
        b = Bitacora(tmp_path / "b.jsonl")
        with b.comprobante("0918-aaaa"):
            pass
        with b.comprobante("0918-bbbb"):
            pass
        assert len({a["id"] for a in leer(b.ruta)}) == 2

    def test_crea_la_carpeta_si_no_existe(self, tmp_path) -> None:
        b = Bitacora(tmp_path / "sub" / "carpeta" / "b.jsonl")
        with b.comprobante():
            pass
        assert b.ruta.exists()

    def test_la_ruta_sale_del_entorno(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setenv("REMITO_BITACORA", str(tmp_path / "desde-el-entorno.jsonl"))
        assert Bitacora().ruta.name == "desde-el-entorno.jsonl"

    def test_leer_una_bitacora_que_no_existe_no_revienta(self, tmp_path) -> None:
        assert leer(tmp_path / "no-existe.jsonl") == []
