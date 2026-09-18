"""El README no puede afirmar cosas que el código desmiente.

Los nueve evaluadores lo dijeron con estas palabras: verifican una afirmación con grep, y si
falla una, no creen ninguna de las demás. El 18/09/2026 este repositorio se publicó con el
README diciendo "no hay base de datos" mientras `base.py` ya existía, y con la tabla de módulos
sin tres de ellos. Se descubrió leyéndolo, no corriendo nada.

Estos tests son la respuesta a eso. No revisan estilo ni completitud: revisan que cada número y
cada nombre propio que el README pone por escrito siga siendo cierto.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
README = (RAIZ / "README.md").read_text(encoding="utf-8")
SRC = RAIZ / "src" / "remito"

# __init__ y __main__ son plomería de Python, no partes del proyecto que alguien vaya a abrir.
PLOMERIA = {"__init__.py", "__main__.py"}


@pytest.mark.parametrize(
    "modulo",
    sorted(p.name for p in SRC.glob("*.py") if p.name not in PLOMERIA),
)
def test_cada_modulo_esta_en_la_tabla(modulo: str) -> None:
    """Si nace un módulo y nadie lo agrega al README, la tabla se vuelve una foto vieja.

    Ya pasó: `base.py`, `roturas.py` y `comprobante.py` no estaban, y el README decía que no
    había base de datos mientras SQLite ya andaba.
    """
    assert f"src/remito/{modulo}" in README, (
        f"{modulo} existe y no está en la tabla del README"
    )


def test_los_archivos_que_el_readme_nombra_existen() -> None:
    """Al revés: que no prometa archivos que no están."""
    for ruta in set(re.findall(r"`((?:src/|docs/|tests/)[\w./-]+)`", README)):
        assert (RAIZ / ruta).exists(), f"el README nombra {ruta} y no existe"


def test_el_reparto_de_las_roturas_es_el_que_dice() -> None:
    """El README publica 6 / 5 / 1. Es el número que más pesa de todo el repositorio, así que
    no puede salir de la memoria de nadie."""
    from remito.roturas import Defensa, por_defensa

    for cuantas, defensa in (
        (len(por_defensa(Defensa.ARITMETICA)), "las frena la aritmética"),
        (len(por_defensa(Defensa.EL_EXTRACTOR)), "consistente consigo misma"),
        (len(por_defensa(Defensa.NINGUNA)), "sin defensa posible"),
    ):
        assert f"**{cuantas} de 12**" in README, (
            f"el README no dice '{cuantas} de 12' para {defensa}"
        )


def test_los_servicios_de_docker_que_el_readme_manda_correr_existen() -> None:
    compose = (RAIZ / "docker-compose.yml").read_text(encoding="utf-8")
    for servicio in re.findall(r"docker compose run --rm (\w+)", README):
        assert f"  {servicio}:" in compose, (
            f"el README manda correr el servicio '{servicio}' y no está en docker-compose.yml"
        )


def test_el_hash_congelado_que_el_readme_manda_verificar_da() -> None:
    """El README dice que `sha256sum -c CRITERIOS.sha256` tiene que dar. Que dé."""
    esperado = (RAIZ / "CRITERIOS.sha256").read_text(encoding="utf-8").split()[0]
    real = hashlib.sha256((RAIZ / "CRITERIOS.md").read_bytes()).hexdigest()
    assert real == esperado


def test_los_cuatro_chequeos() -> None:
    from remito.validacion import Chequeo

    assert f"los {len(Chequeo)} chequeos" in README or "cuatro chequeos" in README


def test_no_promete_lo_que_no_hay() -> None:
    """El error que los nueve nombraron primero.

    Mientras no exista el extractor, el README no puede abrir prometiendo que lee fotos. El día
    que exista, este test se saca en el mismo commit que lo agrega.
    """
    apertura = README.split("## ")[0].lower()
    for promesa in ("entra la foto", "sale la mercadería cargada", "subís una foto"):
        assert promesa not in apertura, (
            f"el README promete '{promesa}' en la apertura y el extractor no existe"
        )
    assert "no lee fotos" in README.lower()


def test_toda_excepcion_definida_se_levanta_en_algun_lado() -> None:
    """Una excepción con docstring que nunca se levanta es el código mintiendo sobre sí mismo.

    Encontrado el 18/09/2026 consolidando: `ImporteAmbiguo` estaba definida con un docstring
    que decía "se levanta en vez de elegir" y el parser elegía igual, en silencio. Alguien
    que lee `plata.py` se lleva una impresión del comportamiento que el código no tiene.
    """
    import ast

    src = RAIZ / "src" / "remito"
    definidas, levantadas = {}, set()
    for archivo in src.glob("*.py"):
        arbol = ast.parse(archivo.read_text(encoding="utf-8"))
        for n in ast.walk(arbol):
            if isinstance(n, ast.ClassDef) and any(
                isinstance(b, ast.Name) and ("Error" in b.id or "Exception" in b.id or b.id.endswith("ValueError"))
                for b in n.bases
            ):
                definidas[n.name] = archivo.name
            if isinstance(n, ast.Raise) and isinstance(n.exc, ast.Call):
                if isinstance(n.exc.func, ast.Name):
                    levantadas.add(n.exc.func.id)
    huerfanas = {n: f for n, f in definidas.items() if n not in levantadas}
    assert not huerfanas, f"definidas y nunca levantadas: {huerfanas}"


# Acá había un test que buscaba redondeos escritos a mano con una expresión regular, para
# que no volvieran a aparecer cuatro formas de la misma cuenta. Se borró el mismo día que se
# escribió: marcaba `(cantidad + 1) // 2 + 1` de `validacion.py`, que es el techo de una
# división y no un redondeo, y las tres líneas del test que cita las formas viejas a
# propósito. Una expresión regular no distingue dos fórmulas enteras distintas, y un guardián
# al que hay que irle agregando excepciones deja de significar algo.
#
# Lo que sí fija la propiedad está en `test_plata.py`: un test que comprueba que la única
# implementación que quedó da lo mismo que las cuatro que había sueltas.
