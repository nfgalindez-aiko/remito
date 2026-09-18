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
tres formas de romperla, sin red y sin API keys. **Verificado el 18/09/2026: 79 segundos** desde
el comando hasta la salida, en una máquina con la imagen base y la caché de build borradas antes
de cronometrar. `docker compose run --rm tests` corre las 258 pruebas adentro de la imagen.

| Frente | Estado | Nota |
|---|---|---|
| `PLAN.md` — qué construir y por qué | cerrado | Escrito 18/09/2026 |
| `CRITERIOS.md` — criterios congelados | **cerrado** | sha256 `7c99f2d8…7259`, 18/09/2026 |
| Conjunto de datos etiquetado | bloqueado | Falta fotografiar. Es el activo del proyecto |
| Demo por terminal (`cli.py`) | **cerrado** | Corre sin red ni API keys. Verificado por Python |
| `docker compose` | **cerrado, corrido** | 73 s en máquina limpia. Dos servicios: `remito demo` y `tests` |
| `README.md` | **reescrito** | Prometía leer fotos y decía "no hay base de datos" con SQLite andando. 13 tests lo vigilan |
| `docs/adr/` | **2 documentos** | 0001 Postgres revertido; 0002 el extractor opcional y el costo de que los evals no corran en cada PR |
| CI | **verde** | `docker compose run --rm tests` + la demo + el sha256, por el mismo camino que corre un evaluador |
| Módulo de plata (`src/remito/plata.py`) | **cerrado** | Centavos enteros |
| Generador de comprobantes sintéticos | **cerrado** | 4 casos de certificación, imágenes degradadas |
| Base de datos (`base.py`) | **cerrado** | SQLite. Idempotencia por clave primaria, test de 12 hilos |
| Alerta de aumento | **cerrado el motor** | Comparación cruzada sin dividir. Falta elegir el umbral, y por qué: `LIMITES.md` §11 |
| Validación determinista (`validacion.py`) | **cerrado** | Los dos vetos y las mañas, con la factura real de fixture |
| `LIMITES.md` | **cerrado** | 13 entradas, separando decisión / medido / sin medir |
| Los 12 documentos rotos a propósito | **cerrado** | 6 las agarra la aritmética, 5 dependen del extractor, 1 no tiene defensa |
| Bitácora y `RUNBOOK.md` | **cerrado** | Identificador por comprobante, y el RUNBOOK arranca por el síntoma |
| `remito procesar <foto>` | **cerrado** | Camino completo: foto, T0, cuentas, base. Tres códigos de salida |
| Tests | — | 307 en el contenedor, 1 falla esperada documentada |
| Esquema de etiquetado | bloqueado | Sale del bloque de exploración, después de las fotos |
| Baseline T0 (`baseline.py`) | **a medio hacer, y escrito** | Lee los sintéticos (98,8%, espejismo) y NO lee la foto real. `LIMITES.md` §13 |
| Lectura de la foto con modelo | vía abierta | Se certifica el instrumento primero (`CRITERIOS.md` §7) |
| Repo público | **sí** | github.com/nfgalindez-aiko/remito |

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

**R12 — Un caso de prueba de una entrada rota necesita tres piezas, no dos: la verdad, la
lectura que esa entrada produciría, y la entrada.** Con la verdad y la entrada sola no se puede
probar nada, porque el papel casi siempre está bien: lo que está mal es lo que alguien leyó de
él. Causa: se escribió el catálogo de roturas con dos piezas y los tests lo rechazaron.

**R17 — Un identificador que una persona va a copiar a mano no lleva O, 0, I, l ni 1.** Alguien
lo anota en el margen del papel y después lo tipea, o lo dice por teléfono. Perder un poco de
espacio de combinaciones sale más barato que un llamado para deletrear un UUID.

**R16 — Las equivocaciones se commitean y después se corrigen, no se arreglan antes de
commitear.** El 18/09/2026 se revirtieron tres decisiones reales —Postgres, un caso de prueba mal
diseñado, el catálogo de roturas— y las tres se corrigieron antes de guardarlas, así que el
historial no las muestra. Siete de los nueve evaluadores nombraron los borrados como la señal
número uno, y el repo iba 3.990 líneas agregadas contra 71 borradas. No se fabrica un borrado
para que la estadística quede linda; se deja de esconderlos.

**R15 — Verificar por el camino que el README promete, no por el que a uno le queda cómodo.**
Los tests pasaban con `python -m pytest` en la máquina y fallaban con
`docker compose run --rm tests`, que es el comando que dice el README. Se empujó igual. Lo
encontró el CI. Por eso el CI corre por docker y no sobre un Python instalado a mano: un tilde
verde sobre un camino que nadie más usa no significa nada.

**R14 — Un README que afirma algo falso en un renglón no se cree en ninguno.** Los nueve lo
nombraron con esas palabras: verifican una afirmación con grep, y si falla una, descartan las
demás. El 18/09/2026 este repo se publicó diciendo "no hay base de datos" con `base.py` ya
andando, y prometiendo en la primera línea que entra una foto y sale el stock cuando no hay
extractor. Ahora `tests/test_readme.py` verifica cada número y cada nombre propio del README
contra el código, y corrido contra el README viejo falla en cinco puntos.

**R13 — Lo que se va a publicar se audita antes del primer `push`, no después.** Un dato que
entra en un commit y se empuja queda público para siempre, aunque se borre en el commit
siguiente. Se revisa: CUIT, nombre, domicilio, código de cliente, `.env`, claves, y **el nombre
de terceros que no pidieron aparecer**. El 18/09/2026 el proveedor real aparecía 19 veces,
incluida su maña de facturación; se reemplazó por `P01` en los archivos y en el historial antes
de conectar el remoto. Reemplazar un texto en un historial que nadie clonó no es squashear: los
9 commits conservan sus fechas, sus mensajes y sus diffs.

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
| **Habilitar WSL y terminar el arranque de Docker** | Nicolás | `wsl --install` como administrador y reiniciar. La característica `Microsoft-Windows-Subsystem-Linux` está deshabilitada en Windows; por eso Docker Desktop no llega ni a la pantalla de licencia |
| Esquema de etiquetado | asistente | Sale del bloque de exploración, después de las fotos |
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

## 10. Sesión 18/09/2026 — las doce roturas, y hasta dónde llega la tesis — CERRADA

`src/remito/roturas.py`. Cada rotura tiene tres piezas, y la del medio es la que hace que el
catálogo sirva: **la verdad** (lo que dice el papel, siempre impecable), **la lectura** (lo que
un lector ingenuo produciría con la entrada rota) y la imagen cuando corresponde.

**Error de diseño propio, encontrado por mis propios tests.** La primera versión devolvía sólo
la verdad y la imagen. Con eso es imposible probar nada: el papel de una foto movida está
perfecto, la que está mal es la lectura. El test de `linea_tapada` falló pidiendo justamente
esa pieza que faltaba. → R12.

**El reparto, que es el resultado que importa:**

| | |
|---|---|
| 6 de 12 | las agarra la aritmética |
| 5 de 12 | la lectura sale **consistente consigo misma y mal**: sólo la salva que el extractor diga "no sé" |
| 1 de 12 | sin defensa: el papel que nunca se leyó |

**La validación determinista cubre la mitad.** Eso no es un mal resultado —la otra mitad son
roturas de la foto, no de los números— pero decir "la aritmética veta al modelo" sin decir esto
sería vender algo que no es. Las cinco del medio son todas la misma familia: quien lee arma el
pie sumando lo que vio, le da consistente porque lo calculó de ahí, y pasa los cuatro chequeos.

**Segundo error propio, y el test lo encontró:** la rotura sin defensa no estaba escrita en
`LIMITES.md`. Hay un test que lo verifica y falló. Ahora es `LIMITES.md` §12, y es la peor de
las doce: produce una lectura buena y una ausencia, y una ausencia no se examina.

**No se afirma el reparto 6/5/1 en ningún assert.** Un número a mano en un test invita a
reclasificar una rotura para que el número cierre. Lo que impide mentir con la clasificación es
que cada etiqueta se verifica rotura por rotura: si el catálogo dice que la agarra el veto del
subtotal y la agarra otro, el test falla y lo dice.

---

## 11. Sesión 18/09/2026 — anonimizar antes de publicar — CERRADA

Nicolás creó `github.com/nfgalindez-aiko/remito`, público. Antes de conectar el remoto se
auditó lo que se iba a empujar: ni un CUIT, ni su nombre, ni su domicilio, ni el código de
cliente, ni un `.env` en ningún commit. 31 archivos.

Lo que sí había: **el nombre real del proveedor, 19 veces**, incluida la frase "redondea el
total un centavo para abajo, siempre". Es una empresa real a la que Nicolás le sigue comprando.
Preguntado, decidió que no hace falta que se sepa quién es.

Se reemplazó por `P01` en los archivos **y en el historial**, con `filter-branch`, antes del
primer `push`. Se conservan los 9 commits con sus fechas, sus mensajes y sus diffs: lo único
que cambió son 16 cadenas de texto y los hashes, que nadie tenía todavía. Verificado después:
cero apariciones en cualquier objeto de la base de git, no sólo en los archivos de trabajo.

`CRITERIOS.md` salió ileso porque ya usaba `P01` desde el principio: el congelado sigue
verificando con el mismo sha256 `7c99f2d8…7259`. Si el documento congelado hubiera nombrado al
proveedor, no se habría podido anonimizar sin romper la única cosa que lo hace valer.

Queda como R13. El remoto está conectado y **no se empujó**: el README afirma que
`docker compose run --rm remito demo` anda, y eso todavía no se corrió nunca.

---

## 12. Sesión 18/09/2026 — Docker corrido y repo publicado — CERRADA

`docker compose run --rm remito demo`: **73 segundos** desde el comando hasta la salida, con la
imagen base y la caché de build borradas antes de cronometrar. El umbral que nombraron los nueve
evaluadores eran dos minutos. Antes de esto el número no existía y estaba marcado "sin verificar"
en esta misma tabla durante todo el día.

**Se agregó `docker compose run --rm tests`**, que corre las 258 pruebas adentro de la misma
imagen. Sin eso, "258 tests" es un número que el lector tendría que creer: para comprobarlo habría
que instalar Python y pytest a mano, que es justo la fricción que el requisito nº1 quiere evitar.

**Dos cosas que sólo aparecieron al correrlo, no al escribirlo:**

- La imagen excluía los `.md`, así que el test que exige que una rotura sin defensa esté escrita
  en `LIMITES.md` no encontraba el archivo y fallaba adentro del contenedor. Se metieron los
  documentos en la imagen. La alternativa —que el test se saltee cuando no encuentra el archivo—
  se descartó: un guardián que se desactiva solo no es un guardián.
- `docker compose run` reutiliza la imagen ya construida y no la reconstruye sola. El primer
  arreglo pareció no funcionar hasta correr `docker compose build`.

**Se midió tres veces y sólo la tercera sirve.** 38 s la primera corrida (con una imagen más
liviana, sin pytest), 58 s reconstruyendo sin caché pero con la imagen base ya bajada, y 73 s en
el caso que de verdad importa: una máquina que no tiene nada. Los dos primeros números habrían
quedado bien en el README y habrían sido falsos.

**El repositorio se publicó** en github.com/nfgalindez-aiko/remito, después de la auditoría de la
sección 11 y no antes.

---

## 13. Sesión 18/09/2026 — el README mentía, y lo encontró el otro chat — CERRADA

El chat general revisó el estado y puso arriba de todo algo que acá se había pasado por alto: el
repositorio ya era público y **el README prometía lo que no existe**. Tenía razón, y al
verificarlo apareció algo peor: además de abrir con "entra la foto, sale la mercadería cargada"
sin que haya extractor, decía **"no hay base de datos"** con `base.py` funcionando desde hacía
horas, y la tabla de módulos no listaba `base.py`, `comprobante.py` ni `roturas.py`.

Es exactamente el error que los nueve nombraron primero, cometido en este repositorio, publicado.
→ R14.

**Reescrito para decir lo que es:** un validador determinista que puede vetar a un modelo,
escrito antes que el modelo a propósito. Eso no es un hueco, es una decisión: el que juzga se
escribe antes que el que propone, porque escribirlo después es escribirlo para que apruebe lo que
el modelo ya devolvió. Y el reparto 6/5/1 de las roturas —lo que contradice la tesis— pasó a
estar arriba de todo, por consejo del otro chat: "el no escrito" es de las señales que buscan, y
estaba enterrado.

**`tests/test_readme.py`**, 13 pruebas: que cada módulo esté en la tabla, que los archivos que
nombra existan, que el reparto de las roturas sea el que publica, que los servicios de docker que
manda correr existan, que el hash congelado dé, y que no prometa leer fotos mientras no las lea.
Corrido contra el README viejo, falla en los cinco puntos.

**CI en verde**, corriendo por `docker compose` y no sobre un Python instalado en el runner. Si
el CI instalara las dependencias por su cuenta, probaría algo que ningún lector hace.

**La primera corrida del CI falló, y tenía razón.** Dos tests del README leen
`docker-compose.yml` y `docs/`, que no estaban adentro de la imagen: pasaban en la máquina y
fallaban por el camino que el README promete. Se había empujado sin volver a correr los tests
dentro de Docker. → R15.

**Cambio de práctica, por consejo del otro chat.** Las equivocaciones se commitean y después se
corrigen. Hoy se revirtieron tres decisiones reales y las tres se arreglaron antes de guardar, o
sea que el historial no las muestra: 3.990 agregadas contra 71 borradas. → R16. Los dos commits
`fix:` de esta sesión son los primeros que sí lo muestran.

**`docs/adr/0002`**: el extractor opcional, con dos costos admitidos. Quien corra sólo la demo
nunca lo ve funcionar. Y los evals no pueden correr en cada pull request porque los secretos no
están disponibles para PRs de un fork, así que el requisito "CI que falla si baja la exactitud"
se cumple sólo en `main`, con tope de gasto, y el resultado de cada corrida se commitea con su
costo en dólares.

---

## 14. Sesión 18/09/2026 — T0, y por qué no se puede comparar todavía — CERRADA

Sin crédito de API y sin fotos, lo único que valía la pena era el baseline T0: leer el
comprobante **sin modelo**, con OCR y reglas. `CRITERIOS.md` §2 ya se había comprometido a
construirlo. Efecto lateral que no se había visto: el repositorio pasa a leer imágenes de
verdad, sin una sola API key.

**Sobre comprobantes sintéticos:** 98,8% de los campos y 11 de 12 documentos perfectos en las
limpias; 55% y 4 de 12 en las degradadas, donde además se niega a leer 5 de 12 en vez de
inventar. **Ese número es un espejismo y está dicho en el propio módulo:** el parser se escribió
mirando esas imágenes. Es entrenar y evaluar con los mismos datos, con otro disfraz.

**Primera evidencia de punta a punta de la tesis**, sobre 24 sintéticos degradados: T0 se negó a
leer 12, leyó bien 5, y de las 7 que leyó mal **la aritmética frenó las 7**. Cero mercadería
falsa aprobada. Con 7 casos el intervalo al 95% no descarta hasta un 35%, así que es una señal,
no una prueba, y se reporta así.

**Y el resultado que más vale: T0 devuelve `None` con la foto real de Nicolás.** El espejismo
quedó confirmado empíricamente en vez de sólo advertido. Medido, paso por paso:

- El OCR lee bien: 235 palabras, confianza mediana 91.
- El pie sale exacto: `SUB-TOTAL 38.068,23` y `Unidades: 26`.
- Las filas se agrupan bien: código y descripción correctos.
- **Las columnas de plata no se leen.** Donde va el precio devuelve `A ; a a a]`.
- Entonces T0 se niega, que es lo correcto.

**Dos bugs propios, encontrados midiendo y no leyendo:**

- `"TOTAL"` es subcadena de `"SUB-TOTAL"`, así que el total del comprobante leía el subtotal, en
  los doce documentos. Un subtotal es un importe creíble: mirando la salida no se notaba. Lo
  encontró contar campos contra la verdad. Y `"IVA"` aparece arriba de todo en "IVA: Responsable
  Inscripto", así que el IVA quedaba siempre en cero.
- La tolerancia para agrupar filas era de 14 píxeles fijos, sacados de que el generador dibuja
  filas de 34 px. Sobre una foto de 2576x1932 parte cada renglón. Ahora sale de la altura de
  letra medida en cada imagen. Hay un test con el nombre del bug.

**Se paró de ajustar a propósito.** Seguir tocando parámetros de OCR contra una sola foto es
sobreajustar, no arreglar. Queda un `xfail(strict=True)` que describe lo que tiene que pasar y
avisa el día que alguien lo arregle.

**Consecuencia que va a `LIMITES.md` §13 y es la más importante:** con T0 a medio hacer, el
modelo le va a ganar por noventa puntos sin esfuerzo y la comparación de `CRITERIOS.md` §2 no
significa nada. Un baseline abandonado es un espantapájaros. **Hasta que T0 tenga un intento
honesto sobre fotos reales, esa comparación no se reporta.** Escrito antes de que exista el
modelo, que es cuando escribirlo cuesta algo.

**El guardián de floats se dividió en dos.** `baseline.py` no calcula plata: la lee, y hace
geometría de verdad —ángulos, alturas en píxeles— donde los reales son reales. Forzarlos a
enteros sería deformar el código para cumplir una regla que no le aplica. En su lugar se le
exige lo que sí corresponde: que todo importe que devuelve haya salido de `parse_importe` sin
pasar por ninguna cuenta, verificado en ejecución.

Arranque en frío: **79 segundos**, contra 73 antes de meter Tesseract.

---

## 15. Sesión 18/09/2026 — la bitácora, el RUNBOOK, y una pérdida silenciosa — CERRADA

**La bitácora no es logging de manual.** Existe para una sola pregunta, que es la que se hace de
verdad tres semanas después: *"esta factura quedó en revisión, ¿por qué?"*. De ahí sale todo lo
demás: un identificador que arranca con el día y se puede decir por teléfono (`0918-k3f2`), sin
las letras y números que se copian mal (→ R17); un archivo y no la salida estándar, que es lo que
el usuario está leyendo; y un chequeo que **rechaza cualquier valor con forma de CUIT antes de
escribirlo**, porque un archivo de registro es lo último que alguien mira antes de mandarlo
adjunto pidiendo ayuda.

**`RUNBOOK.md`** arranca por el síntoma como lo ve una persona, no por el nombre técnico de la
causa. Incluye qué hacer cuando el sistema aprueba algo mal, que es el único caso sin tolerancia,
y una sección final de lo que el RUNBOOK **no** cubre: no hay copias de seguridad automáticas, no
hay guardia y no hay alertas, porque este repositorio es defendible y no operable.

**`remito procesar <foto>`** ata el camino completo por primera vez: foto, T0, cuentas, base. Tres
códigos de salida porque son tres situaciones distintas para un script: entró, miralo, sacá otra.

**Y probándolo apareció el peor bug de todo el proyecto.** T0 no lee el número de factura, así que
deja `?` en los cuatro campos que forman la clave de la base. Dos facturas completamente distintas
entraron las dos como `?|?|?|?`: la primera se cargó, la segunda dijo "ya estaba" y **su
mercadería no entró nunca, sin un solo mensaje de error**. Silenciosa, que es lo que la hace la
peor.

Ninguno de los 302 tests lo agarró, porque todos usaban comprobantes con número. Lo encontró
correr el comando de verdad con dos imágenes distintas. Es el mismo aprendizaje de R15 en otro
disfraz: probar por el camino real, no por el cómodo.

**Se commiteó el bug y después el arreglo**, que es lo que dice R16. El arreglo no es inventarle
una clave —un hash del contenido haría que dos fotos del mismo papel con una letra distinta de
OCR se carguen dos veces, que es peor— sino negarse a cargar lo que no se puede identificar, que
es lo que hace el resto del proyecto cuando no sabe. El test de regresión, corrido contra el
commit anterior, falla en los cinco casos.

**Queda un límite nuevo a la vista, en `LIMITES.md` §14: hoy T0 no puede cargar nada por sí
solo.** Sirve como baseline de lectura, que es para lo que se construyó, y no como sistema
completo.

**Y un detalle de texto que era una mentira chica:** la salida decía "APROBADO: entra al stock" y
dos renglones después "A REVISIÓN". `revisar` contesta si las cuentas cierran, que no es lo mismo
que si la mercadería entra.

---

## 16. Cómo actualizar esto

Una sección nueva por sesión de trabajo, numerada correlativa, con fecha en el título y su
estado. La más nueva abajo. Las viejas no se tocan.

Lo que le sirve al chat que vende: qué se puede mostrar ya, si el repo es público, y la URL
cuando exista. Hoy: nada, no, y no hay.
