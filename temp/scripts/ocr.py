#!/usr/bin/env python
"""Herramienta para transcribir PDFs escaneados con agentes (ver temp/ocr_agent.md).

Comandos:
  info <pdf>                                   Páginas, capa de texto y muestra de cada parte del libro.
  preparar <pdf> <trabajo> [--paginas R] [--lote N] [--alto PX]
                                               Crea las imágenes (paginas/), la capa OCR (capa/) y el manifiesto.
  pendientes <trabajo> [--max N]               Lotes con páginas sin transcribir, listos para lanzar agentes.
  validar <trabajo> [--paginas R]              Revisa cada transcripción contra la capa OCR del PDF.
  capa <trabajo> <pagina>                      Último recurso: escribe la capa OCR como transcripción (queda marcada).
  limpiar <trabajo>                            Quita las cursivas en markdown (*texto*) y pasa las llamadas ¹ ² a [n].
  cortes <trabajo> [--alto 0.13] [--todos]     Cortes entre páginas dudosos ([[sigue]] contra la puntuación),
                                               con un recorte del inicio de cada página en cortes/.
  unir <trabajo> <salida.txt> [--paginas R]    Junta las páginas en un solo .txt (notas renumeradas).

R es una lista de páginas del PDF contadas desde 1: "13-547" o "13-80,82-547".
Requiere PyMuPDF: python -m pip install --user pymupdf
"""
import difflib
import json
import os
import re
import sys

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

MARCA_SIGUE = "[[sigue]]"
MARCA_BLANCO = "[[en blanco]]"
MARCA_CAPA = "[[capa]]"
SEP_NOTAS = "---NOTAS---"
RE_LLAMADA = re.compile(r"\[(\d{1,3})\]")
RE_NOTA = re.compile(r"^\[(\d{1,3}|sigue)\]\s*(.*)$")
# cursiva en markdown: *texto* o _texto_ (la marca de apertura va tras inicio/espacio/signo, la de cierre antes de espacio/signo)
VOLADOS = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹", "0123456789")
RE_VOLADO = re.compile(r"[⁰¹²³⁴⁵⁶⁷⁸⁹]+")
RE_CURSIVA = re.compile(r"(^|[\s(\[\'\"—])([*_])(\S(?:[^*_\n]*?\S)?)\2(?=$|[\s.,;:!?)\]\'\"—\[])", re.M)
# frases del ejemplo de .claude/agents/ocr-transcriptor.md (actual y anteriores) que los agentes copiaron alguna vez
FRASES_EJEMPLO = ["aaa bbb ccc", "hhh iii jjj", "kkk lll mmm", "texto de la nota uno",
                  "scorpion is little, yet able to sting a lion to death",
                  "should look so low as poor we", "love is like fire, very operative"]


def en_capa(frase, pc):
    """True si la mayoría de los pares de palabras de la frase están en la capa OCR (la frase es de esta página)."""
    w = palabras(frase)
    pares = set(zip(w, w[1:]))
    capa = set(zip(pc, pc[1:]))
    return bool(pares) and len(pares & capa) >= 0.5 * len(pares)
# títulos: "## " = <h2> (obra, capítulo, división principal), "### " = <h3> (subdivisión)
RE_TITULO = re.compile(r"^(##|###) +(.*)$")
# fin de párrafo: punto, signo, comillas o paréntesis de cierre (las llamadas [n] se quitan antes)
RE_FIN = re.compile(r"[.!?:'\"’”)\]]$")
# referencia bíblica que cierra una cita de la página anterior: "Ps. lxxxix. 30", "Job xxi. 23", "1 Cor. iii. 4"
RE_REFERENCIA = re.compile(r"^([1-3] )?[A-Z][a-z]+\.? [ivxlcIVXLC]+\.? ?\d")
# inicio de una división numerada: "(4.)", "[2.]", "3.", "VI.", "Remedy (3).", "Obj. 2", "Reason 7."
RE_DIVISION = re.compile(r"^(\(\d+\.?\)|\[\d+\.\]|\d+\.\s|[IVXL]+\.\s|(Device|Remedy|Reason|Duty|Use|Obj|Object|Ans|Answer|Motive|Means|Quest)\b)")


# ---------- utilidades ----------

def salir(msg):
    print("ERROR: " + msg)
    sys.exit(1)


def leer(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def escribir(p, s):
    os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(s)


def abrir_pdf(pdf):
    if fitz is None:
        salir("falta PyMuPDF. Instálalo con: python -m pip install --user pymupdf")
    if not os.path.exists(pdf):
        salir("no existe " + pdf)
    return fitz.open(pdf)


def opcion(args, nombre, defecto=None):
    if nombre in args:
        i = args.index(nombre)
        if i + 1 >= len(args):
            salir("falta el valor de " + nombre)
        v = args[i + 1]
        del args[i:i + 2]
        return v
    return defecto


def rango(texto, total):
    """'13-80,82-547' -> [13, ..., 80, 82, ..., 547] (contando desde 1)."""
    if not texto:
        return list(range(1, total + 1))
    paginas = []
    for parte in texto.split(","):
        parte = parte.strip()
        if "-" in parte:
            a, b = parte.split("-", 1)
            paginas.extend(range(int(a), int(b) + 1))
        elif parte:
            paginas.append(int(parte))
    fuera = [p for p in paginas if p < 1 or p > total]
    if fuera:
        salir("páginas fuera del PDF (1-%d): %s" % (total, fuera[:5]))
    return sorted(set(paginas))


def nombre_pagina(n):
    return "p%04d" % n


def manifiesto(trabajo):
    p = os.path.join(trabajo, "manifiesto.json")
    if not os.path.exists(p):
        salir("no hay manifiesto en %s; ejecuta primero 'preparar'" % trabajo)
    return json.loads(leer(p))


def ruta(trabajo, carpeta, n, ext):
    return os.path.join(trabajo, carpeta, nombre_pagina(n) + ext).replace("\\", "/")


def palabras(s):
    """Palabras normalizadas para comparar con la capa OCR."""
    s = s.lower().replace("ſ", "s").replace("æ", "ae").replace("œ", "oe")
    s = re.sub(r"-\s*\n\s*", "", s)  # guiones de fin de línea de la capa
    return re.findall(r"[a-z0-9]+", s)


def partes(texto):
    """Separa una transcripción en (cuerpo, notas)."""
    if SEP_NOTAS in texto:
        cuerpo, notas = texto.split(SEP_NOTAS, 1)
    else:
        cuerpo, notas = texto, ""
    return cuerpo.strip(), notas.strip()


# ---------- info ----------

def cmd_info(args):
    if not args:
        salir("uso: info <pdf>")
    d = abrir_pdf(args[0])
    n = d.page_count
    print("Archivo:", args[0])
    print("Páginas:", n, "| tamaño:", d[0].rect, "| creado por:", d.metadata.get("creator"), "/", d.metadata.get("producer"))
    con_texto = 0
    for i in range(n):
        t = d[i].get_text().strip()
        if len(t) > 200:
            con_texto += 1
    print("Páginas con capa de texto (>200 caracteres): %d de %d" % (con_texto, n))
    print()
    print("Mapa del libro: páginas casi vacías (portadillas, blancas) y cambios del título corrido.")
    print("pág.  caract.  primeras líneas de la capa")
    recientes = []
    for i in range(n):
        t = d[i].get_text().strip()
        lineas = [l.strip() for l in t.splitlines() if l.strip()]
        muestra = " | ".join(lineas[:3])[:90]
        # título corrido: letras de las dos primeras líneas, sin números romanos ni palabras cortas
        cab = re.sub(r"[^a-z ]", " ", " ".join(lineas[:2]).lower())
        titulo = " ".join(w for w in cab.split() if len(w) > 2 and not re.match(r"^[ivxlc]+$", w))
        corto = len(t) < 600
        nuevo = not any(difflib.SequenceMatcher(None, titulo, r).ratio() > 0.6 for r in recientes)
        if corto or nuevo:
            print("%4d  %5d  %s" % (i + 1, len(t), muestra))
        if not corto and nuevo:
            recientes = (recientes + [titulo])[-6:]
        elif not corto:
            recientes = [r for r in recientes if r != titulo] + [titulo]


# ---------- preparar ----------

def cmd_preparar(args):
    paginas_txt = opcion(args, "--paginas")
    lote = int(opcion(args, "--lote", "5"))
    alto = int(opcion(args, "--alto", "1568"))
    if len(args) < 2:
        salir("uso: preparar <pdf> <trabajo> [--paginas R] [--lote N] [--alto PX]")
    pdf, trabajo = args[0], args[1]
    d = abrir_pdf(pdf)
    paginas = rango(paginas_txt, d.page_count)
    for c in ("paginas", "capa", "texto"):
        os.makedirs(os.path.join(trabajo, c), exist_ok=True)
    nuevas = 0
    for n in paginas:
        img = ruta(trabajo, "paginas", n, ".png")
        capa = ruta(trabajo, "capa", n, ".txt")
        if os.path.exists(img) and os.path.exists(capa):
            continue
        p = d[n - 1]
        z = alto / p.rect.height
        pix = p.get_pixmap(matrix=fitz.Matrix(z, z), colorspace=fitz.csGRAY)
        pix.save(img)
        escribir(capa, p.get_text())
        nuevas += 1
    lotes = []
    for i in range(0, len(paginas), lote):
        grupo = paginas[i:i + lote]
        lotes.append({"id": "L%04d" % grupo[0], "paginas": grupo})
    escribir(os.path.join(trabajo, "manifiesto.json"), json.dumps({
        "pdf": os.path.abspath(pdf).replace("\\", "/"),
        "trabajo": os.path.abspath(trabajo).replace("\\", "/"),
        "paginas": paginas,
        "lotes": lotes,
    }, ensure_ascii=False, indent=1))
    print("Páginas: %d (%d imágenes nuevas) | lotes de %d: %d" % (len(paginas), nuevas, lote, len(lotes)))
    print("Siguiente paso: python temp/scripts/ocr.py pendientes \"%s\"" % trabajo)


# ---------- pendientes ----------

def transcrita(trabajo, n):
    p = ruta(trabajo, "texto", n, ".txt")
    return os.path.exists(p) and leer(p).strip() != ""


def cmd_pendientes(args):
    maximo = int(opcion(args, "--max", "20"))
    if not args:
        salir("uso: pendientes <trabajo> [--max N]")
    trabajo = args[0]
    m = manifiesto(trabajo)
    base = m["trabajo"]
    pend = []
    for l in m["lotes"]:
        faltan = [n for n in l["paginas"] if not transcrita(trabajo, n)]
        if faltan:
            pend.append((l["id"], faltan))
    total = sum(len(f) for _, f in pend)
    print("Lotes pendientes: %d (%d páginas). Se muestran %d." % (len(pend), total, min(maximo, len(pend))))
    print("CARPETA: %s" % base)
    for lid, faltan in pend[:maximo]:
        print("%s  PÁGINAS: %s" % (lid, " ".join(nombre_pagina(n) for n in faltan)))


# ---------- validar ----------

def tramos_ausentes(a, b, minimo, saltar_cabecera=False):
    """Tramos de >= minimo palabras de 'a' que no aparecen en 'b'.
    Con saltar_cabecera, ignora un tramo corto al inicio (el encabezado de página de la capa)."""
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    tramos = []
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if saltar_cabecera and i1 <= 2 and (i2 - i1) <= 14:
            continue
        if op in ("delete", "replace") and (i2 - i1) >= minimo and (i2 - i1) > 2 * (j2 - j1):
            tramos.append(" ".join(a[i1:i2]))
    return tramos, sm.ratio()


def movido(tramo, otro):
    """True si el tramo está en 'otro' en otro lugar (en bloques de 3+ palabras seguidas que cubren el 70 %).
    Pasa cuando un título (## / ###) se movió antes de su párrafo: el texto no falta, cambió de sitio."""
    if not tramo:
        return False
    sm = difflib.SequenceMatcher(None, tramo, otro, autojunk=False)
    cubierto = sum(b.size for b in sm.get_matching_blocks() if b.size >= 3)
    return cubierto >= 0.7 * len(tramo)


def parecido_en_texto(tramo, texto):
    """Mayor parecido (0-1, por caracteres) entre el tramo y algún pasaje de igual largo del texto.
    Sirve para los tramos que la capa OCR leyó mal ("tlie liath" por "the hath") o que mezcló
    de dos columnas: el tramo está en la transcripción, pero escrito bien."""
    norm = lambda s: re.sub(r"[^a-z ]", "", re.sub(r"\s+", " ", s.lower()))
    a, b = norm(tramo), norm(texto)
    n = len(a)
    if not n:
        return 0.0
    mejor = 0.0
    for i in range(0, max(1, len(b) - n), 3):
        sm = difflib.SequenceMatcher(None, a, b[i:i + n], autojunk=False)
        if sm.quick_ratio() > mejor:
            mejor = max(mejor, sm.ratio())
    return mejor


def es_adorno(tramo):
    """Raya de adorno que la capa OCR lee como letras sueltas ("v v v x v")."""
    t = tramo.split()
    return len(t) >= 5 and sum(len(w) <= 2 for w in t) >= 0.7 * len(t)


def revisar_pagina(trabajo, n):
    errores, avisos = [], []
    pt = ruta(trabajo, "texto", n, ".txt")
    if not os.path.exists(pt) or not leer(pt).strip():
        return ["falta la transcripción"], []
    texto = leer(pt)
    capa = leer(ruta(trabajo, "capa", n, ".txt")) if os.path.exists(ruta(trabajo, "capa", n, ".txt")) else ""
    pc = palabras(capa)

    if MARCA_CAPA in texto:
        avisos.append("usa la capa OCR (bloqueo del filtro); revísala a mano contra la imagen")
    if texto.strip() == MARCA_BLANCO:
        if len(pc) > 40:
            errores.append("marcada en blanco, pero la capa OCR tiene %d palabras" % len(pc))
        return errores, avisos

    # formato
    if re.search(r"\*\*|```|^(#|####+) |</?(i|em|b|strong|u)>", texto, re.M | re.I):
        errores.append("restos de markdown")
    cursivas = RE_CURSIVA.findall(texto)
    if cursivas:
        errores.append("cursivas marcadas con asteriscos (%d); quítalas con 'limpiar'" % len(cursivas))
    if RE_VOLADO.search(texto):
        errores.append("llamadas de nota en superíndice (¹ ²); pásalas a [n] con 'limpiar'")
    if (re.match(r"(?i)\s*(here is|here's)\b", texto) or re.search(r"(?i)\b(transcription|transcripci[oó]n|listo)\b", texto[:200])
            or re.search(r"(?i)(^|\n)\s*(listo|done)\.?\s*$", texto)):
        errores.append("texto agregado por el agente (comentario o 'listo')")
    for frase in FRASES_EJEMPLO:
        if " ".join(palabras(frase)[:5]) in " ".join(palabras(texto)) and not en_capa(frase, pc):
            errores.append("texto copiado del ejemplo de las instrucciones: «%s»" % frase)
    if texto.count(SEP_NOTAS) > 1:
        errores.append("%s aparece más de una vez" % SEP_NOTAS)
    if MARCA_SIGUE in texto and not texto.lstrip().startswith(MARCA_SIGUE):
        errores.append("%s solo puede ir en la primera línea" % MARCA_SIGUE)
    cuerpo, notas = partes(texto)

    # notas
    llamadas = [int(x) for x in RE_LLAMADA.findall(cuerpo)]
    numeros = []
    for linea in [l for l in notas.splitlines() if l.strip()]:
        mm = RE_NOTA.match(linea.strip())
        if not mm:
            errores.append("línea de notas sin [n] al inicio: «%s»" % linea.strip()[:60])
        elif mm.group(1) != "sigue":
            numeros.append(int(mm.group(1)))
    if sorted(set(llamadas)) != sorted(set(numeros)):
        sin_nota = sorted(set(llamadas) - set(numeros))
        sin_llamada = sorted(set(numeros) - set(llamadas))
        if sin_nota:
            errores.append("llamadas sin nota al pie: %s" % sin_nota)
        if sin_llamada:
            errores.append("notas sin llamada en el texto: %s" % sin_llamada)
    if numeros != sorted(numeros):
        avisos.append("las notas no están en orden: %s" % numeros)
    # una nota [sigue] copiada tal cual de la página anterior (el agente la repitió)
    previa = ruta(trabajo, "texto", n - 1, ".txt")
    if "[sigue]" in notas and os.path.exists(previa):
        _, notas_prev = partes(leer(previa))
        cola = lambda l: re.sub(r"^\[(\d+|sigue)\]\s*", "", l.strip())
        prev = set(cola(l) for l in notas_prev.splitlines() if l.strip())
        for l in notas.splitlines():
            if l.strip().startswith("[sigue]") and len(cola(l)) > 20 and cola(l) in prev:
                errores.append("la nota [sigue] repite una nota de la página anterior: «%s»" % cola(l)[:60])

    # cobertura contra la capa OCR
    pt_ = palabras(re.sub(r"\[\[[^\]]*\]\]|\[(\d+|sigue|ilegible|griego|hebreo)\]|" + re.escape(SEP_NOTAS), " ", texto))
    if len(pc) >= 40:
        omitidos, ratio = tramos_ausentes(pc, pt_, 8, saltar_cabecera=True)
        # los títulos (## / ###) pueden venir del índice del libro: no cuentan como texto agregado
        sin_titulos = "\n".join(l for l in texto.splitlines() if not RE_TITULO.match(l))
        pt_st = palabras(re.sub(r"\[\[[^\]]*\]\]|\[(\d+|sigue|ilegible|griego|hebreo)\]|" + re.escape(SEP_NOTAS), " ", sin_titulos))
        agregados, _ = tramos_ausentes(pt_st, pc, 8)
        proporcion = len(pt_) / float(len(pc))
        if proporcion < 0.85:
            errores.append("la transcripción tiene %d palabras y la capa OCR %d (%.0f%%): posible omisión" % (len(pt_), len(pc), proporcion * 100))
        elif proporcion > 1.15:
            avisos.append("la transcripción tiene %d palabras y la capa OCR %d (%.0f%%)" % (len(pt_), len(pc), proporcion * 100))
        if ratio < 0.45:
            errores.append("parecido muy bajo con la capa OCR (%.2f): ¿es el texto de otra página?" % ratio)
        elif ratio < 0.80:
            avisos.append("parecido bajo con la capa OCR (%.2f)" % ratio)
        for t in omitidos:
            if movido(t.split(), pt_):
                continue
            if es_adorno(t):
                avisos.append("raya de adorno leída como letras en la capa OCR: «%s»" % t[:60])
                continue
            p = parecido_en_texto(t, cuerpo)
            if p >= 0.65:
                # la capa lo leyó mal o mezcló renglones de dos columnas; el texto sí está
                avisos.append("tramo de la capa mal leído, pero presente (parecido %.2f): «%s»" % (p, t[:100]))
            else:
                errores.append("posible omisión (está en la capa OCR, parecido %.2f): «%s»" % (p, t[:120]))
        for t in agregados:
            if not movido(t.split(), pc):
                avisos.append("posible texto agregado (no está en la capa OCR): «%s»" % t[:120])
    elif len(pt_) > 80 and len(pc) < 10:
        avisos.append("la capa OCR está casi vacía; no se pudo comparar")

    ileg = texto.count("[ilegible]")
    if ileg:
        avisos.append("%d [ilegible]" % ileg)
    return errores, avisos


def cmd_validar(args):
    paginas_txt = opcion(args, "--paginas")
    if not args:
        salir("uso: validar <trabajo> [--paginas R]")
    trabajo = args[0]
    m = manifiesto(trabajo)
    paginas = m["paginas"]
    if paginas_txt:
        pedidas = set(rango(paginas_txt, max(paginas)))
        paginas = [p for p in paginas if p in pedidas]
    total_e = total_a = 0
    malas = []
    for n in paginas:
        errores, avisos = revisar_pagina(trabajo, n)
        if errores or avisos:
            print("página %d (%s):" % (n, nombre_pagina(n)))
            for e in errores:
                print("  ERROR " + e)
            for a in avisos:
                print("  aviso " + a)
        if errores:
            malas.append(n)
        total_e += len(errores)
        total_a += len(avisos)
    print()
    for aviso in saltos_numeracion(trabajo, paginas):
        print("aviso " + aviso)
    print("Páginas: %d | errores: %d | avisos: %d" % (len(paginas), total_e, total_a))
    if malas:
        print("Páginas con errores: " + ",".join(str(n) for n in malas))


def numero_impreso(trabajo, n):
    """Número de página impreso según la capa OCR (un número solo en los primeros renglones)."""
    p = ruta(trabajo, "capa", n, ".txt")
    if not os.path.exists(p):
        return None
    for linea in leer(p).splitlines()[:4]:
        m = re.fullmatch(r"\s*(\d{1,4})\s*", linea)
        if m:
            return int(m.group(1))
    return None


def saltos_numeracion(trabajo, paginas):
    """Páginas que faltan (o sobran) en el escaneo: la diferencia entre el número impreso y el
    del PDF cambia y se mantiene en las dos páginas siguientes (así se ignoran los errores del OCR)."""
    nums = [(n, numero_impreso(trabajo, n)) for n in paginas]
    nums = [(n, k - n) for n, k in nums if k is not None]
    avisos = []
    for i in range(1, len(nums) - 2):
        antes, ahora = nums[i - 1][1], nums[i][1]
        if ahora != antes and nums[i + 1][1] == ahora and nums[i + 2][1] == ahora \
                and (i < 2 or nums[i - 2][1] == antes):
            n0, n1 = nums[i - 1][0], nums[i][0]
            dif = ahora - antes
            if abs(dif) > 20:  # el OCR leyó mal varias cifras seguidas (352 -> 852)
                continue
            que = "faltan %d páginas del impreso" % dif if dif > 0 else "el impreso retrocede %d páginas (¿repetidas?)" % -dif
            if n1 - n0 > 1:  # entre ambas hay páginas sin número (portadillas, notas)
                que += " (hay páginas sin número en medio: puede ser solo una página en blanco no escaneada; míralo)"
            else:
                que += "; no pongas [[sigue]] en ese corte, marca el hueco en el texto y avisa al usuario"
            avisos.append("numeración impresa: entre p%04d (impresa %d) y p%04d (impresa %d) %s"
                          % (n0, n0 + antes, n1, n1 + ahora, que))
    return avisos


# ---------- limpiar ----------

def cmd_limpiar(args):
    """Quita las cursivas en markdown (*texto*) que a veces escriben los agentes."""
    if not args:
        salir("uso: limpiar <trabajo>")
    trabajo = args[0]
    m = manifiesto(trabajo)
    total = 0
    for n in m["paginas"]:
        p = ruta(trabajo, "texto", n, ".txt")
        if not os.path.exists(p):
            continue
        t = leer(p)
        nuevo, k = re.subn(r"</?(i|em|b|strong|u)>", "", t, flags=re.I)  # etiquetas HTML de cursiva
        while True:
            nuevo, j = RE_CURSIVA.subn(r"\1\3", nuevo)
            if not j:
                break
            k += j
        # llamadas de nota escritas como superíndice unicode (²) -> [2]
        nuevo, s = RE_VOLADO.subn(lambda v: "[%s]" % v.group(0).translate(VOLADOS), nuevo)
        if s:
            print("página %d: %d llamadas en superíndice pasadas a [n]" % (n, s))
        if k or s:
            escribir(p, nuevo)
            total += k
        if k:
            print("página %d: %d cursivas" % (n, k))
    print("Cursivas quitadas: %d. Revisa los asteriscos que queden (pueden ser signos impresos):" % total)
    print('  grep -n "\\*" "%s/texto/"*.txt' % trabajo)


# ---------- cortes entre páginas ----------

def cuerpo_pagina(trabajo, n):
    t = leer(ruta(trabajo, "texto", n, ".txt")).replace(MARCA_CAPA, "").strip()
    cuerpo, _ = partes(t)
    return cuerpo


def fin_de_parrafo(cuerpo):
    """True si el último párrafo de la página termina como fin de párrafo (o es un título)."""
    ultimo = [p for p in re.split(r"\n\s*\n", cuerpo) if p.strip()]
    ultimo = ultimo[-1].strip() if ultimo else ""
    if RE_TITULO.match(ultimo) or ultimo == MARCA_BLANCO:
        return True
    ultimo = re.sub(r"(\[\d+\])+$", "", ultimo).rstrip()
    return bool(RE_FIN.search(ultimo))


def cortes_dudosos(trabajo, paginas, todos=False):
    """Cortes entre páginas donde la marca [[sigue]] contradice la puntuación.
    Devuelve [(n, tipo, final de la anterior, inicio de la página)]."""
    dudosos = []
    for a, n in zip(paginas, paginas[1:]):
        if n != a + 1:
            continue
        previo, actual = cuerpo_pagina(trabajo, a), cuerpo_pagina(trabajo, n)
        if MARCA_BLANCO in (previo, actual) or not previo or not actual:
            continue
        sigue = actual.startswith(MARCA_SIGUE)
        inicio = actual[len(MARCA_SIGUE):].strip() if sigue else actual
        if re.match(r"#{2,3} ", inicio) or previo.endswith("-"):
            continue
        termina = fin_de_parrafo(previo)
        mayuscula = re.match(r"[A-Z]", inicio) is not None
        if sigue and termina and mayuscula and not RE_REFERENCIA.match(inicio):
            dudosos.append((n, "tiene [[sigue]] pero la anterior termina con punto", previo[-50:], inicio[:50]))
        elif not sigue and not termina and not re.match(r"[a-z]", inicio) and not RE_DIVISION.match(inicio):
            dudosos.append((n, "sin [[sigue]] pero la anterior queda a medias", previo[-50:], inicio[:50]))
        elif todos and not sigue and termina and mayuscula and not RE_DIVISION.match(inicio):
            dudosos.append((n, "sin [[sigue]], la anterior termina con punto (revisión completa)", previo[-50:], inicio[:50]))
    return dudosos


def cmd_cortes(args):
    """Lista los cortes dudosos y recorta el inicio de cada página (cortes/pNNNN.png) para mirar la sangría."""
    alto_recorte = float(opcion(args, "--alto", "0.13"))
    ok = opcion(args, "--ok")
    todos = "--todos" in args
    if todos:
        args.remove("--todos")
    if not args:
        salir("uso: cortes <trabajo> [--alto 0.13] [--ok 104,112,...]")
    trabajo = args[0]
    m = manifiesto(trabajo)
    os.makedirs(os.path.join(trabajo, "cortes"), exist_ok=True)
    p_rev = os.path.join(trabajo, "cortes", "revisados.txt")
    revisados = set(int(x) for x in re.findall(r"\d+", leer(p_rev))) if os.path.exists(p_rev) else set()
    if ok:
        revisados |= set(rango(ok, max(m["paginas"])))
        escribir(p_rev, "\n".join(str(n) for n in sorted(revisados)) + "\n")
        print("Marcadas como revisadas: %s" % ok)
    paginas = [n for n in m["paginas"] if transcrita(trabajo, n)]
    dudosos = [d for d in cortes_dudosos(trabajo, paginas, todos) if d[0] not in revisados]
    if dudosos and fitz is None:
        salir("falta PyMuPDF para hacer los recortes")
    os.makedirs(os.path.join(trabajo, "cortes"), exist_ok=True)
    for n, tipo, fin, inicio in dudosos:
        img = ruta(trabajo, "paginas", n, ".png")
        rec = ruta(trabajo, "cortes", n, ".png")
        if os.path.exists(img) and not os.path.exists(rec):
            src = fitz.open(img)
            r = src[0].rect
            src[0].get_pixmap(clip=fitz.Rect(0, 0, r.width, r.height * alto_recorte)).save(rec)
        print("página %d: %s\n  …%s ‖ %s\n  recorte: %s" % (n, tipo, fin.replace("\n", " "), inicio.replace("\n", " "), rec))
    # láminas de hasta 8 recortes con su número de página, para revisarlos de un vistazo
    for f in os.listdir(os.path.join(trabajo, "cortes")):
        if f.startswith("lamina_"):
            os.remove(os.path.join(trabajo, "cortes", f))
    laminas = []
    for i in range(0, len(dudosos), 8):
        grupo = [n for n, _, _, _ in dudosos[i:i + 8]]
        ancho, alto_fila, etiqueta = 700, 0, 22
        imgs = [fitz.Pixmap(ruta(trabajo, "cortes", n, ".png")) for n in grupo]
        filas = [(n, px, ancho * px.height / float(px.width)) for n, px in zip(grupo, imgs)]
        doc = fitz.open()
        pag = doc.new_page(width=ancho, height=sum(h + etiqueta for _, _, h in filas))
        y = 0
        for n, px, h in filas:
            pag.insert_text((6, y + 16), "p%04d" % n, fontsize=14, color=(0.8, 0, 0))
            pag.insert_image(fitz.Rect(0, y + etiqueta, ancho, y + etiqueta + h), pixmap=px)
            y += h + etiqueta
        sal = os.path.join(trabajo, "cortes", "lamina_%02d.png" % (i // 8 + 1)).replace("\\", "/")
        pag.get_pixmap().save(sal)
        laminas.append(sal)
    print()
    for l in laminas:
        print("lámina: " + l)
    print("Cortes dudosos: %d (sin contar %d ya revisados). En cada recorte mira si el primer renglón tiene sangría:" % (len(dudosos), len(revisados)))
    print("  con sangría = párrafo nuevo (sin [[sigue]]); pegado al margen = continúa (con [[sigue]]).")
    print("  Corrige las marcas que estén mal y registra las correctas con --ok <páginas>.")


# ---------- capa (último recurso) ----------

def cmd_capa(args):
    if len(args) < 2:
        salir("uso: capa <trabajo> <pagina>")
    trabajo, n = args[0], int(args[1])
    capa = leer(ruta(trabajo, "capa", n, ".txt"))
    lineas = [l.strip() for l in capa.splitlines()]
    texto = re.sub(r"-\n(?=[a-z])", "", "\n".join(lineas))
    texto = re.sub(r"(?<!\n)\n(?!\n)", " ", texto)
    texto = re.sub(r"[ \t]+", " ", texto).strip()
    escribir(ruta(trabajo, "texto", n, ".txt"), MARCA_CAPA + "\n" + texto + "\n")
    print("Escrita la capa OCR en %s. Revísala a mano contra la imagen antes de unir." % ruta(trabajo, "texto", n, ".txt"))


# ---------- unir ----------

def normalizar(s):
    """Espaciado moderno: sin espacio antes de ; : ! ? , . ni dentro de las comillas."""
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r" +([;:!?,.](?!\.\.))", r"\1", s)
    s = re.sub(r"(^|[\s(\[—])' +(?=\w)", r"\1'", s)
    s = re.sub(r"(?<=[\w.,;:!?)])\s+'(?=[\s,.;:)\]—]|$)", "'", s)
    return s.strip()


class Nota(object):
    def __init__(self, numero, texto):
        self.numero = numero
        self.texto = texto


def cmd_unir(args):
    paginas_txt = opcion(args, "--paginas")
    if len(args) < 2:
        salir("uso: unir <trabajo> <salida.txt> [--paginas R]")
    trabajo, salida = args[0], args[1]
    m = manifiesto(trabajo)
    paginas = m["paginas"]
    if paginas_txt:
        pedidas = set(rango(paginas_txt, max(paginas)))
        paginas = [p for p in paginas if p in pedidas]
    faltan = [n for n in paginas if not transcrita(trabajo, n)]
    if faltan:
        salir("faltan transcripciones de las páginas: %s" % ",".join(str(n) for n in faltan[:30]))

    salida_items = []   # str (párrafo) o list[Nota] (bloque de notas)
    pendientes = []     # notas cuya llamada ya salió y aún no se imprimen
    ultima_nota = None
    contador = 0
    avisos = []

    def volcar():
        if pendientes:
            salida_items.append(list(pendientes))
            del pendientes[:]

    for n in paginas:
        texto = leer(ruta(trabajo, "texto", n, ".txt")).replace(MARCA_CAPA, "").strip()
        if texto == MARCA_BLANCO:
            continue
        sigue = texto.startswith(MARCA_SIGUE)
        if sigue:
            texto = texto[len(MARCA_SIGUE):].strip()
        cuerpo, notas_txt = partes(texto)

        # notas de la página: número local -> Nota con número global
        locales = {}
        for linea in [l.strip() for l in notas_txt.splitlines() if l.strip()]:
            mm = RE_NOTA.match(linea)
            if not mm:
                continue
            if mm.group(1) == "sigue":
                if ultima_nota is not None:
                    ultima_nota.texto = (ultima_nota.texto.rstrip("-") if ultima_nota.texto.endswith("-") else ultima_nota.texto + " ") + mm.group(2)
                else:
                    avisos.append("página %d: [sigue] en notas sin nota anterior" % n)
                continue
            contador += 1
            nota = Nota(contador, mm.group(2))
            locales[int(mm.group(1))] = nota
            ultima_nota = nota

        parrafos = [p.strip() for p in re.split(r"\n\s*\n", cuerpo) if p.strip()]
        for i, p in enumerate(parrafos):
            p = re.sub(r"\s*\n\s*", " ", p)
            mt = RE_TITULO.match(p)
            es_titulo = mt is not None
            marca = mt.group(1) + " " if mt else ""
            if es_titulo:
                p = mt.group(2).strip()
                volcar()

            def cambiar(mm):
                nota = locales.get(int(mm.group(1)))
                if nota is None:
                    return mm.group(0)
                if nota not in pendientes:
                    pendientes.append(nota)
                return "[%d]" % nota.numero
            p = RE_LLAMADA.sub(cambiar, p)
            p = normalizar(p)

            previo = salida_items[-1] if salida_items and isinstance(salida_items[-1], str) else None
            previo_titulo = previo is not None and RE_TITULO.match(previo) is not None
            previo_abierto = previo is not None and not previo_titulo and not RE_FIN.search(re.sub(r"(\[\d+\])+$", "", previo).rstrip())
            continua = (i == 0 and previo is not None and not es_titulo and not previo_titulo and
                        (sigue or previo.endswith("-") or (previo_abierto and re.match(r"[a-z]", p))))
            if continua:
                if not sigue:
                    avisos.append("página %d: se unió al párrafo anterior sin [[sigue]] («%s»)" % (n, p[:40]))
                if previo.endswith("-") and re.match(r"[a-z]", p):
                    salida_items[-1] = previo[:-1] + p
                else:
                    salida_items[-1] = previo + " " + p
            else:
                salida_items.append(marca + p)
        sin_usar = [k for k, v in locales.items() if v not in pendientes and not any(isinstance(x, list) and v in x for x in salida_items)]
        for k in sin_usar:
            avisos.append("página %d: la nota [%d] no tiene llamada en el texto" % (n, k))
            pendientes.append(locales[k])
    volcar()

    lineas = []
    for item in salida_items:
        if isinstance(item, list):
            lineas.append("__________")
            lineas.extend("[%d] %s" % (nota.numero, normalizar(nota.texto)) for nota in item)
            lineas.append("")
        else:
            lineas.append(item)
            lineas.append("")
    escribir(salida, "\n".join(lineas).strip() + "\n")
    for a in avisos:
        print("aviso " + a)
    print("Escrito %s: %d páginas, %d párrafos, %d notas." % (
        salida, len(paginas), sum(1 for x in salida_items if isinstance(x, str)), contador))


COMANDOS = {
    "info": cmd_info,
    "preparar": cmd_preparar,
    "pendientes": cmd_pendientes,
    "validar": cmd_validar,
    "capa": cmd_capa,
    "limpiar": cmd_limpiar,
    "cortes": cmd_cortes,
    "unir": cmd_unir,
}

if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) < 2 or sys.argv[1] not in COMANDOS:
        print(__doc__)
        sys.exit(1)
    COMANDOS[sys.argv[1]](sys.argv[2:])
