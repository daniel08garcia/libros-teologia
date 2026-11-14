# Libros de teología

Biblioteca de sermones y libros puritanos y reformados traducidos al español, publicados como HTML estático.

## Estructura

- `siglo/<siglo>/<Autor>/...html`: los textos publicados (por ejemplo `siglo/XVII/John Owen/`). Las obras de varios autores van en `siglo/<siglo>/Varios Autores/<Obra>/<Serie>/`.
- `index.html`: índice generado; no se edita a mano. Después de agregar o renombrar archivos, se regenera con `node createToC.js && npx --yes prettier@3.3.3 --write index.html`. El diseño está en `indice/` (`plantilla.html`, `indice.css`, `indice.js`) y los datos de autores (años de vida, color, colecciones), series y títulos de obra en `indice/autores.json`. Si `createToC.js` avisa de un autor sin datos, agrégalo ahí.
- Los siglos de `siglo/` son los de la época en que el autor escribió la obra, no los de la edición traducida.
- Búsqueda: `crearBusqueda.js` genera `pagefind/` (un registro por párrafo; no se versiona). El sitio lo publica la GitHub Action `.github/workflows/publicar.yml`, que corre `createToC.js` y `crearBusqueda.js`; `temp/` no se publica.
- `temp/originales/`: originales en inglés que el usuario deja para traducir.
- `temp/trabajo/`: carpetas de trabajo de cada traducción (ignoradas por git). Los archivos sueltos de la raíz, como las instrucciones de agentes y los scripts `cripplegate-*.js`, sí se versionan.
- `temp/scripts/sermones.js`: herramienta del flujo de traducción (dividir, revisar, aplicar, unir, html, validar). `temp/scripts/falsos-cognados.json` es el glosario que usa `revisar`.

## Traducir un libro o sermón

Sigue la guía `temp/ai_agent.md`: flujo completo, parámetros, prompts de los agentes y glosario de falsos cognados. La sección 4.1 cubre los libros de varios autores y usa *Puritan Sermons: The Morning Exercises at Cripplegate* como ejemplo. Sus instrucciones de agentes (`temp/trabajo/cripplegate-traductor.md` y `cripplegate-revisor.md`) sirven de modelo para obras nuevas.

- Usa agentes Haiku para traducir y revisar (el usuario lo prefiere por costo) y lanza como máximo 20 a la vez.
- Antes de `aplicar`, filtra las correcciones de citas bíblicas hechas de memoria (`temp/trabajo/cripplegate-filtrar-citas.js`).
- Termina siempre con `validar` (0 errores) y regenerando el índice.

## Reglas

- No hagas commits ni borres archivos sin confirmación del usuario. El usuario hace sus propios commits.
- `siglo/XVII/William Bates/El Pecado El Mal Más Formidable II.html` está vacío a propósito (es un recordatorio de traducción pendiente). No lo borres ni lo trates como un error.
- Responde al usuario en español.
