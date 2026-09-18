"""La base. SQLite, un archivo, sin servidor. Por qué no Postgres: `docs/adr/0001`.

Dos cosas de SQLite que hay que hacer a mano y que si no se hacen fallan en silencio:

- **Las claves foráneas vienen apagadas.** `PRAGMA foreign_keys = ON` por conexión, no por
  base. Sin eso, `REFERENCES` es decorativo: se pueden insertar líneas de un comprobante
  que no existe y nadie protesta.
- **Una transacción diferida toma el candado de escritura tarde**, recién en el primer
  INSERT. Dos procesos que empiezan a la vez leen, deciden, y uno se lleva un
  `SQLITE_BUSY` a mitad de camino. `BEGIN IMMEDIATE` lo toma de entrada. Es la diferencia
  entre que la carga concurrente ande y que ande casi siempre.

La plata se guarda en columnas INTEGER con `CHECK (typeof(x) = 'integer')`. SQLite tiene
afinidad de tipos, no tipos: en una columna INTEGER entra un 1.5 sin chistar y sale un
float. El CHECK es lo único que hace que "nunca float" también valga adentro del archivo.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date, datetime, timezone
from enum import Enum
from pathlib import Path

from .comprobante import Comprobante
from .plata import Centavos, comparar_costo_unitario
from .validacion import Chequeo, DesvioConocido, Veredicto

PLATA = "INTEGER NOT NULL CHECK (typeof({0}) = 'integer')"

ESQUEMA = f"""
CREATE TABLE IF NOT EXISTS comprobante (
    id_unico        TEXT PRIMARY KEY,
    proveedor       TEXT NOT NULL,
    tipo            TEXT NOT NULL,
    punto_venta     TEXT NOT NULL,
    numero          TEXT NOT NULL,
    fecha           TEXT NOT NULL,
    remito_numero   TEXT,
    estado          TEXT NOT NULL CHECK (estado IN ('aprobado', 'a_revision')),
    subtotal        {PLATA.format('subtotal')},
    total           {PLATA.format('total')},
    iva             {PLATA.format('iva')},
    percepcion_iibb {PLATA.format('percepcion_iibb')},
    unidades        INTEGER,
    cargado_en      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS linea (
    comprobante_id  TEXT NOT NULL REFERENCES comprobante(id_unico) ON DELETE CASCADE,
    posicion        INTEGER NOT NULL,
    codigo          TEXT NOT NULL,
    descripcion     TEXT NOT NULL,
    cantidad        INTEGER NOT NULL CHECK (cantidad > 0 AND typeof(cantidad) = 'integer'),
    precio_unitario {PLATA.format('precio_unitario')},
    subtotal        {PLATA.format('subtotal')},
    PRIMARY KEY (comprobante_id, posicion)
);

CREATE TABLE IF NOT EXISTS desvio_conocido (
    proveedor           TEXT NOT NULL,
    chequeo             TEXT NOT NULL,
    tolerancia_centavos INTEGER NOT NULL,
    confirmado_por      TEXT NOT NULL,
    fecha               TEXT NOT NULL,
    nota                TEXT NOT NULL,
    PRIMARY KEY (proveedor, chequeo)
);

CREATE INDEX IF NOT EXISTS idx_linea_codigo ON linea(codigo);
CREATE INDEX IF NOT EXISTS idx_comprobante_prov_fecha ON comprobante(proveedor, fecha);
"""


class Carga(str, Enum):
    NUEVO = "nuevo"
    YA_ESTABA = "ya_estaba"


# Segundos que un escritor espera el candado antes de rendirse con SQLITE_BUSY.
# Generoso a propósito, y por eso con el número al lado: medido el 18/09/2026 en esta
# máquina, 12 hilos cargando la misma factura esperaron 99 ms el peor y 19 ms la mediana.
# 30 segundos son 300 veces el peor caso medido. El margen está para el día que alguien
# cargue un lote mientras otro proceso lee, no ajustado a la prueba.
# Va entero, no 30.0: el guardián de "nunca float" no acepta excepciones en estos
# módulos, y "este float está bien, no es plata" es el razonamiento que deja pasar
# al que sí importa.
ESPERA_CANDADO_SEG = 30


def conectar(ruta: Path | str = ":memory:") -> sqlite3.Connection:
    conn = sqlite3.connect(ruta, isolation_level=None, timeout=ESPERA_CANDADO_SEG)
    conn.execute("PRAGMA foreign_keys = ON")
    # WAL deja que un lector y un escritor convivan. Sin esto, la prueba de carga
    # concurrente falla por el modo de journal, no por la lógica que se quiere probar.
    if ruta != ":memory:":
        conn.execute("PRAGMA journal_mode = WAL")
    conn.executescript(ESQUEMA)
    return conn


def cargar(conn: sqlite3.Connection, c: Comprobante, v: Veredicto) -> Carga:
    """Guarda el comprobante una sola vez. Devuelve si lo cargó o si ya estaba.

    La unicidad la hace la clave primaria de la tabla, no un `if ya existe` en Python.
    Preguntar y después insertar deja una ventana entre las dos cosas: dos fotos del mismo
    remito cargadas a la vez pasan las dos el chequeo y entra la mercadería duplicada.
    Acá se intenta insertar y se mira si la base lo aceptó.

    `BEGIN IMMEDIATE` toma el candado de escritura antes del primer INSERT, no en el medio.
    """
    conn.execute("BEGIN IMMEDIATE")
    try:
        cur = conn.execute(
            """INSERT INTO comprobante
               (id_unico, proveedor, tipo, punto_venta, numero, fecha, remito_numero,
                estado, subtotal, total, iva, percepcion_iibb, unidades, cargado_en)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT (id_unico) DO NOTHING""",
            (
                c.id_unico, c.proveedor, c.tipo, c.punto_venta, c.numero,
                c.fecha.isoformat(), c.remito_numero,
                "aprobado" if v.aprobado else "a_revision",
                c.pie.subtotal, c.pie.total, c.pie.iva, c.pie.percepcion_iibb,
                c.pie.unidades, datetime.now(timezone.utc).isoformat(timespec="seconds"),
            ),
        )
        if cur.rowcount == 0:
            conn.execute("ROLLBACK")
            return Carga.YA_ESTABA

        conn.executemany(
            """INSERT INTO linea
               (comprobante_id, posicion, codigo, descripcion, cantidad,
                precio_unitario, subtotal)
               VALUES (?,?,?,?,?,?,?)""",
            # La posición es parte de la clave, no el código: el mismo producto puede venir
            # dos veces en la misma factura, a distinto precio, si entró en dos partidas.
            [
                (c.id_unico, i, l.codigo, l.descripcion, l.cantidad,
                 l.precio_unitario, l.subtotal)
                for i, l in enumerate(c.lineas)
            ],
        )
        conn.execute("COMMIT")
        return Carga.NUEVO
    except Exception:
        conn.execute("ROLLBACK")
        raise


def guardar_desvio(conn: sqlite3.Connection, d: DesvioConocido) -> None:
    conn.execute(
        """INSERT INTO desvio_conocido
           (proveedor, chequeo, tolerancia_centavos, confirmado_por, fecha, nota)
           VALUES (?,?,?,?,?,?)
           ON CONFLICT (proveedor, chequeo) DO UPDATE SET
             tolerancia_centavos = excluded.tolerancia_centavos,
             confirmado_por      = excluded.confirmado_por,
             fecha               = excluded.fecha,
             nota                = excluded.nota""",
        (d.proveedor, d.chequeo.value, d.tolerancia_centavos,
         d.confirmado_por, d.fecha.isoformat(), d.nota),
    )


def desvios_de(conn: sqlite3.Connection, proveedor: str) -> tuple[DesvioConocido, ...]:
    filas = conn.execute(
        "SELECT proveedor, chequeo, tolerancia_centavos, confirmado_por, fecha, nota "
        "FROM desvio_conocido WHERE proveedor = ?",
        (proveedor,),
    ).fetchall()
    return tuple(
        DesvioConocido(p, Chequeo(ch), tol, quien, date.fromisoformat(f), nota)
        for p, ch, tol, quien, f, nota in filas
    )


@dataclass(frozen=True)
class Compra:
    fecha: date
    comprobante: str
    cantidad: int
    subtotal: Centavos


@dataclass(frozen=True)
class Aumento:
    codigo: str
    descripcion: str
    antes: Compra
    ahora: Compra
    por_diez_mil: int
    """El aumento en diezmilésimas. 2150 son 21,5%. Entero, calculado sin dividir en float."""

    @property
    def porcentaje(self) -> str:
        entero, resto = divmod(self.por_diez_mil, 100)
        return f"{entero},{resto:02d}%"


def historial(conn: sqlite3.Connection, proveedor: str, codigo: str) -> list[Compra]:
    """Todas las compras aprobadas de un producto a un proveedor, de la más vieja a la más nueva.

    Sólo las aprobadas. Un comprobante que está en la cola de revisión humana todavía no es
    un hecho: si sus números entraran al historial, un precio mal leído se convertiría en
    una alerta de aumento que nunca pasó, y el sistema perdería la única cosa que tiene
    para ofrecer, que es que sus avisos sean ciertos.
    """
    filas = conn.execute(
        """SELECT c.fecha, c.id_unico, l.cantidad, l.subtotal
           FROM linea l JOIN comprobante c ON c.id_unico = l.comprobante_id
           WHERE c.proveedor = ? AND l.codigo = ? AND c.estado = 'aprobado'
           ORDER BY c.fecha, c.id_unico, l.posicion""",
        (proveedor, codigo),
    ).fetchall()
    return [Compra(date.fromisoformat(f), cid, cant, Centavos(sub)) for f, cid, cant, sub in filas]


def aumento_de(conn: sqlite3.Connection, proveedor: str, codigo: str) -> Aumento | None:
    """Compara las dos últimas compras del producto. Devuelve None si no aumentó.

    No divide para comparar: `comparar_costo_unitario` multiplica cruzado, y por eso un
    producto cuyo costo real es 1.981,7367 no aparece como aumentado cuando no lo está.
    """
    compras = historial(conn, proveedor, codigo)
    if len(compras) < 2:
        return None
    antes, ahora = compras[-2], compras[-1]
    if comparar_costo_unitario(ahora.subtotal, ahora.cantidad, antes.subtotal, antes.cantidad) <= 0:
        return None

    # (ahora/cant_ahora − antes/cant_antes) / (antes/cant_antes), en diezmilésimas, con
    # enteros: se multiplica por 10.000 antes de la única división, que es entera.
    numerador = (ahora.subtotal * antes.cantidad - antes.subtotal * ahora.cantidad) * 10_000
    denominador = antes.subtotal * ahora.cantidad
    descripcion = conn.execute(
        "SELECT descripcion FROM linea WHERE comprobante_id = ? AND codigo = ? LIMIT 1",
        (ahora.comprobante, codigo),
    ).fetchone()
    return Aumento(
        codigo=codigo,
        descripcion=descripcion[0] if descripcion else codigo,
        antes=antes,
        ahora=ahora,
        por_diez_mil=numerador // denominador,
    )


def aumentos(conn: sqlite3.Connection, proveedor: str) -> list[Aumento]:
    codigos = [
        fila[0]
        for fila in conn.execute(
            """SELECT DISTINCT l.codigo FROM linea l
               JOIN comprobante c ON c.id_unico = l.comprobante_id
               WHERE c.proveedor = ? AND c.estado = 'aprobado'""",
            (proveedor,),
        )
    ]
    encontrados = [a for c in sorted(codigos) if (a := aumento_de(conn, proveedor, c))]
    return sorted(encontrados, key=lambda a: -a.por_diez_mil)
