from __future__ import annotations

import json
from datetime import date
import pytest

from remito.comprobante import Comprobante, Linea, PieDeComprobante
from remito.plata import Centavos

from remito.cli import DATOS as FIXTURES  # noqa: E402


def cargar(nombre: str) -> dict:
    return json.loads((FIXTURES / f"{nombre}.json").read_text(encoding="utf-8"))


def armar(datos: dict) -> Comprobante:
    pie = datos["pie"]
    return Comprobante(
        proveedor=datos["proveedor"],
        tipo=datos["tipo"],
        punto_venta=datos["punto_venta"],
        numero=datos["numero"],
        fecha=date.fromisoformat(datos["fecha"]),
        remito_numero=datos.get("remito_numero"),
        hoja=datos.get("hoja"),
        lineas=tuple(
            Linea(
                codigo=l["codigo"],
                descripcion=l["descripcion"],
                cantidad=l["cantidad"],
                precio_unitario=Centavos(l["precio_unitario"]),
                subtotal=Centavos(l["subtotal"]),
            )
            for l in datos["lineas"]
        ),
        pie=PieDeComprobante(
            subtotal=Centavos(pie["subtotal"]),
            total=Centavos(pie["total"]),
            iva=Centavos(pie["iva"]),
            percepcion_iibb=Centavos(pie["percepcion_iibb"]),
            percepcion_iva=Centavos(pie["percepcion_iva"]),
            impuestos_internos=Centavos(pie["impuestos_internos"]),
            otros_descuentos=Centavos(pie["otros_descuentos"]),
            unidades=pie.get("unidades"),
        ),
    )


@pytest.fixture
def datos_p01() -> dict:
    return cargar("p01-2026-09-17")


@pytest.fixture
def p01(datos_p01: dict) -> Comprobante:
    """La factura A 0026-00183517 de P01, 17/09/2026. El primer papel del proyecto."""
    return armar(datos_p01)


def _hay_ocr() -> bool:
    """Hacen falta las dos cosas: el paquete de Python y el binario del sistema.

    Son independientes: `pip install pytesseract` no instala Tesseract, sólo lo llama.
    """
    import importlib.util
    import shutil

    return (
        importlib.util.find_spec("pytesseract") is not None
        and shutil.which("tesseract") is not None
    )


# T0 necesita el binario de Tesseract, que no viene con pip. Adentro de la imagen siempre
# está, así que `docker compose run --rm tests` -que es el comando del README y el que corre
# el CI- ejecuta todo. En una máquina sin Tesseract estos tests se saltean diciendo qué falta,
# en vez de reventar con un error que no explica nada.
necesita_ocr = pytest.mark.skipif(
    not _hay_ocr(),
    reason="falta pytesseract o el binario de tesseract; en Docker están los dos. "
    "En Debian/Ubuntu: pip install pytesseract && apt-get install tesseract-ocr tesseract-ocr-spa",
)
