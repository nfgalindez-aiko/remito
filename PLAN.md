# remito

Entra la foto de un remito de proveedor sacada con el celular. Sale stock cargado, costo por producto, y alerta cuando un proveedor aumentó.

## Para qué existe esto

No es un producto. Es la prueba de que Nicolás Galindez sabe trabajar.

Diez evaluadores técnicos —un CTO de fintech en Madrid, un Head of Engineering de una aseguradora, un founder de IA en San Francisco, un staff engineer que revisa quince PRs por semana, un mantenedor de open source, un senior escéptico del código hecho con IA, y cuatro más— leyeron su perfil y dijeron qué repositorio público les haría cambiar de opinión. Los nueve que contestaron dijeron que lo haría.

Ninguno dijo "contratado". Los nueve dijeron lo mismo: **el repo compra una llamada de cuarenta minutos donde ellos eligen un archivo al azar y preguntan por qué esa línea y qué se rompe si la sacás.** Todo lo que sigue está pensado para ganar esa llamada.

## Por qué este proyecto y no otro

Cuatro evaluadores propusieron por separado el mismo proyecto con distinto nombre: documento sucio → extracción con modelo → validación determinista → descuadres. Otros dos pidieron lo mismo de fondo: plata que tiene que cerrar.

Y hay una ventaja que ninguno de ellos puede comprar: Nicolás atendió un kiosco veintiún años. Sabe qué es un remito de dos hojas con el total en la segunda, un proveedor que factura distinto de lo que entrega, y un aumento que aparece sin aviso. Ese conocimiento del oficio es el diferencial del proyecto.

**Alternativa barata**, si hay poco tiempo: abrir el motor de Wild Tech con sus incidentes y sus artículos rechazados. Cuesta unas tres semanas en vez de seis. Dos evaluadores la propusieron.

## El error a no cometer

Los nueve lo nombraron, y contradice el instinto inicial: **ancho en vez de hondo.**

"Que tenga un poco de todo" es exactamente lo que mata estos repos. Auth, roles, dark mode, i18n, panel de administración, Kubernetes, Kafka, microservicios para tres usuarios. Hoy el ancho es gratis: cualquiera lo genera en una tarde. Lo único que cuesta es la profundidad.

Un repo ancho deja peor que no tener ninguno. Hoy son indiferentes; un repo flojo los vuelve activamente negativos.

## Qué tiene que tener adentro

Ordenado por cuántos de los nueve lo pidieron.

1. **`docker compose up` que levanta en una máquina limpia, sin una sola API key**, con datos sembrados y **doce documentos rotos a propósito**. Los nueve. Es lo que más repos mata: si no arranca en dos minutos, cierran la pestaña.
2. **Validación determinista que puede vetar al modelo.** Si las líneas no suman el total impreso, no se aprueba: va a cola de revisión humana. Ocho.
3. **Plata en enteros de centavos o Decimal, nunca float**, con un test que lo demuestra. Siete.
4. **Idempotencia con UNIQUE en la base**, no con un `if existe`, y un test que dispara el mismo evento dos veces en paralelo. Siete.
5. **`LIMITES.md`** — lo que esto NO hace: a partir de qué volumen se rompe, qué no maneja, qué se decidió bancar. Siete.
6. **`evals/`** con cien casos etiquetados a mano, tabla de exactitud por versión, y CI que falla si baja. Cinco.
7. **Tope de gasto en dólares por corrida**, implementado, con el costo real medido. Cinco.
8. **Un test con el nombre de un bug real** y el archivo que lo rompió guardado como fixture. Cinco.
9. **`docs/adr/`** con al menos una decisión revertida y el costo admitido. Cinco.
10. **Prompts versionados en archivos**, con un changelog de por qué murió cada versión. Cuatro.
11. **Logs estructurados con correlation id** y un `RUNBOOK.md`. Tres.

## Cómo se nota que hubo criterio humano

Lo más importante del informe. Los nueve coincidieron: **nadie busca si lo escribió una IA. Buscan si alguien decidió.**

- **Borrados.** La señal número uno, la nombraron siete. Van a correr `git log --shortstat`. Si el repo es +14.000 / −300, nadie cambió de opinión nunca. Un commit que saca una abstracción y explica por qué vale más que toda la carpeta de código.
- **Asimetría deliberada.** El código generado es parejo: mismo docstring, mismo try/catch en todos lados. El dirigido tiene relieve: el módulo de plata con treinta tests y comentarios de por qué, el exportador de CSV pelado y sin gracia. Uniformidad significa que nadie priorizó.
- **Números con procedencia.** `MAX_CONCURRENCY = 3  # arriba de 3 tira 429 a los 40s, medido 11/03`. Los modelos eligen 5, 10, 30, 100.
- **Comentarios del por qué, y del camino que NO se tomó.** "Este proveedor devuelve 200 con el error en el body." Eso no está en ningún dataset.
- **Reverts con motivo**, y commits `fix:` dos semanas después del feature. Si nunca se rompió nada, nunca se usó.
- **Historial repartido en semanas**, con huecos, con algún martes a las 23:40. No 180 commits de un fin de semana.
- **Vocabulario del oficio sostenido:** remito, descuadre, contraasiento. No `DataService` ni `ItemManager`.
- **Convergencia:** una sola forma de hacer HTTP en todo el repo. Tres formas significa que cada archivo salió de una conversación distinta.
- **Manejo de error angosto:** try alrededor de la única llamada que falla, distinguiendo reintentable de no reintentable. Try uniforme es plantilla.
- **El "no" escrito.** Los modelos nunca dicen que no.
- **Dependencias pocas y justificadas.** Van a correr `depcheck`.

## Otros errores nombrados

- README escrito antes que el código, prometiendo lo que no hay. Verifican una afirmación con grep; si falla una, no creen ninguna.
- Emojis y "🚀 Features".
- Roadmap y "coming soon".
- Gastar tres semanas en el frontend.
- `.env` en el historial, aunque se haya borrado después.
- Squashear la historia para que quede prolija. Eso borra la única evidencia que importa.
- Anunciar "construido con IA" como titular.
- Empezar tres repos.
- Publicarlo a medias.

## Cómo construirlo

**No usar ultracode ni orquestación masiva de agentes para generar.** Produce código parejo y ancho, y un historial de 180 commits en un fin de semana: exactamente las dos cosas que los evaluadores dijeron que delatan que nadie decidió.

Opus con esfuerzo alto, decisiones de a una, commits repartidos en días reales. Los workflows y los agentes sirven acá para **revisar y criticar** lo ya hecho, nunca para escribirlo.

## Primer paso

Sacar cien fotos de remitos viejos del kiosco, tachar CUIT y razón social, y etiquetar los campos a mano. Ese conjunto es el activo del proyecto; el código viene después.

## Cómo se coordina con el otro chat

Este proyecto se construye en un chat aparte. El chat de búsqueda de trabajo (Workana, Fiverr, LinkedIn, el radar) necesita saber en qué anda esto para usarlo como prueba frente a clientes.

**`ESTADO.md` en esta misma carpeta es el puente.** El chat que construye lo actualiza; el chat que vende lo lee. Nada de contexto importante vive solamente en una conversación.
