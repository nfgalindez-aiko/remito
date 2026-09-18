# Lo que esto no hace

Escrito mientras se construye, no al final. Cada entrada dice si es una decisión tomada, un
límite medido, o un límite que todavía no se midió. Las tres categorías son distintas y
mezclarlas sería mentir por omisión.

Al 18/09/2026 no hay ninguna medición sobre documentos reales todavía: sólo hay una factura
mirada, y está quemada en el bloque de exploración. Las entradas marcadas **sin medir** son
honestas sobre eso; no se van a llenar con números inventados para que la lista quede completa.

---

## 1. La validación aritmética no puede atrapar un número inventado — **límite real, medido en el diseño**

Es el límite más importante del proyecto y contradice su propia tesis, así que va primero.

Si la foto se comió la tira de totales y el modelo, en vez de decir "no está", inventa un total
sumando las líneas que sí vio, ese número **cierra perfecto contra el SUB-TOTAL y pasa los dos
vetos**. Ningún chequeo de consistencia interna puede verlo: es consistente por construcción.

La tesis del proyecto es que las cuentas deterministas pueden vetar al modelo. En este caso no
pueden. La única defensa posible es que el extractor conteste "no está" en vez de un número, y
eso es una propiedad del modelo, no de la aritmética.

Está implementado como caso de certificación (`sintetico.caso_fuga`, `CRITERIOS.md` §7 caso 3).
Cuánto pasa en la práctica: **sin medir**, porque todavía no hay extractor.

## 2. No compara precios entre comprobantes de distinto tipo — **decisión**

Un comprobante A lleva los precios netos y un B los lleva con el IVA adentro. Comparar el precio
de un A contra el de un B da un aumento del 21% que nunca ocurrió.

El sistema sólo compara neto contra neto del mismo tipo de comprobante. Si un proveedor cambia
de A a B, la serie de precios de ese proveedor **se corta**, y la alerta de aumento no dice nada
en vez de decir algo falso. Se prefiere el silencio al número mentiroso.

## 3. El costo es el neto, y eso vale sólo para un Responsable Inscripto — **decisión**

El IVA es crédito fiscal y la percepción de IIBB es pago a cuenta: ninguno de los dos es costo de
reposición. Para un Monotributista sería al revés, el IVA sí es costo, y todos los números de
costo de este sistema estarían mal.

No hay una opción de configuración para eso. El sistema asume Responsable Inscripto y no
pregunta. Si alguna vez hace falta lo otro, es un cambio de modelo de datos, no un `if`.

## 4. El precio unitario impreso se ignora para costear — **decisión, con medición**

En la factura P01 2026-09-17, cuatro de seis líneas tienen `precio impreso × cantidad ≠ subtotal
impreso`, por uno o dos centavos. El proveedor liquida con más decimales de los que imprime.

El costo autoritativo sale del subtotal con su cantidad, nunca del precio impreso. Consecuencia:
**el sistema no puede reportar un costo unitario exacto en centavos**, porque no existe: el costo
real de una unidad de KOKIS MEMBRILLITO era 1.981,7367 pesos. Lo que se muestra en pantalla es un
redondeo para mirar, y las comparaciones se hacen sin dividir.

## 5. No lee el QR de AFIP — **decisión consciente, no omisión**

El QR de una factura electrónica trae el tipo, el número, la fecha, el CUIT y el total, firmados.
Leerlo daría los totales gratis, sin modelo y sin error.

No se lee **a propósito**. Todo el proyecto existe para medir si la validación determinista puede
rescatar una extracción poco confiable; leer el QR cortocircuita justo eso y dejaría un sistema
que anda pero que no prueba nada. En un producto de verdad sería lo primero que habría que hacer,
y esa es exactamente la diferencia entre un producto y esto.

## 6. Una sola hoja por documento, dos como mucho — **decisión**

Los remitos de tres hojas o más quedan afuera. No es una limitación técnica profunda: es que no
hay ninguno en el conjunto de datos y no se construye para un caso que no se puede medir.

## 7. No maneja notas de crédito ni devoluciones — **decisión**

Un contraasiento por mercadería devuelta no entra. El stock que carga este sistema sólo sube.

## 8. Cantidades enteras solamente — **decisión**

Todo se cuenta en unidades enteras. Un remito de fiambrería con 1,5 kg de queso no entra. En un
kiosco casi todo viene en bultos y unidades, así que el caso no aparece en el conjunto de datos.

## 9. Los números escritos a mano son ruido — **decisión**

La factura P01 tiene un "6" arriba a la izquierda y un "2" en el medio, puestos a mano por
alguien. No se extraen y no se interpretan. Si un proveedor escribiera a mano una corrección de
precio sobre el papel, este sistema la ignoraría y cargaría el precio impreso.

## 10. Cuánto aguanta antes de romperse — **sin medir**

No hay número todavía. Lo que se va a medir, en este orden:

- A partir de qué mala calidad de foto el sistema deja de poder leer, y si en ese punto se
  **niega** o **inventa**. Lo segundo es el fracaso, no lo primero.
- Cuántos comprobantes por corrida entran en el tope de gasto en dólares.
- Cuántas líneas por documento soporta antes de que la extracción se degrade.
- Cuántos proveedores distintos toleran los prompts antes de necesitar uno por proveedor.

Hasta que existan esos números, esta sección dice "sin medir". No dice "escala bien".

## 11. La alerta de aumento no tiene umbral mínimo — **decisión pendiente, a propósito**

`aumento_de` informa cualquier suba, por chica que sea. Hoy eso incluye subas de una
diezmilésima, que en pantalla se leen "0,00%" y son ruido.

Falta elegir a partir de qué porcentaje vale la pena avisar. **No está elegido todavía, y no se
va a inventar**: ese número sale de mirar el historial de precios real del kiosco y ver cuánto
se mueven los precios entre entregas normales. Hoy no hay historial, así que cualquier umbral
sería uno de los que eligen los modelos —5, 10, 30— sin nada detrás.

Mientras tanto la función informa todo y el que llama decide. Cuando exista el historial, el
umbral se elige con él y se escribe con su medición al lado.

## 12. La degradación sintética no es una foto de un teléfono barato — **limitación del método**

El generador ensucia imágenes limpias con rotación, sombra y desenfoque. Eso sirve para ordenar
casos de más fácil a más difícil, pero **no** modela el sensor de un teléfono barato: el ruido, la
compresión y el color son distintos.

Cualquier número que salga de imágenes degradadas por código es un orden de magnitud, no una
medición de la vida real. Lo que se mide de verdad se mide sobre fotos de verdad.

## 13. El conjunto de datos es de un solo kiosco, de un solo partido — **limitación del método**

Entre 40 y 100 comprobantes, de los proveedores que le venden a un kiosco de San Clemente del
Tuyú. Distribuidoras de golosinas, mayormente. No hay farmacia, no hay corralón, no hay
gastronomía, no hay importado.

Un resultado bueno acá no dice nada sobre un remito de repuestos de auto. El bloque virgen
reserva al menos dos proveedores enteros justamente para tener alguna evidencia de generalización,
pero dos proveedores nuevos son dos, no una muestra.

## 14. El bloque virgen alcanza para distinguir "anda" de "está roto", nada más — **límite calculado**

Con doce a veinte documentos en el bloque virgen, el intervalo de confianza al 95% sobre la
proporción de documentos correctos mide entre 30 y 40 puntos de ancho. Aun con un 100% de
aciertos sobre quince documentos, la cota inferior honesta es 79,6%.

Eso quiere decir que este conjunto de datos **no puede** distinguir un 88% de un 93%, y que
cualquier comparación entre dos métodos necesita una diferencia mayor a 30 puntos para no ser
ruido. Está calculado en `CRITERIOS.md` §5, antes de medir nada, y por eso los umbrales de éxito
son anchos: prometer precisión fina con este n sería mentir.
