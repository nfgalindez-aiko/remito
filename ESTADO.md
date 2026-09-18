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

**Para quién es** (definido por el chat general el 18/09/2026): para **un** lector, un evaluador
técnico que abre un archivo al azar y pregunta por qué esa línea. No para un kiosquero, no para
los clientes de Workana —ésos no abren repositorios—. Defendible, no usable: sin interfaz, sin
usuarios, sin la parte aburrida de todo producto. Pero **tiene que correr**: arrancar en una
máquina limpia sin una sola API key es el requisito nº1 de los nueve.

**Fecha de corte: 9 de octubre de 2026**, tres semanas desde el arranque. Lo que haya ese día se
publica con un `LIMITES.md` honesto que diga hasta dónde llegó. Un repo chico y terminado vale
más que uno grande a medias; publicarlo a medias vuelve a los evaluadores activamente negativos.

**Qué se puede mostrar hoy:** `docker compose run --rm remito demo` — la factura real del kiosco y
tres formas de romperla, sin red y sin API keys. **La ruta por Docker está SIN VERIFICAR**: no
hay Docker en la máquina. Por Python corre y está verificado.

| Frente | Estado | Nota |
|---|---|---|
| `PLAN.md` — qué construir y por qué | cerrado | Escrito 18/09/2026 |
| `CRITERIOS.md` — criterios congelados | **cerrado** | sha256 `7c99f2d8…7259`, 18/09/2026 |
| Conjunto de datos etiquetado | bloqueado | Falta fotografiar. Es el activo del proyecto |
| Demo por terminal (`cli.py`) | **cerrado** | Corre sin red ni API keys. Verificado por Python |
| `docker compose up` | **sin verificar** | Escrito, nunca corrido: falta Docker en la máquina |
| `README.md` | **cerrado** | Cada afirmación verificada con grep, una por una |
| `docs/adr/0001` | **cerrado** | Postgres, revertido el mismo día, con el costo admitido |
| Módulo de plata (`src/remito/plata.py`) | **cerrado** | Centavos enteros |
| Generador de comprobantes sintéticos | **cerrado** | 4 casos de certificación, imágenes degradadas |
| Base de datos (`base.py`) | **cerrado** | SQLite. Idempotencia por clave primaria, test de 12 hilos |
| Alerta de aumento | **cerrado el motor** | Comparación cruzada sin dividir. Falta elegir el umbral, y por qué: `LIMITES.md` §11 |
| Validación determinista (`validacion.py`) | **cerrado** | Los dos vetos y las mañas, con la factura real de fixture |
| `LIMITES.md` | **cerrado** | 13 entradas, separando decisión / medido / sin medir |
| Tests | — | 198, todos en verde |
| Esquema de etiquetado | bloqueado | Sale del bloque de exploración, después de las fotos |
| Baseline T0 (OCR+regex, sin modelo) | vía abierta | No se toca hasta tener datos |
| Lectura de la foto con modelo | vía abierta | Se certifica el instrumento primero (`CRITERIOS.md` §7) |
| Repo público | no | 9 commits locales, sin remoto |

**Quién es quién.** Nicolás decide y aporta el oficio (21 años de kiosco) y los papeles. El
asistente hace el trabajo técnico. Los agentes, cuando se usen, sirven para **revisar y
criticar**, nunca para escribir el código: código escrito en paralelo sale parejo y ancho, que
es exactamente lo que los evaluadores dijeron que delata que nadie decidió.

---

## 2. Reglas

Corpus numerado. Se citan por número.

**R1 — El precio unitario impreso es un redondeo de presentación, no el precio.** El costo
unitario autoritativo es `subtotal_línea ÷ cantidad`. Medido: en 4 de 6 líneas del primer
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

**R9 — Un caso de prueba "con señal" tiene que llevar su verdad adentro de la imagen.** Si se
le tapan líneas, ningún extractor puede recuperarlas y el fracaso se leería como que el
instrumento no sirve. Tapar líneas es un caso distinto, donde lo correcto no es extraer bien
sino no aprobar. Confundir los dos hace que la certificación no certifique nada.

**R11 — La aritmética no puede atrapar un número inventado que ella misma valida.** Si falta el
TOTAL en la foto y el modelo lo inventa sumando las líneas, cierra contra el SUB-TOTAL y pasa
los dos vetos. Ningún chequeo de consistencia interna ve eso. La única defensa es que el
extractor conteste "no está", y eso hay que medirlo aparte.

**R10 — Todo número que va a la prosa se recalcula desde el dato, con un test.** Causa: el
18/09/2026 el asistente escribió "en 3 de 6 líneas" en dos lugares del ESTADO y en el fixture,
cuando eran 4 de 6. La tabla de mediciones, generada por código, siempre estuvo bien; el error
apareció al resumirla a mano, colapsando dos líneas idénticas (las dos de Kokis, que fallan las
dos por el mismo centavo). Lo encontró el test que recontaba el dato en vez de repetir la
afirmación. `CRITERIOS.md` se salvó porque ahí sólo está la tabla, sin resumen en prosa.

---

## 3. Pendientes

| Qué | Dueño | Por qué espera |
|---|---|---|
| Juntar y fotografiar los 40-100 comprobantes | Nicolás | Es el activo del proyecto; sin esto no hay nada |
| Tapar CUIT, razón social y domicilio del destinatario antes de que una foto entre al repo | Nicolás / asistente | `CRITERIOS.md` §11 |
| **Instalar Docker Desktop** | Nicolás | Ahora es lo más urgente: hay un `docker-compose.yml` escrito que nadie corrió nunca. No se publica sin haberlo visto arrancar |
| Esquema de etiquetado | asistente | Sale del bloque de exploración, después de las fotos |
| Los 12 documentos rotos a propósito | asistente | El generador ya da 4; faltan 8 roturas más |
| Elegir el umbral mínimo de la alerta de aumento | asistente | Sale del historial real. Hoy sería inventar un número: `LIMITES.md` §11 |
| Publicar el repo en GitHub | Nicolás | Cuando haya algo que valga la pena mostrar |

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

**Tercer hallazgo: el precio unitario impreso está redondeado para mostrar.** En 4 de 6 líneas,
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

## 6. Sesión 18/09/2026 — el módulo de plata — CERRADA

Se escribió el núcleo: `plata.py`, `comprobante.py`, `validacion.py`, con la factura de P01 como
fixture etiquetado a mano. 57 tests, todos en verde. No hay modelo todavía, ni base de datos, ni
lectura de fotos: primero las cuentas que van a poder vetarlo.

**Se midió dónde se rompe el float, en vez de suponerlo.** La suma de las seis líneas de P01 da
exacta también en float: el float NO falla al sumar importes de kiosco. Falla al redondear.
Medido sobre los 19.999.900 netos posibles de $1 a $200.000, calcular el IVA del 21% en float da
un centavo distinto que en enteros en 147.239 casos, el 0,736%. El primero es $3,50: en enteros
0,74, en float 0,73. Con una factura por día, un error cada cuatro meses y medio. Ese número y su
fecha están comentados en `plata.py`, y el caso de $3,50 es un test.

**Decisión: no se divide nunca para comparar costos.** El costo unitario real de una línea casi
nunca cae en centavos redondos (5.945,21 / 3 = 1.981,7367). En vez de dividir y redondear, se
comparan los subtotales cruzados: `sub_a × cant_b` contra `sub_b × cant_a`, enteros, exacto. Hay
un test con dos líneas que imprimirían el mismo precio unitario y sin embargo cuestan distinto.

**Decisión: el parser no adivina nunca.** Si un importe puede leerse de dos formas, levanta
excepción en vez de elegir. Un número plausible e inventado pasa la validación y entra a la base
siendo falso, que es el peor error que puede cometer este sistema porque no deja rastro. El caso
que sí es indistinguible —el OCR se come la coma y "737,61" llega como "73761"— no se resuelve en
el parser sino en el veto del subtotal, y hay un test que lo demuestra.

**Se descubrió que el congelado no sobrevivía a un `git clone`.** `core.autocrlf=true`, que es lo
que instala Git for Windows por defecto, reescribe los finales de línea al clonar: cambian los
bytes y el sha256 de `CRITERIOS.md` deja de verificar, justo cuando alguien lo quiere comprobar.
Arreglado con `.gitattributes`, y verificado clonando el repo en otra carpeta con esa opción
forzada.

**Error del asistente, con su causa:** ver R10. Se dijo "3 de 6 líneas" cuando eran 4 de 6.

---

## 7. Sesión 18/09/2026 — el generador y un límite que duele — CERRADA

Se escribió `sintetico.py`: comprobantes inventados con la respuesta conocida, dibujados como
una factura y degradados hasta que parezcan una foto de celular (torcida, con sombra, con
desenfoque, sobre la mesa). Sirve para certificar que el medidor mide antes de gastar un papel
real, y es la mitad de los 12 documentos rotos a propósito que pide `PLAN.md`.

La aritmética del generador imita la del proveedor: el precio se calcula con cuatro decimales y
se imprime con dos, así que aparecen solas las líneas donde `precio impreso × cantidad` no da el
subtotal. Un generador que hiciera las cuentas "bien" produciría comprobantes más limpios que
los reales y certificaría un medidor que después falla con el primer papel del kiosco.

**Error de diseño propio, corregido:** el caso "con señal" se había hecho con la hoja superpuesta
tapando 4 de 5 líneas. Así la verdad no está en la imagen y ningún extractor puede recuperarla:
el caso no certificaba nada. Se separó en dos casos distintos. → R9.

**Límite encontrado, y es el más importante hasta ahora.** El caso de fuga —la foto que se comió
la tira de totales— es el único modo de falla que la validación aritmética **no puede atrapar**.
Si el modelo no ve el TOTAL y lo inventa sumando las líneas, ese número inventado cierra
perfecto contra el SUB-TOTAL y pasa los dos vetos. La tesis del proyecto es que las cuentas
pueden vetar al modelo; acá no pueden, y hay que decirlo. → R11.

La defensa no puede ser aritmética: tiene que ser que el extractor devuelva "no está" en vez de
un número, y eso se mide, no se supone. Es el caso 3 de `CRITERIOS.md` §7 y va a `LIMITES.md`.

---

## 8. Sesión 18/09/2026 — la demo que se puede correr — CERRADA

El chat general definió tres cosas que cambiaron la prioridad: defendible y no usable, un solo
lector (evaluador técnico), y fecha de corte el 9 de octubre de 2026. Prioridad declarada, en
orden: que arranque limpio, que el veto funcione y esté testeado, que `LIMITES.md` sea honesto.

Con eso se dejaron de lado las 8 roturas que faltaban y se hizo la demo.

**`remito demo`** toma la factura de P01 y la rompe de tres maneras: la hoja que tapa una
línea, la hoja que tapa mercadería sin cargo (que no mueve un peso, y por eso hace falta el
segundo veto), y la coma que se come el OCR. Muestra cuál entra y cuál no, con el motivo. Sin
red, sin API keys, sin modelo, sin fotos.

**Decisión revertida el mismo día: Postgres.** A la mañana la decisión era Postgres adentro del
compose; a la tarde, con el lector definido, no había respuesta buena a "¿por qué Postgres en un
CLI de un usuario?". Va SQLite cuando haya algo que persistir. `docs/adr/0001-sin-postgres.md`
lo escribe con el costo admitido: hoy **no existe** la idempotencia con `UNIQUE` que pidieron
siete de los nueve evaluadores, y eso no se arregla escribiendo el ADR.

**El fixture se movió de `tests/` al paquete.** Estaba mal: la demo dependía de la carpeta de
tests para arrancar, así que la imagen de Docker habría tenido que copiar los tests para que el
programa funcione.

**Cada afirmación del README se verificó una por una**, como lo haría un evaluador con grep: el
hash, la demo, los tests, "sin red", los cuatro chequeos, los archivos nombrados, las
dependencias. La única que no se pudo verificar es `docker compose`, y está marcada como sin
verificar en la tabla de arriba en vez de darse por buena.

**"Nunca float" ahora es un test, no una frase.** Grep encuentra la palabra en los comentarios
que explican por qué no se usa y no distingue prosa de código. `test_nada_de_float.py` lee el
árbol sintáctico de los tres módulos donde vive la plata y busca literales decimales,
divisiones verdaderas e importaciones de `decimal`. Incluye un test que falla si nace un módulo
nuevo que maneje `Centavos` y nadie lo agrega a la lista.

**Cuarto error de conteo en prosa**, el mismo de R10: la demo decía "cuatro formas de romperla"
y "los cinco chequeos" cuando eran tres y cuatro. Esta vez no se corrigió el texto: los números
salen del dato (`len(Chequeo)`, contar los casos rechazados) y hay un test que lo comprueba.

---

## 9. Sesión 18/09/2026 — la base — CERRADA

`src/remito/base.py`: SQLite, un archivo, sin servidor. Salda la deuda que el ADR 0001 había
declarado.

**Idempotencia por la clave primaria, no por un `if ya existe`.** Preguntar y después insertar
deja una ventana entre las dos cosas por la que entra la mercadería duplicada. El test dispara
12 hilos cargando la misma factura a la vez: gana uno, los otros once reciben `ya_estaba`, y en
la base quedan 6 líneas, no 72. Dicho con honestidad en el propio test: SQLite serializa a los
escritores, así que eso prueba que la restricción se cumple, no que aguante contención real.

**Tres cosas de SQLite que si no se hacen fallan en silencio**, y las tres están con su
comentario:
- Las claves foráneas vienen **apagadas**, por conexión. Sin el PRAGMA, `REFERENCES` es
  decorativo. Hay un test que mete una línea huérfana y espera que la base la rechace.
- Una transacción diferida toma el candado tarde y revienta con `SQLITE_BUSY` a mitad de camino.
  Va `BEGIN IMMEDIATE`.
- SQLite tiene **afinidad** de tipos, no tipos: un 1.5 entra en una columna INTEGER sin chistar.
  Las columnas de plata llevan `CHECK (typeof(x) = 'integer')`. Es lo único que hace que "nunca
  float" también valga adentro del archivo, y hay un test que lo intenta.

**Espera del candado: 30 segundos, medidos.** Con 12 hilos la espera peor fue 99 ms y la mediana
19 ms. 30 s son 300 veces el peor caso medido; el margen está para un lote real, no ajustado a
la prueba. El número y su fecha están en el comentario de la constante.

**El estado del comprobante decide si entra al historial de precios.** Lo que está en la cola de
revisión humana no es un hecho: si sus números alimentaran el historial, un precio mal leído se
volvería una alerta de aumento que nunca pasó, y lo único que este sistema tiene para ofrecer es
que sus avisos sean ciertos.

**El guardián de "nunca float" funcionó solo.** Al nacer `base.py` el test falló pidiendo que se
lo agregara a la lista, y después agarró un `timeout=30.0` que no es plata sino un tiempo de
espera. No se le agregó una excepción: pasó a ser `30`. "Este float está bien, no es plata" es
exactamente el razonamiento que deja pasar al que sí importa.

**Error propio, encontrado al releer:** había escrito un `assert ... or True` en un test, que lo
convierte en un test que no prueba nada y que pasa siempre. Corregido, y el test ahora comprueba
lo que decía comprobar: que las dos compras imprimen el mismo precio unitario y aun así el costo
real subió.

---

## 10. Cómo actualizar esto

Una sección nueva por sesión de trabajo, numerada correlativa, con fecha en el título y su
estado. La más nueva abajo. Las viejas no se tocan.

Lo que le sirve al chat que vende: qué se puede mostrar ya, si el repo es público, y la URL
cuando exista. Hoy: nada, no, y no hay.
