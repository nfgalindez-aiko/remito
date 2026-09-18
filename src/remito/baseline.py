"""T0: leer el comprobante sin modelo. OCR y reglas escritas a mano.

Éste es el baseline que decide si el modelo se gana el lugar. `CRITERIOS.md` §2 lo fijó
antes de escribir una línea: si el modelo no le gana a esto por más de 25 puntos, no
justifica la latencia, el gasto ni la no-determinación, y el proyecto honesto pasa a ser un
parser determinista con el modelo como respaldo.

Casi ningún repositorio de extracción se molesta en construir su baseline trivial, y es
justamente el que convierte "el modelo anda" en "el modelo aporta".

ADVERTENCIA SOBRE LO QUE SE PUEDE MEDIR ACÁ, Y ES IMPORTANTE

Este parser se escribió mirando los comprobantes que genera `sintetico.py`. Medirlo contra
esos mismos comprobantes no dice cuán bueno es: dice que funciona mecánicamente. Es la
misma fuga que ajustar un modelo y evaluarlo con los datos de entrenamiento, con otro
disfraz.

El número de T0 que vale sale de las fotos reales del kiosco, sobre el bloque de
entrenamiento, y todavía no existe. Los tests de este módulo comprueban que anda, no que
sea bueno, y están escritos con esas palabras.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date

import pytesseract
from PIL import Image
from pytesseract import Output

from .comprobante import Comprobante, Linea, PieDeComprobante
from .plata import Centavos, ImporteInvalido, parse_importe

# Rango de búsqueda del enderezado, en grados, y el paso.
# El generador tuerce entre -4,5 y +4,5; ±7 lo cubre con margen. Las fotos reales del
# mostrador pueden venir más torcidas y esto va a quedar corto: cuando existan, se mide y
# se corrige acá, no se sube "por las dudas". Cada grado de rango cuesta tiempo.
TOPE_GRADOS, PASO_GRADOS = 7.0, 0.5

# Cuánto de la altura de una letra se tolera para decir que dos palabras están en la misma
# fila. Es una fracción y no un número de píxeles: la primera versión usaba 14 px fijos,
# sacados de que el generador dibuja filas de 34 px, y sobre una foto real de 2576x1932
# partía cada renglón en pedazos. Leía 235 palabras con confianza mediana 91 y armaba cero
# líneas. Un número atado al tamaño de una imagen no es una constante, es una casualidad.
FRACCION_DE_ALTURA = 0.7

# T0 no intenta leer la fecha. Esta explicita para que nadie la confunda con una leida.
SIN_FECHA = date(1970, 1, 1)

_MONEDA = re.compile(r"^\$?\s*\d[\d.]*[.,]\d{1,2}$")
_CODIGO = re.compile(r"^\d{2,6}$")
_ENTERO = re.compile(r"^\d{1,4}$")


@dataclass(frozen=True)
class Palabra:
    texto: str
    x: int
    y: int
    alto: int
    confianza: int


def _varianza_del_perfil(img: Image.Image, angulo: float) -> float:
    """Cuánto se concentra la tinta en pocas alturas al rotar la imagen ese ángulo.

    Con el texto derecho, cada renglón tapa una franja y entre renglones no hay nada: el
    perfil horizontal tiene picos y valles, y su varianza es alta. Torcido, la tinta se
    reparte y la varianza baja. El máximo de la varianza es el ángulo que endereza.

    Se hace así y no con OpenCV a propósito: OpenCV pesa más que todo el resto del
    proyecto junto y esto son veinte líneas de aritmética.
    """
    g = img.convert("L").rotate(angulo, resample=Image.BILINEAR, fillcolor=255)
    # A un cuarto de tamaño alcanza para ver dónde están los renglones y cuesta la
    # dieciseisava parte. Medido: sin reducir, enderezar tarda cerca de 30 s.
    g = g.resize((max(1, g.width // 4), max(1, g.height // 4)))
    px = g.load()
    filas = [sum(1 for x in range(g.width) if px[x, y] < 128) for y in range(g.height)]
    media = sum(filas) / len(filas)
    return sum((f - media) ** 2 for f in filas) / len(filas)


def enderezar(img: Image.Image) -> tuple[Image.Image, float]:
    """Devuelve la imagen derecha y el ángulo que hizo falta.

    Sin esto no hay nada que hacer. Medido sobre un comprobante torcido 3 grados: sin
    enderezar, el OCR pone el código de una línea a 50 píxeles de su propio subtotal y
    agrupar por altura junta la cantidad de una fila con el precio de la de abajo. Las
    cinco líneas salen mal. Enderezado, salen las cinco bien.

    Cuesta 1,9 s por imagen en esta máquina, medido el 18/09/2026. Es el paso más caro de
    T0 y sigue siendo veinte veces más barato que una llamada a un modelo.
    """
    mejor_angulo, mejor_varianza = 0.0, -1.0
    angulo = -TOPE_GRADOS
    while angulo <= TOPE_GRADOS + 1e-9:
        v = _varianza_del_perfil(img, angulo)
        if v > mejor_varianza:
            mejor_angulo, mejor_varianza = angulo, v
        angulo += PASO_GRADOS
    if mejor_angulo == 0.0:
        return img, 0.0
    return (
        img.rotate(mejor_angulo, resample=Image.BICUBIC, fillcolor=(255, 255, 255), expand=True),
        mejor_angulo,
    )


def palabras_de(img: Image.Image) -> list[Palabra]:
    d = pytesseract.image_to_data(
        img, lang="spa", config="--psm 6", output_type=Output.DICT
    )
    return [
        Palabra(
            d["text"][i].strip(), d["left"][i], d["top"][i], d["height"][i],
            int(d["conf"][i]),
        )
        for i in range(len(d["text"]))
        if d["text"][i].strip()
    ]


def tolerancia_de_fila(palabras: list[Palabra]) -> float:
    """La altura típica de una letra en ESTA imagen, no en la que usamos para probar."""
    altos = sorted(p.alto for p in palabras)
    return (altos[len(altos) // 2] if altos else 20) * FRACCION_DE_ALTURA


def _filas(palabras: list[Palabra]) -> list[list[Palabra]]:
    tolerancia = tolerancia_de_fila(palabras)
    filas: list[list[Palabra]] = []
    for p in sorted(palabras, key=lambda p: (p.y, p.x)):
        if filas and abs(filas[-1][0].y - p.y) <= tolerancia:
            filas[-1].append(p)
        else:
            filas.append([p])
    return [sorted(f, key=lambda p: p.x) for f in filas]


def _importe(texto: str) -> Centavos | None:
    if not _MONEDA.match(texto):
        return None
    try:
        return parse_importe(texto)
    except ImporteInvalido:
        return None


def _linea_de(fila: list[Palabra]) -> Linea | None:
    """Una fila de la tabla, leída sin saber dónde están las columnas.

    Se probó primero detectar los bordes de columna con la fila de encabezados. Se
    descartó: el encabezado de un proveedor distinto dice otra cosa, o no se lee, y
    entonces no se lee ninguna línea. Esta versión sólo usa el orden de izquierda a
    derecha, que es el único invariante entre proveedores: primero el código, al final la
    plata, y la cantidad entre la descripción y el primer importe.
    """
    textos = [p.texto for p in fila]
    if not textos or not _CODIGO.match(textos[0]):
        return None

    importes = [(i, c) for i, t in enumerate(textos) if (c := _importe(t)) is not None]
    if len(importes) < 2:
        return None
    (i_precio, precio), (i_subtotal, subtotal) = importes[-2], importes[-1]

    # La cantidad es el último entero suelto antes del precio. "Suelto" quiere decir que
    # no es parte de la descripción: va después de las palabras y antes de la plata.
    cantidades = [
        int(t) for t in textos[1:i_precio]
        if _ENTERO.match(t) and not any(ch.isalpha() for ch in t)
    ]
    if not cantidades:
        return None

    descripcion = " ".join(
        t for t in textos[1:i_precio] if any(ch.isalpha() for ch in t)
    ).strip()
    if not descripcion:
        return None

    try:
        return Linea(textos[0], descripcion, cantidades[-1], precio, subtotal)
    except ValueError:
        return None


def _pie_de(palabras: list[Palabra]) -> list[Palabra]:
    """Sólo lo que está de la tira de totales para abajo.

    Existe porque buscar rótulos en toda la hoja agarra la ocurrencia equivocada, y
    equivocarse acá no se nota: devuelve un número plausible. Dos casos reales, los dos
    medidos el 18/09/2026 sobre comprobantes sintéticos:

    - "IVA" aparece arriba de todo, en "IVA: Responsable Inscripto". Buscar el valor
      debajo de ese rótulo no encuentra nada y el IVA quedaba en cero, siempre.
    - El encabezado de la tabla dice "SUBTOTAL", así que el subtotal del pie competía con
      un rótulo de columna que está a media hoja de distancia.
    """
    anclas = [p.y for p in palabras if "SUB-TOTAL" in p.texto.upper().replace(" ", "")]
    if not anclas:
        anclas = [p.y for p in palabras if "UNIDADES" in p.texto.upper()]
    return [p for p in palabras if p.y >= max(anclas) - 10] if anclas else palabras


def _valor_debajo(
    palabras: list[Palabra], etiqueta: str, *, exacto: bool = False, ventana_x: int = 90
) -> Centavos | None:
    """El número que está debajo de un rótulo del pie.

    La tira de totales pone los rótulos en un renglón y los valores en el siguiente, así
    que leer por renglones los mezcla: el OCR devuelve `$ » 386) $0 $ 76.329,81` de un
    tirón. Por coordenadas sale limpio.

    `exacto` existe por "TOTAL", que es subcadena de "SUB-TOTAL". Sin eso el total del
    comprobante leía el subtotal, en los doce documentos de prueba, y como el subtotal es
    un importe perfectamente creíble nadie lo hubiera notado mirando la salida.
    """
    def coincide(p: Palabra) -> bool:
        t = p.texto.upper().replace(" ", "").strip(":$")
        return t == etiqueta if exacto else etiqueta in t

    rotulos = [p for p in palabras if coincide(p)]
    if not rotulos:
        return None
    r = rotulos[0]
    candidatos = [
        (p.y, c)
        for p in palabras
        if 5 < p.y - r.y < 70 and abs(p.x - r.x) < ventana_x and (c := _importe(p.texto))
    ]
    return min(candidatos)[1] if candidatos else None


def _unidades(palabras: list[Palabra]) -> int | None:
    """"Unidades: 21". Acá el valor va al lado, no debajo.

    Recibe todas las palabras y no sólo la franja del pie: "Unidades" está ARRIBA de la
    tira de totales, no adentro. Restringirlo a la franja lo dejaba afuera y el campo
    quedaba en None, que después hace que el segundo veto no exista.
    """
    for p in palabras:
        if "UNIDADES" in p.texto.upper():
            tolerancia = tolerancia_de_fila(palabras)
            al_lado = [
                q for q in palabras
                if abs(q.y - p.y) <= tolerancia and 0 < q.x - p.x < p.alto * 12
                and _ENTERO.match(q.texto)
            ]
            if al_lado:
                return int(min(al_lado, key=lambda q: q.x).texto)
    return None


def leer(img: Image.Image, *, proveedor: str = "?", tipo: str = "?") -> Comprobante | None:
    """Lee el comprobante de la imagen. Devuelve None si no encuentra lo mínimo.

    Devolver None es una respuesta legítima y es lo que hay que hacer cuando no se ve: el
    caso de fuga de `CRITERIOS.md` §7 mide exactamente que no invente un total.

    Los campos que T0 no intenta leer —proveedor, número, fecha— quedan en "?". No es que
    fallen: no se intentaron. Reconocer el encabezado de cada proveedor es trabajo del
    modelo, y meterle reglas acá sería inflar el baseline a mano para que la comparación
    quede pareja, que es lo contrario de lo que un baseline sirve.
    """
    derecha, _ = enderezar(img)
    palabras = palabras_de(derecha)
    if not palabras:
        return None

    lineas = tuple(l for fila in _filas(palabras) if (l := _linea_de(fila)) is not None)
    if not lineas:
        return None

    pie = _pie_de(palabras)
    subtotal = _valor_debajo(pie, "SUB-TOTAL") or _valor_debajo(pie, "SUBTOTAL")
    total = _valor_debajo(pie, "TOTAL", exacto=True, ventana_x=160)
    if subtotal is None or total is None:
        return None

    return Comprobante(
        proveedor=proveedor,
        tipo=tipo,
        punto_venta="?",
        numero="?",
        fecha=SIN_FECHA,
        lineas=lineas,
        pie=PieDeComprobante(
            subtotal=subtotal,
            total=total,
            iva=_valor_debajo(pie, "IVA") or Centavos(0),
            percepcion_iibb=_valor_debajo(pie, "PERC") or Centavos(0),
            unidades=_unidades(palabras),
        ),
    )
