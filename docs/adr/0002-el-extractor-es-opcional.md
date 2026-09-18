# ADR 0002 — El extractor es opcional. La demo nunca toca la red

**Fecha:** 18/09/2026
**Estado:** aceptada, antes de escribir una sola línea del extractor

## El conflicto

Dos requisitos del proyecto se empujan en direcciones contrarias.

El primero, que los nueve evaluadores pusieron antes que cualquier otro: **el repositorio tiene
que arrancar en una máquina limpia sin una sola API key.** Es lo que más repos mata; si no
arranca en dos minutos, cierran la pestaña.

Y el proyecto, para ser lo que dice, tiene que leer fotos con un modelo. Eso necesita una llave
y cuesta plata por corrida.

## La decisión

**El extractor es un componente opcional que nada más del repositorio necesita para funcionar.**

- `docker compose run --rm remito demo` y `docker compose run --rm tests` **no hacen una sola
  llamada de red**, hoy y después de que el extractor exista. Hay tests que lo comprueban
  buscando importaciones de red en el paquete.
- El extractor se invoca con un comando propio, y si no encuentra `ANTHROPIC_API_KEY` **dice
  qué falta y cómo conseguirlo**, en vez de reventar con una traza.
- Los comprobantes sintéticos con respuesta conocida, que ya existen, permiten certificar el
  extractor sin gastar una foto real ni un peso de más de los necesarios.

## Lo que esto cuesta

**Quien corra sólo la demo nunca ve el extractor funcionar.** Va a ver la mitad que se niega, no
la que lee. Es el costo directo de la decisión y no se puede compensar con documentación: hay
que asumir que una parte de los lectores se queda con la mitad.

**Los evals no pueden correr en cada pull request.** Los secretos de GitHub Actions no están
disponibles para los pull requests que vienen de un fork, por una razón obvia: cualquiera
mandaría un PR que imprime la llave. Entonces el requisito de "CI que falla si baja la
exactitud" no se puede cumplir en el flujo normal.

Cómo se resuelve, y se escribe ahora para no improvisarlo después:

- El trabajo de evals corre **sólo en `main`**, con la llave como secreto y **con el tope de
  gasto activado**. Es el único lugar del proyecto donde se gasta plata sin que alguien apriete
  un botón, y por eso el tope no es opcional ahí.
- El resultado de cada corrida se **commitea** como archivo, con la fecha, la versión del prompt
  y el costo real en dólares. Así la tabla de exactitud por versión que pide el plan existe y se
  puede leer sin correr nada.
- En los pull requests corre todo menos los evals, y se dice en el propio CI que los evals no
  corrieron, en vez de dejar un tilde verde que parezca que sí.

## Lo que se consideró y se descartó

- **Meter la llave en el repositorio.** No hace falta explicarlo.
- **Un modelo local para no necesitar llave.** Agrega gigabytes a una imagen que hoy arranca en
  73 segundos, y el requisito era arrancar rápido, no arrancar sin internet.
- **Respuestas grabadas del modelo para la demo.** Tentador: la demo mostraría el extractor sin
  llave. Descartado porque sería una demo que siempre acierta, y lo que este proyecto quiere
  mostrar es qué pasa cuando el modelo se equivoca. Una grabación del caso bueno es publicidad.
