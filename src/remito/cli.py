"""La demo. Se corre sin API keys, sin red y sin fotos.

`remito demo` toma la factura real del kiosco y unas cuantas versiones rotas de ella, las
pasa por la validación, y muestra cuál entra y cuál no con el motivo. Es lo que hay que
poder mostrar en dos minutos en una máquina limpia.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import sys
from datetime import date
from pathlib import Path

from .comprobante import Comprobante, Linea, PieDeComprobante
from .plata import Centavos, formatear
from .validacion import Chequeo, DesvioConocido, Gravedad, Veredicto, revisar

# Adentro del paquete, no en tests/. La factura de P01 es un dato que la demo necesita
# para correr, no material de prueba: si viviera en tests/, la imagen de Docker tendria
# que copiar la carpeta de tests para que el programa arranque.
DATOS = Path(__file__).parent / "datos"

# La consola de Windows sale en cp1252 y se come los acentos. Adentro de Docker no pasa,
# pero la demo tiene que verse bien en la máquina de cualquiera, no sólo en Linux.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

VERDE, ROJO, AMARILLO, GRIS, FIN = "\033[32m", "\033[31m", "\033[33m", "\033[90m", "\033[0m"

Caso = tuple[str, Comprobante, Veredicto, str]


def _color(texto: str, color: str) -> str:
    return texto if not sys.stdout.isatty() else f"{color}{texto}{FIN}"


def cargar_json(ruta: Path) -> Comprobante:
    datos = json.loads(ruta.read_text(encoding="utf-8"))
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
                l["codigo"], l["descripcion"], l["cantidad"],
                Centavos(l["precio_unitario"]), Centavos(l["subtotal"]),
            )
            for l in datos["lineas"]
        ),
        pie=PieDeComprobante(
            subtotal=Centavos(pie["subtotal"]),
            total=Centavos(pie["total"]),
            iva=Centavos(pie.get("iva", 0)),
            percepcion_iibb=Centavos(pie.get("percepcion_iibb", 0)),
            percepcion_iva=Centavos(pie.get("percepcion_iva", 0)),
            impuestos_internos=Centavos(pie.get("impuestos_internos", 0)),
            otros_descuentos=Centavos(pie.get("otros_descuentos", 0)),
            unidades=pie.get("unidades"),
        ),
    )


def imprimir(titulo: str, c: Comprobante, v: Veredicto, explicacion: str = "") -> None:
    print(f"\n{titulo}")
    if explicacion:
        print(_color(f"  {explicacion}", GRIS))
    print(
        _color(
            f"  {c.proveedor}  factura {c.tipo} {c.punto_venta}-{c.numero}  "
            f"{c.fecha:%d/%m/%Y}  {len(c.lineas)} líneas  total {formatear(c.pie.total)}",
            GRIS,
        )
    )
    if v.aprobado:
        print("  " + _color("APROBADO", VERDE) + "  entra al stock sin que nadie lo mire")
    else:
        print("  " + _color("A REVISIÓN", ROJO) + "  no entra: las cuentas no cierran")
    for d in v.descuadres:
        etiqueta = (
            _color("veto ", ROJO) if d.gravedad is Gravedad.VETO else _color("aviso", AMARILLO)
        )
        donde = f"{d.chequeo.value}" + (f" {d.linea}" if d.linea else "")
        print(f"    {etiqueta}  {donde:<10} {d.detalle}")


def armar_casos() -> list[Caso]:
    p01 = cargar_json(DATOS / "p01-2026-09-17.json")
    maña = DesvioConocido(
        proveedor="P01",
        chequeo=Chequeo.TOTAL,
        tolerancia_centavos=1,
        confirmado_por="Nicolás",
        fecha=date(2026, 9, 18),
        nota="redondea el total un centavo para abajo, siempre",
    )

    tapada = dataclasses.replace(p01, lineas=p01.lineas[:-1])

    regalo = Linea("9999", "PROMO SIN CARGO", 2, Centavos(0), Centavos(0))
    con_regalo = dataclasses.replace(
        p01, lineas=p01.lineas + (regalo,), pie=dataclasses.replace(p01.pie, unidades=28)
    )
    sin_el_regalo = dataclasses.replace(con_regalo, lineas=con_regalo.lineas[:-1])

    coma = dataclasses.replace(
        p01.lineas[0], precio_unitario=Centavos(7376100), subtotal=Centavos(36880500)
    )
    ocr = dataclasses.replace(p01, lineas=(coma,) + p01.lineas[1:])

    return [
        (
            "La factura como vino",
            p01,
            revisar(p01),
            "El TOTAL impreso no cierra con sus propias partes por un centavo. Es legítima\n"
            "  igual: tiene CAE. Un validador ingenuo la rechaza y manda a revisión el 100%\n"
            "  de los comprobantes de este proveedor, para siempre.",
        ),
        (
            "La misma, una vez que confirmaste que ese centavo es normal acá",
            p01,
            revisar(p01, (maña,)),
            "El desvío queda anotado con quién lo confirmó y cuándo. No vuelve a molestarte,\n"
            "  y sigue siendo un error en cualquier otro proveedor.",
        ),
        (
            "La segunda hoja tapó la última línea al sacar la foto",
            tapada,
            revisar(tapada, (maña,)),
            "Dos chequeos independientes la agarran: la plata y el conteo de unidades.",
        ),
        (
            "Lo tapado era mercadería sin cargo: no mueve un peso",
            sin_el_regalo,
            revisar(sin_el_regalo, (maña,)),
            "Acá la plata cierra perfecto y el chequeo del subtotal no ve nada. Por eso el\n"
            "  conteo de unidades es un veto aparte y no un adorno.",
        ),
        (
            "Al leer la foto se perdió una coma: 737,61 entró como 73.761",
            ocr,
            revisar(ocr, (maña,)),
            "Cien veces más caro. Ningún parser puede distinguirlo mirando el texto:\n"
            "  $ 73761 es un importe perfectamente válido.",
        ),
    ]


def demo() -> int:
    # Los casos se arman primero y recién después se cuentan. Escribir "cuatro formas de
    # romperla" a mano en el encabezado es la manera más barata de que el texto y el código
    # terminen diciendo cosas distintas: ya pasó tres veces en este repo. Regla R10.
    casos = armar_casos()
    rechazados = sum(1 for _, _, v, _ in casos if not v.aprobado)

    print(
        f"\nUna factura de verdad de un kiosco de San Clemente, y {rechazados} formas de "
        f"romperla.\nNada de esto usa internet, ni una API key, ni un modelo. "
        "Son las cuentas solas."
    )
    for i, (titulo, c, v, explicacion) in enumerate(casos, 1):
        imprimir(f"{i}. {titulo}", c, v, explicacion)

    print(
        "\n"
        + _color(
            "Lo que esto NO puede atrapar está en LIMITES.md, y va primero en esa lista:\n"
            "si la foto se comió el TOTAL y el modelo lo inventa sumando las líneas, ese\n"
            f"número cierra contra el subtotal y pasa los {len(Chequeo)} chequeos. "
            "La aritmética no lo ve.\n",
            GRIS,
        )
    )
    return 0


def revisar_archivo(ruta: Path) -> int:
    c = cargar_json(ruta)
    v = revisar(c)
    imprimir(ruta.name, c, v)
    return 0 if v.aprobado else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="remito", description="Comprobantes de compra de kiosco: las cuentas que vetan."
    )
    sub = parser.add_subparsers(dest="comando", required=True)
    sub.add_parser("demo", help="la factura real del kiosco y unas cuantas formas de romperla")
    rev = sub.add_parser("revisar", help="validar un comprobante en JSON")
    rev.add_argument("archivo", type=Path)

    args = parser.parse_args(argv)
    if args.comando == "demo":
        return demo()
    return revisar_archivo(args.archivo)


if __name__ == "__main__":
    raise SystemExit(main())
