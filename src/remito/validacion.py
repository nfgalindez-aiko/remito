"""Las cuentas que pueden vetar al modelo.

El modelo lee la foto y propone números. Acá se decide si entran. Si la aritmética no
cierra, no entra, por más seguro que el modelo diga estar: la confianza que reporta un
modelo es una opinión sobre sí mismo, y la suma de las líneas es un hecho.

Las tolerancias de los cuatro chequeos son distintas a propósito. Cada una tiene su
medición en CRITERIOS.md sección 3. Una tolerancia uniforme sería una plantilla, no una
decisión, y dejaría pasar en un lugar lo que sobra en otro.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum

from .comprobante import Comprobante, Linea
from .plata import formatear


def diferencia(centavos: int) -> str:
    """Un centavo se dice en centavos; seis mil pesos se dicen en pesos.

    Escribir "-611524 centavos" obliga al que lee a dividir por cien mentalmente para
    entender si lo que falta es una moneda o media caja de galletitas."""
    if abs(centavos) < 100:
        return f"{centavos:+d} centavos"
    return ("faltan " if centavos < 0 else "sobran ") + formatear(abs(centavos))


class Chequeo(str, Enum):
    SUBTOTAL = "subtotal"
    UNIDADES = "unidades"
    LINEA = "linea"
    TOTAL = "total"


class Gravedad(str, Enum):
    VETO = "veto"
    """No entra. Va a revisión humana sí o sí."""
    AVISO = "aviso"
    """Se anota, no frena."""


@dataclass(frozen=True)
class Descuadre:
    chequeo: Chequeo
    gravedad: Gravedad
    detalle: str
    diferencia_centavos: int = 0
    linea: str | None = None


@dataclass(frozen=True)
class DesvioConocido:
    """Una maña del proveedor: un desvío sistemático y legítimo, confirmado por un humano.

    Idea de Nicolás, 18/09/2026. P01 redondea el total un centavo para abajo, siempre.
    La primera vez el documento frena y lo mira él; una vez confirmado, deja de frenar.

    Afloja UN chequeo de UN proveedor. Nunca se aplica en general: un sistema que sube la
    tolerancia para todos por culpa de uno deja pasar errores reales en los otros ocho.

    Queda registrado quién lo confirmó y cuándo, porque es una decisión de negocio que
    alguien va a tener que defender frente a un contador.
    """

    proveedor: str
    chequeo: Chequeo
    tolerancia_centavos: int
    confirmado_por: str
    fecha: date
    nota: str

    def cubre(self, comprobante: Comprobante, chequeo: Chequeo, diferencia: int) -> bool:
        return (
            self.proveedor == comprobante.proveedor
            and self.chequeo is chequeo
            and abs(diferencia) <= self.tolerancia_centavos
        )


@dataclass(frozen=True)
class Veredicto:
    aprobado: bool
    descuadres: tuple[Descuadre, ...] = field(default=())

    @property
    def vetos(self) -> tuple[Descuadre, ...]:
        return tuple(d for d in self.descuadres if d.gravedad is Gravedad.VETO)


def tolerancia_linea(cantidad: int) -> int:
    """Centavos que se le perdonan a `precio_unitario × cantidad` contra el subtotal impreso.

    El precio unitario impreso está redondeado a dos decimales, pero el proveedor liquida
    con más: el subtotal de la línea 15004 de P01 dividido 3 da 1.981,7367, y el papel
    imprime 1.981,74.

    Si el precio real redondea al impreso con error de hasta medio centavo, entonces
    |subtotal_impreso − precio_impreso × q| ≤ 0,005·q + 0,005. Eso da la fórmula de abajo.

    Para q=5 la cota da 4 centavos. El peor desvío observado en P01 fue 2. La cota es más
    ancha que el dato porque está derivada del mecanismo, no ajustada a la muestra: seis
    líneas de un proveedor no alcanzan para fijar un umbral.
    """
    return (cantidad + 1) // 2 + 1


def revisar_linea(linea: Linea) -> Descuadre | None:
    esperado = linea.precio_unitario * linea.cantidad
    dif = linea.subtotal - esperado
    if abs(dif) <= tolerancia_linea(linea.cantidad):
        return None
    return Descuadre(
        chequeo=Chequeo.LINEA,
        gravedad=Gravedad.VETO,
        linea=linea.codigo,
        diferencia_centavos=dif,
        detalle=(
            f"{formatear(linea.precio_unitario)} × {linea.cantidad} = "
            f"{formatear(esperado)}, pero el papel dice {formatear(linea.subtotal)} "
            f"({diferencia(dif)}, se toleran {tolerancia_linea(linea.cantidad)} centavos)"
        ),
    )


def revisar(
    comprobante: Comprobante,
    desvios_conocidos: tuple[DesvioConocido, ...] = (),
) -> Veredicto:
    descuadres: list[Descuadre] = []

    def registrar(chequeo: Chequeo, gravedad: Gravedad, dif: int, detalle: str) -> None:
        for d in desvios_conocidos:
            if d.cubre(comprobante, chequeo, dif):
                descuadres.append(
                    Descuadre(
                        chequeo=chequeo,
                        gravedad=Gravedad.AVISO,
                        diferencia_centavos=dif,
                        detalle=f"{detalle} — maña conocida de {d.proveedor}, "
                        f"confirmada por {d.confirmado_por} el {d.fecha}: {d.nota}",
                    )
                )
                return
        descuadres.append(Descuadre(chequeo, gravedad, detalle, dif))

    if not comprobante.lineas:
        return Veredicto(
            aprobado=False,
            descuadres=(
                Descuadre(
                    Chequeo.SUBTOTAL,
                    Gravedad.VETO,
                    "el comprobante no tiene ni una línea",
                ),
            ),
        )

    for linea in comprobante.lineas:
        if (d := revisar_linea(linea)) is not None:
            descuadres.append(d)

    # Veto duro 1. Medido en P01: las seis líneas suman 38.068,23 y el SUB-TOTAL impreso
    # dice 38.068,23. Exacto. Por eso acá la tolerancia es cero y no se negocia: es el
    # chequeo que detecta la línea que quedó tapada por la segunda hoja.
    suma = sum(l.subtotal for l in comprobante.lineas)
    if (dif := suma - comprobante.pie.subtotal) != 0:
        registrar(
            Chequeo.SUBTOTAL,
            Gravedad.VETO,
            dif,
            f"las líneas suman {formatear(suma)} y el SUB-TOTAL impreso dice "
            f"{formatear(comprobante.pie.subtotal)} ({diferencia(dif)})",
        )

    # Veto duro 2, independiente del anterior. Si una línea tapada tuviera subtotal cero,
    # el chequeo de arriba no la vería y este sí. Cuesta una suma; se mantienen los dos.
    if comprobante.pie.unidades is not None:
        unidades = sum(l.cantidad for l in comprobante.lineas)
        if (dif := unidades - comprobante.pie.unidades) != 0:
            registrar(
                Chequeo.UNIDADES,
                Gravedad.VETO,
                dif,
                f"las líneas suman {unidades} unidades y el pie dice "
                f"{comprobante.pie.unidades}",
            )

    # Acá NO va un veto. CRITERIOS.md 3.4: la factura A 0026-00183517 de P01, con CAE
    # válido, no cierra contra sus propios componentes impresos por un centavo. Vetar
    # sobre el TOTAL manda a revisión humana el 100% de los comprobantes de ese proveedor.
    # Se avisa y se sigue; lo que decide es el SUB-TOTAL.
    pie = comprobante.pie
    componentes = (
        pie.subtotal
        + pie.iva
        + pie.percepcion_iibb
        + pie.percepcion_iva
        + pie.impuestos_internos
        - pie.otros_descuentos
    )
    if (dif := componentes - pie.total) != 0:
        registrar(
            Chequeo.TOTAL,
            Gravedad.AVISO,
            dif,
            f"los componentes suman {formatear(componentes)} y el TOTAL impreso dice "
            f"{formatear(pie.total)} ({diferencia(dif)})",
        )

    return Veredicto(
        aprobado=not any(d.gravedad is Gravedad.VETO for d in descuadres),
        descuadres=tuple(descuadres),
    )
