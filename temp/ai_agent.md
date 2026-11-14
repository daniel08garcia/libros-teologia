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
- Texto plano UTF-8. Sin markdown, sin negritas, sin itálicas, sin listas, sin títulos con #.
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
