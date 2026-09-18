# remito

Entra la foto de un comprobante de compra de kiosco. Sale la mercadería cargada con su costo,
o el motivo por el cual no se puede cargar.

Lo difícil no es leer la foto: eso hoy lo hace cualquier modelo. Lo difícil es **saber cuándo
lo leyó mal**, y negarse. Este repositorio es sobre eso.

## Qué corre hoy

```
docker compose run --rm remito demo
```

Sin API keys, sin red, sin configurar nada. Toma una factura real de un kiosco de San Clemente
del Tuyú, la rompe de tres maneras distintas, y muestra cuál entra y cuál va a revisión humana
con el motivo.

Sin Docker, con Python 3.12 o más nuevo:

```
PYTHONPATH=src python -m remito demo
```

Los tests:

```
python -m pytest
```

## Lo que todavía NO hay

No hay lectura de fotos. No hay modelo. No hay base de datos. No hay interfaz.

Lo que hay es el núcleo aritmético que después va a poder vetar al modelo, y el generador de
comprobantes de prueba que sirve para medirlo. El orden es deliberado: las cuentas que deciden
si un número entra se escriben antes que el que propone los números.

`LIMITES.md` tiene la lista completa de lo que esto no hace, separando lo que es una decisión
tomada de lo que todavía no se midió.

## El hallazgo que justifica el proyecto

La factura de P01 del 17/09/2026 es legítima, tiene CAE, y **no cierra contra sus propias
partes impresas**:

```
38.068,23 (neto) + 609,09 (perc. IIBB) + 7.994,33 (IVA 21%) = 46.671,65
TOTAL impreso                                               = 46.671,64
```

Un centavo. El validador obvio —"si las líneas no suman el total, rechazar"— manda a revisión
humana el 100% de los comprobantes de ese proveedor, el primer día, para siempre.

Lo que sí cierra exacto es la suma de las líneas contra el **SUB-TOTAL**, y la suma de unidades
contra el campo `Unidades` del pie. Ésos son los dos vetos duros, y son dos porque una línea de
mercadería sin cargo no mueve la plata pero sí mueve el conteo.

Está medido en `CRITERIOS.md` §3, con la tabla línea por línea.

## Cómo está armado

| | |
|---|---|
| `src/remito/plata.py` | Centavos enteros. Nunca float. El parser levanta excepción antes que adivinar un importe |
| `src/remito/validacion.py` | Los cuatro chequeos, con tolerancias distintas y su medición al lado |
| `src/remito/sintetico.py` | Comprobantes inventados con la respuesta conocida, degradados como una foto de celular |
| `src/remito/cli.py` | La demo |
| `CRITERIOS.md` | Los criterios, congelados con su sha256 **antes** de tener el conjunto de datos |
| `LIMITES.md` | Lo que no hace, incluido lo que contradice la tesis del proyecto |
| `docs/adr/` | Las decisiones, incluida una revertida el mismo día |

El congelado se comprueba así, y el hash tiene que dar:

```
sha256sum -c CRITERIOS.sha256
```

## Por qué "remito" si el documento es una factura

Porque en el kiosco el papel que trae el fletero se llama remito, aunque diga FACTURA arriba.
La de P01 trae `Remito N° 114727` como campo adentro: el mismo papel es el comprobante
fiscal y el que acompaña la mercadería.

El vocabulario del repositorio es el del mostrador —remito, descuadre, maña del proveedor,
bulto— y no el de un manual.
