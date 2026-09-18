"""Los doce documentos rotos a propósito.

Requisito 1 de `PLAN.md`: los nueve evaluadores pusieron primero que el repositorio
arranque con datos sembrados y documentos rotos.

Cada rotura tiene tres piezas, y la del medio es la que hace que esto sirva:

- **la verdad**: lo que dice el papel. Siempre completa y consistente.
- **la lectura**: lo que un lector ingenuo produciría con la entrada rota. Es lo que
  después pasa por la validación. Sin esta pieza no se puede probar nada: el papel de una
  foto movida está perfecto, la que está mal es la lectura.
- **la imagen**, cuando la rotura es de la foto y no de los números.

Y una clasificación: **quién la agarra**.

- `ARITMETICA` — la lectura no cierra. Los vetos la frenan. Son la tesis del proyecto.
- `EL_EXTRACTOR` — la lectura es internamente consistente **y está mal**. Cierra contra sí
  misma y pasa los cuatro chequeos. La única defensa es que el que lee conteste "no sé".
- `NINGUNA` — no hay nada que revisar, porque lo que se perdió nunca llegó a leerse.

Esa clasificación es la medida honesta de hasta dónde llega validar con aritmética, y hay
tests que la verifican rotura por rotura en vez de creerle a la etiqueta.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from enum import Enum
from typing import Callable

from PIL import Image, ImageFilter

from .comprobante import Comprobante, Linea, PieDeComprobante
from .plata import Centavos, iva, redondear
from .sintetico import caso_sin_senal, degradar, dibujar, generar
from .validacion import Chequeo


class Defensa(str, Enum):
    ARITMETICA = "la agarran los vetos"
    EL_EXTRACTOR = "el que lee la foto tiene que decir 'no sé'"
    NINGUNA = "sin defensa hoy"


@dataclass(frozen=True)
class Caso:
    verdad: Comprobante
    lectura: Comprobante | None
    """Lo que un lector ingenuo produciría. None cuando no hay nada legible."""
    imagen: Image.Image | None = None


@dataclass(frozen=True)
class Rotura:
    nombre: str
    que_paso: str
    """Lo que pasó en el mostrador, no en el código."""
    defensa: Defensa
    chequeo: Chequeo | None
    armar: Callable[[], Caso]


def _base(semilla: int = 20, lineas: int = 6) -> Comprobante:
    return generar(semilla, proveedor="P99", cantidad_lineas=lineas)


def _pie_inventado(lineas: tuple[Linea, ...]) -> PieDeComprobante:
    """El pie que armaría quien no lo vio: sumando lo que sí vio.

    Sale consistente por construcción. Ése es exactamente el problema.
    """
    subtotal = Centavos(sum(l.subtotal for l in lineas))
    impuesto = iva(subtotal)
    iibb = Centavos(redondear(subtotal * 16, 1000))  # percepción de IIBB al 1,6%
    return PieDeComprobante(
        subtotal=subtotal, iva=impuesto, percepcion_iibb=iibb,
        total=Centavos(subtotal + impuesto + iibb),
        unidades=sum(l.cantidad for l in lineas),
    )


# --- la lectura no cierra: las agarra la aritmética ------------------------------------


def _coma_comida() -> Caso:
    c = _base()
    l = c.lineas[0]
    rota = dataclasses.replace(
        l, precio_unitario=Centavos(l.precio_unitario * 100),
        subtotal=Centavos(l.subtotal * 100),
    )
    return Caso(c, dataclasses.replace(c, lineas=(rota,) + c.lineas[1:]))


def _digito_cambiado() -> Caso:
    c = _base()
    l = c.lineas[2]
    rota = dataclasses.replace(l, subtotal=Centavos(l.subtotal + 50_000))
    return Caso(c, dataclasses.replace(c, lineas=c.lineas[:2] + (rota,) + c.lineas[3:]))


def _linea_leida_dos_veces() -> Caso:
    c = _base()
    return Caso(c, dataclasses.replace(c, lineas=c.lineas + (c.lineas[1],)))


def _cantidad_mal() -> Caso:
    """La plata cierra igual: sólo falla el conteo. Es la rotura que justifica que el veto
    de unidades exista aparte del de la plata."""
    c = _base()
    l = c.lineas[0]
    rota = dataclasses.replace(l, cantidad=l.cantidad + 1)
    return Caso(c, dataclasses.replace(c, lineas=(rota,) + c.lineas[1:]))


def _bonificacion_perdida() -> Caso:
    """Una línea sin cargo no mueve un peso: el veto de la plata no la ve, el de unidades sí."""
    c = _base()
    regalo = Linea("9999", "PROMO SIN CARGO", 3, Centavos(0), Centavos(0))
    verdad = dataclasses.replace(
        c, lineas=c.lineas + (regalo,),
        pie=dataclasses.replace(c.pie, unidades=(c.pie.unidades or 0) + 3),
    )
    return Caso(verdad, dataclasses.replace(verdad, lineas=verdad.lineas[:-1]))


def _linea_tapada() -> Caso:
    """La segunda hoja apoyada encima tapó el último renglón.

    La rotura es de la foto, pero la lectura que produce sí es aritméticamente detectable:
    faltan una línea de plata y sus unidades, y el pie —que se ve— las reclama.
    """
    c = _base(21)
    return Caso(c, dataclasses.replace(c, lineas=c.lineas[:-1]),
                degradar(dibujar(c), 21, hoja_superpuesta=True))


# --- la lectura cierra y está mal: la aritmética no puede verla ------------------------


def _total_recortado() -> Caso:
    """El encuadre se comió la tira de totales y los dos últimos renglones.

    Quien lee arma el pie sumando lo que vio. Le da consistente, porque lo calculó de ahí.
    Pasa los cuatro chequeos y entra a la base sin las dos líneas que nunca se vieron.
    Es el límite 1 de `LIMITES.md`, y es el que contradice la tesis del proyecto.
    """
    c = _base(22)
    vistas = c.lineas[:-2]
    return Caso(c, Comprobante(
        proveedor=c.proveedor, tipo=c.tipo, punto_venta=c.punto_venta, numero=c.numero,
        fecha=c.fecha, lineas=vistas, pie=_pie_inventado(vistas),
        remito_numero=c.remito_numero, hoja=c.hoja,
    ), degradar(dibujar(c), 22, recortar_pie=True))


def _falta_la_segunda_hoja() -> Caso:
    """El papel dice "Hoja 1/2" y hay una sola foto.

    La mitad que se ve cierra consigo misma si el pie se arma con ella. Lo único que
    delata que falta media factura es el campo `Hoja`, y leerlo es trabajo del extractor:
    ninguna suma lo puede deducir.
    """
    c = dataclasses.replace(_base(25, lineas=10), hoja="1/2")
    primera = c.lineas[:5]
    return Caso(c, Comprobante(
        proveedor=c.proveedor, tipo=c.tipo, punto_venta=c.punto_venta, numero=c.numero,
        fecha=c.fecha, lineas=primera, pie=_pie_inventado(primera),
        remito_numero=c.remito_numero, hoja="1/2",
    ), degradar(dibujar(c), 25))


def _foto_movida() -> Caso:
    """Sacada con una mano mientras la otra sostenía el papel. No se lee nada."""
    c = _base(23)
    return Caso(c, None, degradar(dibujar(c), 23).filter(ImageFilter.GaussianBlur(9)))


def _no_es_un_comprobante() -> Caso:
    """Una foto cualquiera. Hay que decir que no es un comprobante, no extraer campos igual."""
    return Caso(_base(24), None, caso_sin_senal())


def _papel_arrugado() -> Caso:
    """El renglón cayó sobre un pliegue y se leyeron dos dígitos de más en la cantidad.

    Quien lee ajusta el subtotal a la cantidad que creyó ver, porque multiplicar es lo
    obvio. Le cierra todo, y cargó doce cajas donde había dos.
    """
    c = _base(28)
    l = c.lineas[1]
    rota = dataclasses.replace(
        l, cantidad=l.cantidad + 10,
        subtotal=Centavos(l.precio_unitario * (l.cantidad + 10)),
    )
    leidas = (c.lineas[0], rota) + c.lineas[2:]
    return Caso(c, Comprobante(
        proveedor=c.proveedor, tipo=c.tipo, punto_venta=c.punto_venta, numero=c.numero,
        fecha=c.fecha, lineas=leidas, pie=_pie_inventado(leidas),
        remito_numero=c.remito_numero, hoja=c.hoja,
    ), degradar(dibujar(c), 28))


# --- lo que nunca se leyó: sin defensa ------------------------------------------------


def _dos_papeles_en_la_misma_foto() -> Caso:
    """Dos facturas distintas apoyadas una al lado de la otra.

    Quien lee agarra la de la izquierda entera y la de la derecha no existe. Lo que
    devuelve está impecable y entra bien. La mercadería de la otra factura nunca se cargó,
    y no hay chequeo posible sobre un documento que nadie leyó: no hay con qué compararlo.

    La defensa no es aritmética ni del extractor. Es contar los papeles antes de sacar la
    foto, que es una regla de mostrador y está en `LIMITES.md`.
    """
    izquierda, derecha = _base(26), _base(27)
    a, b = dibujar(izquierda), dibujar(derecha)
    lienzo = Image.new("RGB", (a.width + b.width, max(a.height, b.height)), (250, 250, 245))
    lienzo.paste(a, (0, 0))
    lienzo.paste(b, (a.width, 0))
    return Caso(izquierda, izquierda, degradar(lienzo, 26))


LAS_DOCE: tuple[Rotura, ...] = (
    Rotura("coma_comida", "el OCR se comió la coma decimal y el precio quedó cien veces más caro",
           Defensa.ARITMETICA, Chequeo.SUBTOTAL, _coma_comida),
    Rotura("digito_cambiado", "un 8 leído como 3 en el subtotal de un renglón",
           Defensa.ARITMETICA, Chequeo.SUBTOTAL, _digito_cambiado),
    Rotura("linea_leida_dos_veces", "el renglón quedó sobre el doblez del papel y se extrajo dos veces",
           Defensa.ARITMETICA, Chequeo.SUBTOTAL, _linea_leida_dos_veces),
    Rotura("cantidad_mal", "la columna de unidades dice 5 y se leyó 6: la plata cierra igual",
           Defensa.ARITMETICA, Chequeo.UNIDADES, _cantidad_mal),
    Rotura("bonificacion_perdida", "se perdió un renglón sin cargo, que no mueve un peso",
           Defensa.ARITMETICA, Chequeo.UNIDADES, _bonificacion_perdida),
    Rotura("linea_tapada", "la segunda hoja apoyada encima tapó el último renglón",
           Defensa.ARITMETICA, Chequeo.SUBTOTAL, _linea_tapada),
    Rotura("total_recortado", "el encuadre se comió la tira de totales y los dos últimos renglones",
           Defensa.EL_EXTRACTOR, None, _total_recortado),
    Rotura("falta_la_segunda_hoja", "el papel dice Hoja 1/2 y hay una sola foto",
           Defensa.EL_EXTRACTOR, None, _falta_la_segunda_hoja),
    Rotura("papel_arrugado", "el renglón cayó sobre un pliegue y la cantidad se leyó de más",
           Defensa.EL_EXTRACTOR, None, _papel_arrugado),
    Rotura("foto_movida", "salió movida y no se lee un solo número",
           Defensa.EL_EXTRACTOR, None, _foto_movida),
    Rotura("no_es_un_comprobante", "la foto no es un comprobante: se coló otra cosa",
           Defensa.EL_EXTRACTOR, None, _no_es_un_comprobante),
    Rotura("dos_papeles_en_la_misma_foto", "dos facturas distintas apoyadas una al lado de la otra",
           Defensa.NINGUNA, None, _dos_papeles_en_la_misma_foto),
)


def por_defensa(defensa: Defensa) -> tuple[Rotura, ...]:
    return tuple(r for r in LAS_DOCE if r.defensa is defensa)
