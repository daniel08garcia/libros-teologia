# Prepara "The Works of William Perkins", vol. 3 (transcrito con ocr.py) para la traducción con sermones.js.
# Modelo: watson-preparar.py. Una carpeta por obra en siglo/XVI/William Perkins/<Obra>/, un HTML por pieza.
# - Cada pieza empieza en un título "## " del original (capítulo, sección del Credo, punto, etc.).
# - QUITAR: piezas que no se publican (portadillas, índices). BORRAR_TITULO: el título se quita y su texto
#   queda en la pieza anterior. JUNTAR: la pieza se agrega a la anterior (su título queda como <h2>).
# - PREFACIO: dedicatorias y avisos al lector de cada obra; se juntan en una sola pieza con id 0.
# - Las piezas pequeñas (< 2.500 caracteres, salvo capítulos) se agregan a la anterior.
# - Las piezas muy largas (> 85.000) se cortan en partes de unos 65.000 caracteres, entre párrafos y nunca
#   delante de un bloque de notas; las partes siguientes no llevan título propio («(Part 2)»).
# - Pasa cada nota a un párrafo propio y quita la línea "__________" (el README pide un <p> por nota).
# - Escribe plan.json (destino, fecha, id, saltar, versiculo, titulo_original) en el orden de las piezas.
#
# Las partes se cortan, si se puede, antes de un subtítulo "### " (versículo), hasta 12.000 caracteres después de la meta.
# Uso: python temp/trabajo/perkins3-preparar.py
import io, json, math, os, re

ORIG = "temp/originales/[WP] The Works of William Perkins (vol.3).txt"
SALIDA = "temp/trabajo/perkins-v3"
BASE = "siglo/XVI/William Perkins"


def romano(n):
    out = ""
    for v, s in ((1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"), (90, "XC"), (50, "L"), (40, "XL"),
                 (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")):
        while n >= v:
            out += s; n -= v
    return out


# Obras: (línea inicial, línea final, carpeta, fecha de la primera edición). Líneas 1-based del .txt.
OBRAS = [
    (1, 5377, "Exposición Del Sermón Del Monte", "1608-01-01"),
    (5378, 9329, "Comentario Al Capítulo 11 De Hebreos", "1607-01-01"),
    (9330, 12272, "Exposición De Los Tres Primeros Capítulos Del Apocalipsis", "1604-01-01"),
    (12273, 13195, "El Combate Entre Cristo Y El Diablo", "1606-01-01"),
    (13196, 13436, "Exposición De Los Dos Primeros Versículos De Sofonías 2", "1605-01-01"),
    (13437, 14360, "Del Llamamiento Al Ministerio", "1605-01-01"),
    (14361, 14706, "Diálogo Sobre El Fin Del Mundo", "1587-01-01"),
    (14707, 16574, "Exposición De La Epístola De Judas", "1606-01-01"),
    (16575, 17529, "Discurso Del Maldito Arte De La Brujería", "1608-01-01"),
    (17530, 17992, "Resolución Para El Hombre Del Campo", "1585-01-01"),
    (17993, 10 ** 9, "Economía Cristiana O Gobierno De La Familia", "1609-01-01"),
]
# Líneas que se reemplazan antes de cortar: (línea, comienzo esperado, texto nuevo). Sirven para poner un título
# "## " donde empieza el comentario propiamente dicho (el OCR lo dejó como párrafo o como "### ").
REEMPLAZAR = [
    (66, "A Godly and Learned EXPOSITION VPON Christs Sermon in the Mount. Matth. 5. 1.",
     lambda t: "## CHAP. 5.\n\n### " + t[len("A Godly and Learned EXPOSITION VPON Christs Sermon in the Mount. "):]),
    (9645, "A GODLY AND LEARNED EXPOSITION OF the three first Chapters", lambda t: "## CHAP. 1."),
    (13239, "### AN EXHORTATION TO REPENTANCE. Zephaniah",
     lambda t: "## AN EXHORTATION TO REPENTANCE.\n\n### " + t[len("### AN EXHORTATION TO REPENTANCE. "):]),
    (14857, "A Godly and Learned EXPOSITION VPON THE EPISTLE OF IVDE,",
     lambda t: "## A Godly and Learned EXPOSITION VPON THE EPISTLE OF IVDE."),
    (17538, "London, Printed by Iohn Haviland", lambda t: ""),
]
# Portadillas de cada obra (su título es el nombre de la carpeta) y la del segundo tratado del ministerio
QUITAR = {1, 9330, 12273, 13196, 13437, 13742, 14361, 14707, 16575, 17993, 17997}
BORRAR_TITULO = set()
PREFACIO = {5, 48, 5378, 9334, 9362, 9607, 12277, 12342, 13200, 13441, 14369, 14379, 14711, 14763, 16579}
JUNTAR = {
          16675,            # Brujería: el cap. I va con el texto de Éx. 22. 18
          17566,            # Resolución: el tratado va con su portada y su sumario
          18007}            # Economía: el cap. II va con el I (muy corto)
CORTES_TEXTO = {}
SEPARAR = {9621, 12533}
PEQUENA, GRANDE, PARTE = 2500, 85000, 65000

PEQ = {"a", "an", "the", "of", "in", "on", "to", "and", "but", "or", "for", "by", "his", "at", "with", "into", "as",
       "it", "is", "vnto", "vpon", "from", "that"}


def titulo_ingles(t):
    t = re.sub(r"^#+ ", "", t).strip().rstrip(".,:")
    if sum(c.isupper() for c in t) > 0.6 * sum(c.isalpha() for c in t):
        ps = t.lower().split()
        t = " ".join(p if (i and p in PEQ) else p[:1].upper() + p[1:] for i, p in enumerate(ps))
    return re.sub(r"\b(Chap\.?) ([IVXLivxl]+)\b", lambda m: m.group(1) + " " + m.group(2).upper(), t)


def parrafos(lineas):
    return [p.strip() for p in re.split(r"\n\s*\n", "\n".join(lineas)) if p.strip()]


def notas_aparte(ps):
    out = []
    for p in ps:
        if p.startswith("__________"):
            out.extend(l.strip() for l in p.split("\n")[1:] if l.strip())
        else:
            out.append(p)
    return out


L = io.open(ORIG, encoding="utf-8").read().split("\n")
for n, ini, f in REEMPLAZAR:
    assert L[n - 1].startswith(ini), (n, L[n - 1][:80])
    L[n - 1] = f(L[n - 1])
N = len(L)
titulos2 = [i + 1 for i, l in enumerate(L) if l.startswith("## ")]

piezas = []   # dict(obra, fecha, lineas, cab, pref)
for o0, o1, carpeta, fecha in OBRAS:
    o1 = min(o1, N)
    inicios = [x for x in titulos2 if o0 <= x <= o1]
    for k, a in enumerate(inicios):
        b = inicios[k + 1] - 1 if k + 1 < len(inicios) else o1
        if a in QUITAR:
            continue
        lineas = L[a - 1:b]
        if a in BORRAR_TITULO:
            if piezas and piezas[-1]["obra"] == carpeta:
                piezas[-1]["lineas"] += [""] + lineas[1:]
            continue
        pz = dict(obra=carpeta, fecha=fecha, lineas=lineas, cab=a, pref=a in PREFACIO)
        ant = piezas[-1] if piezas and piezas[-1]["obra"] == carpeta else None
        chars = sum(len(x) + 1 for x in lineas)
        es_cap = re.match(r"## (CHAP|Chap)", L[a - 1])
        if ant and (a in JUNTAR or (ant["pref"] and pz["pref"])
                    or (chars < PEQUENA and not es_cap and not pz["pref"] and not ant["pref"] and a not in SEPARAR)):
            ant["lineas"] += [""] + lineas
            continue
        piezas.append(pz)

# Cortes por texto (Cómo conocer a Cristo crucificado: el aviso al lector y el tratado van en la misma sección)
nuevas = []
for pz in piezas:
    hecho = False
    for ini, tit in CORTES_TEXTO.items():
        idx = [i for i, l in enumerate(pz["lineas"]) if l.startswith(ini)]
        if idx:
            i = idx[0]
            nuevas.append(dict(pz, lineas=pz["lineas"][:i]))
            nuevas.append(dict(pz, lineas=["## " + tit, ""] + pz["lineas"][i:], pref=False, cab=pz["cab"] + i))
            hecho = True
    if not hecho:
        nuevas.append(pz)
piezas = nuevas

texto, plan, ids = [], [], {}
for pz in piezas:
    ps = notas_aparte(parrafos(pz["lineas"]))
    if not ps:
        continue
    total = sum(len(p) for p in ps)
    partes = [ps]
    if total > GRANDE:
        n = math.ceil(total / PARTE)
        partes, actual, acum = [], [], 0
        objetivo = total / n
        for i, p in enumerate(ps):
            actual.append(p)
            acum += len(p)
            sig = ps[i + 1] if i + 1 < len(ps) else None
            meta = objetivo * (len(partes) + 1)
            if (len(partes) < n - 1 and acum >= meta and sig is not None
                    and not re.match(r"\[\d+\] ", sig) and not p.startswith("#")
                    and (sig.startswith("### ") or (acum >= meta + 12000 and not sig.startswith("#")))):
                partes.append(actual); actual = []
        if actual:
            partes.append(actual)
    d = f"{BASE}/{pz['obra']}"
    base_tit = titulo_ingles(ps[0]) if ps[0].startswith("## ") else "Untitled"
    for k, parte in enumerate(partes):
        es_titulo = parte[0].startswith("## ")
        if pz["pref"]:
            idp = "0"
        else:
            ids[d] = ids.get(d, 0) + 1
            idp = romano(ids[d])
        tit = base_tit if len(partes) == 1 else f"{base_tit} (Part {k + 1})"
        texto.append("@@SERMON@@\n\n" + "\n\n".join(parte))
        plan.append(dict(destino=d, fecha=pz["fecha"], id=idp, saltar=1 if es_titulo else 0, versiculo=None,
                         titulo_original=tit, linea=pz["cab"], inicio=parte[0][:100]))

os.makedirs(SALIDA, exist_ok=True)
io.open(f"{SALIDA}/original-marcado.txt", "w", encoding="utf-8", newline="\n").write("\n\n".join(texto) + "\n")
io.open(f"{SALIDA}/plan.json", "w", encoding="utf-8", newline="\n").write(json.dumps(plan, ensure_ascii=False, indent=1) + "\n")
print(len(plan), "piezas;", sum(len(t) for t in texto), "caracteres")
for p, t in zip(plan, texto):
    print(f"{p['destino'].split('/')[-1][:16]:16} {p['id']:6} {len(t) // 1000:4}k {p['saltar']} {p['titulo_original'][:75]}")
