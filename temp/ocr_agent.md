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
| 4    | Comparar cada página con la capa OCR (omisiones, notas, formato)     | Script `validar`                                            | Ninguno                                        |
| 5    | Corregir las páginas con errores                                     | Agente transcriptor de nuevo, o el orquestador a mano       | Haiku / orquestador                            |
| 6    | Unir las páginas en un `.txt`, renumerar las notas, quitar guiones   | Script `unir`                                               | Ninguno                                        |

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

- **Se omiten:** la portada del volumen, la página del impresor, el índice general (CONTENTS) y los índices alfabéticos del final.
- **Se incluyen:** prefacios, memorias, notas del editor, epístolas dedicatorias, "To the Reader" y todas las obras. Las portadillas de cada obra (una página con solo el título) también, porque marcan dónde empieza.
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

### Paso 4: Validar

```bash
python temp/scripts/ocr.py validar "temp/trabajo/<nombre>"
```

Por cada página revisa:

| Control | Tipo |
| --- | --- |
| Falta la transcripción o está vacía | ERROR |
| Restos de markdown, comentarios del agente ("listo", "Here is") | ERROR |
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
2. **Notas que no cuadran:** casi siempre es una llamada `[n]` que el agente no vio (superíndice pequeño) o una nota que continúa en la página siguiente. Mira la imagen y corrige a mano.
3. **Falso positivo** (por ejemplo, la capa OCR leyó dos veces un renglón): no hagas nada y menciónalo en el reporte.

Vuelve a ejecutar `validar` hasta que no queden errores, salvo los falsos positivos que ya revisaste.

### Paso 6: Unir

```bash
python temp/scripts/ocr.py unir "temp/trabajo/<nombre>" "temp/originales/<nombre del PDF>.txt"
```

Qué hace:

- Junta las páginas en orden y salta las `[[en blanco]]`.
- Une el párrafo que sigue en la página siguiente (`[[sigue]]`) y la palabra cortada con guion entre páginas.
- Renumera las notas de forma continua en todo el libro (`[1]`, `[2]`… `[613]`) y las agrupa al final de cada sección, antes del siguiente título, después de una línea `__________`. Una nota que continúa en la página siguiente (`[sigue]` en las notas) se une a la anterior.
- Quita los espacios antes de `; : ! ?` y dentro de las comillas, que son de la tipografía de la época.
- Los títulos marcados con `## ` quedan como párrafo propio, sin la marca.

Revisa los avisos de `unir` (por ejemplo, un párrafo unido sin `[[sigue]]`) y lee por encima el principio y el final del `.txt`.

### Paso 7: Reporte al usuario

Reporta en español:

- PDF, páginas transcritas y páginas omitidas (índices, etc.).
- Archivo de salida.
- Errores de `validar` que quedaron como falsos positivos, páginas resueltas con la capa OCR (sección 4) y avisos de `unir`.
- Que el `.txt` ya se puede traducir con `temp/ai_agent.md` (modo `--multiple`). Las portadillas y los títulos de cada obra sirven para marcar dónde empieza cada una.

No borres `temp/trabajo/<nombre>/` sin preguntar: las imágenes sirven para revisar dudas durante la traducción.

---

## 4. Problemas conocidos

### "Output blocked by content filtering policy"

En las pruebas, una página con un relato de martirio (un pastor desnudado y torturado, del *Precious Remedies* de Brooks) hizo fallar al agente dos veces seguidas con este error. Luego, dentro de un lote con la capa OCR, la misma página pasó sin problema. Es un falso positivo del filtro de la API, no un problema del texto ni del prompt. Qué hacer, en orden:

1. Lanza esa página **sola** en un agente nuevo (el bloqueo depende de la salida exacta, y a veces pasa al segundo intento).
2. Si vuelve a fallar, ejecuta `python temp/scripts/ocr.py capa "temp/trabajo/<nombre>" <página>`. Escribe la capa OCR del PDF como transcripción, marcada con `[[capa]]`. Luego corrígela tú contra la imagen, o déjala marcada y avísale al usuario en el reporte. `validar` la seguirá mostrando como aviso.

Como cada página va en su archivo, un bloqueo no hace perder las demás páginas del lote: las que ya se escribieron quedan hechas.

### Tipografía y diseño

- **Encabezados y números de página:** el agente los omite. Si alguno se cuela, `unir` no los quita: corrígelo en la página.
- **Notas en dos columnas:** el agente las ordena por número.
- **Versalitas:** se transcriben con mayúscula inicial (`Christian Reader`). Las cursivas se pierden: el `.txt` es texto plano, como los demás originales.
- **Griego y hebreo:** el agente los copia si los lee con seguridad, o escribe `[griego]` / `[hebreo]`. Búscalos al final (`grep -n "\[griego\]\|\[hebreo\]"`) y menciónalos en el reporte.
- **Erratas del impreso** ("saved his live"): se copian tal cual. No las corrijas.
- **Ortografía antigua** (ſ, `vv` por `w`, `u`/`v` intercambiadas): en libros del siglo XVII sin modernizar, el agente debe copiarla tal cual. La capa OCR de esos libros suele ser mucho peor, así que `validar` dará más avisos falsos. Haz primero una prueba con 10 páginas y revisa a mano.

### Costo

Cada página entra como imagen (unos 1 900 tokens) más la capa (unos 1 000) y sale como texto (unos 900). A eso se suma el contexto fijo de cada agente, que con el agente general es de unos 35 000 tokens. Medido en la prueba (agente general con Haiku):

| Forma | Tokens por agente | Por página |
| --- | --- | --- |
| 1 página por agente | ~45 000 | ~45 000 |
| 5 páginas por agente | ~75 000–85 000 | ~16 000 |

Por eso se usan lotes de 5 páginas y, cuando está disponible, el agente `ocr-transcriptor`, que tiene menos contexto fijo. Lotes más grandes ahorran un poco más, pero un fallo deja más páginas pendientes y el agente se distrae más con el contexto largo. No pases de 8.

---

## 5. Prueba piloto (noviembre de 2026)

Con el volumen 1 de Brooks, páginas 82–101 del PDF (Epístola dedicatoria, "A Word to the Reader" y el inicio de *Precious Remedies*), en 4 lotes de 5 páginas:

- `validar`: 0 errores tras quitar el falso positivo del encabezado de página.
- Notas: 54 notas renumeradas, incluida una que continuaba en la página siguiente (`[sigue]`), y notas en dos columnas bien ordenadas.
- `[[sigue]]` correcto en todas las páginas que empezaban a mitad de párrafo.
- Latín y referencias bíblicas correctos. Griego copiado cuando era legible, `[griego]` cuando no.
- El agente ignoró bien una mancha que la capa OCR leía como comilla.
- Comparación previa de dos variantes (solo imagen / imagen + capa): con la capa, el agente no metió una palabra que la otra variante había agregado ("and") y conservó un guion de palabra compuesta (`play-books`). Por eso el agente recibe la capa.
