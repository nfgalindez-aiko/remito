# Estado de remito

Puente entre el chat que construye y el chat que busca trabajo. **Quien construye lo actualiza,
quien vende lo lee.** Si algo importante vive solo en una conversación, se pierde.

Las secciones numeradas no se reescriben ni se borran. Si algo resulta falso, se marca FALSO en
el título viejo y se corrige en una sección nueva que apunta a la vieja.

---

## 1. El proyecto en una pantalla

**Objetivo.** Entra la foto de un comprobante de compra de proveedor sacada con el celular. Sale
stock cargado, costo por producto, y alerta cuando un proveedor aumentó. No es un producto: es
la prueba de que Nicolás Galindez sabe trabajar, pensada para ganar una llamada de cuarenta
minutos donde un evaluador abre un archivo al azar y pregunta por qué esa línea.

**Tesis que se está probando.** La validación determinista sobre la salida del modelo convierte
una extracción poco confiable en un sistema utilizable, y el conocimiento del oficio es lo que
define bien las validaciones.

**Qué se puede mostrar hoy a un cliente:** nada todavía. No hay repo público, no hay URL, no hay
código. Hay criterios congelados y un hallazgo técnico real (sección 5).

| Frente | Estado | Nota |
|---|---|---|
| `PLAN.md` — qué construir y por qué | cerrado | Escrito 18/09/2026 |
| `CRITERIOS.md` — criterios congelados | **cerrado** | sha256 `7c99f2d8…7259`, 18/09/2026 |
| Conjunto de datos etiquetado | bloqueado | Falta fotografiar. Es el activo del proyecto |
| Esquema de etiquetado | en curso | Próximo paso. Sale de exploración |
| Baseline T0 (OCR+regex, sin modelo) | vía abierta | No se toca hasta tener datos |
| Validación determinista | vía abierta | Reglas ya especificadas en `CRITERIOS.md` §3 |
| `docker compose up` | bloqueado | **Docker no está instalado en la máquina** |
| Repo público | no | Sin commits todavía |

**Quién es quién.** Nicolás decide y aporta el oficio (21 años de kiosco) y los papeles. El
asistente hace el trabajo técnico. Los agentes, cuando se usen, sirven para **revisar y
criticar**, nunca para escribir el código: código escrito en paralelo sale parejo y ancho, que
es exactamente lo que los evaluadores dijeron que delata que nadie decidió.

---

## 2. Reglas

Corpus numerado. Se citan por número.

**R1 — El precio unitario impreso es un redondeo de presentación, no el precio.** El costo
unitario autoritativo es `subtotal_línea ÷ cantidad`. Medido: en 3 de 6 líneas del primer
documento, `precio × cantidad ≠ subtotal` por 1 a 2 centavos. Usar el precio impreso para la
alerta de aumento produce aumentos de un centavo que no existen.

**R2 — El veto duro va contra el SUB-TOTAL, nunca contra el TOTAL.** Una factura A real con CAE
válido no cierra contra sus propios componentes impresos por 1 centavo. La regla literal de
`PLAN.md` ("si las líneas no suman el total impreso, no se aprueba") rechazaría ese documento
legítimo. Corregida en `CRITERIOS.md` §3.4.

**R3 — Nunca comparar precios entre comprobante A y B/C.** El B trae el IVA adentro del precio.
La comparación produce un "aumento del 21%" que no ocurrió. Sólo neto contra neto, mismo tipo.

**R4 — Para un Responsable Inscripto, ni el IVA ni la percepción de IIBB son costo.** El costo de
reposición es el neto. El IVA es crédito fiscal, la percepción es pago a cuenta.

**R5 — Todo documento que se mira antes de congelar criterios queda quemado.** Se asigna de por
vida al bloque de exploración y no puede aparecer en entrenamiento ni en el virgen. La forma
honesta de manejar el sesgo es declararlo y pagarlo, no negarlo.

**R6 — El corte de datos es por proveedor y por fecha, nunca aleatorio.** Un corte aleatorio pone
el layout del mismo proveedor de los dos lados y mide memorización de plantilla, no
generalización.

**R7 — Los errores se agrupan por foto, no por campo.** 600 campos extraídos de 20 documentos no
son 600 observaciones independientes: una foto mal sacada arruina el documento entero. Los
intervalos se calculan con bootstrap remuestreando documentos.

**R8 — Las mañas del proveedor se aprenden una vez y se anotan. Idea de Nicolás, 18/09/2026.**
Cada proveedor tiene desvíos sistemáticos y legítimos: P01 redondea el total un centavo
para abajo. La primera vez que aparece, el documento va a revisión humana. Nicolás confirma que
es normal, y el desvío queda registrado como maña conocida de ese proveedor, con quién lo
confirmó y cuándo. A partir de ahí no vuelve a frenar un documento.

Lo que **no** está en la lista de mañas sigue siendo error. La lista no afloja el chequeo: lo
hace específico. Un sistema que afloja la tolerancia para todos los proveedores por culpa de uno
deja pasar errores reales en los otros ocho.

La lista de mañas se ajusta con datos, así que sólo puede crecer con documentos de exploración y
entrenamiento. Una maña aprendida mirando el bloque virgen es fuga (R6).

---

## 3. Pendientes

| Qué | Dueño | Por qué espera |
|---|---|---|
| Juntar y fotografiar los 40-100 comprobantes | Nicolás | Es el activo del proyecto; sin esto no hay nada |
| Tapar CUIT, razón social y domicilio del destinatario antes de que una foto entre al repo | Nicolás / asistente | `CRITERIOS.md` §11 |
| Instalar Docker Desktop | Nicolás | Requisito nº1 de los evaluadores; hoy no está en la máquina |
| Primer commit del repo | Nicolás | Comando dado; el commit es lo que le da fecha al congelado |
| Esquema de etiquetado | asistente | Sale del bloque de exploración, después de las fotos |
| Decidir si el proyecto se llama "remito" cuando el documento real es una factura | Nicolás | Afecta el vocabulario de todo el repo |

---

## 4. Sesión 18/09/2026 — arranque y método — CERRADA

Se leyeron `PLAN.md` y `ESTADO.md`. Se adoptó el método v2 del escritorio, adaptado: está escrito
para predicción sobre series de tiempo y acá el problema es extracción, pero las piezas
transfieren casi una a una (baseline trivial, certificación del instrumento, partición con
bloque virgen, n efectivo, adversario, el "no" escrito).

Decisiones tomadas:

- **Stack: Python.** Elegido por Nicolás sobre TypeScript. `Decimal` nativo, pytest, ecosistema de
  evals y visión.
- **Identidad de git configurada en el repo** (local, no global). Sin esto los commits salen con
  autor vacío y el historial —que es la evidencia principal para los evaluadores— no prueba nada.
- **Docker no está instalado.** Es el requisito que los nueve evaluadores pusieron primero.
- **Volumen declarado: entre 40 y 100 comprobantes.** Alcanza, con el bloque virgen justo. Las
  consecuencias estadísticas están calculadas y escritas en `CRITERIOS.md` §5.

Entregable: `CRITERIOS.md` congelado, sha256 `7c99f2d8016fad9f80ebb62d33dedb44412851e89c3e08e465407a5a5d877259`,
verificado con dos herramientas independientes.

---

## 5. Sesión 18/09/2026 — el primer documento rompe el plan — CERRADA

Nicolás mandó foto del comprobante "más complejo": proveedor `P01`, 17/09/2026, distribuidora de
golosinas de La Costa. Se transcribió a mano y se verificó la aritmética con código.

**Primer hallazgo: no es un remito, es una Factura A que oficia de remito.** Trae `Remito N°
114727` como campo adentro. El documento es a la vez el comprobante fiscal y el papel que
acompaña la mercadería. Esto afecta el vocabulario de todo el repo y está en pendientes.

**Segundo hallazgo — el que más vale: el TOTAL no cierra con sus propios componentes impresos.**

```
38.068,23 (neto) + 609,09 (perc. IIBB 1,6%) + 7.994,33 (IVA 21%) = 46.671,65
TOTAL impreso                                                    = 46.671,64
                                                             dif = 1 centavo
```

La regla literal de `PLAN.md` rechaza esta factura legítima. → R2.

**Tercer hallazgo: el precio unitario impreso está redondeado para mostrar.** En 3 de 6 líneas,
`precio × cantidad ≠ subtotal`, por 1 a 2 centavos. El subtotal de la línea 15004 dividido 3 da
1981,7367, no los 1981,74 que imprime el papel. → R1.

**Lo que sí cierra exacto**, y por eso es el veto duro: la suma de las 6 líneas contra el
SUB-TOTAL (38.068,23, dif 0), y la suma de `UNID` contra el campo `Unidades` (26 = 26). Son dos
chequeos independientes de líneas ocultas, que es el modo de falla que motivó el proyecto: en
esta misma foto la segunda hoja tapa parte de la primera.

**Verificaciones que descartan explicaciones aburridas:** el IVA es exactamente el 21% del neto
con redondeo half-up (7.994,3283 → 7.994,33, dif 0) y la percepción de IIBB es exactamente el
1,6000% del neto. El centavo que falta no está ni en el IVA ni en la percepción. No sabemos por
qué está. Se banca, se documenta, y se revisa si aparece un desvío mayor en otro documento.

Otras cosas que el documento enseña y que van al esquema de etiquetado: **tres formatos de fecha
distintos en el mismo papel** (`17/09/2026`, `17/9/2026`, `20260927`), números manuscritos encima
del papel que son ruido, `Hoja 1/1` como campo (puede ser 1/2), y un QR de AFIP que daría los
totales gratis pero que se decidió no leer porque cortocircuita lo que el proyecto quiere medir.

---

## 6. Cómo actualizar esto

Una sección nueva por sesión de trabajo, numerada correlativa, con fecha en el título y su
estado. La más nueva abajo. Las viejas no se tocan.

Lo que le sirve al chat que vende: qué se puede mostrar ya, si el repo es público, y la URL
cuando exista. Hoy: nada, no, y no hay.
