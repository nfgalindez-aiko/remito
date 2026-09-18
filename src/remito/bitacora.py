"""La bitácora: qué pasó con cada comprobante, para poder contestarlo tres semanas después.

No es logging de manual. Existe para una sola pregunta, que es la que se hace de verdad:
*"esta factura quedó en revisión, ¿por qué?"*. Todo lo de abajo sale de esa pregunta.

**Un identificador por comprobante, que se pueda decir por teléfono.** `0918-k3f2`, no
`f47ac10b-58cc-4372-a567-0e02b2c3d479`. Quien atiende el mostrador va a leerlo en voz alta
o anotarlo en el margen del papel, así que no lleva las letras y los números que se
confunden a mano: ni O ni 0, ni I ni l ni 1. Empieza con el día, que es lo que la persona
recuerda.

**Va a un archivo, nunca a la salida estándar.** La salida estándar es lo que el usuario
está leyendo; mezclar las dos cosas arruina las dos. Y nunca a `/dev/null`: un proceso que
corre sin dejar rastro no se puede revisar después, que es justo para lo que existe esto.

**No puede contener un CUIT.** No es una convención, es un chequeo: la bitácora rechaza el
valor y levanta excepción. Un archivo de registro es lo último que alguien revisa antes de
mandarlo adjunto en un correo para pedir ayuda.
"""

from __future__ import annotations

import json
import os
import re
import secrets
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

# Sin O, 0, I, l, 1: son las que se copian mal de un papel a un teclado.
_ALFABETO = "abcdefghjkmnpqrstuvwxyz23456789"

# 11 dígitos con o sin guiones. Cualquier cosa con esa forma no entra a la bitácora.
_CUIT = re.compile(r"\b\d{2}-?\d{8}-?\d\b")


class DatoQueNoVaEnLaBitacora(ValueError):
    """Se intentó anotar algo que no puede quedar escrito en un archivo."""


def nuevo_id(cuando: datetime | None = None) -> str:
    """`0918-k3f2`. El día adelante porque es lo que la persona recuerda.

    Cuatro caracteres al azar sobre un alfabeto de 31 dan cerca de un millón de
    combinaciones por día. Un kiosco carga decenas de comprobantes por día, así que la
    probabilidad de que dos choquen el mismo día es despreciable. No es una clave: la
    unicidad de verdad la da la base con `Comprobante.id_unico`.
    """
    ahora = cuando or datetime.now(timezone.utc)
    sufijo = "".join(secrets.choice(_ALFABETO) for _ in range(4))
    return f"{ahora:%m%d}-{sufijo}"


def _limpio(valor: Any) -> Any:
    if isinstance(valor, str):
        if _CUIT.search(valor):
            raise DatoQueNoVaEnLaBitacora(f"parece un CUIT: {valor!r}")
        return valor
    if isinstance(valor, (int, float, bool)) or valor is None:
        return valor
    if isinstance(valor, (list, tuple)):
        return [_limpio(v) for v in valor]
    if isinstance(valor, dict):
        return {k: _limpio(v) for k, v in valor.items()}
    return _limpio(str(valor))


@dataclass
class Seguimiento:
    """El hilo de un comprobante. Todas sus anotaciones llevan el mismo identificador."""

    id: str
    bitacora: Bitacora

    def anotar(self, evento: str, **campos: Any) -> None:
        self.bitacora.escribir(self.id, evento, campos)


class Bitacora:
    def __init__(self, ruta: Path | str | None = None) -> None:
        self.ruta = Path(ruta) if ruta else Path(os.environ.get("REMITO_BITACORA", "remito.jsonl"))

    def escribir(self, id: str, evento: str, campos: dict[str, Any]) -> None:
        linea = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "id": id,
            "evento": evento,
            **{k: _limpio(v) for k, v in campos.items()},
        }
        self.ruta.parent.mkdir(parents=True, exist_ok=True)
        # Una línea por evento y append: dos procesos escribiendo a la vez no se pisan a
        # mitad de línea mientras cada línea entre en el buffer del sistema.
        with self.ruta.open("a", encoding="utf-8") as f:
            f.write(json.dumps(linea, ensure_ascii=False) + "\n")

    @contextmanager
    def comprobante(self, id: str | None = None) -> Iterator[Seguimiento]:
        """Abre el hilo de un comprobante y lo cierra pase lo que pase.

        Si el proceso revienta en el medio, queda anotado que reventó y con qué. Un
        comprobante cuyo último evento es "recibido" y nada más es exactamente el caso que
        el RUNBOOK dice cómo investigar.
        """
        s = Seguimiento(id or nuevo_id(), self)
        s.anotar("abierto")
        try:
            yield s
        except Exception as e:
            s.anotar("reventó", error=type(e).__name__, detalle=str(e)[:200])
            raise
        finally:
            s.anotar("cerrado")


def leer(ruta: Path | str) -> list[dict[str, Any]]:
    """Todas las anotaciones, para poder buscarlas desde un test o desde el RUNBOOK."""
    p = Path(ruta)
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def hilo_de(ruta: Path | str, id: str) -> list[dict[str, Any]]:
    """Lo que le pasó a un comprobante, en orden. Es la respuesta a la única pregunta."""
    return [a for a in leer(ruta) if a.get("id") == id]
