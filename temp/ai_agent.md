# Instrucciones para el agente: traducción automática de sermones

Este documento es para un modelo de IA que actúa como **orquestador**. El usuario le entrega este archivo junto con un texto original en inglés, y el orquestador lo traduce al español y lo deja publicado en el formato del proyecto (ver `README.md`, sección "Cómo Crear el Archivo HTML de un Sermón").

Ejemplo de cómo lo pide el usuario:

```
Lee temp/ai_agent.md y procesa este original:
  original: temp/originales/edwards-vol1.txt
  modo:     --multiple
  destino:  siglo/XVIII/Jonathan Edwards/The Works of Jonathan Edwards/Volumen 1
  autor:    Jonathan Edwards
  fecha:    1834-01-01
```

Para un libro de varios autores (ver la sección 4.1):

```
Lee temp/ai_agent.md y procesa este original:
  original: temp/originales/PURITAN SERMONS - VOL. 1 - Various Puritans.txt
  modo:     --multiple
  destino:  (por serie; ver la sección 4.1)
  autor:    varios
  fecha:    (por serie; ver la sección 4.1)
```

---

## 1. Resumen del flujo y modelos

El trabajo mecánico lo hacen scripts, que son exactos y no cuestan tokens. Los modelos solo se usan donde hace falta entender el idioma.

| Paso | Qué se hace                                                             | Quién lo hace                                                      | Modelo recomendado                                                                                                                |
| ---- | ----------------------------------------------------------------------- | ------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------- |
| 1    | Dividir en sermones y en fragmentos de máx. 6,000 caracteres            | Script `dividir`                                                   | Ninguno. Con `--multiple`, el orquestador solo decide dónde empieza cada sermón.                                                  |
| 2    | Traducir cada fragmento                                                 | **Agente traductor** (uno por fragmento, en paralelo)              | **No razonador**, gama media (p. ej. Claude Sonnet sin pensamiento extendido). Para ahorrar: Haiku, después de una prueba piloto. |
| 3    | Revisar coherencia y falsos cognados                                    | Script `revisar` (detecta) + **agente revisor** (decide y corrige) | **No razonador**, gama económica (p. ej. Claude Haiku). Trabaja sobre una lista de alertas ya preparada.                          |
| 4    | Unir, generar HTML, validar numeración, separación y formato            | Scripts `unir`, `html`, `validar`                                  | Ninguno. El orquestador solo interviene si el reporte trae errores.                                                               |
| —    | Coordinar, poner títulos en español, llenar metadatos, resolver errores | **Orquestador** (el modelo que lee este archivo)                   | Gama media. Puede razonar, porque lee poco texto: solo reportes y los primeros párrafos de cada sermón.                           |

Por qué la traducción no usa un modelo razonador:

- El razonamiento se cobra como texto de salida y se repite en cada fragmento. En un libro de cientos de fragmentos es el costo más grande.
- Traducir un fragmento corto con reglas explícitas no mejora mucho con razonamiento. En cambio, aumenta el riesgo de que el modelo "mejore", resuma o reorganice el texto.
- Lo que evita las alucinaciones en este flujo son otras tres cosas:
  1. Fragmentos cortos.
  2. La regla de **un párrafo inglés = un párrafo español**.
  3. Los controles automáticos de `revisar`: cuenta de párrafos, notas `[n]`, secciones `§ n`, numeraciones, longitud y texto sin traducir.

**Prueba piloto, la primera vez:** traduce un sermón completo con Sonnet y otro con Haiku. Haz que el usuario compare los dos y usa el modelo más barato que dé una calidad aceptable.

### Cómo lanzar los agentes en Claude Code

Usa la herramienta `Agent` con `model: "sonnet"` (o `"haiku"`) y `effort: "low"` para el traductor, y `model: "haiku"` con `effort: "low"` para el revisor. En otra plataforma, usa el equivalente: un subagente con herramientas para leer y escribir archivos, sin razonamiento extendido.

**Regla de costo:** el orquestador **no copia el texto** de los fragmentos en los prompts. Solo pasa rutas de archivos. Cada subagente lee y escribe sus propios archivos, y responde con una sola línea (`OK s01-f003 12`). Así el contexto del orquestador se mantiene pequeño durante todo el libro.

---

## 2. Parámetros de entrada

| Parámetro              | Obligatorio | Descripción                                                                                                                        |
| ---------------------- | ----------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| `original`             | Sí          | Archivo en inglés: `.txt`, `.md` o `.html`. Los párrafos van separados por líneas en blanco.                                       |
| `--uno` / `--multiple` | Sí          | `--uno` (por defecto): el archivo contiene un solo sermón. `--multiple`: contiene varios sermones o capítulos.                     |
| `destino`              | Sí          | Carpeta dentro de `siglo/` donde van los HTML, p. ej. `siglo/XVIII/Jonathan Edwards/The Works of Jonathan Edwards/Volumen 2`.      |
| `autor`                | Sí          | Nombre del autor tal como aparece en la carpeta, p. ej. `Jonathan Edwards`. En un libro de varios autores: `varios` (sección 4.1). |
| `fecha`                | No          | Fecha de publicación o predicación, `AAAA-MM-DD`. Si no se da, se omite el atributo.                                               |
| `id inicial`           | No          | Si no se da, los ids continúan después del último que haya en la carpeta destino.                                                  |

Si falta `destino` o `autor`, pregúntale al usuario **una sola vez**, antes de empezar. No inventes esos datos.

---

## 3. Archivos y carpetas

```
temp/scripts/sermones.js            # todos los comandos (Node; usa jsdom del proyecto)
temp/scripts/falsos-cognados.json   # glosario de falsos cognados para el revisor
temp/trabajo/<nombre>/              # carpeta de trabajo de cada original
  manifiesto.json                   # sermones, fragmentos, metadatos y estado
  fragmentos/s01-f001.en.txt        # fragmento en inglés (lo crea "dividir")
  fragmentos/s01-f001.es.txt        # traducción (la escribe el agente traductor)
  fragmentos/s01-f001.revision.json # alertas (las crea "revisar")
  fragmentos/s01-f001.correcciones.json  # correcciones (las escribe el agente revisor)
  sermones/s01.es.txt               # sermón completo en español (lo crea "unir")
```

`<nombre>` es el nombre del archivo original sin extensión, p. ej. `temp/trabajo/edwards-vol1/`.

Todos los comandos se ejecutan desde la raíz del repositorio. Si `node_modules` no existe, ejecuta `npm install` primero.

---

## 4. Paso a paso para el orquestador

### Paso 1: Dividir

**Con `--uno`:**

```bash
node temp/scripts/sermones.js dividir "<original>" "temp/trabajo/<nombre>"
```

**Con `--multiple`:**

1. Lista los encabezados posibles:
   ```bash
   node temp/scripts/sermones.js candidatos "<original>"
   ```
2. Decide dónde empieza cada sermón. Puedes hacerlo de dos formas:

   - Si todos los inicios siguen un patrón, usa `--patron`. Por ejemplo: `--patron "^SERMON [IVXLC]+"`.
   - Si no, haz una copia del original en `temp/trabajo/<nombre>/original-marcado.txt`. En la copia, inserta una línea `@@SERMON@@`, rodeada de líneas en blanco, antes de cada sermón. Usa los números de línea `L…` que da `candidatos`.

   Ten en cuenta lo siguiente:

   - Un encabezado como `APPLICATION` o `SECTION II` **no** empieza un sermón nuevo.
   - Un sermón predicado en varias partes ("Sermon I", "Sermon II" de la misma obra) se deja en archivos separados, terminados en `I`, `II`, etc.
   - El texto anterior al primer sermón (prefacio, índice) queda como su propio bloque. Si no se va a publicar, márcalo `"omitir": true` en el manifiesto.

3. Divide:
   ```bash
   node temp/scripts/sermones.js dividir "<original o copia marcada>" "temp/trabajo/<nombre>" --multiple [--patron "<regex>"]
   ```
4. Revisa la lista que imprime el comando. Cada sermón debe empezar con su encabezado. Si un corte está mal, corrige el patrón o las marcas y repite con `--forzar`.

**Títulos marcados.** Los originales transcritos de PDF con `temp/scripts/ocr.py` traen los títulos marcados: `## ` (título de obra, capítulo o división principal) y `### ` (subdivisión). Las marcas pasan por todo el flujo: el traductor las conserva, `revisar` da error si una se pierde o sobra, y `html` las convierte en `<h2>` y `<h3>`. El primer `## ` de cada obra es su título y va en el `<h1>`: sáltalo con `saltar_parrafos`. Con `--multiple`, las marcas ayudan a ubicar dónde empieza cada obra (`grep -n "^## " <original>`). Un original de un solo sermón o capítulo puede no tener ninguna marca: no pasa nada.

El tamaño por defecto es de 6,000 caracteres por fragmento. Los cortes siempre caen entre párrafos y **un párrafo nunca se divide**: si un párrafo solo pasa del límite, va solo en su propio fragmento (en el manifiesto queda con `"parrafo_largo": true`), aunque mida más de 6,000 caracteres.

### Paso 2: Traducir

1. Ejecuta `node temp/scripts/sermones.js estado "temp/trabajo/<nombre>"`. El comando muestra los fragmentos por traducir.
2. Lanza un **agente traductor** por fragmento con el prompt de la sección 5. Corre de 5 a 8 agentes a la vez.
3. Para llenar el prompt, toma del `manifiesto.json` el número de párrafos (`parrafos`) de cada fragmento.
4. Repite `estado` hasta que no quede ningún fragmento por traducir.

### Paso 3: Revisar

1. Detecta los problemas automáticamente:
   ```bash
   node temp/scripts/sermones.js revisar "temp/trabajo/<nombre>"
   ```
2. Revisa los errores **estructurales** de cada fragmento: párrafos, notas, secciones, numeración, longitud, texto sin traducir, texto agregado o formato.
   - Si hay errores, **vuelve a traducir** ese fragmento. Borra su `.es.txt`, lanza de nuevo al traductor y agrega al prompt el `detalle` del error.
   - Haz como máximo 2 intentos por fragmento. Si sigue fallando, anótalo para el reporte final y continúa con los demás.
3. Lanza un **agente revisor** por cada fragmento que no tenga errores estructurales, con el prompt de la sección 6. El revisor escribe `<clave>.correcciones.json`, que puede ser `[]` si no hay cambios.
4. Aplica las correcciones:
   ```bash
   node temp/scripts/sermones.js aplicar "temp/trabajo/<nombre>"
   ```
   El fragmento queda `REVISADO` si todas las correcciones se aplicaron y no quedan errores estructurales.
5. Si una corrección falla porque no se encontró el texto exacto, lanza de nuevo al revisor para ese fragmento. Si el problema es simple, corrígelo tú mismo con una edición puntual del `.es.txt` y vuelve a ejecutar `aplicar` con un `[]`.

### Paso 4: Unir, poner metadatos y generar el HTML

1. Une los fragmentos:
   ```bash
   node temp/scripts/sermones.js unir "temp/trabajo/<nombre>"
   ```
   El comando imprime los primeros 4 párrafos de cada sermón. Úsalos para el paso siguiente sin leer el archivo completo.
2. Edita el `manifiesto.json`. En `comun`, pon `autor`, `fecha` y `destino`. En cada sermón, llena estos campos:

   | Campo             | Qué poner                                                                                                                                                                                                                         |
   | ----------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
   | `titulo`          | Título en español, sin el "SERMÓN VI:". Sigue el estilo de los archivos que ya existen en el destino. En Edwards se usa mayúscula en cada palabra: `La Agonía De Cristo`.                                                         |
   | `titulo_original` | Título en inglés, sin el número de sermón: `Christ's Agony`.                                                                                                                                                                      |
   | `saltar_parrafos` | Cuántos párrafos iniciales se omiten porque ya van en el `<h1>`. Normalmente `1`, la línea del título.                                                                                                                            |
   | `versiculo`       | `"auto"` si después del título vienen la referencia y luego el versículo (el caso normal en un sermón). `null` si es un tratado sin texto bíblico. También puede ser `{"referencia": "...", "texto": "..."}` si el orden es otro. |
   | `id`              | Déjalo en `null` para numerar automáticamente, o pon un número romano.                                                                                                                                                            |
   | `omitir`          | `true` para no publicar ese bloque.                                                                                                                                                                                               |

3. Genera los HTML:
   ```bash
   node temp/scripts/sermones.js html "temp/trabajo/<nombre>"
   ```
   - Los ids se asignan en orden, después del último id de la carpeta.
   - Si el archivo ya existe, se conserva su id. En ese caso, para reemplazarlo usa `--sobrescribir`.
   - El comando imprime el versículo y el primer párrafo de cada sermón. Revisa que el versículo no sea en realidad el título ni la referencia. Si lo es, ajusta `saltar_parrafos` o `versiculo` y repite con `--sobrescribir`.
   - Para una vista previa sin tocar el repositorio, usa `--salida <carpeta>`.

### Paso 5: Validar

1. Valida la carpeta destino:
   ```bash
   node temp/scripts/sermones.js validar "<destino>"
   ```
   El comando revisa lo siguiente:
   - Que el formato del `README.md` se cumpla: atributos `data-*`, `<title>`, un solo `<h1>`, solo etiquetas permitidas, sin estilos ni `<div>` extra, y que las rutas `../` existan.
   - Que la numeración de la carpeta sea consecutiva, sin ids repetidos ni huecos.
   - Que los sermones estén bien separados: un encabezado "SERMÓN …" a mitad del archivo indica dos sermones unidos, y un texto muy corto indica un sermón cortado.
   - Que no queden restos: texto en inglés, markdown, `@@`, `PENDIENTE` o "Here is the translation".
2. Corrige todos los **ERROR** que vengan de los archivos que acabas de crear. Hazlo en el manifiesto o en `sermones/sNN.es.txt`, y vuelve a ejecutar `html --sobrescribir`. Los **avisos** se revisan y se mencionan en el reporte.
3. Regenera el índice y calcula los vectores de la búsqueda por sentido de los textos nuevos (quedan en `vectores/` para el commit):
   ```bash
   node createToC.js
   npx --yes prettier@3.3.3 --write index.html
   node crearVectores.js
   ```

### Paso 6: Reporte final al usuario

Entrega al usuario un resumen corto con lo siguiente:

- Los archivos creados, con su id y título.
- Los fragmentos que no se pudieron revisar y por qué.
- Los avisos de `validar` que quedaron.
- Cuántas correcciones de vocabulario se aplicaron, por término. Sale de los archivos `*.correcciones.aplicadas-*.json`.

**No hagas commit ni borres la carpeta de trabajo** a menos que el usuario lo pida.

### 4.1. Libros de varios autores (`autor: varios`)

Algunas colecciones reúnen sermones de muchos predicadores. Estos libros **no se reparten** entre las carpetas de cada autor: se publican juntos, en el orden del libro, dentro de `siglo/<siglo>/Varios Autores/<Título del libro en español>/`.

- **Una carpeta por serie original, no por volumen.** Si el libro reúne varias obras originales, cada una con su propia numeración y su propio año, crea una carpeta por obra. Ponle un número al inicio para que el índice respete el orden del libro, y el año al final: `1 El Ejercicio Matutino De Cripplegate (1661)`. Una serie puede empezar en un volumen y seguir en el siguiente, pero va en la misma carpeta.
- **Ids = número del sermón en el libro.** `SERM. 6.` lleva el id `VI`. Los prefacios llevan el id `0`: van antes del sermón I y el índice los muestra como "Prefacio". Si una serie tiene dos prefacios (por ejemplo, una dedicatoria y un prefacio al lector), únelos en un solo archivo antes de dividir. Para eso, quita la línea de encabezado del segundo para que no se corte ahí.
- **Un volumen por carpeta de trabajo.** Cada volumen tiene su propio original y su propia carpeta de trabajo (`temp/trabajo/<libro>-vol1/`). Como un volumen puede tener más de una serie, `destino`, `fecha` e `id` se llenan **en cada sermón**, no en `comun`.
- **El autor va en cada sermón.** Deja `comun.autor` en `null` y llena `autor` en **cada** sermón del `manifiesto.json`. Tómalo del encabezado del sermón (por ejemplo, `… - REV. THOMAS MANTON`). Si falta en algún sermón, `html` lo salta y te lo dice. En los prefacios, usa la firma que aparece al final.
- **Cómo escribir el nombre:** sin títulos ni grados (`Rev.`, `D.D.`, `M.A.`), con mayúscula inicial y el nombre de pila en inglés: `Thomas Manton`, `Richard Baxter`. Si el autor ya tiene carpeta en `siglo/` (p. ej. `William Bates`), escríbelo igual que esa carpeta. Usa siempre la misma forma para el mismo autor.
- **El prompt del traductor** recibe en `{{autor}}` el autor de ese sermón, no `varios`.
- **Títulos.** Muchos títulos son preguntas (`How may we be universally and exactly conscientious?`). Tradúcelos como preguntas, con `¿…?`, y con mayúscula en cada palabra, como en el resto del proyecto. El nombre del archivo se genera sin `¿ ? ¡` ni los caracteres no válidos en Windows (` / : * " < > |`). El `<title>` y el `<h1>` sí llevan los signos.
- **Versículo unido.** Si el texto bíblico viene en un solo párrafo con la forma `texto del versículo.— Referencia.`, usa `"versiculo": "unido"`. Así `html` separa el texto y la referencia en el `<blockquote>`. El traductor debe conservar esa forma.
- **Índice.** El índice muestra el autor de cada sermón cuando la carpeta de autor tiene `"coleccion": true` en `indice/autores.json` (ya está así para `Varios Autores`). Si usas otro nombre de carpeta para una colección, agrégala ahí. Para un autor nuevo, agrega también sus años de vida en ese archivo; `createToC.js` avisa de los autores que no los tienen.

**Ejemplo: _Puritan Sermons 1659–1689: The Morning Exercises at Cripplegate_** (6 volúmenes, 161 sermones, 75 autores). El script `temp/trabajo/cripplegate-preparar.js` llena los manifiestos de `temp/trabajo/cripplegate-vol1` a `-vol6`: serie, destino, fecha, id, autor, título original y versículo. Los originales se recortaron antes de dividir: se quitó el índice del inicio y se unieron los dos prefacios de las series 5 y 6. Se divide con `--multiple --patron "^(SERM|PREF). ?[0-9]*.? "`. El prefacio del editor (Nichols, 1844) va con `"omitir": true`.

Herramientas de esta obra, todas en `temp/trabajo/`:

- `cripplegate-traductor.md` y `cripplegate-revisor.md`: las instrucciones de los agentes. El prompt de cada agente solo dice "Lee y sigue las instrucciones de …", la carpeta y la lista de fragmentos. Así cada lanzamiento cuesta poco contexto al orquestador.
- `cripplegate-lotes.js <serie> [--revisar]`: lista los lotes pendientes, de hasta 4 fragmentos seguidos del mismo sermón para traducir y de 5 a 8 para revisar. Claude Code permite como máximo 20 agentes a la vez.
- `cripplegate-filtrar-citas.js <trabajo>`: se ejecuta **antes de `aplicar`**. Separa las correcciones que solo acercan una cita a la RV1960 de memoria, porque los revisores sin la Biblia a la vista cometían errores (por ejemplo, "Aminadib" o "No será yo avergonzado"). Las guarda en `<clave>.correcciones.citas-descartadas.json`.
- `cripplegate-lotes-revision.js <serie> [--max 15] [--parrafos 110]`: agrupa en lotes para el revisor los fragmentos con `.revision.json` y sin `.correcciones.json`, solo de sermones ya traducidos por completo. Ojo: también incluye fragmentos cuyo revisor sigue trabajando; con revisores en curso hay que restar a mano las claves ya lanzadas.
- `cripplegate-titulos.js <serie> [--simular]`: después de `unir`, pone `titulo` en los manifiestos a partir del encabezado traducido (quita "SERM. N." y "- REV. NOMBRE" y pone mayúscula inicial en cada palabra). Los títulos corregidos a mano van en `AJUSTES` ("volN/sNN"). Si cambias un título después de generar el HTML, borra el archivo viejo, porque el nombre cambia.
- Antes de `html`, en los prefacios con dos partes (series 2, 5 y 6) se marca el segundo encabezado con `## ` directamente en `sermones/sNN.es.txt`.
- Al final de cada serie: limpieza "de el"/"a el" → "del"/"al" solo en los fragmentos de esa serie, y búsqueda de falsos cognados que los revisores tienden a aceptar (ingenuo, graciosa, pretender).

Lecciones de la serie 1:

- El revisor tiende a "corregir" citas bíblicas de memoria. Su instrucción ahora lo prohíbe: solo corrige una cita si cambia el sentido.
- Los nombres de archivo largos se cortan solos con " ---" (máximo 70 caracteres), como en el resto del proyecto, para no pasar el límite de rutas de Windows.
- `"versiculo": "unido"` corta en el último guion seguido de espacio. Así "Heb. 6:4—6" queda completo.

### 4.2. Obras completas de un autor transcritas con OCR

**Ejemplo: _The Complete Works of Thomas Brooks_** (Grosart, 6 volúmenes; el vol. 1 trae la biografía de Brooks y cuatro obras). Se publica **una carpeta por obra** en `siglo/XVII/Thomas Brooks/<Obra>/`, con un HTML por división principal (capítulo, artimaña, objeción). La epístola y el prólogo al lector van con id `0`. La biografía del editor va aparte, en la carpeta del autor (`Vida De Thomas Brooks`). El prefacio del editor y los documentos del apéndice de la biografía no se publican.

Herramientas, todas en `temp/trabajo/`:

- `brooks-preparar.py <vol>`: corta el `.txt` del OCR en piezas, por rangos de líneas fijados a mano en el script (uno por HTML), y escribe `original-marcado.txt` y `plan.json`, con destino, fecha, id, `saltar_parrafos`, `versiculo` y título original de cada pieza. Además hace dos cosas:
  - Pasa cada nota del bloque `__________` a su propio párrafo, porque el README pide un `<p>` por nota.
  - En la primera artimaña de cada grupo, mueve el encabezado del grupo (`## II. Las diversas artimañas…`) después del de la artimaña (`### Artimaña (1)…`). Así `saltar_parrafos: 1` quita solo el título de la artimaña, que va en el `<h1>`, y el del grupo queda como `<h2>`.
- `brooks-manifiesto.py <vol>`: después de `dividir --multiple`, copia `plan.json` al manifiesto.
- `brooks-traductor.md`, `brooks-revisor.md`: las instrucciones de los agentes.
- `brooks-siguiente.js <vol> <N> [--revisar]`: entrega los siguientes N lotes y lleva el registro de los lanzados (ver las lecciones del volumen 2). Reemplaza el uso manual de `brooks-lotes.js` mientras hay agentes en curso.
- `brooks-lotes.js <vol> [--revisar] [--excluir claves]`: lista los lotes pendientes. **Lanza exactamente los lotes que imprime**: al armarlos a mano se quedó fuera un fragmento (s16-f005), que solo apareció con `estado`.
- `brooks-llamadas.md`: instrucciones para un agente que **solo repone llamadas de nota `[n]`** perdidas dentro del texto. Es más barato y seguro que retraducir el fragmento.
- `brooks-titulos-trad.js <vol> [--simular]`: después de `unir`, pone `titulo` (sacado de `### Artimaña (n). …` / `### Obj. n. …`, o fijado a mano en `TITULOS`), `titulo_original` (título de la obra + encabezado inglés) y `versiculo: "unido"` donde corresponde.
- `brooks-comillas.js <vol> [--simular]`: cambia las citas entre comillas simples a «», el estilo de la biblioteca, sin tocar apóstrofos ingleses (`Fuller's`).

Lecciones del volumen 1 (334 fragmentos, 78 HTML):

- **Llamadas de nota perdidas.** Fue el error estructural más común: 28 fragmentos perdieron las `[n]` del texto (s08-f001 perdió las 9) y conservaron los párrafos de las notas. Se repararon con `brooks-llamadas.md`. El traductor ahora tiene una regla que le pide contarlas antes de escribir.
- **Errores del OCR en referencias.** La "l" romana (50) se lee como "1": `Isa. 1. 11` es `Isa. l. 11`, y `Jer. 1. 6` / `Ps. 1. 21` igual. Los traductores lo señalaron. Búscalos en el original con `grep -nE "(Isa|Jer|Ps|Psalm)\.? 1\. [0-9]"`. Antes de traducir, revisa también `xiv 33` y otros versículos imposibles.
- **El filtro de citas** separaba por error correcciones cuyo motivo contenía "rv" dentro de una palabra ("ene**rv**ar"). Ahora busca `\bRV`.
- **Revisores con falsos cognados del siglo XVII**: "holy ingenuity" no es "ingenuidad", sino franqueza o nobleza. Tampoco "corrijas" una cita que ya está en la RV1960 (Sal. 73:17, "Hasta que, entrando en el santuario"). Lee los informes de los revisores: a veces explican cambios dudosos.
- **Etiquetas sin glosario.** "Direction (n)" salió como "Consejo" y como "Dirección" según el agente. Agrega al traductor toda etiqueta repetida de la obra (Direction → Consejo, Duty → Deber, Evil → Mal) y unifica con `grep -oh "^### [^ (.]*" *.es.txt | sort | uniq -c`.
- **`validar` no entra en subcarpetas.** Ejecútalo en cada carpeta de obra.

Lecciones del volumen 2 (366 fragmentos, 47 HTML, 3 obras):

- **Notas de capítulos partidos.** En los capítulos largos que se cortan en varios HTML, el OCR deja todas las notas en un bloque al final del capítulo. `brooks-preparar.py` ahora mueve cada nota a la pieza donde está su llamada: en este volumen movió 372.
- **La regla de contar llamadas funcionó:** 0 llamadas perdidas, frente a 28 fragmentos en el volumen 1. Varios agentes avisaron que corrigieron solos alguna que se les había pasado.
- **`brooks-siguiente.js <vol> <N> [--revisar]`** entrega los N lotes siguientes y anota en `lanzados-v<vol>.txt` los fragmentos ya lanzados. Así no se lanza un fragmento dos veces ni se olvida ninguno, aunque los agentes terminen en desorden. Esta vez no faltó ningún fragmento.
- **Revisores fuera de su lista:** un revisor revisó también la clave siguiente a su lista y pisó el archivo de otro. El prompt ahora dice "Claves (revisa solo estas): …".
- **RV1960 "corregida" otra vez:** un revisor cambió "con amor inalterable" (Ef. vi. 24, RV1960) por "con sinceridad", siguiendo la KJV, y el motivo no decía "RV", así que el filtro no lo separó. Lee los informes: cuando un revisor dice "la cita X dice Y en el inglés", comprueba si la traducción ya es la RV1960.
- **"END OF VOL. II."** queda como último párrafo del volumen: quítalo del `.en.txt` y del `.es.txt` antes de `unir`.
- **Títulos de otras obras de Brooks dentro del texto:** los agentes los traducen cada uno a su manera («Hilo de perlas», «Sarta de perlas»). Al final, unifícalos con el título publicado (`grep -oh "«[^»]*perlas»" *.es.txt`).
- En Git Bash, `grep "[А-Я]"` da falsos positivos con las letras acentuadas. Para buscar caracteres cirílicos usa Node (`/[Ѐ-ӿ]/`).

Lecciones del volumen 3 (344 fragmentos, 28 HTML, 2 obras):

- **Llamadas de nota:** 0 perdidas otra vez. La regla del traductor y la redistribución de notas de `brooks-preparar.py` bastan.
- **El límite de 20 agentes lo impone también el entorno:** el lanzamiento que pasa de 20 falla ("Concurrent subagent limit reached"), pero `brooks-siguiente.js` ya anotó esos lotes como lanzados. Lánzalos en cuanto se libere un hueco, sin volver a pedirlos.
- **Revisión mientras se termina la traducción:** se puede empezar a revisar los sermones ya completos. Después, vuelve a correr `revisar` sobre todo el volumen para que los últimos fragmentos tengan su `.revision.json` antes de repartirlos.
- **Correcciones de los revisores que hay que leer antes de `aplicar`:** de 64, cinco estaban mal o eran peligrosas:
  - Invirtieron el sentido: "perish or else overcome" → "será vencido"; "fresh" (pez de mar que sigue siendo de agua dulce) → "fresco".
  - Un reemplazo de párrafo entero (`texto`) apuntaba al número de párrafo equivocado y habría borrado otro párrafo. Prefiere convertirlo en `buscar`/`reemplazar`.
  - Dos fueron paráfrasis más libres que el original. Busca en el `.en.txt` la frase de cada corrección que cambie el sentido.
- **Citas bíblicas cambiadas por el traductor:** en 2 Tes. ii. 10-12 el traductor puso otro versículo del pasaje (v. 12) en lugar del que cita Brooks (v. 10), y el revisor lo dejó. Cuando un revisor avisa "la traducción dice X y el inglés Y", compruébalo.
- **"Isa. I. 10"** (con I mayúscula) también es `Isa. l. 10`, capítulo 50; corrígelo en el `.es.txt`.
- **Cursiva markdown:** un traductor puso `*plenitudo fontis*`. Busca `\*[^ ]` en los `.es.txt`; los asteriscos de las notas de portada del original sí se dejan.
- **Apóstrofos sueltos del original** (`telarañas;'[779]`): `brooks-comillas.js` no los toca porque no tienen pareja. Quítalos a mano (`grep -o ".\{0,30\}'.\{0,20\}" *.es.txt`).
- Los títulos de piezas largos se cortan en el nombre del archivo con `---` (`… Peligrosa Del ---.html`). Si no te gusta, acorta el título en `TITULOS` antes de `html`.

Lecciones del volumen 4 (321 fragmentos, 24 HTML, una sola obra de 58 sermones):

- **Una obra larga sin capítulos:** las secciones de 100k a 160k caracteres (las 16 señales, los 15 motivos, la objeción 4) se cortaron en sus puntos numerados (`1.`, `5. Fifthly`, …), con `tramos()`, en piezas de 40k a 100k. El título del HTML lleva el rango: «Señales De La Verdadera Santidad (1-5)».
- **Falsos cognados nuevos que pasaron al traductor:** «gracious» → «agraciado» (un fragmento entero) y «graciosamente». Búscalos con `grep -oi "agraciad\|graciosa\?mente\|gracios[oa]s\?"` antes de revisar; el revisor solo ve las alertas de su fragmento.
- **El traductor cambia rangos de versículos** («Mat. ix. 1-9» → «1-6») y referencias erróneas del original («Heb. vi. 7» → «2 Cor. vii. 1»). La regla es conservar los números de Brooks: compáralos cuando un revisor lo avise.
- **Sustituciones globales con `sed`:** `s/posición/tesis/g` también cambió «disposición» y «oposición» («distesis», «otesis»). Usa límites de palabra (`\bposición\b`) y revisa el resultado con `grep -o "[a-z]*tesis"`.
- **`html` no sobrescribe:** si corriges un `.es.txt` después de generar los HTML, vuelve a correr `unir`, `brooks-titulos-trad.js` y `html … --sobrescribir`. Sin esa opción, `html` solo avisa que el archivo ya existe y deja la versión vieja.
- **"profession" sin «de fe»:** fue la corrección más frecuente de los revisores (unas 20 de 63). Conviene que el traductor escriba «profesión de fe» cuando se trata de la religión.

Lecciones del volumen 5 (406 fragmentos, 31 HTML, tres obras: *La llave de oro*, *El paraíso abierto*, *Una palabra a tiempo*):

- **Un volumen con varias obras:** cada obra tiene su epístola como id 0 y su propia carpeta. Los números de pieza se reinician en cada obra (`id` I, II… dentro de cada una), y `OBRAS` de `brooks-titulos-trad.js` lleva una entrada por obra.
- **El traductor completa los versículos de memoria:** en Juan x. 18 y xvii. 4 agregó frases de la RV1960 que Brooks no cita. Y en Heb. x. 12 dejó «para siempre» donde lo pone la RV1960, no donde lo pone Brooks (con «se sentó»), aunque el argumento depende de eso. El revisor lo detecta comparando con el inglés. Acepta esas correcciones.
- **Correcciones de los revisores que hubo que rechazar o ajustar** (6 de 90):
  - En Joel i. 4 invirtieron oruga/saltón, que la traducción ya tenía como la RV1960.
  - Una corrección cambió «seria y sinceramente» por «seriamente y sinceramente», que no corrige nada.
  - Otra apuntaba al párrafo 3 cuando la frase estaba en el 2. Antes de `aplicar`, comprueba que cada `buscar` esté en su párrafo.
  - Las demás traducían el falso cognado con otra palabra poco natural («alma regenerada» por «gracious soul»); se cambiaron a las del glosario.
- **Falsos cognados nuevos:**
  - exquisite (torments) → «intensísimos», «atroces», no «exquisitos». Salió en 5 fragmentos.
  - security (carnal) → «despreocupación», «seguridad carnal».
  - vexation → «aflicción».
  - ingenuity → «franqueza».
  - sensible sinner → «pecador despierto».
  - concernments → «intereses».
  - conceited god → «dios imaginario».
  - convictions (de pecado) → «conciencia de culpa»: un fragmento tenía 16 casos de «convicciones».
- **Títulos de las obras de Brooks citados en el texto:** cada traductor inventa el suyo («Hilo de perlas», «Un collar de perlas», «La llave privada del cielo»). Busca `grep -ohiE "(sarta|hilo|collar|cadena) de perlas|llave (secreta|privada) del cielo|…"` y unifícalos con los nombres de las carpetas publicadas.
- **Asteriscos de Grosart:** las notas de portada que empiezan con `* ` dan falsos positivos estructurales en las epístolas. Márcalas como revisadas en el manifiesto; el vol. 3 ya las publicó así.
- **Tratamiento:** en las epístolas a una persona («Sir», «Madam») se usa «usted» y «su». Los revisores corrigieron un «tu alma» suelto.

Lecciones del volumen 6 (305 fragmentos, 29 HTML, siete obras: *Las lamentaciones de Londres* y seis sermones sueltos con su epístola):

- **Obras de un solo sermón:** cada una lleva su carpeta, con la epístola (y la nota de Grosart) como id 0 y el sermón como id I. *Un cordial celestial*, que no tiene epístola, va como un único HTML con id I.
- **Una obra de un millón de caracteres** (*London's Lamentations*) se cortó en 18 piezas de 20k a 100k siguiendo sus listas: los 13 pecados, los 13 apoyos y los 16 deberes. Para ver dónde cortar, sirve listar los párrafos que empiezan con `^[0-9]+\. ` y con `\(n\.\)`, con su posición acumulada en caracteres (`awk '{c+=length($0)} /^[0-9]+\. /{print NR, c}'`).
- **Falsos positivos estructurales antes de revisar:** si marcas `revisado` en el manifiesto antes de lanzar a los revisores, `brooks-siguiente.js --revisar` se salta esos fragmentos y no los revisa nadie. Márcalos después de `aplicar`, cuando `estado` los deja como pendientes solo por los asteriscos de Grosart.
- **"improve" → «mejorar»:** fue el falso cognado más frecuente (un fragmento tenía 13 casos). Le siguen «exquisito», «afecciones», «profesores» y «divierte» (amuse = desconcertar). Los revisores los corrigieron, pero conviene buscar `mejor[ao]` cerca de «gracia», «tiempo», «hacienda».
- **Correcciones que agregan una oración omitida:** revisa la puntuación del punto de unión. En s13-f002 el `reemplazar` dejaba una mayúscula después de punto y coma.
- **Revisores que dejan errores con «me pareció defendible»:** «my glass is out» quedó como «mi candela se apagó» (es el reloj de arena). Lee las «dudas» de los informes; a veces son errores reales.

### 4.3. Un volumen de obras selectas (varias obras de un autor)

**Ejemplo: _Select Works of Thomas Watson_** (edición de 1855, a dos columnas; 642 fragmentos, 113 HTML). El volumen tiene *A Body of Practical Divinity* (el Catecismo Menor, los Diez Mandamientos y el Padrenuestro), siete sermones, *The Art of Divine Contentment* y cuatro tratados. Se publicó en `siglo/XVII/Thomas Watson/` con **una carpeta por obra**:

- `Un Tratado De Teología Práctica`, `Los Diez Mandamientos` y `El Padrenuestro`: las tres partes del *Body*, cada una en su carpeta.
- `Sermones Selectos`.
- `El Arte Del Contentamiento Divino`: un HTML por capítulo.
- `Tratados`: un HTML por tratado.
- `Vida De Thomas Watson`: la noticia biográfica, en la carpeta del autor.

Herramientas, todas en `temp/trabajo/`:

- `watson-preparar.py` corta el libro por zonas (`ZONAS`: líneas, destino y fecha) y por los títulos `## ` del OCR. Las secciones muy largas se cortan además en las líneas de `CORTES`, con su título inglés; los títulos de las primeras partes van en `TITULO_PARTE1`. Cuando el párrafo que sigue al título es «Ref. texto» o «texto, Ref.», lo parte en dos párrafos y pone `versiculo: "auto"`.
- `watson-manifiesto.py` copia el plan al manifiesto.
- `watson-siguiente.js <N> [--revisar]` hace lo mismo que el de Brooks, con 6 fragmentos por lote para traducir y 10 para revisar.
- `watson-arreglos.js` hace los arreglos globales después de `aplicar`.
- `watson-titulos-trad.js` pone los títulos en español.

Lecciones:

- **Ordinales con punto:** los traductores escribieron «1.º. El espíritu…» 291 veces (Watson usa «1st.»). `watson-arreglos.js` lo cambia a «1.º El espíritu…». Conviene que el traductor lo sepa de antemano: «1st,» → «1.º,», «1st.» → «1.º».
- **Párrafos partidos por el OCR a media frase:** se reconocen porque el párrafo no termina en puntuación y el siguiente empieza en minúscula. Aparecieron 5. Únelos en el `.en.txt` y en el `.es.txt` a la vez, para que sigan correspondiéndose 1 a 1. Búscalos con Node (`!/[.:;?!"”)\]—]$/` seguido de `/^[a-z]/`) y revisa también los límites entre fragmentos.
- **Versículos que `preparar` no reconoció.** Pasó con tres formas, que hay que partir a mano en referencia y texto, con `versiculo: "auto"`:
  - `### Ref. texto` (s52, s84, s87, s90).
  - El texto largo de un mandamiento, de más de 400 caracteres (s56).
  - La referencia con un libro sin punto, como `James iii. 6.`, que la expresión regular no esperaba.
  Revisa en el registro de `html` el «primer párrafo» de cada pieza: si empieza con `###` o con una referencia, falta partirlo.
- **Comillas en el versículo:** unos traductores pusieron el texto del versículo entre «» y otros no. Como va en un `<blockquote>`, se quitaron todas.
- **Capitulares del original:** «EN el primer mandamiento…», «HABIENDO terminado…». Búscalas con Node (`/^\p{Lu}{2,}\p{Ll}/u`, sin los números romanos) y pásalas a «En», «Habiendo».
- **Errores de imprenta en las referencias de los encabezados:** «Exod. xx. 13» en el octavo mandamiento (es xx. 15), «Exod. XX. 16», «Mat. X. 16» y «Gen. i. 25» (es l. 25, porque «God will surely visit you» está en Gén. 50). En los encabezados se corrigieron. Dentro del texto se conserva el número de Watson, salvo que el error sea evidente.
- **Nombres:** el original dice «Barak» en Jer. xlv. 5, pero el pasaje habla de Baruc. Se tradujo «Baruc».
- **El revisor dejaba omisiones «porque el sentido se conserva»** (un término hebreo, un verbo de una cita). El prompt del revisor ahora pide corregir **toda** omisión, aunque sea de una palabra.
- **Correcciones rechazadas (3 de 93):**
  - «put up their shop-windows» traducido como «abren las persianas», cuando significa cerrar la tienda.
  - Una corrección de Deut. vi. 13 que quitaba «solo», que la RV1960 sí tiene.
  - Un cambio innecesario de Prov. xxii. 14.

  Las de citas que **quitan** frases agregadas por el traductor (versículos completados de memoria) se aceptan todas.
- **Un revisor no escribió su archivo** (`s94-f006`), aunque respondió «OK». Antes de `aplicar`, comprueba que cada `.es.txt` tenga su `.correcciones.json`. Otro revisor escribió archivos de claves ajenas y los borró. La clave siguiente tuvo que revisarse igual.
- **Una corrección fallida porque el traductor ya lo había hecho bien:** latín «et en proximum» → «in». Márcala como revisada en el manifiesto.
- **Títulos con dos puntos** («La Primera Petición: Santificado Sea Tu Nombre») se ven bien en el `<h1>` y en el índice. En el nombre del archivo se pierden los dos puntos.

### 4.4. Un volumen de obras completas con ortografía antigua (Perkins)

**Ejemplo: _The Works of William Perkins_, vol. 1** (Londres, c. 1616; 962 fragmentos, 231 piezas, 18 obras, unos 4,4 millones de caracteres). Es el texto transcrito con `ocr.py` (ver `temp/ocr_agent.md`). Se publicó en `siglo/XVI/William Perkins/`, **una carpeta por obra**, y cada obra lleva su propia fecha de primera edición.

Herramientas, todas en `temp/trabajo/`:

- `perkins1-preparar.py` corta el volumen por obras (`OBRAS`: líneas, carpeta y fecha) y por los títulos `## `. Usa estas listas:
  - `QUITAR`: portadillas que no se publican.
  - `BORRAR_TITULO`: títulos que repiten el de la obra.
  - `PREFACIO`: dedicatorias y avisos, que se juntan en el id 0.
  - `JUNTAR`: secciones que van con la anterior.
  - `CORTES_TEXTO`: cortes que no empiezan en un título.
  - `SEPARAR`: piezas cortas que deben quedar solas.

  Las piezas de más de 85.000 caracteres se cortan en partes de unos 65.000, nunca delante de un bloque de notas. Las partes siguientes llevan `saltar 0`.
- `perkins1-manifiesto.py` copia `plan.json` al manifiesto.
- `perkins-siguiente.js` reparte los lotes (6 para traducir, 10 para revisar). Para revisar solo entrega claves que ya tienen `.revision.json`: corre `revisar` otra vez cuando terminen las últimas traducciones.
- `perkins-traductor.md` y `perkins-revisor.md` son las instrucciones de los agentes. Cubren la ortografía de 1600 (vnto, haue, Iesus), las etiquetas (Quest./Answ./Obiect./Vse), el Credo, el Padrenuestro y el Decálogo fijos, y los términos de controversia.
- `perkins1-arreglos.js` hace los arreglos globales después de `aplicar`: notas de imprenta de las tablas, párrafos partidos y capitulares.
- `perkins1-titulos-trad.js` pone los títulos y las partes «(Parte N)». También pone `versiculo` como objeto `{referencia, texto}` en las piezas que empiezan con un texto bíblico, y `saltar_parrafos 2` donde el segundo párrafo es el subtítulo del capítulo.

Lecciones:

- **Ioh. / Iob.:** la edición confunde Juan y Job. La regla del traductor (si el capítulo pasa de 42 o el contexto es del Evangelio, es Juan) funcionó; los revisores corrigieron los casos que quedaban.
- **«Cap. 5. 12» sin libro** remite al mismo libro recién citado. Los primeros traductores inventaban el libro («Apoc.», «Ef.»). La regla está ahora en las dos instrucciones.
- **«Profession»** es casi siempre «profesión de fe». El glosario lo marca en cada aparición y los revisores lo corrigieron unas 15 veces. Pero en *Las vocaciones* («callings and professions») significa oficios: se rechazó esa corrección.
- **Falsos cognados del inglés de 1600** que corrigieron los revisores: «improve» = refutar, «trying» = prueba, «discourse» = plática, «conference» = conversación, «deputy» = delegado, «caled» = calmó, «faith» por «saith».
- **Notas de imprenta de las tablas plegadas** («Place this Table betweene fol. 74. and 75.»): a veces son un párrafo propio y a veces van pegadas al comienzo del párrafo siguiente. Los traductores las tradujeron («Colóquese esta tabla…»). Se quitan después de `aplicar`, en los dos idiomas a la vez.
- **Un traductor desalineó un fragmento** (`s227-f001`): partió un párrafo en dos y omitió el último, aunque el recuento le daba igual. `revisar` lo detectó por longitud (80 % del inglés). Se rearmó a mano. Revisa siempre las alertas de «longitud» antes de lanzar los revisores.
- **Numeración desplazada:** algunos traductores escribieron «Razón II.» u «Obj. IV.» donde el inglés dice «II. Reason.». `revisar` lo marca como error de numeración; se arregla con sed antes de revisar.
- **Interlocutores de los diálogos:** «Ch.» es la Iglesia (*Church*) en la 1.ª de Juan en diálogo y el «Cristiano» en otros diálogos. Un lote lo tradujo mal; el revisor lo corrigió mirando la lista de interlocutores del comienzo.
- **Los revisores Haiku encuentran poco** (152 correcciones en 962 fragmentos, la mayoría vocabulario, citas completadas de memoria y referencias cambiadas). Las alertas de «aprehender» casi siempre son falsos positivos: es la fe que aprehende a Cristo.
- **Ninguna corrección de cita fue de RV1960 «de memoria»:** el filtro no separó ninguna. Las de citas quitaron frases que el traductor había agregado al completar el versículo.

**Vol. 2** (1631; 767 fragmentos, 116 piezas, 8 obras, 3,9 millones de caracteres). Se usaron las mismas herramientas con el prefijo `perkins2-`, y se agregaron dos:

- `perkins2-notas.js [<trabajo>]` corre después de `unir`. El OCR deja las notas al margen al final del capítulo. Cuando un capítulo largo se corta en partes, las notas quedan en otra parte que sus llamadas, y la página de la Parte 1 se publica sin sus notas. El script mueve cada nota «[n] …» a la pieza de la misma obra que tiene la llamada [n]. **El vol. 1 tenía el mismo fallo** (941 llamadas sin nota en 17 piezas): se arregló con este script y se regeneró su HTML. Antes se comprobó que `html --salida` daba los mismos archivos que los publicados. Córrelo siempre en volúmenes con notas al margen y piezas en partes. Para comprobar, cuenta las llamadas que no tienen nota en su pieza: deben ser 0.
- `perkins-v2/comprobar-correcciones.js [--lista]` comprueba antes de `aplicar` que cada «buscar» está en su párrafo y lista todas las correcciones. Los revisores Haiku se equivocaron de número de párrafo en 8 de 102 correcciones; el texto estaba en otro párrafo y se corrigió el número.

Lecciones del vol. 2:

- **Párrafos cortados entre dos fragmentos** («Apo-» al final de uno, «stle» al comienzo del siguiente): `perkins2-arreglos.js` tiene `CRUZAR` para unirlos, además de `UNIR` dentro de un fragmento. El detector `perkins-v2/cortes2.js` encuentra los dos casos.
- **Las alertas de los traductores no siempre se cumplen:** varios avisaron de cortes que no existían. Fíate del detector, no de los informes.
- **Restos del OCR que el traductor copió:** una frase duplicada (`s107-f004`), descripciones del transcriptor en las notas («(nota marginal del margen…)», `s108-f002`) y una «A» suelta (`s69-f002`). Se quitan en los dos idiomas.
- **Los traductores «corrigen» el original en silencio:** en una tabla, «The Rubenites warre» quedó como «La guerra contra los filisteos». Lee las dudas que reportan los revisores y decide tú.
- **Una corrección del revisor era un error del OCR:** «mobilitie» es «nobilitie» (m/n) y no «plebe». Se descartó antes de `aplicar`.
- **«Pretend», «actually», «earnest», «affections», «comfortable»** fueron los falsos cognados más corregidos en este volumen.
- **Pausa a mitad de la revisión:** detén los agentes con TaskStop y quita de `lanzados-rev.txt` las claves que no tienen `.correcciones.json`. Si no, el reparto no las vuelve a dar. Deja el estado en un `REANUDAR.md` en la carpeta de trabajo.
- **Un revisor dijo «OK» y no escribió el archivo** (`s114-f003`). Antes de `aplicar`, cuenta los fragmentos sin `.correcciones.json`.

**Vol. 3** (1631; 1110 fragmentos, 119 piezas, 11 obras, 5,6 millones de caracteres). Se usaron las mismas herramientas con el prefijo `perkins3-`. Cambios en las herramientas:

- `perkins3-preparar.py` tiene `REEMPLAZAR`: cambia una línea del original antes de cortar. Sirve para poner un `## ` donde empieza el comentario y el OCR lo dejó como párrafo («A Godly and Learned EXPOSITION … Matth. 5. 1.» pasa a «## CHAP. 5.» + «### Matth. 5. 1. …») o como `### `.
- Las partes de las piezas largas se cortan, si se puede, antes de un subtítulo `### ` (versículo), hasta 12.000 caracteres después de la meta. Los títulos de las partes son «Mateo 5 (Parte N)», «Hebreos 11 (Parte N)», «Apocalipsis 2 (Parte N)».
- `perkins3-titulos-trad.js`: `VERSICULOS` acepta un tercer valor, `saltar_parrafos` (la *Brujería* tiene título, «### ÉX. 22. 18.» y el versículo: `["Éx. 22. 18", 3, 3]`).
- `perkins3-arreglos.js` quita la puntuación doble tras una referencia («19.:», «10.,»): 404 casos. Es frecuente en todo el volumen.
- `perkins-v3/comprobar-correcciones.js` acepta las correcciones de párrafo completo (`texto`), que el script del vol. 2 no leía.
- `perkins-traductor.md` tiene una sección «Obras del vol. 3»: brujería, pronósticos, gobierno de la familia, Apocalipsis, diálogo Cristiano/Mundano y letra capital perdida.

Lecciones del vol. 3:

- **Un corte de partes puede caer a media frase** cuando el OCR dejó un párrafo partido en dos. `CRUZAR` sirve también entre dos piezas seguidas de la misma obra (`s35-f011` + `s36-f001`). El detector `cortes2.js` no lo ve: compara el último párrafo de cada pieza con el primero de la siguiente.
- **Los traductores cambian el sentido «para que tenga lógica»** cuando el inglés trae un error del OCR («did not say in their hearts», «prone to doe good», «approved» por «reproved»). En estos casos la lectura del traductor era la buena. Revisa sus avisos, pero casi siempre se dejan.
- **Correcciones erróneas de los revisores**, descartadas antes de `aplicar`:
  - «el que vivo» (Apoc. 1:18) cambiado por «el que vive»: la RV1960 dice «el que vivo»;
  - una corrección que borraba palabras («de su profesión pública» → «pública»);
  - una de párrafo completo con el número de párrafo equivocado (`s65-f001`), que pisó el párrafo 3 con el texto del 4. Se rehízo a mano.

  Revisa una por una las correcciones de tipo `texto`.
- **Nombres ingleses en las dedicatorias:** se dejan en inglés (Sir John Savile, no «sir Juan»), como en los vols. 1 y 2. Un traductor los tradujo.
- **El registro del diálogo** (*Fin del mundo*) quedó mezclado: unos lotes usaban «usted» entre Cristiano y Mundano y otros los tuteaban. Se unificó a mano a «usted» en `sermones/s80.es.txt`, sin tocar las citas bíblicas. Conviene fijar el registro en las instrucciones antes de traducir diálogos.
- **Si el sentido del inglés parece absurdo, mira la imagen** (`ocr-perkins-v3/paginas/pNNNN.png`; la página sale de `grep` en `ocr-perkins-v3/texto/`). «wee must have the company … of obstinate sinners» era «must **hate**» en el impreso: el OCR confundió t/v. Se corrigió en el `.txt` del OCR, el original, el fragmento y la traducción.
- **Con 20 agentes a la vez, el volumen entero tomó unas 185 tandas de traducción y 111 de revisión.** Los revisores corrigieron 164 cosas en 1110 fragmentos. La mayoría fueron «profession» → «profesión de fe», «actually», «pretend», «apprehension» → «percepción», frases añadidas a las citas y omisiones.

---

## 5. Prompt del agente traductor

Llena los campos `{{…}}` y pasa el texto tal cual.

```
Eres un traductor profesional de textos teológicos protestantes de los siglos XVI al XIX, del inglés al español.

ARCHIVO A TRADUCIR: {{ruta}}/fragmentos/{{clave}}.en.txt
ESCRIBE LA TRADUCCIÓN EN: {{ruta}}/fragmentos/{{clave}}.es.txt
CONTEXTO: fragmento {{n}} de {{total}} de "{{encabezado_en}}" ({{autor}}).
{{si es un reintento: "INTENTO ANTERIOR RECHAZADO POR: <detalle de los errores>"}}

FORMATO (obligatorio):
- El archivo tiene exactamente {{parrafos}} párrafos separados por una línea en blanco. Tu traducción debe tener exactamente {{parrafos}} párrafos, en el mismo orden: un párrafo inglés = un párrafo español. No unas, dividas, omitas ni agregues párrafos.
- Cada párrafo va en una sola línea, con una línea en blanco entre párrafos.
- Texto plano UTF-8. Sin markdown, sin negritas, sin itálicas, sin listas. No agregues títulos con #. Única excepción: si un párrafo del original empieza con "## " o "### " (marca de título), tu párrafo empieza con la misma marca y luego el título traducido: "## CHAPTER III." → "## CAPÍTULO III.".
- Conserva exactamente los marcadores de nota como [613] y las secciones como § 14. Las notas al final ([613] Rom. ix. 5.) también se traducen y conservan su número.
- Conserva las numeraciones al inicio de los párrafos (1., 2., I., II.). "First," → "Primero,".
- Encabezados: SERMON VI: → SERMÓN VI:, DOCTRINE. → DOCTRINA., APPLICATION. → APLICACIÓN., IMPROVEMENT. → APLICACIÓN., USE I. → USO I., SECT. II. → SECCIÓN II.
- Limita tu respuesta a la traducción. No agregues notas del traductor, comentarios ni explicaciones, ni dentro ni fuera del archivo.

ESTILO:
- Español neutro, formal y fluido, fiel al sentido. No resumas ni omitas nada, aunque parezca repetitivo.
- Cuando el predicador se dirige a la congregación: "you" plural → "ustedes"; "thou" → "tú".
- Citas bíblicas: usa la Reina-Valera 1960 cuando la cita sea reconocible (ahí sí se usa "vosotros"). Si el autor parafrasea, traduce la paráfrasis.
- Excepción: si el predicador explica las palabras del versículo una por una (por ejemplo, el texto del sermón), y la RV1960 usa otras palabras, traduce el inglés de forma literal. Así el versículo coincide con la explicación. Ejemplo: Job 33:23 "a messenger with him, an interpreter, one among a thousand" se traduce "un mensajero, un intérprete, uno entre mil", no "algún elocuente mediador muy escogido".
- Referencias bíblicas: traduce el libro y conserva los números como en el original. Por ejemplo: Matt. v. 8. → Mat. v. 8.; Psal. → Sal.; Gen. → Gén.; Exod. → Éx.; Rev. → Apoc.; Acts → Hch.; John → Juan; James → Sant.; 1 Pet. → 1 Ped.; Eccl. → Ecl.
- Términos: the gospel → el evangelio; natural men → hombres naturales; the saints → los santos; awakened → despertados; ordinances → ordenanzas; means of grace → medios de gracia; the elect → los elegidos; Sabbath → día de reposo; divines → teólogos.
- Presta atención a los términos con varias interpretaciones y elige la más adecuada al contexto teológico y al inglés del siglo XVIII. Evita los falsos cognados:
  - gracious → misericordioso, clemente, benigno, afable, de gracia (NUNCA "gracioso")
  - conviction / convictions / under convictions (sobre el pecado o un juicio) → conciencia de culpa, culpabilidad, convencimiento de pecado, redargüido (NO "convicción", que es una opinión firme)
  - sensible of → consciente de; insensible → indiferente, sin conciencia de
  - apprehension → comprensión, percepción (no "aprehensión")
  - professor (of religion) → profesante, el que profesa la fe (no "profesor")
  - conversation (KJV) → conducta, manera de vivir
  - experimental religion → religión experiencial o vivencial
  - awful → solemne, imponente, temible
  - exquisite (torments) → intensísimos
  - actually → en realidad (no "actualmente")
  - presently → en seguida, pronto
  - realize → darse cuenta, comprender
  - comfortable → consolador, reconfortante
  - improve (time, a mercy) → aprovechar
  - quicken → vivificar
  - for want of → por falta de
  - suffer (= permit) → permitir
  - ingenuous → sincero, noble
  - candid → imparcial
  - solicitous → preocupado, ansioso
  - frame (of mind) → disposición
  - earnest (of the Spirit) → arras
  - abroad → por todas partes

Cuando termines de escribir el archivo, responde solamente: OK {{clave}} <número de párrafos que escribiste>
```

---

## 6. Prompt del agente revisor

```
Eres revisor de traducciones del inglés al español de textos teológicos protestantes de los siglos XVI al XIX.

LEE ESTOS ARCHIVOS:
- Original:    {{ruta}}/fragmentos/{{clave}}.en.txt
- Traducción:  {{ruta}}/fragmentos/{{clave}}.es.txt
- Alertas:     {{ruta}}/fragmentos/{{clave}}.revision.json
ESCRIBE: {{ruta}}/fragmentos/{{clave}}.correcciones.json

Los párrafos de ambos archivos se corresponden 1 a 1 y están separados por líneas en blanco. El párrafo 1 es el primero.

TAREA:
1. Revisa cada alerta de "vocabulario" del archivo de alertas. Compara el párrafo español con el inglés y decide si, en ese contexto, la palabra es un falso cognado. Usa las "sugerencias" y la "nota". Si es un error, corrígelo. Si la palabra es correcta en ese contexto (por ejemplo, "convicción" con el sentido de creencia firme, o "pecado actual"), no la cambies.
2. Lee toda la traducción comparando cada párrafo con el inglés y corrige solo errores reales:
   - omisiones o frases agregadas
   - sentido cambiado o invertido
   - otros falsos cognados
   - citas bíblicas reconocibles que no siguen la Reina-Valera 1960
   - términos traducidos de forma distinta dentro del mismo fragmento
   - restos en inglés
   No cambies el estilo si la traducción ya es correcta y natural.
3. Escribe el archivo de correcciones como un arreglo JSON (UTF-8). Escribe [] si no hay nada que corregir. Cada corrección tiene una de estas dos formas:
   {"parrafo": 4, "buscar": "texto exacto copiado de la traducción", "reemplazar": "texto corregido", "motivo": "gracious ≠ gracioso"}
   {"parrafo": 7, "texto": "párrafo completo corregido", "motivo": "faltaba la segunda oración"}
   - "buscar" debe ser una copia exacta de una parte del párrafo español, lo bastante larga para ser única (de 3 a 8 palabras).
   - Usa "texto", que reemplaza el párrafo completo, solo si falta o sobra una oración entera.
   - No cambies, quites ni agregues marcadores [n], § n ni numeraciones.
   - No uses markdown ni comillas tipográficas distintas de las que ya tiene el texto.

Cuando termines, responde solamente: OK {{clave}} <número de correcciones>
```

---

## 7. Referencia de comandos

| Comando                                                                           | Qué hace                                                                                                                                                                                                      |
| --------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `candidatos <original>`                                                           | Lista las líneas que parecen encabezados, con su número de línea, para decidir los cortes con `--multiple`.                                                                                                   |
| `dividir <original> <trabajo> [--multiple] [--patron re] [--max 6000] [--forzar]` | Crea el manifiesto y los fragmentos `.en.txt`.                                                                                                                                                                |
| `estado <trabajo>`                                                                | Muestra el avance y las claves por traducir y por revisar.                                                                                                                                                    |
| `revisar <trabajo> [clave…]`                                                      | Compara inglés y español y escribe `<clave>.revision.json`.                                                                                                                                                   |
| `aplicar <trabajo> [clave…]`                                                      | Aplica `<clave>.correcciones.json`, revalida y marca el fragmento como revisado.                                                                                                                              |
| `unir <trabajo>`                                                                  | Junta los fragmentos de cada sermón en `sermones/sNN.es.txt`.                                                                                                                                                 |
| `html <trabajo> [--solo s01] [--sobrescribir] [--salida dir]`                     | Genera los HTML del proyecto con los ids, las rutas `../`, los acentos como entidades y el ajuste a 80 columnas.                                                                                              |
| `validar <carpeta o archivo> [--recursivo]`                                       | Revisa el formato, la numeración y la separación. Termina con código 1 si hay errores.                                                                                                                        |
| `escanear <carpeta o archivo> [--todo] [--json casos.json]`                       | Busca falsos cognados en traducciones ya publicadas. Sin el inglés al lado, solo usa los términos de alta precisión, a menos que se pase `--todo`. Con `--json` exporta cada caso con su contexto en español. |
| `corregir <decisiones.json> [--simular]`                                          | Aplica decisiones `{"archivo", "buscar", "reemplazar"}` directamente en los HTML publicados. Encuentra el texto aunque tenga entidades (`&aacute;`) o saltos de línea.                                        |

### Revisar traducciones ya publicadas (sin el original en inglés)

1. Exporta los casos: `node temp/scripts/sermones.js escanear siglo --json temp/trabajo/cognados/casos.json`.
2. Divide los casos en lotes de unos 170, sin partir un mismo archivo entre lotes.
3. Lanza un agente revisor por lote. Cada uno decide `cambiar`, `mantener` o `duda` por caso, usando solo el contexto en español.
4. Une las decisiones, aplica con `corregir --simular` y luego sin `--simular`.
5. Pregúntale al usuario por los casos `duda`, porque puede consultar el original en inglés.

Todos se ejecutan como `node temp/scripts/sermones.js <comando> …`.

---

## 8. Glosario de falsos cognados

`temp/scripts/falsos-cognados.json` es una lista de entradas como esta:

```json
{
  "termino": "gracious",
  "en": "\\bgracious(ly|ness)?\\b",
  "es": "\\bgracios(o|a|os|as|amente)\\b",
  "solo_es": true,
  "sugerencias": ["misericordioso", "clemente", "benigno", "afable"],
  "nota": "En español 'gracioso' significa chistoso..."
}
```

- `es` es una expresión regular que se busca en el español, sin acentos y en minúsculas. Por eso se escribe `conviccion` y no `convicción`.
- `en` es una expresión regular que se busca en el **párrafo inglés correspondiente**. La alerta solo salta si aparecen los dos. Esto evita falsas alarmas: si "convicción" viene de "persuasion", no se marca.
- `solo_es: true` indica que el término casi siempre es error, aunque no se vea el inglés. Esas entradas son las que usa `escanear`.

Para agregar un término nuevo, agrega una entrada y pruébalo con `revisar` sobre un fragmento donde aparezca.
