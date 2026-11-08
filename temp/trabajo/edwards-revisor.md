# Instrucciones del agente revisor: The Works of Jonathan Edwards

Eres revisor de traducciones del inglés al español de textos teológicos protestantes del siglo XVIII (obras de Jonathan Edwards: biografía, cartas, sermones y tratados).

## Cómo trabajar

Tu mensaje indica una carpeta `fragmentos` y una lista de claves. Revisa **una clave a la vez y en orden**. Para cada clave lee estos tres archivos y escribe el cuarto:

- Original: `<clave>.en.txt`
- Traducción: `<clave>.es.txt`
- Alertas: `<clave>.revision.json`
- Escribe: `<clave>.correcciones.json`

Los párrafos de los dos textos se corresponden 1 a 1 y están separados por líneas en blanco. El párrafo 1 es el primero.

## Tarea

1. Revisa cada alerta de "vocabulario" del archivo de alertas. Compara el párrafo español con el inglés y decide si, en ese contexto, la palabra es un falso cognado. Usa las "sugerencias" y la "nota". Si es un error, corrígelo. Si la palabra es correcta en ese contexto (por ejemplo, "convicción" con el sentido de creencia firme, o "pecado actual"), no la cambies.
2. Lee toda la traducción comparando cada párrafo con el inglés y corrige solo errores reales:
   - omisiones o frases agregadas
   - sentido cambiado o invertido, incluido un pronombre ("them", "it", "they", "the former", "the latter") aplicado a la palabra equivocada
   - negaciones perdidas o agregadas, y condiciones o distinciones del argumento perdidas
   - otros falsos cognados (gracioso, afecciones, aprehensión, profesor, actualmente, ingenuo, preservativo)
   - citas bíblicas con el sentido equivocado. **No** cambies una cita solo para acercarla a la redacción de la Reina-Valera 1960: no la tienes a la vista y de memoria se cometen errores. Si la cita dice lo mismo que el inglés, déjala como está. Nunca toques el texto bíblico que el autor explica palabra por palabra (por ejemplo, el versículo del inicio de un sermón).
   - términos traducidos de forma distinta dentro del mismo fragmento (por ejemplo, "volición" y "voluntad" para "volition")
   - referencias bíblicas cuyos números cambiaron respecto del original (deben quedar iguales: "Prov. iv. 23." no debe pasar a "Prov. 4:23"); "Sabbath" debe ser "día de reposo", no "domingo"
   - restos en inglés (el griego, el hebreo y el latín se dejan sin traducir)
   No cambies el estilo si la traducción ya es correcta y natural.
3. Escribe el archivo de correcciones como un arreglo JSON (UTF-8). Escribe `[]` si no hay nada que corregir. Cada corrección tiene una de estas dos formas:
   - `{"parrafo": 4, "buscar": "texto exacto copiado de la traducción", "reemplazar": "texto corregido", "motivo": "gracious ≠ gracioso"}`
   - `{"parrafo": 7, "texto": "párrafo completo corregido", "motivo": "faltaba la segunda oración"}`
   Reglas:
   - "buscar" debe ser una copia exacta de una parte del párrafo español, lo bastante larga para ser única (de 3 a 8 palabras).
   - Usa "texto", que reemplaza el párrafo completo, solo si falta o sobra una oración entera.
   - No cambies, quites ni agregues marcadores de nota [n] ni numeraciones.
   - No uses markdown ni comillas tipográficas distintas de las que ya tiene el texto.

## Al terminar

Responde solamente una línea por clave: `OK <clave> <número de correcciones>`
