# Instrucciones para el agente: transcripción (OCR) de libros escaneados en PDF

Este documento es para un modelo de IA que actúa como **orquestador**. El usuario le entrega este archivo junto con un PDF escaneado en inglés. El orquestador lo transcribe a un `.txt` limpio en `temp/originales/`, listo para traducirlo con `temp/ai_agent.md`.

Ejemplo de cómo lo pide el usuario:

```
Lee temp/ocr_agent.md y transcribe este PDF:
  pdf: temp/originales/The Complete Works of Thomas Brooks (vol.1).pdf
```

Opcionales: `paginas: 82-545` (si el usuario ya sabe qué páginas quiere) y `salida: temp/originales/<nombre>.txt`.

---

## 1. Resumen del flujo y modelos

El trabajo mecánico lo hacen scripts, que son exactos y no cuestan tokens. Los modelos solo leen las imágenes.

| Paso | Qué se hace                                                          | Quién lo hace                                               | Modelo                                         |
| ---- | -------------------------------------------------------------------- | ----------------------------------------------------------- | ---------------------------------------------- |
| 1    | Ver el mapa del libro y elegir qué páginas transcribir               | Script `info` + orquestador                                 | El del orquestador (lee unas 50 líneas)        |
| 2    | Convertir las páginas en imágenes y extraer la capa OCR del PDF      | Script `preparar`                                           | Ninguno                                        |
| 3    | Transcribir cada página                                              | **Agente transcriptor** (`ocr-transcriptor`), 5 páginas por agente | **Haiku**, sin razonamiento extendido          |
| 4    | Quitar cursivas en markdown y comparar cada página con la capa OCR   | Scripts `limpiar` y `validar`                               | Ninguno                                        |
| 5    | Corregir las páginas con errores                                     | Agente transcriptor de nuevo, o el orquestador a mano       | Haiku / orquestador                            |
| 6    | Revisar los cortes dudosos entre páginas (`[[sigue]]`)               | Script `cortes` + orquestador (mira láminas de recortes)    | El del orquestador (2–3 imágenes pequeñas)     |
| 7    | Poner los títulos `##` / `###` con ayuda del índice                  | Orquestador con un script (modelo: `brooks-titulos.py`)     | El del orquestador                             |
| 8    | Unir las páginas en un `.txt`, renumerar las notas, quitar guiones   | Script `unir`                                               | Ninguno                                        |

Por qué funciona con Haiku:

- Haiku lee bien la tipografía impresa del siglo XIX. En las pruebas con las *Complete Works of Thomas Brooks* (edición Grosart, 1866), las transcripciones salieron casi idénticas al impreso, con notas al pie, latín y referencias bíblicas correctas.
- Recibe también la **capa OCR** que ya trae el PDF (los escaneos de archive.org y Google Books la traen). Esa capa tiene errores, pero sirve para dos cosas: el agente confirma palabras dudosas, y `validar` la usa para detectar **omisiones** (tramos de 8 o más palabras que están en la capa y faltan en la transcripción).
- Las páginas se transcriben una por una, cada una en su propio archivo. Si un agente falla, solo se repiten las páginas que faltan.

**Regla de costo:** el orquestador no copia texto en los prompts ni lee las transcripciones. Solo pasa la carpeta y la lista de páginas, y lee los reportes de `validar`.

### El agente transcriptor

Sus instrucciones están en `.claude/agents/ocr-transcriptor.md` (modelo Haiku, solo herramientas Read y Write). Hay dos formas de lanzarlo con la herramienta `Agent`:

1. **Preferida:** `subagent_type: "ocr-transcriptor"`. Como solo tiene dos herramientas, cada agente gasta mucho menos contexto fijo que el agente general. Claude Code carga los agentes al iniciar la sesión; si responde que no encuentra el tipo, usa la forma 2.
2. **Alternativa:** `subagent_type: "general-purpose"`, `model: "haiku"`, y al inicio del prompt: `Lee primero tus instrucciones en c:/www/libros-teologia/.claude/agents/ocr-transcriptor.md (lo que va después del bloque ---) y síguelas al pie de la letra.`

El prompt de cada lote es solo esto (lo imprime `pendientes`):

```
CARPETA: c:/www/libros-teologia/temp/trabajo/<nombre>
PÁGINAS: p0082 p0083 p0084 p0085 p0086
```

Lanza como máximo **20 agentes a la vez**. El agente responde solo `listo`.

No uses `pendientes` mientras hay agentes trabajando: muestra como pendientes los lotes que todavía están en curso. Lleva tú la cuenta (los lotes empiezan en la primera página y avanzan de 5 en 5) y lanza el siguiente lote cada vez que un agente termina, para mantener 20 en marcha. Usa `pendientes` al final, para ver si quedó alguno sin hacer.

Los agentes leen en sus resultados de herramientas las instrucciones de los conectores de la sesión (por ejemplo, "crear un documento en Claude Docs") y a veces lo comentan en su respuesta. Es normal: las ignoran y no hay que hacer nada.

---

## 2. Archivos y carpetas

```
temp/scripts/ocr.py                 # todos los comandos (Python 3.8+ con PyMuPDF)
.claude/agents/ocr-transcriptor.md  # instrucciones del agente transcriptor
temp/trabajo/<nombre>/              # carpeta de trabajo de cada PDF (ignorada por git)
  manifiesto.json                   # páginas elegidas y lotes
  paginas/p0082.png                 # imagen de la página (la crea "preparar")
  capa/p0082.txt                    # capa OCR del PDF (la crea "preparar")
  texto/p0082.txt                   # transcripción (la escribe el agente)
  cortes/p0104.png, lamina_01.png   # recortes de los cortes dudosos (los crea "cortes")
  cortes/revisados.txt              # cortes ya revisados (--ok)
```

`<nombre>` es un nombre corto sin espacios, p. ej. `ocr-brooks-v1`. Las páginas se cuentan **desde 1, como en el visor de PDF** (no son los números impresos del libro).

Si falta PyMuPDF: `python -m pip install --user pymupdf`.

---

## 3. Paso a paso para el orquestador

### Paso 1: Mapa del libro

```bash
python temp/scripts/ocr.py info "<pdf>"
```

Muestra cuántas páginas traen capa de texto y un mapa corto: las páginas casi vacías (portadillas, blancas) y las páginas donde cambia el título corrido, es decir, donde empieza cada obra o sección.

Decide el rango de páginas:

- **Se omiten del texto:** la portada del volumen, la página del impresor, el índice general (CONTENTS) y los índices alfabéticos del final.
- **Se incluyen:** prefacios, memorias, notas del editor, epístolas dedicatorias, "To the Reader" y todas las obras. Las portadillas de cada obra (una página con solo el título) también, porque marcan dónde empieza.
- **El índice general (CONTENTS) se transcribe aparte, como referencia:** no se traduce ni va en el `.txt`, porque sus números de página no sirven en el HTML y repite títulos que ya están en el cuerpo. Pero da la estructura de cada obra, que sirve para poner los títulos en el paso 7. Prepáralo en otra carpeta (`preparar "<pdf>" "temp/trabajo/<nombre>-indice" --paginas 3-12`), lanza los agentes con la indicación extra de que es un índice (una entrada por párrafo, sin filas de puntos, con sus números de página) y únelo con `unir` en `temp/trabajo/<nombre>/indice.txt`.
- **Si el documento no tiene índice** (un solo sermón o capítulo, un folleto), no pasa nada: se salta esa parte, y en el paso 7 se usan solo los títulos impresos.
- Si el usuario dio `paginas`, usa ese rango.
- Si la capa de texto falta en casi todo el libro, avisa al usuario: la transcripción funciona igual, pero `validar` no podrá detectar omisiones.

### Paso 2: Preparar

```bash
python temp/scripts/ocr.py preparar "<pdf>" "temp/trabajo/<nombre>" --paginas 13-545
```

Crea las imágenes en escala de grises a 1568 px de alto (el máximo que el modelo ve sin reducir) y la capa de cada página. Es reanudable: no repite las imágenes que ya existen. Opciones: `--lote 5` (páginas por agente) y `--alto 1568`.

Para excluir páginas sueltas del medio, usa comas: `--paginas 13-79,81-545`.

### Paso 3: Transcribir

```bash
python temp/scripts/ocr.py pendientes "temp/trabajo/<nombre>"
```

Imprime la carpeta y una línea por lote pendiente (hasta 20). Lanza un agente por lote (sección 1), espera a que terminen y vuelve a ejecutar `pendientes`. Repite hasta que no quede ninguno.

Si un agente falla, no hagas nada especial: sus páginas siguen pendientes y salen en la siguiente vuelta. Ver la sección 4 para el error del filtro de contenido.

### Paso 4: Limpiar y validar

```bash
python temp/scripts/ocr.py limpiar "temp/trabajo/<nombre>"
python temp/scripts/ocr.py validar "temp/trabajo/<nombre>"
```

`limpiar` quita las cursivas que los agentes marcan con asteriscos (`*Remedy (2).*`), aunque las instrucciones lo prohíben: en el volumen 1 de Brooks hubo 96. Al final lista el comando para ver los asteriscos que quedan; revísalos, porque algunos son signos impresos (llamadas de nota del editor como `below.*`, `Carus*`) y se quedan. Un asterisco suelto al inicio de un párrafo (`*Object. 3.`) es resto de markdown: quítalo.

Puedes validar mientras los agentes siguen trabajando, con `--paginas` sobre las páginas ya terminadas, y corregir sobre la marcha.

Por cada página `validar` revisa:

| Control | Tipo |
| --- | --- |
| Falta la transcripción o está vacía | ERROR |
| Restos de markdown, cursivas con asteriscos, comentarios del agente ("listo", "Here is" al inicio) | ERROR |
| Frases del ejemplo de las instrucciones del agente que no están en la capa OCR (texto copiado) | ERROR |
| Parecido con la capa OCR menor a 0,45 (¿es el texto de otra página?) | ERROR |
| `[[sigue]]` fuera de la primera línea, o `---NOTAS---` repetido | ERROR |
| Llamadas `[n]` sin nota al pie, o notas sin llamada | ERROR |
| Tramo de 8+ palabras de la capa OCR que falta en la transcripción | ERROR (posible omisión) |
| La transcripción tiene menos del 85 % de las palabras de la capa | ERROR (posible omisión) |
| Tramo de 8+ palabras que no está en la capa | aviso (posible texto agregado) |
| Más del 115 % de las palabras, parecido bajo con la capa, `[ilegible]`, notas desordenadas | aviso |
| Página marcada `[[en blanco]]` pero la capa tiene texto | ERROR |

La capa OCR también tiene errores, así que un aviso no siempre es un problema. Los tramos que `validar` cita sirven para ubicar el problema rápido.

### Paso 5: Corregir

Para cada página con ERROR:

1. **Omisiones o texto agregado:** abre la imagen (`paginas/pNNNN.png`) y la transcripción, y compara solo el tramo citado. Si es una omisión real, corrígela con una edición puntual. Si son varias o la página está muy mal, borra `texto/pNNNN.txt` y vuelve a lanzar el agente para esa página sola.
2. **Notas que no cuadran:** mira la imagen y corrige a mano. Los casos vistos:
   - Llamada `[n]` que el agente no vio (superíndice pequeño).
   - El mismo número de llamada dos veces: la segunda suele ser otro número (en Brooks, un `[1]` que era `[4]`).
   - Nota impresa **sin llamada** en el texto (pasa en la edición Grosart). Pon la llamada junto a la frase a la que se refiere la nota (la cita bíblica, el nombre o la frase latina que comenta) y menciónalo en el reporte.
   - Nota que sigue en un segundo párrafo, escrita como una línea aparte sin `[n]`: únela a la nota anterior.
   - Nota marcada con `*` en vez de número: dale el número que le toca en la página, en el texto y en la nota.
   - Nota inventada con una anotación a lápiz (`[*] [manuscrito ilegible]`): bórrala, con su llamada.
3. **Parecido muy bajo con la capa:** compara las primeras palabras de `texto/pNNNN.txt` con `capa/pNNNN.txt` y con las páginas vecinas. En Brooks, un agente escribió el texto de la página 515 en el archivo de la 516 y viceversa: se arregla intercambiando los dos archivos.
4. **Texto copiado del ejemplo:** borra la línea copiada. Mira la imagen por si la página tenía algo real en ese lugar.
5. **Falso positivo:** no hagas nada y menciónalo en el reporte. Los vistos hasta ahora:
   - Griego o hebreo, que la capa OCR lee como basura (`«ei idvva cui0 i ruv»`): aparece como "posible omisión" en casi todas las páginas con griego.
   - Una nota bien transcrita que la capa leyó con errores (`Koble` por `Noble`, `MenlirU` por `Mentiris`).
   - La capa leyó dos veces un renglón.

Vuelve a ejecutar `validar` hasta que no queden errores, salvo los falsos positivos que ya revisaste.

### Paso 6: Cortes entre páginas

Un párrafo que sigue en la página siguiente debe quedar unido en el `.txt`. `unir` lo une cuando la página lleva `[[sigue]]`, cuando la anterior termina con guion, o cuando la página empieza con minúscula y la anterior queda sin punto final. Pero el agente a veces se equivoca con `[[sigue]]`: lo omite cuando la página empieza con mayúscula ("God", "I", una cita), o lo pone en un párrafo nuevo. Revísalo así:

```bash
python temp/scripts/ocr.py cortes "temp/trabajo/<nombre>"
```

Lista los cortes que contradicen la puntuación:

- La página tiene `[[sigue]]`, empieza con mayúscula y la anterior termina con punto. Puede ser cualquiera de las dos cosas.
- La página no tiene `[[sigue]]`, empieza con mayúscula y la anterior queda a medias (sin punto final). Se excluyen las divisiones numeradas (`(4.)`, `VI.`, `Remedy (3).`, `Obj.`), que en estos libros empiezan párrafo aunque la anterior quede a medias.

Para cada caso recorta el inicio de la página (`cortes/pNNNN.png`) y los junta en láminas de 8 con su número (`cortes/lamina_01.png`…). Mira las láminas, no las páginas enteras. En cada recorte compara el primer renglón con el margen de los siguientes:

- **Con sangría:** párrafo nuevo. Quita `[[sigue]]` de la página.
- **Pegado al margen:** continúa. Pon `[[sigue]]` si falta.

Luego registra las páginas que ya estaban bien, para que no vuelvan a salir: `cortes "<trabajo>" --ok 104,112,127`. Vuelve a ejecutar `cortes` hasta que salga 0.

En el volumen 1 de Brooks hubo 18 casos, en 3 láminas: 3 `[[sigue]]` mal puestos (párrafos nuevos con sangría) y 15 correctos. Además había 5 páginas que empezaban con minúscula sin `[[sigue]]`; `unir` las une solas, pero conviene ponerles la marca para que los datos queden coherentes.

La geometría de la capa OCR (la posición del primer renglón) **no** sirve para decidir esto de forma automática: se probó con las 535 páginas y el OCR a veces se salta el primer renglón o lo parte, así que daba unos 30 falsos resultados. La puntuación más los recortes es más fiable y barato.

### Paso 7: Títulos (`##` y `###`)

El `.txt` conserva los títulos marcados, y al publicar `sermones.js html` los convierte: `## ` → `<h2>`, `### ` → `<h3>`. Los traductores conservan las marcas, y `revisar` da error si una se pierde (ver `temp/ai_agent.md`). El agente transcriptor marca con `## ` solo los títulos impresos en renglón aparte. Los niveles y las divisiones internas los pones tú:

- **`## ` (h2):** título de cada obra, prefacio, memoria, epístola, "To the Reader", NOTE, capítulos, apéndices, y las divisiones numeradas principales del tratado que aparecen en el índice (en *Precious Remedies*, las partes I–IV; en *The Mute Christian*, I–V; en *A String of Pearls*, I–VII). Al publicar, el primer `## ` de cada obra va en el `<h1>`.
- **`### ` (h3):** las subdivisiones con etiqueta impresa que el índice enumera: `Device (n)`, `Reason n`, `Evil n`, `Motive (n)`, `Obj. n`, `Quest.`. No las enumeraciones menudas dentro de una subdivisión (`Remedy (n)`, `[1.]`, `(1.)`, las de un sermón corto): son demasiadas y llenarían la página de títulos.
- **Texto del título:** la etiqueta tal como está impresa ("Reason (2).", "Object. 3.") más su enunciado, que es la primera oración del párrafo (la frase en cursiva), si tiene menos de unos 160 caracteres y ninguna llamada de nota. Si es más larga, usa el resumen del índice. La etiqueta pasa al título y se quita del párrafo; la primera oración también se quita del párrafo, porque ya está en el título. No inventes texto: todo sale del cuerpo o del índice.
- **Etiqueta precedida de una frase introductoria** ("The third device that Satan hath to draw the soul to sin is," / "Device (3). By extenuating…"): el título va **antes** de la frase introductoria, y la primera oración se queda también en el párrafo. Si no, la lectura queda cortada: "…is," seguido de otra cosa.
- **Sin índice** (un solo sermón o capítulo): basta con los títulos impresos. Si el sermón trae divisiones impresas como `DOCTRINE.`, `APPLICATION.` o `USE I.` en renglón aparte, pueden ir como `## `. Si no hay ninguna, el texto queda sin títulos internos.

Hazlo con un script de una sola vez sobre `texto/`, con una copia de seguridad antes. Sin `--aplicar`, el script solo lista los títulos propuestos: revísalos antes de aplicar. Usa de modelo `temp/trabajo/brooks-titulos.py`: sus funciones `poner` (etiqueta + primera oración), `entero` (un párrafo corto entero pasa a título), `juntar` (dos párrafos forman un título) y `serie` (todas las etiquetas de un tipo en un rango de páginas, con las variantes impresas `Reason 4.`, `Reason (5).`, `Object. 3.`, `Objection (5).`) sirven para otros libros. Solo cambia la lista de páginas y etiquetas.

Después vuelve a ejecutar `validar` y `cortes`. `validar` ya no da error por el texto que solo cambió de lugar (la etiqueta y la frase que pasaron al título). `cortes` puede listar una página que ahora empieza con el párrafo que sigue a un título: regístrala con `--ok`.

Errores vistos al hacerlo en Brooks:
- Cortar la primera oración en abreviaturas o exclamaciones ("1 Tim.", "xii.", "Sir !", "Oh!"). El script las salta, y además exige un mínimo de 30 caracteres.
- Los resúmenes del índice traen coletillas que no son del título ("answered eight ways", "&c."). Quítalas.
- Al índice le pueden faltar entradas (en Brooks faltaba el "Device (8)" de la parte III), y eso corre los títulos que vienen después. Compara siempre etiqueta por etiqueta.

### Paso 8: Unir

```bash
python temp/scripts/ocr.py unir "temp/trabajo/<nombre>" "temp/originales/<nombre del PDF>.txt"
```

Qué hace:

- Junta las páginas en orden y salta las `[[en blanco]]`.
- Une el párrafo que sigue en la página siguiente (`[[sigue]]`, o página que empieza con minúscula tras un párrafo sin punto final) y la palabra cortada con guion entre páginas. Nunca une un título ni algo que venga después de un título.
- Renumera las notas de forma continua en todo el libro (`[1]`, `[2]`… `[613]`) y las agrupa al final de cada sección, antes del siguiente título, después de una línea `__________`. Una nota que continúa en la página siguiente (`[sigue]` en las notas) se une a la anterior.
- Quita los espacios antes de `; : ! ?` y dentro de las comillas, que son de la tipografía de la época.
- Los títulos quedan como párrafo propio, con su marca (`## ` o `### `), y antes de cada título se vuelcan las notas pendientes.

Revisa los avisos de `unir` (por ejemplo, un párrafo unido sin `[[sigue]]`) y lee por encima el principio y el final del `.txt`. Busca también los títulos de cada obra (`grep -n "^THE EPISTLE\|^CHAPTER"` o los que correspondan) para confirmar que cada obra empieza donde debe.

### Paso 9: Reporte al usuario

Reporta en español:

- PDF, páginas transcritas y páginas omitidas (índices, etc.).
- Archivo de salida.
- Errores de `validar` que quedaron como falsos positivos, páginas resueltas con la capa OCR (sección 4) y avisos de `unir`.
- Que el `.txt` ya se puede traducir con `temp/ai_agent.md` (modo `--multiple`). Las portadillas y los títulos de cada obra sirven para marcar dónde empieza cada una.

No borres `temp/trabajo/<nombre>/` sin preguntar: las imágenes sirven para revisar dudas durante la traducción.

### Paso 10: Mejorar estas instrucciones

Al terminar cada libro, agrega a esta guía (sección 4 o 6), a `.claude/agents/ocr-transcriptor.md` o a `temp/scripts/ocr.py` lo que aprendiste: errores nuevos del agente, falsos positivos de `validar` y controles que habrían detectado antes un problema. Si un error se repite y se puede detectar con un script, agrega el control a `validar` o a `cortes` en vez de solo documentarlo. Anota el libro en la bitácora (sección 6).

---

## 4. Problemas conocidos

### "Output blocked by content filtering policy"

En las pruebas, una página con un relato de martirio (un pastor desnudado y torturado, del *Precious Remedies* de Brooks) hizo fallar al agente dos veces seguidas con este error. Luego, dentro de un lote con la capa OCR, la misma página pasó sin problema. Es un falso positivo del filtro de la API, no un problema del texto ni del prompt. Qué hacer, en orden:

1. Lanza esa página **sola** en un agente nuevo (el bloqueo depende de la salida exacta, y a veces pasa al segundo intento).
2. Si vuelve a fallar, ejecuta `python temp/scripts/ocr.py capa "temp/trabajo/<nombre>" <página>`. Escribe la capa OCR del PDF como transcripción, marcada con `[[capa]]`. Luego corrígela tú contra la imagen, o déjala marcada y avísale al usuario en el reporte. `validar` la seguirá mostrando como aviso.

Como cada página va en su archivo, un bloqueo no hace perder las demás páginas del lote: las que ya se escribieron quedan hechas.

### Errores frecuentes del agente transcriptor

Vistos en el volumen 1 de Brooks (535 páginas). Las instrucciones del agente ya los prohíben, pero Haiku los repite de vez en cuando; por eso existen los controles de `limpiar`, `validar` y `cortes`.

| Error | Cuántas veces | Cómo se detecta |
| --- | --- | --- |
| Cursivas con asteriscos (`*To dwell upon…*`) | 96 pares en 30 páginas | `limpiar` los quita; `validar` da ERROR si quedan |
| Copia una línea del ejemplo de sus instrucciones (`[sigue] scorpion is little…`) en una página que no la tiene | 1 (y otro agente lo hizo y lo corrigió él mismo) | `validar`: "texto copiado del ejemplo". Desde entonces el ejemplo usa palabras de relleno (`aaa bbb ccc`) |
| Escribe el texto de dos páginas en los archivos cruzados | 1 par (515/516) | `validar`: parecido muy bajo con la capa |
| Transcribe una anotación a lápiz como nota (`[*] [manuscrito ilegible]`) | 1 | `validar`: línea de notas sin número |
| `[[sigue]]` en un párrafo nuevo con sangría | 3 | `cortes` |
| Falta `[[sigue]]` en una página que continúa | 5 (todas con minúscula inicial) | `unir` las une igual; `cortes` lista las que empiezan con mayúscula |
| Llamada de nota repetida o ausente | 5 | `validar`: llamadas sin nota / notas sin llamada |
| Nota de dos párrafos partida en dos líneas | 1 | `validar`: línea de notas sin número |

El agente avisa en su respuesta de la mayoría de sus dudas (`listo — dudas: …`). Léelas: suelen señalar justo las páginas que después fallan en `validar`.

### Tipografía y diseño

- **Encabezados y números de página:** el agente los omite. Si alguno se cuela, `unir` no los quita: corrígelo en la página.
- **Notas en dos columnas:** el agente las ordena por número.
- **Versalitas:** se transcriben con mayúscula inicial (`Christian Reader`). Las cursivas se pierden: el `.txt` es texto plano, como los demás originales.
- **Griego y hebreo:** el agente los copia si los lee con seguridad, o escribe `[griego]` / `[hebreo]`. Búscalos al final (`grep -n "\[griego\]\|\[hebreo\]"`) y menciónalos en el reporte.
- **Erratas del impreso** ("saved his live"): se copian tal cual. No las corrijas.
- **Ortografía antigua** (ſ, `vv` por `w`, `u`/`v` intercambiadas): en libros del siglo XVII sin modernizar, el agente debe copiarla tal cual. La capa OCR de esos libros suele ser mucho peor, así que `validar` dará más avisos falsos. Haz primero una prueba con 10 páginas y revisa a mano.
- **Asteriscos impresos:** en la edición Grosart, las notas del editor sobre las portadas usan `*` (`Its title-page is given below.*` y luego `* The MUTE CHRISTIAN…`). Son del libro y se quedan.
- **Portadas antiguas:** Grosart reproduce la portada original de cada obra al principio o al final de la obra (la de *Apples of Gold* va al final). Se transcriben, un renglón por línea.
- **Saltos raros del impreso:** a veces una página termina a media frase y la siguiente empieza con una división nueva (Brooks, "and therefore in the" / "VI. Sixth place"). Es así en el impreso: no falta texto ni hay que unir.

### Costo

Cada página entra como imagen (unos 1 900 tokens) más la capa (unos 1 000) y sale como texto (unos 900). A eso se suma el contexto fijo de cada agente, que con el agente general es de unos 35 000 tokens. Medido en la prueba (agente general con Haiku):

| Forma | Tokens por agente | Por página |
| --- | --- | --- |
| 1 página por agente | ~45 000 | ~45 000 |
| 5 páginas por agente | ~75 000–85 000 | ~16 000 |
| 5 páginas por agente, con `ocr-transcriptor` (volumen 1 de Brooks completo) | ~37 000–53 000 (media ~45 000) | ~9 000 |

Por eso se usan lotes de 5 páginas y el agente `ocr-transcriptor`, que tiene menos contexto fijo. Lotes más grandes ahorran un poco más, pero un fallo deja más páginas pendientes y el agente se distrae más con el contexto largo. No pases de 8. Cada lote tardó de 1 a 2 minutos; con 20 agentes a la vez, las 535 páginas se transcribieron en algo más de una hora.

---

## 5. Prueba piloto (noviembre de 2026)

Con el volumen 1 de Brooks, páginas 82–101 del PDF (Epístola dedicatoria, "A Word to the Reader" y el inicio de *Precious Remedies*), en 4 lotes de 5 páginas:

- `validar`: 0 errores tras quitar el falso positivo del encabezado de página.
- Notas: 54 notas renumeradas, incluida una que continuaba en la página siguiente (`[sigue]`), y notas en dos columnas bien ordenadas.
- `[[sigue]]` correcto en todas las páginas que empezaban a mitad de párrafo.
- Latín y referencias bíblicas correctos. Griego copiado cuando era legible, `[griego]` cuando no.
- El agente ignoró bien una mancha que la capa OCR leía como comilla.
- Comparación previa de dos variantes (solo imagen / imagen + capa): con la capa, el agente no metió una palabra que la otra variante había agregado ("and") y conservó un guion de palabra compuesta (`play-books`). Por eso el agente recibe la capa.

---

## 6. Bitácora

Un renglón por libro transcrito, con lo que dejó de nuevo. Agrega el tuyo al terminar (paso 10).

| Fecha | Libro | Páginas | Resultado y lecciones |
| --- | --- | --- | --- |
| 2026-11 | Brooks, *Complete Works* vol. 1 (Grosart, 1866) | 13–547 (535) | 107 lotes, 2 365 párrafos, 1 328 notas. Errores del agente: cursivas con asteriscos, una línea copiada del ejemplo, dos páginas cruzadas, `[[sigue]]` mal puesto. De aquí salieron `limpiar`, `cortes`, los controles nuevos de `validar`, el ejemplo con palabras de relleno y el paso de títulos (índice aparte en `indice.txt`; 69 títulos `##` y 95 `###`, con `brooks-titulos.py`). Quedaron 13 falsos positivos de `validar` (griego y hebreo de la capa) y 74 `[griego]`/`[hebreo]`. |
