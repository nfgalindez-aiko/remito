# datos

Acá van las fotos de los comprobantes.

## `crudo/`

Las fotos como salen del celular, sin enderezar, sin recortar y sin retocar. **Esta carpeta está
en `.gitignore` y nunca se commitea**: las fotos traen CUIT, razón social, domicilio y código de
cliente del destinatario.

Cómo sacarlas, que importa más que la calidad:

- Donde te las dan, con la luz que haya. Sobre el mostrador, no sobre un escritorio ordenado.
- **Los comprobantes de dos hojas, dos fotos**: una como queda naturalmente, con la hoja tapando,
  y otra con las hojas separadas y todo a la vista. La primera es el caso difícil; la segunda es
  de donde sale la verdad para etiquetar. Sin la segunda no hay forma de saber qué decía la línea
  tapada.
- No enderezar, no recortar, no retocar. Que salgan torcidas.
- Unas cuantas a propósito mal: de lejos, con poca luz, con el papel arrugado o en la mano.
- No borrar ninguna que "salió mal". Ésas son las que dicen dónde está el límite, y sin ellas
  `LIMITES.md` no se puede escribir.

La variación es el activo, no la calidad. Un conjunto de fotos todas perfectas produce un número
de exactitud alto que no dice nada sobre lo que pasa en un mostrador.

## Por qué no hay nada acá en el repositorio público

Porque las fotos son de un kiosco real, con los datos fiscales de su dueño y de sus proveedores.
Lo que sí está versionado es una factura transcripta y anonimizada, en
`src/remito/datos/p01-2026-09-17.json`, con cada importe impreso al lado de su valor en centavos
puesto a mano.
