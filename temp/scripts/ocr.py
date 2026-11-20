#!/usr/bin/env python
"""Herramienta para transcribir PDFs escaneados con agentes (ver temp/ocr_agent.md).

Comandos:
  info <pdf>                                   Páginas, capa de texto y muestra de cada parte del libro.
  preparar <pdf> <trabajo> [--paginas R] [--lote N] [--alto PX]
                                               Crea las imágenes (paginas/), la capa OCR (capa/) y el manifiesto.
  pendientes <trabajo> [--max N]               Lotes con páginas sin transcribir, listos para lanzar agentes.
  validar <trabajo> [--paginas R]              Revisa cada transcripción contra la capa OCR del PDF.
  capa <trabajo> <pagina>                      Último recurso: escribe la capa OCR como transcripción (queda marcada).
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
    if re.search(r"\*\*|```|^(#|###+) ", texto, re.M):
        errores.append("restos de markdown")
    if re.search(r"(?i)\b(here is|transcription|transcripci[oó]n|listo)\b", texto[:200]) or re.search(r"(?i)(listo|done)\s*$", texto):
        errores.append("texto agregado por el agente (comentario o 'listo')")
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

    # cobertura contra la capa OCR
    pt_ = palabras(re.sub(r"\[\[[^\]]*\]\]|\[(\d+|sigue|ilegible|griego|hebreo)\]|" + re.escape(SEP_NOTAS), " ", texto))
    if len(pc) >= 40:
        omitidos, ratio = tramos_ausentes(pc, pt_, 8, saltar_cabecera=True)
        agregados, _ = tramos_ausentes(pt_, pc, 8)
        proporcion = len(pt_) / float(len(pc))
        if proporcion < 0.85:
            errores.append("la transcripción tiene %d palabras y la capa OCR %d (%.0f%%): posible omisión" % (len(pt_), len(pc), proporcion * 100))
        elif proporcion > 1.15:
            avisos.append("la transcripción tiene %d palabras y la capa OCR %d (%.0f%%)" % (len(pt_), len(pc), proporcion * 100))
        if ratio < 0.80:
            avisos.append("parecido bajo con la capa OCR (%.2f)" % ratio)
        for t in omitidos:
            errores.append("posible omisión (está en la capa OCR): «%s»" % t[:120])
        for t in agregados:
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
    print("Páginas: %d | errores: %d | avisos: %d" % (len(paginas), total_e, total_a))
    if malas:
        print("Páginas con errores: " + ",".join(str(n) for n in malas))


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
            es_titulo = p.startswith("## ")
            if es_titulo:
                p = p[3:].strip()
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
            continua = (i == 0 and previo is not None and not es_titulo and
                        (sigue or previo.endswith("-") or (re.match(r"[a-z]", p) and not re.search(r"[.!?:'\"]\]?$", previo))))
            if continua:
                if not sigue:
                    avisos.append("página %d: se unió al párrafo anterior sin [[sigue]] («%s»)" % (n, p[:40]))
                if previo.endswith("-") and re.match(r"[a-z]", p):
                    salida_items[-1] = previo[:-1] + p
                else:
                    salida_items[-1] = previo + " " + p
            else:
                salida_items.append(("## " if es_titulo else "") + p)
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
            lineas.append(item[3:] if item.startswith("## ") else item)
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
    "unir": cmd_unir,
}

if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) < 2 or sys.argv[1] not in COMANDOS:
        print(__doc__)
        sys.exit(1)
    COMANDOS[sys.argv[1]](sys.argv[2:])
