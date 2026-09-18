# RUNBOOK

Qué hacer cuando algo sale mal. Cada situación arranca con el síntoma como lo ve una persona,
no con el nombre técnico de la causa.

La bitácora está en `remito.jsonl`, o donde diga `REMITO_BITACORA`. Una línea JSON por evento.
Cada comprobante procesado tiene un identificador como `0918-k3f2` que se imprime en pantalla al
procesarlo, y que ata todos sus eventos.

```
python -c "import sys, json; [print(json.dumps(a, ensure_ascii=False)) for a in __import__('remito.bitacora', fromlist=['x']).hilo_de('remito.jsonl', sys.argv[1])]" 0918-k3f2
```

---

## "Esta factura quedó en revisión y no sé por qué"

Es la pregunta para la que existe todo esto.

1. Buscá el identificador. Si no lo tenés, está en la bitácora por fecha y por archivo:
   `grep '"archivo"' remito.jsonl`.
2. Sacá el hilo con el comando de arriba. El evento `a_revision` trae el campo `motivos`, que es
   la lista de vetos con el texto completo.
3. Los motivos dicen números, no códigos. `las líneas suman 31.952,99 y el SUB-TOTAL impreso
   dice 38.068,23 (faltan 6.115,24)` quiere decir que falta una línea de $6.115,24.

**Lo que suele ser.** Casi siempre la foto no muestra todo el papel: la segunda hoja tapando un
renglón, o el encuadre cortado. Sacá otra foto con las hojas separadas y volvé a procesar. El
veto de `unidades` ayuda a saber cuántos bultos faltan.

**Si los números del papel efectivamente no cierran**, no es un problema del sistema: es un
problema con el proveedor y hay que llamarlo. Eso es lo que el veto está para descubrir.

---

## "Este proveedor me frena TODAS las facturas por un centavo"

Es una maña del proveedor, no un error. Ver `ESTADO.md` R8.

1. Confirmá que el desvío es siempre el mismo y siempre chico. Mirá tres o cuatro facturas
   distintas del mismo proveedor en la bitácora.
2. Registrala con `guardar_desvio`, indicando **quién** la confirmó y **cuándo**. Esos dos campos
   no son burocracia: alguien va a tener que defender esa decisión frente a un contador.
3. A partir de ahí ese proveedor deja de frenar por ese chequeo y por esa tolerancia. Todo lo
   demás sigue igual, y los otros proveedores no se aflojan.

**No subas la tolerancia general.** Aflojar para todos por culpa de uno deja pasar errores reales
en los otros ocho.

---

## "El sistema aprobó algo que estaba mal"

El peor caso, y el único que no tiene tolerancia. `CRITERIOS.md` §4.

1. **Anotá el identificador y el `id_unico` del comprobante antes de tocar nada.**
2. Sacá el hilo completo de la bitácora y guardalo aparte.
3. Buscá el documento en `LIMITES.md`. Si cae en la sección 1 —la foto se comió el total y el
   lector lo inventó sumando las líneas— es un límite conocido y escrito, no un bug nuevo.
4. Si **no** cae en ninguna sección de `LIMITES.md`, es un descubrimiento: hay un modo de falla
   que nadie previó. Va a `LIMITES.md` con su medición y a `ESTADO.md` como sección nueva, antes
   de arreglarlo.
5. Para sacarlo de la base: `DELETE FROM comprobante WHERE id_unico = ?`. Las líneas se van solas
   por `ON DELETE CASCADE`. **Ojo:** el historial de precios cambia al borrar, así que las
   alertas de aumento de ese producto se recalculan.

---

## "Cargué la misma factura dos veces"

No pasa nada, y eso está probado. La clave primaria de la tabla lo impide: la segunda carga
devuelve `ya_estaba` y no duplica la mercadería. Lo vas a ver en la bitácora como
`"evento": "cargado", "resultado": "ya_estaba"`.

Si ves mercadería duplicada de verdad, **no es el mismo comprobante**: son dos comprobantes
distintos del mismo proveedor con el mismo contenido, o el número se leyó mal. Compará los
`id_unico`.

---

## "Dice que un producto aumentó y no aumentó"

Tres causas, en orden de probabilidad:

1. **Se comparó un comprobante A contra uno B o C.** El B trae el IVA adentro del precio, así que
   la comparación inventa un 21% que no ocurrió. `LIMITES.md` §2 dice que esto no debería pasar
   nunca; si pasó, es un bug y hay que anotarlo.
2. **El aumento es real pero diminuto**, del orden de centésimas de por ciento. No hay umbral
   mínimo todavía y el motivo está escrito: elegirlo sin historial real sería inventar un número.
   `LIMITES.md` §11.
3. **Cambió la unidad de venta.** El mismo código a veces viene por bulto y a veces por unidad.
   El sistema compara costo por unidad, así que esto no debería confundirlo, pero si el papel
   dice "5" queriendo decir "5 bultos de 12", el costo unitario que calcula está mal y no hay
   forma de que lo sepa.

---

## "No se pudo leer la foto"

El comando devuelve código 2 y el evento queda como `ilegible`. **Es la respuesta correcta**, no
una falla: el sistema prefiere no leer antes que inventar un número.

Sacá otra foto. Lo que más ayuda, en orden: que entre el papel entero incluida la tira de
totales, que las dos hojas estén separadas, y que no haya sombra encima de la columna de precios.

Hoy, además, hay un límite grande y medido: **T0 no lee fotos reales todavía.** Lee bien el pie y
falla en las columnas de plata. `LIMITES.md` §13. Si estás procesando fotos reales, esperá que
eso esté resuelto.

---

## "Quiero saber si el sistema procesó algo anoche"

```
grep '"evento": "cerrado"' remito.jsonl | tail -20
```

Un comprobante cuyo último evento es `abierto` y nada más significa que el proceso murió sin
llegar a cerrar: se cortó la luz, lo mataron, o algo reventó tan feo que ni el bloque de cierre
corrió. Si reventó de forma normal, hay un evento `reventó` con el tipo de error.

---

## "La bitácora creció mucho"

Son líneas de texto: unos cientos de bytes por comprobante. Un kiosco que carga treinta
comprobantes por día escribe unos pocos megabytes por año.

Si igual hay que achicarla, **no la borres: partila por mes** y guardá las viejas. Es el único
registro de por qué se aprobó cada cosa, y es lo que se mira cuando un número no cuadra tres
meses después.

---

## Lo que este RUNBOOK no cubre

No hay procedimiento de restauración de la base porque **no hay copias de seguridad
automáticas**. La base es un archivo SQLite; copiarlo es la copia. Que eso no esté automatizado
es una decisión de alcance, no un olvido: este repositorio es defendible, no operable.

No hay guardia, no hay alertas y no hay panel. Si el proceso no corre, nadie se entera hasta que
alguien va a cargar una factura.
