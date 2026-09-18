"""Plata. Todo en centavos enteros.

Ningún importe pasa por float, en este archivo ni en ningún otro lado del proyecto.

Por qué, medido el 18/09/2026 en esta máquina: calculando el IVA del 21% sobre cada neto
posible de $1 a $200.000, el 0,736% de los casos (147.239 de 19.999.900) da un centavo
distinto en float que en enteros. El primero es $3,50 — en enteros 0,74, en float 0,73.
Con una factura por día eso es un error cada cuatro meses y medio: lo bastante raro para
no aparecer nunca en las pruebas, y lo bastante seguido para que un contador lo encuentre.

Lo que NO se rompió: la suma de las seis líneas de la factura P01 2026-09-17 da exacta
también en float. Se probó antes de escribir esto. El float no falla al sumar importes
chicos, falla al redondear. La regla igual es "nunca float", porque la frontera entre
los dos casos no la quiero estar cuidando a mano en cada archivo.
"""

from __future__ import annotations

import re
from typing import NewType

Centavos = NewType("Centavos", int)


class ImporteInvalido(ValueError):
    """El texto no es un importe."""


class ImporteAmbiguo(ValueError):
    """El texto podría ser dos importes distintos y no hay forma de saber cuál.

    Se levanta en vez de elegir. Un parser que adivina le pasa un número plausible al
    validador, que lo aprueba porque cierra, y el error entra a la base. Es el modo de
    falla más caro del sistema: el que no deja rastro.
    """


# Todo lo que no sea dígito, separador o signo. El "$" y los espacios raros del OCR.
_BASURA = re.compile(r"[\s$  ]+")
_VALIDO = re.compile(r"^-?[\d.,]+$")


def _quitar_miles(entero: str, sep: str, original: str) -> str:
    """Saca los separadores de miles, pero primero comprueba que los grupos midan tres.

    El OCR sobre una foto torcida agrega y mueve puntos: "3.688,05" puede llegar como
    "3.68.8,05". Sin este chequeo eso se convierte en 3.688 sin protestar, que es un
    número plausible, que cierra con el resto, y que entra a la base siendo falso.
    """
    if sep not in entero:
        return entero
    cabeza, *grupos = entero.split(sep)
    if not cabeza or len(cabeza) > 3 or any(len(g) != 3 for g in grupos):
        raise ImporteInvalido(
            f"los grupos de miles no miden tres dígitos: {original!r}"
        )
    return cabeza + "".join(grupos)


def parse_importe(texto: str) -> Centavos:
    """Convierte el importe tal como está impreso en el papel a centavos enteros.

    La factura P01 2026-09-17 usa DOS formatos distintos en la misma hoja:

        TOTAL      $ 46.671,64     punto de miles, coma decimal   (formato argentino)
        IVA 21%      7994.33       sin miles, punto decimal       (el mismo papel)

    Así que "el punto es separador de miles" es falso y "la coma es el decimal" también.
    La regla que sí funciona es mirar el último separador y cuántos dígitos lo siguen.
    """
    limpio = _BASURA.sub("", texto)
    if not limpio:
        raise ImporteInvalido(f"importe vacío: {texto!r}")
    if not _VALIDO.match(limpio):
        raise ImporteInvalido(f"no es un importe: {texto!r}")

    negativo = limpio.startswith("-")
    if negativo:
        limpio = limpio[1:]
    if not limpio:
        raise ImporteInvalido(f"importe vacío: {texto!r}")

    puntos, comas = limpio.count("."), limpio.count(",")

    if puntos and comas:
        # Están los dos. El que va último es el decimal; el otro es de miles.
        decimal = "." if limpio.rfind(".") > limpio.rfind(",") else ","
        miles = "," if decimal == "." else "."
        entero, _, frac = limpio.rpartition(decimal)
        if miles in frac:
            raise ImporteInvalido(f"separadores fuera de orden: {texto!r}")
        entero = _quitar_miles(entero, miles, texto)
    elif puntos or comas:
        sep = "." if puntos else ","
        cuantos = puntos or comas
        entero, _, frac = limpio.rpartition(sep)
        if len(frac) == 3 and cuantos == 1 and sep == ",":
            # Acá no se puede saber, y por eso no se elige.
            #
            # "1,234" es mil doscientos treinta y cuatro si el papel usa el formato yanqui,
            # o un importe de tres decimales si usa el argentino. Lo segundo no existe en
            # plata, pero tampoco se puede descartar que el OCR haya comido un dígito de
            # "1,2345" o agregado uno a "1,23". Un punto con tres dígitos sí se resuelve
            # -abajo- porque el papel de P01 imprime "38.068" y son miles; una coma con
            # tres dígitos no aparece nunca en un comprobante argentino.
            #
            # Elegir uno de los dos significa entregar un número mil veces distinto del
            # otro, plausible, que después cierra o no cierra por casualidad.
            raise ImporteAmbiguo(
                f"una coma con tres dígitos puede ser miles o decimales: {texto!r}"
            )
        if cuantos > 1 or len(frac) == 3:
            # Varios separadores, o un punto con tres dígitos: son miles.
            # "38.068" son treinta y ocho mil sesenta y ocho, no 38 pesos con 68 milésimos:
            # así está impreso en la factura de P01.
            entero, frac = _quitar_miles(limpio, sep, texto), ""
        elif len(frac) > 3:
            raise ImporteInvalido(f"demasiados dígitos después del separador: {texto!r}")
    else:
        # Sin separador. Son pesos enteros: "$ 1000" son mil pesos.
        #
        # Acá vive el error más caro que puede cometer el OCR: si se come la coma,
        # "737,61" llega como "73761" y esto devuelve $73.761 en vez de $737,61. Cien
        # veces más. No se arregla en el parser —no hay información para distinguirlo—
        # sino en el veto del subtotal: una línea cien veces más grande jamás va a sumar
        # el subtotal impreso. Hay un test que dispara justamente eso.
        entero, frac = limpio, ""

    if not entero:
        entero = "0"
    if not entero.isdigit():
        raise ImporteInvalido(f"no es un importe: {texto!r}")

    centavos = int(entero) * 100 + (int(frac.ljust(2, "0")[:2]) if frac else 0)
    return Centavos(-centavos if negativo else centavos)


def formatear(centavos: int) -> str:
    """Para mostrarle a un humano. Nunca para comparar ni para guardar."""
    signo = "-" if centavos < 0 else ""
    entero, resto = divmod(abs(centavos), 100)
    return f"{signo}{entero:,}".replace(",", ".") + f",{resto:02d}"


def redondear(numerador: int, denominador: int) -> int:
    """`numerador / denominador` redondeado half-up, sin que aparezca un float.

    Half-up y no al par más cercano: AFIP redondea 2,675 a 2,68, y Python redondea al par,
    que da 2,67. Son convenciones distintas y la que manda es la del papel.

    Existe porque esta misma cuenta estaba escrita de cuatro formas distintas en cuatro
    archivos: `(neto * alicuota + 500) // 1000`, `(sub * 16 * 2 + 1000) // 2000`,
    `(num * 2 + den) // (den * 2)` y una cuarta en un test. Todas correctas y todas
    distintas, que es peor que una sola mal: cuatro lugares donde arreglar el día que el
    redondeo tenga que cambiar.

    Sólo para positivos. Con negativos `//` redondea hacia abajo y habría que decidir qué
    significa half-up en ese lado; no hace falta porque las notas de crédito están fuera de
    alcance (`LIMITES.md` §7).
    """
    if denominador <= 0 or numerador < 0:
        raise ValueError(f"redondear sólo maneja positivos: {numerador}/{denominador}")
    return (numerador * 2 + denominador) // (denominador * 2)


def iva(neto: Centavos, alicuota_por_mil: int = 210) -> Centavos:
    """IVA con redondeo half-up, sin float en ningún paso.

    La alícuota va en por mil (210 = 21%) para que sea un entero: 0.21 no existe exacto
    en binario y meterlo acá reintroduce justo el error que este módulo evita.

    Verificado contra P01 2026-09-17: neto 38.068,23 -> 7.994,33, que es lo que imprime
    el papel, al centavo.
    """
    return Centavos(redondear(neto * alicuota_por_mil, 1000))


def comparar_costo_unitario(sub_a: int, cant_a: int, sub_b: int, cant_b: int) -> int:
    """Compara el costo por unidad de dos líneas. Devuelve -1, 0 o 1. No divide nunca.

    El costo unitario de una línea es subtotal/cantidad, y casi nunca cae en un número
    redondo de centavos: la línea 15004 de P01 2026-09-17 da 5.945,21 / 3 = 1.981,7367
    pesos por unidad. Redondear eso a centavos y después comparar dos redondeos produce
    aumentos de un centavo que nunca pasaron, y este sistema existe para avisar aumentos.

    a/b contra c/d, con b y d positivos, es lo mismo que a*d contra c*b. Multiplicar
    enteros es exacto; dividir no. Así que se multiplica.

    Y es la razón por la que el precio unitario IMPRESO no se usa para nada: también es
    un redondeo. El número autoritativo es el subtotal de la línea con su cantidad.
    """
    if cant_a <= 0 or cant_b <= 0:
        raise ValueError("cantidad tiene que ser positiva")
    izq, der = sub_a * cant_b, sub_b * cant_a
    return (izq > der) - (izq < der)
