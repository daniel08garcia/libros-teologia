# Prepara "The Works of William Perkins", vol. 2 (transcrito con ocr.py) para la traducción con sermones.js.
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
# Uso: python temp/trabajo/perkins2-preparar.py
import io, json, math, os, re

ORIG = "temp/originales/[WP] The Works of William Perkins (vol.2).txt"
SALIDA = "temp/trabajo/perkins-v2"
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
    (1, 4094, "Tratado De Los Casos De Conciencia", "1606-01-01"),
    (4095, 8760, "Comentario A La Epístola A Los Gálatas", "1604-01-01"),
    (8761, 9037, "Tratado De La Equidad Cristiana", "1604-01-01"),
    (9038, 9701, "Tratado De Las Imaginaciones Del Hombre", "1607-01-01"),
    (9702, 12611, "El Problema Del Falso Catolicismo", "1604-01-01"),
    (12612, 13292, "Tratado Del Modo Y Orden De La Predestinación", "1598-01-01"),
    (13293, 14362, "El Arte De Profetizar", "1592-01-01"),
    (14363, 10 ** 9, "Compendio O Armonía De Los Libros Del Antiguo Y Nuevo Testamento", "1613-01-01"),
]
# Portadillas de cada obra (su título es el nombre de la carpeta)
QUITAR = {1, 4095, 4155, 7663, 8761, 9038, 9702, 12612, 13293, 14363}
BORRAR_TITULO = set()
PREFACIO = {5, 65, 4099, 4135, 8765, 8788, 9042, 9071, 12616, 12631, 13305, 13320, 14367, 14384}
JUNTAR = {1216, 3030,       # el cap. I de los libros 2.º y 3.º va con el título del libro
          9079,             # Imaginaciones: el cap. I va con el texto de Gén. 8. 21
          9716, 13338}      # Problema: la explicación va con la posición; Arte de profetizar: cap. II con el I
# Cortes que no empiezan en un título: (texto con que empieza el párrafo) -> título inglés de la pieza nueva
CORTES_TEXTO = {
    "THE Apostle in this chapter, giveth sundry exhortations":
        "A Treatise of Christian Equity and Moderation",
}
SEPARAR = {1212, 3026, 4157, 7667, 9075, 13252, 14345}
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
            if (len(partes) < n - 1 and acum >= objetivo * (len(partes) + 1) and sig is not None
                    and not re.match(r"\[\d+\] ", sig) and not sig.startswith("#")):
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
