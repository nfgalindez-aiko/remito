# ADR 0001 — Sin Postgres. SQLite, y por ahora nada

**Fecha:** 18/09/2026
**Estado:** aceptada, después de revertir la decisión contraria el mismo día

## Lo que se decidió primero, y estuvo mal

A la mañana del 18/09 la decisión era Postgres adentro de `docker compose`. El razonamiento
fue: los nueve evaluadores pidieron `docker compose up` en una máquina limpia, `docker
compose` con Postgres es lo que esperan ver, y el historial de precios necesita una base.

Está escrito en la conversación de ese día, con esas palabras: "a una base de datos de verdad
(Postgres, adentro del Docker ese que te dije)".

## Qué cambió

Esa misma tarde se definió para quién es el repo: **para un evaluador técnico que abre un
archivo al azar y pregunta por qué esa línea.** No para un kiosquero. No hay interfaz, no hay
usuarios concurrentes, no hay servidor. La demo es un comando de terminal.

Con eso arriba de la mesa, "¿por qué Postgres acá?" es una pregunta que no tiene una respuesta
buena. La respuesta honesta sería "porque queda bien en el compose", y ésa es exactamente la
clase de decisión que los evaluadores dijeron que buscan detectar: infraestructura que nadie
necesitaba, puesta para aparentar escala.

## La decisión

**Sin Postgres.** Cuando haya algo que persistir, va SQLite.

`docker compose up` sigue existiendo, con un solo servicio. Un compose de un servicio es
raro sólo si uno cree que compose es para orquestar; es para que arranque con un comando, y
eso es literalmente lo que pidieron.

## Lo que esto cuesta, dicho sin adornos

El requisito 4 de `PLAN.md` —idempotencia con `UNIQUE` en la base, no con un `if existe`, con
un test que dispara el mismo evento dos veces en paralelo— lo pidieron siete de los nueve
evaluadores. **Hoy no está**, porque no hay base todavía. La clave existe en el código
(`Comprobante.id_unico`) y está testeada, pero una clave sin un `UNIQUE` que la haga cumplir es
una intención, no una garantía.

Eso no se arregla solo por escribir este documento. SQLite tiene que existir antes de publicar,
con su `UNIQUE` y su test de doble carga. Si llega la fecha de corte y no está, va a
`LIMITES.md` diciendo que no está, no se omite.

La prueba "en paralelo" con SQLite además es más floja que con Postgres: SQLite serializa los
escritores, así que el test prueba que la restricción se cumple, no que aguanta contención
real. Eso también se dice cuando exista.

## Lo que se consideró y se descartó

- **Postgres.** Un servidor de base de datos para un CLI de un usuario. Descartado arriba.
- **Un archivo JSON como base.** No tiene restricción de unicidad: la idempotencia volvería a
  ser un `if existe`, que es exactamente lo que el requisito prohíbe.
- **Nada, ni siquiera SQLite.** Tentador, porque la demo de hoy no persiste nada. Descartado:
  la alerta de aumento necesita el historial de precios, y ése es la mitad del producto.
