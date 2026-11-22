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

`limpiar` quita las cursivas que los agentes marcan con asteriscos (`*Remedy (2).*`), guiones bajos (`_Remedy_`) o etiquetas (`<i>`), aunque las instrucciones lo prohíben: en los volúmenes 1, 2 y 3 de Brooks hubo 96, 77 y 48. También pasa a `[n]` las llamadas que el agente escribe como superíndice unicode (`die.²` → `die.[2]`). Al final lista el comando para ver los asteriscos que quedan; revísalos, porque algunos son signos impresos (llamadas de nota del editor como `below.*`, `Carus*`) y se quedan. Un asterisco suelto al inicio de un párrafo (`*Object. 3.`) es resto de markdown: quítalo.

Puedes validar mientras los agentes siguen trabajando, con `--paginas` sobre las páginas ya terminadas, y corregir sobre la marcha. `limpiar`, en cambio, no tiene `--paginas` y recorre todo `texto/`: ejecútalo cuando hayan terminado todos los agentes. En el volumen 4 se ejecutó antes, y dos agentes que aún escribían vieron cambiar sus archivos en disco (no se perdió nada, pero es un riesgo).

Por cada página `validar` revisa:

| Control | Tipo |
| --- | --- |
| Falta la transcripción o está vacía | ERROR |
| Restos de markdown, cursivas con asteriscos, llamadas en superíndice unicode (`²`), comentarios del agente ("listo", "Here is" al inicio) | ERROR |
| Frases del ejemplo de las instrucciones del agente que no están en la capa OCR (texto copiado) | ERROR |
| Nota `[sigue]` idéntica a una nota de la página anterior (repetida) | ERROR |
| Parecido con la capa OCR menor a 0,45 (¿es el texto de otra página?) | ERROR |
| `[[sigue]]` fuera de la primera línea, o `---NOTAS---` repetido | ERROR |
| Llamadas `[n]` sin nota al pie, o notas sin llamada | ERROR |
| Tramo de 8+ palabras de la capa OCR que falta en la transcripción | ERROR (posible omisión), con su "parecido" con el pasaje más cercano de la transcripción. Si el parecido es de 0,65 o más (la capa leyó mal el tramo o mezcló renglones de dos columnas, pero el texto está), o si es una raya de adorno leída como letras («v v v x v»), baja a aviso |
| La transcripción tiene menos del 85 % de las palabras de la capa | ERROR (posible omisión) |
| Tramo de 8+ palabras que no está en la capa (sin contar los títulos `##`/`###`, que pueden venir del índice) | aviso (posible texto agregado) |
| Más del 115 % de las palabras, parecido bajo con la capa, `[ilegible]`, notas desordenadas | aviso |
| Página marcada `[[en blanco]]` pero la capa tiene texto | ERROR |
| Salto en la numeración impresa (el número de página de la capa avanza de golpe y se mantiene): páginas que faltan en el escaneo | aviso, al final |

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
   - Dos notas juntas en una línea (la segunda empieza a media línea con su número): sepáralas.
   - Una enumeración del texto escrita como llamada (`[4] Fourthly`): es `[4.] Fourthly`, con punto, como esté impreso.
   - Cifras entre corchetes en el texto que no son llamadas (Grosart completa un año: «in [15]88»): `validar` las toma por llamadas sin nota y `unir` las renumeraría. Escríbelas sin corchetes («in 1588»).
   - Una línea del cuerpo puesta entre las notas (en Brooks, `END OF VOL. III.` al pie de la última página): pásala al cuerpo.
   - Si hay varias páginas con notas sin llamada (en el volumen 3 fueron 8), puedes mandarlas a un agente `ocr-transcriptor` de corrección: dale la página, la nota y la orden de poner la llamada donde está impresa o, si no la hay, junto a la frase que la nota comenta. Revisa después cada cambio con `validar`.
3. **Parecido muy bajo con la capa:** compara las primeras palabras de `texto/pNNNN.txt` con `capa/pNNNN.txt` y con las páginas vecinas. En Brooks, un agente escribió el texto de la página 515 en el archivo de la 516 y viceversa: se arregla intercambiando los dos archivos.
4. **Texto copiado del ejemplo:** borra la línea copiada. Mira la imagen por si la página tenía algo real en ese lugar.
5. **Páginas que faltan en el escaneo:** `validar` avisa al final cuando la numeración impresa salta (en Brooks vol. 5, de la p. 39 a la 42). No hay texto que recuperar del PDF: quita el `[[sigue]]` de la página siguiente (si no, `unir` juntaría dos frases que no se conectan), pon al comienzo de esa página un párrafo `[FALTAN EN EL ESCANEO LAS PÁGINAS 40-41 DEL IMPRESO]` y avisa al usuario por si tiene otra copia. Si entre las dos páginas hay portadillas o notas sin número, el salto suele ser solo el reverso en blanco de una portadilla que no se escaneó: míralo y no hagas nada.
6. **Falso positivo:** no hagas nada y menciónalo en el reporte. Los vistos hasta ahora:
   - Griego o hebreo, que la capa OCR lee como basura (`«ei idvva cui0 i ruv»`): aparece como "posible omisión" en casi todas las páginas con griego.
   - Una nota bien transcrita que la capa leyó con errores (`Koble` por `Noble`, `MenlirU` por `Mentiris`).
   - La capa leyó dos veces un renglón.
   - El título corrido de la página («SIXTH PETITION IN THE LORD'S PRAYER») metido por la capa a media página, en los libros a dos columnas. Sale con parecido bajo (0,45-0,52) porque el agente lo omite, con razón.
   - Un tramo con parecido de 0,52 a 0,65 suele ser capa muy mal leída. Las omisiones reales de Watson dieron 0,43 y 0,52, así que mira la imagen en todos los casos por debajo de 0,65.

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

**Revisión completa (`--todos`).** Agrega un tercer tipo de caso: la página no tiene `[[sigue]]`, empieza con mayúscula y la anterior termina con punto. Es la única forma de encontrar una continuación que el agente omitió cuando la frase anterior acaba justo al final de la página. En el volumen 3 dio 37 casos más (5 láminas) y los 37 eran párrafos nuevos: el agente no omitió ninguna continuación con mayúscula. En el volumen 4 dio 8 casos y uno era una continuación omitida (p. 285, «No heart but a sound heart…», pegado al margen). Como cuesta poco (1 a 5 láminas por libro), hazla siempre.

**Escaneo sin sangrías visibles.** En algunas páginas mal escaneadas (Brooks vol. 3, p. 80) ningún párrafo muestra sangría, y el recorte engaña: parece un párrafo nuevo y no lo es. Si en la página entera ningún párrafo tiene sangría clara, decide por el contenido. Lee el final de la página anterior y el principio de esta: si es la misma oración o la misma idea ("…a fulness of redundance." / "There is an overflowing fulness in Christ…"), continúa. En el volumen 3, el orquestador quitó por error el `[[sigue]]` correcto de esa página y lo devolvió al revisar con `--todos`.

**Recortes que engañan.** El recorte muestra solo 3 o 4 renglones. Si el primero parece pegado al margen pero la diferencia es de pocos píxeles, abre la página entera antes de cambiar nada: de 4 dudas del volumen 3, 3 tenían sangría normal en la página completa.

La geometría de la capa OCR (la posición del primer renglón) **no** sirve para decidir esto de forma automática: se probó con las 535 páginas y el OCR a veces se salta el primer renglón o lo parte, así que daba unos 30 falsos resultados. La puntuación más los recortes es más fiable y barato.

### Paso 7: Títulos (`##` y `###`)

El `.txt` conserva los títulos marcados, y al publicar `sermones.js html` los convierte: `## ` → `<h2>`, `### ` → `<h3>`. Los traductores conservan las marcas, y `revisar` da error si una se pierde (ver `temp/ai_agent.md`). El agente transcriptor marca con `## ` solo los títulos impresos en renglón aparte. Los niveles y las divisiones internas los pones tú:

- **`## ` (h2):** título de cada obra, prefacio, memoria, epístola, "To the Reader", NOTE, capítulos, apéndices, y las divisiones numeradas principales del tratado que aparecen en el índice (en *Precious Remedies*, las partes I–IV; en *The Mute Christian*, I–V; en *A String of Pearls*, I–VII). Al publicar, el primer `## ` de cada obra va en el `<h1>`.
- **`### ` (h3):** las subdivisiones con etiqueta impresa que el índice enumera: `Device (n)`, `Reason n`, `Evil n`, `Motive (n)`, `Obj. n`, `Quest.`. No las enumeraciones menudas dentro de una subdivisión (`Remedy (n)`, `[1.]`, `(1.)`, las de un sermón corto): son demasiadas y llenarían la página de títulos.
- **Texto del título:** la etiqueta tal como está impresa ("Reason (2).", "Object. 3.") más su enunciado, que es la primera oración del párrafo (la frase en cursiva), si tiene menos de unos 160 caracteres y ninguna llamada de nota. Si es más larga, usa el resumen del índice. La etiqueta pasa al título y se quita del párrafo; la primera oración también se quita del párrafo, porque ya está en el título. No inventes texto: todo sale del cuerpo o del índice.
- **Etiqueta precedida de una frase introductoria** ("The third device that Satan hath to draw the soul to sin is," / "Device (3). By extenuating…"): el título va **antes** de la frase introductoria, y la primera oración se queda también en el párrafo. Si no, la lectura queda cortada: "…is," seguido de otra cosa.
- **Serie de sermones sobre un texto** (en Brooks, *The Unsearchable Riches of Christ*, con siete doctrinas sacadas de Ef. 3:8): las doctrinas no llevan título impreso, sino que salen en el texto ("Obs. 1.", "Doct.", "The next observation…"). Pon un `## ` por doctrina con las palabras del índice ("The first doctrine.—Those that are lowest…") justo antes del párrafo que la empieza (o antes del versículo que repite el texto al comienzo del sermón). Las divisiones de cada doctrina (I. pruebas, II. propiedades, III. razones, IV. usos; los "Support n", "Use n") van como `### `.
- **Enunciado con llamada de nota** ("Support 2. That God doth… done by them.[1]"): el título lleva la frase sin la llamada, y el párrafo queda entero, con la llamada. Así no se pierde ninguna nota, aunque la frase quede repetida.
- **Sin índice** (un solo sermón o capítulo): basta con los títulos impresos. Si el sermón trae divisiones impresas como `DOCTRINE.`, `APPLICATION.` o `USE I.` en renglón aparte, pueden ir como `## `. Si no hay ninguna, el texto queda sin títulos internos.

Hazlo con un script de una sola vez sobre `texto/`, con una copia de seguridad antes. Sin `--aplicar`, el script solo lista los títulos propuestos: revísalos antes de aplicar. Usa de modelo `temp/trabajo/brooks-titulos.py`: sus funciones `poner` (etiqueta + primera oración), `entero` (un párrafo corto entero pasa a título), `juntar` (dos párrafos forman un título) y `serie` (todas las etiquetas de un tipo en un rango de páginas, con las variantes impresas `Reason 4.`, `Reason (5).`, `Object. 3.`, `Objection (5).`) sirven para otros libros. Solo cambia la lista de páginas y etiquetas. `temp/trabajo/brooks3-titulos.py` tiene una versión más limpia de esas funciones y agrega `insertar`: pone un título del índice antes de un párrafo sin tocarlo (para las doctrinas y las divisiones sin etiqueta impresa).

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

Vistos en los volúmenes 1 a 6 de Brooks (535, 533, 504, 446, 594 y 457 páginas). Las instrucciones del agente ya los prohíben, pero Haiku los repite de vez en cuando; por eso existen los controles de `limpiar`, `validar` y `cortes`. Las columnas de los volúmenes 2 a 6 muestran el efecto de las mejoras hechas después de cada libro.

| Error | Vol. 1 | Vol. 2 | Vol. 3 | Vol. 4 | Vol. 5 | Vol. 6 | Cómo se detecta |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Cursivas con asteriscos, guiones bajos o etiquetas (`*To dwell*`, `_To dwell_`, `<i>`) | 96 (asteriscos) | 77 (sobre todo guiones bajos; muchos agentes los corrigieron solos) | 48 | 24 | 13 (y otras tantas corregidas por los propios agentes) | 22 (y otras corregidas por los propios agentes) | `limpiar` los quita (los tres tipos); `validar` da ERROR si quedan |
| Llamada escrita como superíndice unicode (`²`) | — | — | 1 (p. 57) | 0 | 0 | 0 | `limpiar` la pasa a `[n]`; `validar` da ERROR si queda |
| Copia una línea del ejemplo de sus instrucciones (`[sigue] scorpion is little…`) en una página que no la tiene | 1 | 0 (el ejemplo ahora usa palabras de relleno) | 0 | 0 | 0 | 0 | `validar`: "texto copiado del ejemplo" |
| Escribe el texto de dos páginas en los archivos cruzados | 1 par (515/516) | 0 | 0 | 0 | 0 | 0 | `validar`: parecido muy bajo con la capa |
| Repite al inicio de sus notas una nota `[sigue]` de la página anterior | — | 1 (p. 513) | 0 | 0 | 0 | 0 | `validar`: "la nota [sigue] repite una nota de la página anterior" |
| Numera mal las notas: toma la nota 1 por continuación (`[sigue]`) y corre las demás, o junta dos notas en una línea | — | 1 (p. 533) | 1 (p. 322, dos notas juntas) | 0 | 0 | 0 | `validar`: llamadas sin nota. Mira la imagen |
| Escribe una enumeración como llamada (`[4] Fourthly` por `[4.]`) | — | — | 1 (p. 262) | 0 | 1 (p. 499) | 0 | `validar`: llamada sin nota |
| Pone una línea del cuerpo entre las notas (`END OF VOL. III.`) | — | — | 1 (p. 510) | 0 | 0 | 0 | `validar`: línea de notas sin número |
| Omite texto del cuerpo | 0 | 1 renglón (p. 308) | 0 | 1 (p. 236: los dos últimos párrafos; el agente se detuvo en un "But,") | 0 | 1 (p. 265: el último párrafo y su nota) | `validar`: posible omisión |
| Transcribe una anotación a lápiz como nota (`[*] [manuscrito ilegible]`) | 1 | 0 | 0 | 0 | 0 | 0 | `validar`: línea de notas sin número |
| `[[sigue]]` en un párrafo nuevo con sangría | 3 de 18 cortes dudosos | 0 de 10 | 4 de 20 | 1 de 18 | 1 de 21 | 2 de 17 | `cortes` |
| Falta `[[sigue]]` en una página que continúa | 5 (todas con minúscula inicial) | 3 (ídem) | 2 (ídem); 0 con mayúscula entre 37 revisadas con `--todos` | 3 con minúscula; 1 con mayúscula (p. 285) entre 8 de `--todos` | 3 con minúscula; 3 con mayúscula (p. 135 con `cortes`; 160 y 516 con `--todos`) | 7 con minúscula; 1 con mayúscula (p. 412) entre 17 de `--todos` | `unir` une las de minúscula; `cortes` (y `--todos`) lista las que empiezan con mayúscula |
| Llamada de nota repetida, ausente o nota sin llamada impresa | 5 | 6 | 8 notas sin llamada (corregidas con un agente de corrección) | 1 llamada sin nota (p. 67) | 0 del agente (2 casos del impreso: nota sin llamada en p. 408, llamada sin nota en p. 581) | 0 del agente (1 caso del impreso: «[15]88», año completado por Grosart, que parece llamada) | `validar`: llamadas sin nota / notas sin llamada |
| Nota de dos párrafos partida en dos líneas | 1 | 1 (p. 422, una referencia que era parte de la nota anterior) | 0 | 0 | 0 | 0 | `validar`: línea de notas sin número |
| Se salta una página del lote (no escribe su archivo) | — | — | — | 1 (p. 160; lo avisó el agente) | 0 | 0 | `pendientes` la lista; lánzala sola |
| Pasa a `[1]` el `*` impreso de la nota del editor sobre la portada | — | — | — | 1 (p. 5) | 0 (3 portadas con `*`, bien copiadas) | 0 (pero marcó como `## ` la portada citada en una NOTE) | Revisa `grep "\*"`; ya está en las instrucciones del agente |
| Junta todo el índice (CONTENTS) en un solo párrafo | — | — | — | 1 (p. 2–3, sin sangrías) | 0 | 0 | Mira `indice.txt`; ya está en las instrucciones del agente |
| Escribe páginas que no son de su lote (sobrescribe el trabajo de otro agente) | — | — | — | — | 1 (p. 563-564; lo avisó) | 0 | `validar` las páginas afectadas; ya está en las instrucciones del agente |

Errores nuevos vistos en Watson (*Select Works*, 774 páginas a dos columnas):

- **"Corrige" lo impreso:** cambió un «10th» repetido por «11th» (p. 560), un «Use 1.» fuera de orden por «Use 4.» (p. 47) y agregó una «i.» que faltaba en una referencia (p. 388). Lo dijo en sus dudas, que es donde se detecta: busca en las respuestas palabras como "por la secuencia", "añadí" o "corregí". La regla 1 del agente ahora lo prohíbe de forma explícita.
- **Omite texto entre dos frases iguales:** saltó de un «as if» al siguiente y perdió una oración y media (p. 538); `validar` lo detectó con parecido 0,43. Otra página se detuvo a la mitad (p. 574, 49 % de las palabras).
- **Asteriscos o llamadas sin nota:** el impreso tiene marcas sueltas (`*`, `'`) sin nota al pie. Los agentes las omitieron casi siempre, pero en 3 páginas copiaron el `*` y en una lo pasaron a `[1]`. Como no hay nota, se quitan todos.
- **`[[sigue]]`:** de 61 cortes revisados con `--todos`, 6 marcas de más (párrafos con sangría o con etiqueta «Use», «Branch», «Ans.») y 5 continuaciones sin marca (empiezan con comilla o con un nombre, como «Solon.», pegados al margen).

En el volumen 3 se vio por qué fallaba `[[sigue]]`: varios agentes lo decidían suponiendo cómo terminaba la página anterior, que no tienen delante, en vez de mirar la sangría. Las instrucciones del agente ahora dicen que se decide **solo** por la sangría de la página.

Casos del impreso que parecen errores y no lo son (vistos en el volumen 2):
- **La misma llamada para varias frases:** el impreso pone "¹" en cinco frases de una página y una sola nota ("Clarke, as before"). Todas llevan `[1]`.
- **Llamada dentro de otra nota:** una nota del editor remite a otra con un superíndice; `validar` dice "nota sin llamada en el texto". Es falso positivo, y `unir` pone esa nota al final del bloque.

El agente avisa en su respuesta de la mayoría de sus dudas (`listo — dudas: …`). Léelas: suelen señalar justo las páginas que después fallan en `validar`.

Errores que solo aparecieron al traducir el volumen 1 (los señalaron los traductores):
- **"l" romana leída como "1" en las referencias:** `Isa. 1. 11`, `Jer. 1. 6` y `Ps. 1. 21` son `Isa. l. 11`, `Jer. l. 6` y `Ps. l. 21` (capítulo 50). El capítulo 1 se escribe `i.` en todo el libro, así que un `1.` entre el libro y el versículo es casi siempre este error. Búscalos con `grep -nE "\b[A-Z][a-z]+\.? 1\. [0-9]" <libro>.txt` antes de entregar el texto.
- **Versículo imposible:** `Rom. xiv 33` por `Rom. xiv. 23` (Romanos 14 tiene 23 versículos). Es difícil de detectar con un script; los traductores lo notan.

### Tipografía y diseño

- **Encabezados y números de página:** el agente los omite. Si alguno se cuela, `unir` no los quita: corrígelo en la página.
- **Notas en dos columnas:** el agente las ordena por número.
- **Versalitas:** se transcriben con mayúscula inicial (`Christian Reader`). Las cursivas se pierden: el `.txt` es texto plano, como los demás originales.
- **Griego y hebreo:** el agente los copia si los lee con seguridad, o escribe `[griego]` / `[hebreo]`. Búscalos al final (`grep -n "\[griego\]\|\[hebreo\]"`) y menciónalos en el reporte.
- **Erratas del impreso** ("saved his live"): se copian tal cual. No las corrijas.
- **Ortografía antigua** (ſ, `vv` por `w`, `u`/`v` intercambiadas): en libros del siglo XVII sin modernizar, el agente debe copiarla tal cual. La capa OCR de esos libros suele ser mucho peor, así que `validar` dará más avisos falsos. Haz primero una prueba con 10 páginas y revisa a mano.
- **Asteriscos impresos:** en la edición Grosart, las notas del editor sobre las portadas usan `*` (`Its title-page is given below.*` y luego `* The MUTE CHRISTIAN…`). Son del libro y se quedan.
- **Portadas antiguas:** Grosart reproduce la portada original de cada obra al principio o al final de la obra (la de *Apples of Gold* va al final). Se transcriben, un renglón por línea.
- **Libros a dos columnas** (Watson, *Select Works*, Nueva York, 1855): la regla 3 del agente dice el orden de lectura (columna izquierda entera y luego la derecha; si un título cruza la página, arriba izquierda, arriba derecha, título, abajo izquierda, abajo derecha), y conviene repetirlo en una línea del prompt de cada lote. Los agentes lo hicieron bien en las 774 páginas. Las páginas tienen el doble de texto que las de Brooks (unos 4 000 caracteres): cada lote de 5 páginas gastó unos 55 000-70 000 tokens y tardó 1,5-3 minutos. La capa OCR viene en orden de lectura, pero a veces junta en un renglón palabras de las dos columnas y lee las rayas de adorno como «v v v»; de ahí salían casi todos los falsos positivos de `validar` (71 de 75 antes de agregar el filtro de parecido; 11 después). Un párrafo que llega al pie de una columna y sigue arriba de la otra es el mismo párrafo, sin línea en blanco ni `[[sigue]]`.
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
| 2026-11 | Brooks, *Complete Works* vol. 2 | 7–539 (533) | Primera prueba de las mejoras. 107 lotes, 1 922 párrafos, 1 120 notas; ~46 000 tokens por lote, como antes. `validar` pasó de 11 falsos positivos a 3, y de unos 15 errores reales a 10 (notas y una omisión); 0 textos copiados del ejemplo y 0 páginas cruzadas; los 10 cortes dudosos estaban bien. Errores nuevos: cursivas con guiones bajos y `<i>` (añadidas a `limpiar`) y una nota `[sigue]` repetida de la página anterior (control nuevo en `validar`). Títulos: 25 `##` y 62 `###` con `brooks2-titulos.py`; en *Heaven on Earth* solo capítulos, porque sus divisiones internas no tienen marcas regulares. |
| 2026-11 | Brooks, *Complete Works* vol. 3 | 7–510 (504) | Segunda prueba de las mejoras. ~101 lotes, 1 972 párrafos, 867 notas; ~45 000–55 000 tokens por lote. `validar` dejó 3 falsos positivos (griego y una nota con renglones desordenados en la capa) y ninguna omisión real; 0 textos copiados del ejemplo, 0 páginas cruzadas, 0 notas `[sigue]` repetidas. Cursivas: 48 (de 96 y 77). Errores que quedan: 4 `[[sigue]]` en párrafos nuevos (causa: el agente suponía cómo acababa la página anterior; regla nueva en el agente), 8 notas sin llamada, 2 notas juntas o mal numeradas, una línea del cuerpo entre las notas. Primera revisión `cortes --todos`: 37 casos, ninguna continuación omitida. Nuevo en `limpiar`/`validar`: superíndices unicode → `[n]`. Títulos: 20 `##` y 90 `###` con `brooks3-titulos.py` (siete doctrinas de *Unsearchable Riches* con títulos del índice; máximas y divisiones de *A Cabinet of Jewels*). |
| 2026-11 | Brooks, *Complete Works* vol. 4 (*The Crown and Glory of Christianity*) | 4–449 (446) | Tercera prueba de las mejoras. 90 lotes (más el índice y una página repetida), 742 párrafos (el libro tiene párrafos muy largos: 84 páginas son un solo párrafo, comprobado con la imagen), 754 notas; ~40 000–60 000 tokens por lote. `validar` dejó un solo falso positivo (griego). Cursivas: 24 (de 96, 77 y 48). 0 textos copiados, 0 páginas cruzadas, 0 notas mal numeradas o juntas. Errores nuevos: una página saltada por un agente (lo avisó), una omisión al final de página (los dos últimos párrafos; `validar` la detectó por el 70 % de palabras), el `*` de la portada pasado a `[1]` y el índice en un solo párrafo; los tres últimos están ya en las instrucciones del agente. Cortes: 1 `[[sigue]]` de más entre 18 y 1 continuación omitida con mayúscula entre 8 de `--todos`. Títulos: 11 `##` y 28 `###` con `brooks4-titulos.py` (un solo tratado: doctrina, usos, objeciones y posiciones). |
| 2026-11 | Brooks, *Complete Works* vol. 5 (*The Golden Key*, *Paradise Opened*, *A Word in Season*) | 3–596 (594) | 119 lotes; 1 173 párrafos, 835 notas; ~40 000–68 000 tokens por lote. `validar`: 4 falsos positivos (griego y el colofón final), 0 omisiones, 0 textos copiados, 0 páginas cruzadas. Cursivas: 13 (los agentes corrigieron muchas solos). Nuevo: el escaneo no trae las pp. 40-41 del impreso (lo avisó un agente; ahora `validar` revisa la numeración impresa y avisa de estos huecos); un agente escribió dos páginas de otro lote (lo avisó; regla nueva en el agente). Cortes: 1 `[[sigue]]` de más entre 21; 3 continuaciones con mayúscula sin marca (una con `cortes`, dos solo con `--todos`). Títulos: 14 `##` y 22 `###` con `brooks5-titulos.py` (preguntas y 11 *pleas* de *The Golden Key*/*Paradise Opened*; divisiones de *The Signal Presence of God*). |
| 2026-11 | Brooks, *Complete Works* vol. 6 (*London's Lamentations* y seis sermones o tratados breves) | 8–464 (457) | Sin la «Editorial Postscript» de Grosart (pp. 2–5) ni los índices generales (465–508). 92 lotes; 1 280 párrafos, 543 notas; ~35 000–62 000 tokens por lote. `validar`: 1 falso positivo; 1 omisión real (último párrafo y nota de la p. 265, otra vez al final de página pese a la regla nueva). Cursivas: 22. Lo que más falló fue `[[sigue]]`: 7 páginas que empiezan en minúscula a media frase quedaron sin la marca (los agentes creyeron ver sangría; `unir` las une igual) y 2 marcas de más; `--todos` encontró 1 continuación omitida con mayúscula. Nuevo: un año entre corchetes («[15]88») que parecía llamada de nota. Títulos: 29 `##` y 23 `###` con `brooks6-titulos.py` (secciones de *London's Lamentations* según el índice; 12 máximas del *Heavenly Cordial*). |
| 2026-11 | Watson, *Select Works* (Nueva York, Carter, 1855): *A Body of Practical Divinity*, 7 sermones y 5 tratados | 11–784 (774) | Primer libro **a dos columnas**: regla nueva en el agente (orden de lectura) y una línea en el prompt de cada lote; sin errores de orden. Sin la portada (p. 7), el índice (9–10, aparte en `ocr-watson-indice`), el índice alfabético ni la publicidad del editor (785–800). 155 lotes, 5 492 párrafos, una sola nota (p. 670); ~55 000–70 000 tokens por lote. `validar` daba 75 errores, casi todos capa mezclada entre columnas: se agregó el filtro de parecido (`parecido_en_texto`, `es_adorno`) y quedaron 11 falsos positivos; 2 omisiones reales (pp. 538 y 574). Nuevo: el agente "corrigió" el impreso en 3 páginas (regla 1 ampliada). Cortes: 61 revisados con `--todos`, 11 corregidos. Títulos: 108 `##` (temas del catecismo, sermones con el título del índice, capítulos) y 66 `###` (textos bíblicos de cada lección, temas repetidos, *Sect.*, *Rule*) con `watson-titulos.py`. |
