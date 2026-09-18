# remito

[![tests](https://github.com/nfgalindez-aiko/remito/actions/workflows/tests.yml/badge.svg)](https://github.com/nfgalindez-aiko/remito/actions/workflows/tests.yml)

**Un validador determinista que puede vetar a un modelo. Escrito antes que el modelo, a
propósito.**

El problema es una foto de celular de un comprobante de compra de kiosco —torcida, con sombra,
con la segunda hoja tapando parte de la primera— que tiene que terminar en mercadería cargada
con su costo. Leer la foto hoy lo hace cualquier modelo. Lo difícil es **saber cuándo la leyó
mal, y negarse a cargarla.**

Este repositorio es la mitad que se niega. El que lee la foto todavía no existe: se escribe
después, y se escribe contra estas reglas.

## El resultado que más importa, y contradice la tesis

Se catalogaron doce formas reales de que un comprobante entre mal. El reparto, verificado rotura
por rotura en `tests/test_roturas.py`:

| | |
|---|---|
| **6 de 12** | las frena la aritmética |
| **5 de 12** | la lectura sale **consistente consigo misma y equivocada**: pasa los cuatro chequeos |
| **1 de 12** | sin defensa posible |

Las cinco del medio son todas la misma familia: si quien lee la foto no ve la tira de totales,
la arma sumando lo que sí vio. Le cierra —la calculó de ahí— y entra a la base siendo falsa.
**Ninguna cuenta puede ver eso**, porque es consistente por construcción.

La tesis del proyecto es que la validación determinista puede vetar al modelo. Cubre la mitad.
Está primero en `LIMITES.md` y no en un anexo.

## Qué corre hoy

```
docker compose run --rm remito demo
```

Sin API keys, sin red, sin configurar nada. Toma una factura real de un kiosco de San Clemente
del Tuyú, la rompe de tres maneras, y muestra cuál entra al stock sola y cuál va a revisión
humana con el motivo. Después la carga dos veces para mostrar que la segunda no duplica la
mercadería.

**79 segundos** desde ese comando hasta la salida. Medido el 18/09/2026 en una máquina a la que
se le borró la imagen base y la caché de build antes de cronometrar. Eran 73 antes de que la
imagen incluyera Tesseract, que es el baseline sin modelo.

Los tests, adentro de la misma imagen:

```
docker compose run --rm tests
```

Sin Docker, con Python 3.12 o más nuevo, `pip install pillow pytesseract pytest` y el binario
de Tesseract (`apt-get install tesseract-ocr tesseract-ocr-spa`). Sin Tesseract corre todo menos
los tests del baseline, que se saltean diciendo qué falta:

```
PYTHONPATH=src python -m remito demo
python -m pytest
```

## Lo que NO hay, dicho antes de que lo descubras

**No lee fotos.** No hay modelo, no hay OCR, no hay una sola llamada a una API. La demo trabaja
sobre una factura transcripta a mano, con cada importe impreso al lado de su valor en centavos:
`src/remito/datos/p01-2026-09-17.json`.

**No hay interfaz**, ni la va a haber. **No hay evals con casos reales**, porque el conjunto de
fotos todavía no existe. **No hay ningún número de exactitud**, y `LIMITES.md` dice "sin medir"
con esas palabras en vez de llenarse de estimaciones.

Lo que sí hay: las cuentas que deciden si un número entra, la base que impide cargar dos veces
el mismo papel, un generador de comprobantes de prueba con la respuesta conocida, y el catálogo
de las doce roturas.

El orden es deliberado. El que juzga se escribe antes que el que propone, porque escribirlo
después es escribirlo para que apruebe lo que el modelo ya devuelve.

## Por qué las tolerancias son distintas en cada chequeo

La factura de P01 del 17/09/2026 es legítima, tiene CAE, y **no cierra contra sus propias partes
impresas**:

```
38.068,23 (neto) + 609,09 (perc. IIBB) + 7.994,33 (IVA 21%) = 46.671,65
TOTAL impreso                                               = 46.671,64
```

Un centavo. El validador obvio —"si las líneas no suman el total, rechazar"— manda a revisión
humana el 100% de los comprobantes de ese proveedor, el primer día y para siempre.

Lo que sí cierra exacto es la suma de las líneas contra el **SUB-TOTAL**, y la suma de unidades
contra el campo `Unidades` del pie. Ésos son los dos vetos duros. Son dos y no uno porque una
línea de mercadería sin cargo no mueve un peso pero sí mueve el conteo.

Y el precio unitario impreso está redondeado para mostrar: en cuatro de seis líneas,
`precio × cantidad` no da el subtotal impreso. El costo autoritativo sale del subtotal con su
cantidad, y las comparaciones se hacen multiplicando cruzado en vez de dividiendo, porque
dividir y redondear inventa aumentos de un centavo que nunca pasaron.

Todo medido en `CRITERIOS.md` §3, con la tabla línea por línea.

## Cómo está armado

| | |
|---|---|
| `src/remito/plata.py` | Centavos enteros. Nunca float, y hay un test que lo lee del árbol sintáctico. El parser levanta excepción antes que adivinar un importe |
| `src/remito/comprobante.py` | El comprobante tal como está impreso, no como debería estar |
| `src/remito/validacion.py` | Los cuatro chequeos, con tolerancias distintas y su medición al lado |
| `src/remito/base.py` | SQLite. Idempotencia por la clave primaria, no por un `if ya existe`, con un test de doce hilos |
| `src/remito/baseline.py` | T0: leer el comprobante sin modelo, con OCR y reglas. Es el baseline que decide si el modelo se gana el lugar |
| `src/remito/sintetico.py` | Comprobantes inventados con la respuesta conocida, degradados como una foto de celular |
| `src/remito/roturas.py` | Las doce roturas, cada una con quién la agarra |
| `src/remito/cli.py` | La demo |
| `CRITERIOS.md` | Los criterios, congelados con su sha256 **antes** de tener el conjunto de datos |
| `LIMITES.md` | Lo que no hace, empezando por lo que contradice la tesis |
| `docs/adr/` | Las decisiones, incluida una revertida el mismo día que se tomó |

Hay un test que falla si un módulo nuevo no aparece en esa tabla. Se agregó porque esta tabla ya
quedó desactualizada una vez, y porque un README que miente en un renglón no se cree en ninguno.

El congelado de los criterios se comprueba así, y el hash tiene que dar:

```
sha256sum -c CRITERIOS.sha256
```

## Por qué "remito" si el documento es una factura

Porque en el kiosco el papel que trae el fletero se llama remito, aunque diga FACTURA arriba. La
de P01 trae `Remito N° 114727` como campo adentro: el mismo papel es el comprobante fiscal y el
que acompaña la mercadería.

El vocabulario del repositorio es el del mostrador —remito, descuadre, maña del proveedor,
bulto— y no el de un manual.

## De dónde sale el oficio

Nicolás Galindez atendió un kiosco veintiún años. El centavo que no cierra, la segunda hoja que
tapa el total y el proveedor que factura distinto de lo que entrega no se deducen leyendo
documentación de AFIP.
