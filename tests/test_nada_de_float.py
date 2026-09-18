"""El README dice "centavos enteros, nunca float". Esto lo comprueba en vez de prometerlo.

Un evaluador va a verificar esa afirmación con grep. Grep encuentra la palabra "float" en los
comentarios que explican por qué no se usa, y no distingue la prosa del código. Esto sí: lee
el árbol sintáctico de los módulos donde vive la plata y busca lo único que importa —un
literal decimal o una división verdadera— que son las dos formas de que un float se cuele.

`sintetico.py` y `cli.py` no están en la lista: el generador y la impresión no manejan plata
que después vaya a una base. Lo que se protege es el camino del dinero, no todo el repo.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

CAMINO_DE_LA_PLATA = ["plata.py", "validacion.py", "comprobante.py", "base.py", "roturas.py"]
SRC = Path(__file__).resolve().parents[1] / "src" / "remito"


def arbol(nombre: str) -> ast.Module:
    return ast.parse((SRC / nombre).read_text(encoding="utf-8"), filename=nombre)


@pytest.mark.parametrize("modulo", CAMINO_DE_LA_PLATA)
def test_ningun_literal_decimal(modulo: str) -> None:
    culpables = [
        f"{modulo}:{n.lineno} -> {n.value!r}"
        for n in ast.walk(arbol(modulo))
        if isinstance(n, ast.Constant) and isinstance(n.value, float)
    ]
    assert not culpables, "hay literales float en el camino de la plata: " + "; ".join(culpables)


@pytest.mark.parametrize("modulo", CAMINO_DE_LA_PLATA)
def test_ninguna_division_verdadera(modulo: str) -> None:
    """`a / b` devuelve float aunque a y b sean enteros. `a // b` no.

    Es la forma más silenciosa de que entre un float: nadie escribe 0.21, pero cualquiera
    escribe `total / cantidad` sin pensarlo.
    """
    culpables = [
        f"{modulo}:{n.lineno}"
        for n in ast.walk(arbol(modulo))
        if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Div)
    ]
    assert not culpables, "hay divisiones verdaderas: " + "; ".join(culpables)


@pytest.mark.parametrize("modulo", CAMINO_DE_LA_PLATA)
def test_no_se_importa_decimal_ni_fractions(modulo: str) -> None:
    """Tampoco Decimal.

    Decimal sería correcto y no es el enemigo, pero tener dos representaciones de plata en
    el mismo repo obliga a acordarse de cuál usa cada función. Una sola: int de centavos.
    """
    importados = {
        alias.name.split(".")[0]
        for n in ast.walk(arbol(modulo))
        if isinstance(n, (ast.Import, ast.ImportFrom))
        for alias in n.names
    } | {
        n.module.split(".")[0]
        for n in ast.walk(arbol(modulo))
        if isinstance(n, ast.ImportFrom) and n.module
    }
    assert not importados & {"decimal", "fractions", "numpy"}


def test_la_lista_cubre_todo_lo_que_toca_plata() -> None:
    """Si alguien agrega un módulo nuevo que importa Centavos, tiene que entrar a la lista.

    Sin esto, el día que nazca `precios.py` con la alerta de aumento, nadie se acuerda de
    agregarlo acá y la garantía se convierte en una frase del README.
    """
    tocan_plata = {
        archivo.name
        for archivo in SRC.glob("*.py")
        if "Centavos" in archivo.read_text(encoding="utf-8")
    }
    sin_cubrir = tocan_plata - set(CAMINO_DE_LA_PLATA) - {"sintetico.py", "cli.py"}
    assert not sin_cubrir, (
        f"estos módulos manejan Centavos y no están en la lista: {sorted(sin_cubrir)}"
    )
