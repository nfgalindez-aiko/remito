"""Comprobantes inventados con la respuesta conocida.

Para qué: antes de medir un papel real hay que saber que el medidor mide. Se genera un
comprobante cuyos números decidimos nosotros, se lo degrada hasta que parezca una foto de
celular, y se comprueba que lo que sale del otro lado es lo que pusimos. Si no lo recupera,
no se mide nada real hasta arreglarlo. CRITERIOS.md sección 7.

La aritmética imita la del proveedor de verdad: el precio unitario se calcula con cuatro
decimales y se imprime con dos, así que `precio_impreso × cantidad` no siempre da el
subtotal impreso. Un generador que hiciera las cuentas "bien" produciría comprobantes más
limpios que los reales y certificaría un medidor que después falla con el primer papel.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import date, timedelta

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

from .comprobante import Comprobante, Linea, PieDeComprobante
from .plata import Centavos, formatear, iva, redondear

# Decimilésimas de peso: 10.000 = $1. Es la resolución con la que el proveedor liquida
# antes de imprimir dos decimales.
DIEZMILESIMAS = 10_000

PRODUCTOS = [
    ("1825", "JORGITO BIZCOCHO X 200 GS"),
    ("15004", "KOKIS MEMBRILLITO 500 G"),
    ("3398", "MINI RHODESIA 60 GS"),
    ("2920", "PEPITOS 119 G"),
    ("1661", "CEREALITAS 212 G"),
    ("4410", "CRIOLLITAS 100 G"),
    ("7702", "OPERA X 6"),
    ("5531", "MANA FRUTILLA 200 G"),
    ("9120", "TITA X 12"),
    ("6640", "RHODESIA X 18"),
    ("2201", "CHOCOLINAS 170 G"),
    ("8815", "MELLIZAS X 24"),
    ("3307", "SONRISAS FRUTILLA 118 G"),
    ("1140", "MERENGADAS 118 G"),
    ("7033", "AGUILA LECHE 70 G"),
]


@dataclass(frozen=True)
class Sintetico:
    """El comprobante y la imagen, con la verdad adentro del comprobante."""

    comprobante: Comprobante
    imagen: Image.Image


def generar(
    semilla: int,
    *,
    proveedor: str = "P99",
    cantidad_lineas: int | None = None,
    maña_total_centavos: int = 0,
) -> Comprobante:
    """Un comprobante coherente cuyos números conocemos.

    `maña_total_centavos` desplaza el TOTAL impreso respecto de sus componentes, para
    reproducir lo que hace P01. Con 0 el comprobante cierra perfecto.
    """
    rnd = random.Random(semilla)
    n = cantidad_lineas if cantidad_lineas is not None else rnd.randint(3, 12)

    lineas = []
    for codigo, descripcion in rnd.sample(PRODUCTOS, min(n, len(PRODUCTOS))):
        cantidad = rnd.choice([1, 2, 3, 3, 5, 5, 6, 10, 12])
        precio_real = rnd.randint(300 * DIEZMILESIMAS, 4_000 * DIEZMILESIMAS)
        lineas.append(
            Linea(
                codigo=codigo,
                descripcion=descripcion,
                cantidad=cantidad,
                precio_unitario=Centavos(redondear(precio_real, 100)),
                subtotal=Centavos(redondear(precio_real * cantidad, 100)),
            )
        )

    subtotal = Centavos(sum(l.subtotal for l in lineas))
    iibb = Centavos(redondear(subtotal * 16, 1000))  # percepción de IIBB al 1,6%
    impuesto = iva(subtotal)
    pie = PieDeComprobante(
        subtotal=subtotal,
        iva=impuesto,
        percepcion_iibb=iibb,
        total=Centavos(subtotal + impuesto + iibb - maña_total_centavos),
        unidades=sum(l.cantidad for l in lineas),
    )

    return Comprobante(
        proveedor=proveedor,
        tipo="A",
        punto_venta=f"{rnd.randint(1, 99):04d}",
        numero=f"{rnd.randint(1, 999_999):08d}",
        fecha=date(2026, 1, 1) + timedelta(days=rnd.randint(0, 260)),
        lineas=tuple(lineas),
        pie=pie,
        remito_numero=str(rnd.randint(100_000, 199_999)),
        hoja="1/1",
    )


# --- dibujo ---------------------------------------------------------------------------

ANCHO, MARGEN, ALTO_FILA = 1100, 50, 34
PAPEL, TINTA = (252, 251, 246), (28, 28, 30)


def _fuente(tam: int, negrita: bool = False) -> ImageFont.FreeTypeFont:
    # La que trae Pillow adentro. Nada de fuentes del sistema: esto corre en Docker.
    return ImageFont.load_default(size=tam)


def dibujar(c: Comprobante) -> Image.Image:
    alto = 300 + ALTO_FILA * len(c.lineas) + 170
    img = Image.new("RGB", (ANCHO, alto), PAPEL)
    d = ImageDraw.Draw(img)
    chico, normal, grande = _fuente(19), _fuente(22), _fuente(34)
    x2 = ANCHO - MARGEN

    d.rectangle([MARGEN, 40, x2, alto - 40], outline=TINTA, width=2)
    d.text((MARGEN + 20, 62), f"DISTRIBUIDORA {c.proveedor} S.R.L.", TINTA, grande)
    d.text((MARGEN + 20, 106), "BUENOS AIRES - Partido de La Costa", TINTA, chico)
    d.text((MARGEN + 20, 130), "IVA: Responsable Inscripto", TINTA, chico)

    d.rectangle([620, 58, 660, 104], outline=TINTA, width=2)
    d.text((630, 66), c.tipo, TINTA, grande)
    d.text((690, 58), "FACTURA", TINTA, grande)
    d.text((690, 98), f"{c.punto_venta}-{c.numero}", TINTA, normal)
    d.text((690, 126), f"Fecha: {c.fecha.strftime('%d/%m/%Y')}", TINTA, chico)
    d.text((x2 - 150, 58), f"Hoja {c.hoja}", TINTA, chico)

    d.line([MARGEN, 168, x2, 168], TINTA, 2)
    d.text((MARGEN + 20, 180), "Sres:  CLIENTE DE PRUEBA", TINTA, normal)
    d.text((690, 180), f"Remito N {c.remito_numero}", TINTA, normal)
    d.line([MARGEN, 216, x2, 216], TINTA, 2)

    # Las tres columnas de números van alineadas a la derecha, como en el papel de verdad.
    # Alineadas a la izquierda, un subtotal de seis cifras se sale del recuadro y queda
    # cortado: la imagen dejaría de mostrar la verdad que el fixture dice que tiene, y el
    # extractor fallaría por culpa del generador.
    izq = [MARGEN + 20, MARGEN + 140]
    der = [x2 - 460, x2 - 250, x2 - 20]
    for x, t in zip(izq, ["CODIGO", "DESCRIPCION"]):
        d.text((x, 228), t, TINTA, chico)
    for x, t in zip(der, ["UNID.", "PRECIO", "SUBTOTAL"]):
        d.text((x, 228), t, TINTA, chico, anchor="ra")
    d.line([MARGEN, 258, x2, 258], TINTA, 2)

    y = 272
    for l in c.lineas:
        d.text((izq[0], y), l.codigo, TINTA, normal)
        d.text((izq[1], y), l.descripcion, TINTA, normal)
        d.text((der[0], y), str(l.cantidad), TINTA, normal, anchor="ra")
        d.text((der[1], y), f"$ {formatear(l.precio_unitario)}", TINTA, normal, anchor="ra")
        d.text((der[2], y), f"$ {formatear(l.subtotal)}", TINTA, normal, anchor="ra")
        d.line([MARGEN + 10, y + 27, x2 - 10, y + 27], (185, 185, 180), 1)
        y += ALTO_FILA

    y += 24
    d.text((MARGEN + 20, y), f"Unidades: {c.pie.unidades}", TINTA, normal)
    d.text((500, y), "**Reclamos validos dentro de las 24hs**", TINTA, chico)
    y += 44
    d.line([MARGEN, y, x2, y], TINTA, 2)
    y += 12

    pie = [
        ("SUB-TOTAL", c.pie.subtotal),
        ("PERC. IIBB", c.pie.percepcion_iibb),
        ("IMPU. INT.", c.pie.impuestos_internos),
    ]
    for i, (rotulo, valor) in enumerate(pie):
        x = MARGEN + 20 + i * 200
        d.text((x, y), rotulo, TINTA, chico)
        d.text((x, y + 26), f"$ {formatear(valor)}", TINTA, normal)

    # El IVA con punto decimal y sin separador de miles, como lo imprime P01.
    # Dos formatos de número en la misma hoja: si el generador lo limpiara, el medidor
    # nunca se enfrentaría al caso que sí existe en el papel de verdad.
    d.text((MARGEN + 620, y), "IVA 21%", TINTA, chico)
    d.text((MARGEN + 620, y + 26), f"{c.pie.iva // 100}.{c.pie.iva % 100:02d}", TINTA, normal)

    d.text((x2 - 20, y), "TOTAL", TINTA, normal, anchor="ra")
    d.text((x2 - 20, y + 26), f"$ {formatear(c.pie.total)}", TINTA, grande, anchor="ra")
    return img


# --- degradación ----------------------------------------------------------------------


def degradar(
    img: Image.Image,
    semilla: int,
    *,
    hoja_superpuesta: bool = False,
    recortar_pie: bool = False,
) -> Image.Image:
    """Lo que le pasa al papel entre el mostrador y la foto."""
    rnd = random.Random(semilla)

    if hoja_superpuesta:
        # La segunda hoja apoyada encima, tapando parte de la tabla de líneas. Es el modo
        # de falla que motivó el proyecto: la foto no muestra todo lo que el papel dice.
        tapa = Image.new("RGB", (img.width, img.height // 4), (238, 236, 228))
        ImageDraw.Draw(tapa).line([0, 0, tapa.width, 0], (120, 120, 115), 3)
        img = img.copy()
        img.paste(tapa, (0, int(img.height * 0.45)))

    if recortar_pie:
        # El encuadre se comió la tira de totales. El sistema tiene que decir "no está",
        # no inventar un total que cierre con las líneas.
        img = img.crop((0, 0, img.width, int(img.height * 0.72)))

    fondo = Image.new("RGB", (img.width + 160, img.height + 160), (150, 40, 38))
    fondo.paste(img, (80, 80))
    img = fondo.rotate(rnd.uniform(-4.5, 4.5), expand=True, fillcolor=(150, 40, 38))

    # Sombra: un degradado suave de un lado, como la luz de una cocina a las nueve.
    sombra = Image.linear_gradient("L").resize(img.size).rotate(rnd.choice([0, 90, 270]))
    img = Image.composite(img, ImageEnhance.Brightness(img).enhance(0.55), sombra)

    img = img.filter(ImageFilter.GaussianBlur(rnd.uniform(0.4, 1.1)))
    return ImageEnhance.Contrast(img).enhance(rnd.uniform(0.85, 1.05))


# --- los casos de certificación, CRITERIOS.md sección 7 -------------------------------


def caso_con_senal(semilla: int = 1) -> Sintetico:
    """Difícil de leer, pero todo está a la vista. La respuesta correcta es recuperarlo entero.

    Va sin hoja superpuesta a propósito. Un caso "con señal" cuya verdad no esté en la
    imagen no certifica nada: el extractor fallaría por algo que no es culpa suya, y ese
    fracaso se leería como que el instrumento no sirve. Tapar líneas es el caso de abajo.
    """
    c = generar(semilla)
    return Sintetico(c, degradar(dibujar(c), semilla))


def caso_linea_tapada(semilla: int = 4) -> Sintetico:
    """La segunda hoja apoyada encima tapa parte de la tabla. Es la foto que mandó Nicolás.

    Acá la respuesta correcta NO es extraer bien: es no aprobar. Los totales del pie sí se
    ven, así que la suma de las líneas visibles no va a dar el SUB-TOTAL impreso ni las
    unidades del pie, y los dos vetos lo mandan a revisión humana. Este caso mide si el
    sistema se da cuenta de lo que no vio.
    """
    c = generar(semilla)
    return Sintetico(c, degradar(dibujar(c), semilla, hoja_superpuesta=True))


def caso_sin_senal(semilla: int = 2) -> Image.Image:
    """No es un comprobante. El sistema tiene que decir que no lo es, no extraer campos."""
    rnd = random.Random(semilla)
    img = Image.new("RGB", (900, 700), (150, 40, 38))
    d = ImageDraw.Draw(img)
    for _ in range(40):
        x, y = rnd.randint(0, 880), rnd.randint(0, 680)
        d.ellipse([x, y, x + rnd.randint(10, 90), y + rnd.randint(10, 90)],
                  fill=tuple(rnd.randint(30, 220) for _ in range(3)))
    return img.filter(ImageFilter.GaussianBlur(1.2))


def caso_fuga(semilla: int = 3) -> Sintetico:
    """El TOTAL quedó fuera del encuadre.

    Es el caso más importante de los tres. Un modelo que inventa un total plausible
    produce un número que después cierra contra las líneas y pasa la validación: el error
    entra a la base sin dejar rastro. Tiene que contestar "no está".
    """
    c = generar(semilla)
    return Sintetico(c, degradar(dibujar(c), semilla, recortar_pie=True))
