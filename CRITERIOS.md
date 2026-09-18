# CRITERIOS

Documento congelado. Escrito **antes** de tener el conjunto de datos, para que no se pueda
acomodar el criterio después de ver el resultado. Su sha256 y su fecha están en
`CRITERIOS.sha256` y en el commit que lo introduce.

Si algo de acá abajo resulta mal elegido, **no se edita este archivo**: se escribe un
`CRITERIOS-02.md` que diga qué cambia y por qué, y este queda como está. Un criterio que se
puede editar después del resultado no es un criterio.

---

## 0. Lo único que se miró antes de escribir esto

Un (1) documento: proveedor `P01`, 17/09/2026, Factura A de 6 líneas, fotografiado con
celular sobre una mesa, con la segunda hoja superpuesta tapando parte de la primera.

Ese documento queda **asignado de por vida al bloque de exploración**. No puede aparecer en
entrenamiento ni en el bloque virgen. Escribir los criterios habiendo visto un documento no
es neutral, y la forma honesta de manejarlo es quemarlo, no negarlo.

Nada más se miró. Ni el resto de los papeles, ni ninguna medición.

---

## 1. La pregunta, con horizonte explícito

> Dada **una foto de celular de un comprobante de compra de kiosco** (factura A/B/C o remito,
> una o dos hojas, tomada en condiciones reales: torcida, con sombra, con hojas
> superpuestas), ¿se pueden extraer las líneas y los totales con exactitud suficiente para
> **cargar stock y costo sin que un humano reescriba los números**, y detectar de forma
> confiable los casos en que no se puede?

Dos mitades, y la segunda importa más que la primera: un sistema que extrae al 85% y **sabe
cuál es el 15%** sirve; uno que extrae al 95% y no sabe cuándo se equivocó, no.

**Horizonte**: un documento, de punta a punta, en una sola pasada. No se mide "el campo
proveedor aislado"; se mide el documento como unidad de trabajo, porque la unidad de trabajo
del kiosco es el documento.

**Lo que NO es la pregunta** (se escribe ahora para no correrse después): no es clasificar
documentos, no es OCR genérico, no es conciliar contra el banco, no es predecir precios
futuros.

---

## 2. El baseline trivial a batir

**Baseline T0 — OCR sin modelo.** Tesseract sobre la foto + reglas y expresiones regulares
escritas a mano contra los layouts del bloque de exploración. Cero LLM, cero API, costo cero.

Este es el baseline que casi ningún repo de extracción se molesta en construir, y es el que
decide si el modelo se gana el lugar. Un modelo que le gana a T0 por poco no justifica ni la
latencia ni el gasto ni la no-determinación, y en ese caso el proyecto honesto es un parser
determinista con el modelo como respaldo, no al revés.

**Baseline T1 — el humano.** Tiempo de carga manual del mismo documento, cronometrado sobre
el bloque de exploración. Si el sistema no le gana al humano en tiempo total *incluyendo la
revisión de lo que el sistema marcó como dudoso*, no hay producto. Este número se mide una
vez, con cronómetro, y se escribe con la fecha.

**Baseline T2 — el modelo pelado.** El modelo sin validación determinista encima. Existe para
medir cuánto aporta la validación, que es la tesis central del proyecto. Si la validación no
mueve la aguja, la tesis está mal.

---

## 3. Las reglas de plata, con su medición

Todo en **enteros de centavos**. Nunca float. Las tres tolerancias de abajo son distintas a
propósito: cada una tiene la evidencia que la justifica. Una tolerancia uniforme en los tres
lugares sería una plantilla, no una decisión.

### 3.1 Línea: `precio_unitario × cantidad` contra el subtotal impreso — **tolerancia amplia**

Medido en `P01 2026-09-17`, 6 líneas:

```
1825   q=5    737,61 x 5 =  3.688,05   impreso  3.688,05   dif  0
15004  q=3  1.981,74 x 3 =  5.945,22   impreso  5.945,21   dif -1
15001  q=3  1.981,74 x 3 =  5.945,22   impreso  5.945,21   dif -1
3398   q=5  1.870,63 x 5 =  9.353,15   impreso  9.353,15   dif  0
2920   q=5  1.404,27 x 5 =  7.021,35   impreso  7.021,37   dif +2
1661   q=5  1.223,05 x 5 =  6.115,25   impreso  6.115,24   dif -1
```

El precio unitario impreso es un **redondeo de presentación**. El sistema del proveedor
liquida con más decimales de los que imprime: el subtotal de la línea 15004 dividido 3 da
1981,7367, no 1981,74.

Cota derivada: si el precio real redondea al impreso con error ≤ 0,005, entonces
`|subtotal_impreso − precio_impreso × q| ≤ 0,005·q + 0,005`.

    tolerancia_linea_centavos = ceil(0.5 * cantidad) + 1

Para q=5 da 4 centavos; el peor desvío observado fue 2. La cota es conservadora a propósito:
está derivada del mecanismo, no ajustada al dato.

**Consecuencia que manda en todo lo demás:** el costo unitario autoritativo es
`subtotal_línea ÷ cantidad`, **no** el precio unitario impreso. Quien use el precio impreso
para la alerta de aumento va a reportar aumentos de un centavo que no existen.

### 3.2 Suma de líneas contra el SUB-TOTAL impreso — **tolerancia CERO**

Medido: las 6 líneas suman 38.068,23 y el SUB-TOTAL impreso es 38.068,23. Exacto.

Este es el **veto duro**. Si no da exacto, el documento no se aprueba y va a cola de revisión
humana, sin importar qué tan seguro esté el modelo. Es el chequeo que detecta la línea tapada
por la segunda hoja superpuesta, que es el modo de falla que motivó el proyecto.

### 3.3 Segundo veto independiente: suma de `UNID` contra el campo `Unidades`

Medido: 5+3+3+5+5+5 = 26, y el pie dice `Unidades: 26`.

Detecta lo mismo que 3.2 por otro camino. Se mantienen los dos: si una línea tapada tuviera
subtotal cero, 3.2 no la vería y este sí.

### 3.4 TOTAL contra sus componentes impresos — **tolerancia 1 centavo, y no es negociable**

```
38.068,23 (neto) + 609,09 (perc. IIBB) + 7.994,33 (IVA 21%) = 46.671,65
TOTAL impreso                                               = 46.671,64
                                                         dif = 1 centavo
```

**Una factura A real, con CAE válido, no cierra contra sus propios componentes impresos.**

`PLAN.md` punto 2 dice "si las líneas no suman el total impreso, no se aprueba". Aplicado a
la letra, ese criterio rechaza este documento legítimo y manda a revisión humana el 100% de
los comprobantes de este proveedor. Queda corregido acá: el veto duro es contra el
**SUB-TOTAL** (3.2, exacto), no contra el **TOTAL**.

Verificado además: IVA = neto × 0,21 con redondeo half-up da exacto (7.994,3283 → 7.994,33), y
la percepción de IIBB es 1,6000% del neto exacto. O sea que el centavo no está ni en el IVA ni
en la percepción: está en cómo el proveedor arma el total final. No sabemos por qué. Se
banca, se documenta, y se revisa si aparece un desvío mayor a 1 centavo en otro documento.

### 3.5 Qué es "costo" para el kiosco

El destinatario es Responsable Inscripto: el IVA es crédito fiscal y la percepción de IIBB es
pago a cuenta. **Ninguno de los dos es costo.** El costo de reposición es el **neto**.

Corolario que va a `LIMITES.md`: **está prohibido comparar precios entre un comprobante A y uno
B/C**, porque el B trae el IVA adentro del precio. Comparar A contra B produce un "aumento del
21%" que no ocurrió. La alerta de aumento sólo compara netos contra netos del mismo tipo de
comprobante.

---

## 4. Los números que deciden sí y los que deciden no

Todo se mide **una sola vez**, sobre el bloque virgen, al final.

### Métrica primaria — exactitud a nivel campo, con bootstrap agrupado por documento

Se cuenta cada valor extraído como acierto o error contra la etiqueta humana. El intervalo de
confianza se calcula con **bootstrap remuestreando documentos enteros**, no campos sueltos: los
errores se agrupan por foto (una foto mal sacada arruina el documento completo), así que tratar
600 campos como 600 observaciones independientes daría un intervalo falsamente angosto. Es el
mismo problema que el n efectivo en series autocorrelacionadas, con otro disfraz.

### Métrica operativa — documentos correctos de punta a punta

Todos los campos bien, sin excepción. Es el número que le importa al kiosco y el que se reporta
primero, con su intervalo completo aunque sea ancho.

### Métrica de seguridad — la que más pesa

De los documentos que el sistema **aprobó sin intervención humana**, cuántos tenían algún error
de plata. **El criterio es cero, y no tiene tolerancia estadística.** Un solo documento
aprobado con un número de plata mal es un fracaso del proyecto, se reporta como tal, y no se
compensa con exactitud alta en otro lado. Es la única métrica donde no se negocia el umbral.

### Se declara ÉXITO si, y sólo si, las cuatro:

| # | Condición | Umbral |
|---|---|---|
| A | Documentos aprobados automáticamente con error de plata | **0** |
| B | Exactitud a nivel campo, cota inferior del IC 95% | **≥ 90%** |
| C | Ventaja sobre el baseline T0 (OCR+regex) a nivel campo | **> 25 puntos** |
| D | Documentos que el sistema manda a revisión humana | **< 40%** |

D existe para cerrar la salida fácil: un sistema que manda todo a revisión cumple A
trivialmente y no sirve para nada.

### Se declara FRACASO, y se escribe con esa palabra, si:

- El baseline T0 queda a menos de 25 puntos. El modelo no se ganó el lugar. El entregable pasa
  a ser un parser determinista y se dice por qué en `LIMITES.md`.
- Algún documento aprobado automáticamente tiene un número de plata mal. Sin importar el resto.
- El sistema no le gana al humano (T1) en tiempo total con revisión incluida.
- El intervalo de confianza de la métrica primaria contiene al baseline.

### Se declara NO CONCLUYENTE si:

El resultado cae adentro del margen que el n no alcanza a resolver (sección 5). "No concluyente"
se publica igual, con esa palabra. No se redondea para arriba.

---

## 5. n efectivo y efecto mínimo detectable

Documentos disponibles declarados: **entre 40 y 100**. N exacto se conoce al terminar de
fotografiar; la **regla de partición se fija ahora**, antes de saberlo, y no se toca después.

Poder calculado (Wilson 95% sobre proporción de documentos correctos):

```
n=12:  12/12 aciertos -> cota inferior 75,8%   |  10/12 -> [55,2% , 95,3%]
n=15:  15/15 aciertos -> cota inferior 79,6%   |  12/15 -> [54,8% , 93,0%]
n=20:  20/20 aciertos -> cota inferior 83,9%   |  16/20 -> [58,4% , 91,9%]
n=25:  25/25 aciertos -> cota inferior 86,7%   |  20/25 -> [60,9% , 91,1%]
```

Y para comparar dos métodos sobre el mismo bloque virgen (McNemar aproximado):

```
n=15: hace falta una diferencia mayor a 39 puntos para llamarla real
n=20: hace falta una diferencia mayor a 34 puntos para llamarla real
n=25: hace falta una diferencia mayor a 30 puntos para llamarla real
```

**Consecuencia declarada por adelantado, y es incómoda:** con este n, la métrica a nivel
documento **no puede** distinguir un 88% de un 93%. Sólo distingue "anda" de "está roto". Por eso
la métrica primaria es a nivel campo con bootstrap agrupado, y por eso el umbral C contra el
baseline es de 25 puntos y no de 5: un umbral de 5 puntos sería indetectable con este conjunto
de datos y prometerlo sería mentir.

Lo que **no** consume presupuesto estadístico, porque se prueba de forma exhaustiva y no
muestral:

- La **validación determinista** (sección 3): son tests unitarios sobre aritmética. Se prueban
  todos los casos, no una muestra.
- Los **12 documentos rotos a propósito**: cada uno es un test con nombre, con su resultado
  esperado. No es una medición, es una especificación.

---

## 6. Regla de partición — se fija ahora, se aplica sin mirar

El corte **no es aleatorio**. Un corte aleatorio pone el layout del mismo proveedor de los dos
lados y mide memorización de plantilla, no generalización.

**Bloque virgen B — proveedor nunca visto.** Al menos **2 proveedores completos** salen del
conjunto antes de cualquier otra cosa. Nadie los mira. Responden: ¿anda con un proveedor nuevo?

**Bloque virgen A — proveedor conocido, fecha posterior.** Dentro de los proveedores restantes,
corte temporal: los documentos más nuevos al virgen. Responden: ¿anda en producción con los de
siempre?

A y B se reportan **por separado y siempre**. Promediarlos esconde justamente la diferencia que
importa, y el número promediado no responde ninguna de las dos preguntas.

**Proporciones**: ~35% exploración, ~40% entrenamiento, ~25% virgen, con **piso de 12 documentos
en el virgen**. Si N no alcanza para el piso, se baja entrenamiento, nunca el virgen.

**Embargo.** El equivalente temporal acá es el precio: la alerta de aumento usa el historial de
precios del mismo producto. Ese historial sólo puede incluir documentos de fecha anterior al
corte. Un precio "anterior" que salió de un documento del bloque virgen es fuga.

**Todo lo que se ajusta con datos** —prompts, umbrales de confianza, tolerancias, listas de
sinónimos de productos, normalización de nombres de proveedor— se ajusta **sólo con
exploración + entrenamiento**. Una lista de productos que se armó mirando el virgen es fuga, y
es la fuga más fácil de cometer sin darse cuenta.

**El virgen se consume.** Se abre una vez. Si se mira dos veces, el proyecto pasa a llamarse
exploratorio, con esa palabra, en el README, hasta que existan documentos nuevos por el paso
del tiempo.

---

## 7. Certificación del instrumento — antes de medir nada real

No se mide un documento real hasta que el medidor esté certificado con tres casos de respuesta
conocida:

1. **Con señal.** Comprobante sintético generado con valores conocidos, renderizado a imagen y
   degradado a propósito (rotación, sombra, desenfoque, hoja superpuesta). El medidor tiene que
   recuperar los valores que le pusimos.
2. **Sin señal.** Una foto que no es un comprobante. El sistema tiene que decir que no lo es,
   no extraer campos igual.
3. **El caso de fuga — el que más importa.** Un comprobante con el TOTAL recortado fuera del
   encuadre. El sistema tiene que responder **"no está"**, no inventar un número plausible. Un
   número inventado que casualmente cierra con las líneas es el peor error posible del sistema,
   porque pasa la validación.

Si el instrumento no pasa los tres, no se mide nada real hasta arreglarlo.

---

## 8. Lista completa de hipótesis a probar — este es el denominador

Cada variante evaluada sobre el bloque de entrenamiento es una comparación. Elegir la mejor de
muchas y después reportarla sin corregir es el sesgo del ganador.

**Tope declarado: 12 variantes.** Si hacen falta más, se escribe por qué en `CRITERIOS-02.md`
antes de correr la número 13, no después.

1. T0 — OCR + regex, sin modelo.
2. T1 — carga manual cronometrada.
3. T2 — modelo pelado, sin validación.
4. Modelo + validación determinista (la tesis).
5. Modelo con el layout del proveedor como contexto vs. sin él.
6. Una pasada vs. dos (extraer, y después releer sólo lo que no cerró).
7. Resolución de imagen: original vs. reducida. Contra el tope de gasto.
8. Preprocesado de imagen (enderezar, contraste) vs. foto cruda.
9. Umbral de confianza para mandar a revisión humana: se barre, se elige en entrenamiento.
10. Modelo chico vs. modelo grande. Contra el tope de gasto.
11. Prompt con ejemplos del propio proveedor vs. genérico.
12. Reserva sin asignar, para lo que aparezca. Se escribe cuándo y por qué se usó.

---

## 9. Qué haría abandonar la hipótesis

La hipótesis es: *la validación determinista sobre la salida del modelo convierte una
extracción poco confiable en un sistema utilizable, y el conocimiento del oficio es lo que
define bien las validaciones.*

Se abandona si:

- La validación **no filtra nada**: los errores del modelo pasan los chequeos aritméticos.
  Sería el caso si los errores fueran de copiado consistente (copia mal el precio y mal el
  subtotal, de forma coherente). Se mide directamente: de los documentos con error, qué
  porcentaje fue atrapado por la validación.
- La validación **filtra todo**: manda más del 40% a revisión humana y no hay producto.
- El baseline T0 llega igual de lejos.

Si ninguno de estos tres resultados fuera posible, la hipótesis no sería refutable y habría que
reescribirla. Los tres son posibles.

---

## 10. Qué queda explícitamente afuera

- Conciliar el comprobante contra el pago o el banco.
- Comprobantes que no sean de compra a proveedor.
- Manuscritos. Los números escritos a mano sobre el papel (este documento tiene un "6" y un "2")
  se tratan como ruido y **no se extraen**.
- El QR de AFIP. Leerlo daría los totales gratis y sería lo correcto en un producto, pero
  cortocircuita justamente lo que este proyecto quiere medir. Queda anotado como decisión
  consciente, no como omisión, y va a `LIMITES.md`.
- Más de dos hojas por documento.
- Notas de crédito.

---

## 11. Datos personales

CUIT, razón social, domicilio y código de cliente del **destinatario** se tapan antes de que la
foto entre al repositorio. El mapeo entre el identificador público (`P01`, `P02`, ...) y el
proveedor real vive en un archivo local que está en `.gitignore` y nunca se commitea.
