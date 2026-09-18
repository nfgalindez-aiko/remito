"""El comprobante de compra tal como sale del papel.

Estas clases guardan lo que está IMPRESO, no lo que debería estar. Si el papel dice un
total que no cierra con sus partes —y pasa: ver CRITERIOS.md 3.4— acá se guarda el total
que dice el papel. Corregirlo al cargarlo haría desaparecer justo la evidencia que el
validador necesita para decidir.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from .plata import Centavos


@dataclass(frozen=True)
class Linea:
    codigo: str
    descripcion: str
    cantidad: int
    precio_unitario: Centavos
    """Como está impreso. Es un redondeo de presentación: no se usa para costear.
    Ver plata.comparar_costo_unitario."""
    subtotal: Centavos
    """Como está impreso. ESTE es el número autoritativo de la línea."""

    def __post_init__(self) -> None:
        if self.cantidad <= 0:
            raise ValueError(f"cantidad inválida en línea {self.codigo}: {self.cantidad}")


@dataclass(frozen=True)
class PieDeComprobante:
    """La tira de totales. En P01 viene impresa en la segunda hoja, que en la foto
    tapa parte de la primera. Ese solapamiento es el modo de falla que motivó todo esto."""

    subtotal: Centavos
    total: Centavos
    iva: Centavos = Centavos(0)
    percepcion_iibb: Centavos = Centavos(0)
    percepcion_iva: Centavos = Centavos(0)
    impuestos_internos: Centavos = Centavos(0)
    otros_descuentos: Centavos = Centavos(0)
    unidades: int | None = None
    """El campo "Unidades: 26" del pie. Opcional porque no todos los proveedores lo
    imprimen, pero cuando está es un segundo chequeo independiente de líneas tapadas."""


@dataclass(frozen=True)
class Comprobante:
    proveedor: str
    """Identificador público: P01, P02... El mapeo al proveedor real vive fuera del repo."""
    tipo: str
    """A, B, C o REMITO. Manda: los precios de un A son netos y los de un B traen el IVA
    adentro. Comparar un A contra un B produce un aumento del 21% que no ocurrió."""
    punto_venta: str
    numero: str
    fecha: date
    lineas: tuple[Linea, ...]
    pie: PieDeComprobante
    remito_numero: str | None = None
    """La factura de P01 trae "Remito N° 114727" adentro: el mismo papel es el comprobante
    fiscal y el remito que acompaña la mercadería. De ahí el nombre del proyecto."""
    hoja: str | None = None
    """"1/1", "1/2". Si dice 1/2 y sólo hay una foto, falta la mitad del documento."""

    SIN_LEER = "?"
    """Lo que ponen los lectores en un campo que no intentaron leer. No es lo mismo que
    vacío: vacío sería una lectura que dio nada, esto es que nadie miró."""

    @property
    def identificable(self) -> bool:
        """Si se puede saber QUÉ comprobante es.

        Sin esto no hay idempotencia posible: dos facturas distintas de las que no se leyó
        el número son indistinguibles entre sí, y la base -que las identifica por el
        número- va a tomar la segunda por un duplicado de la primera.
        """
        return self.SIN_LEER not in (self.proveedor, self.tipo, self.punto_venta, self.numero)

    @property
    def id_unico(self) -> str:
        """La clave que va con UNIQUE en la base. Es lo único que impide cargar dos veces
        la misma mercadería cuando sacás dos fotos del mismo papel."""
        return f"{self.proveedor}|{self.tipo}|{self.punto_venta}|{self.numero}"
