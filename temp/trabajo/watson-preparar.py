# Prepara "Select Works of Thomas Watson" (transcrito con ocr.py) para la traducción con sermones.js.
# - Corta el original en piezas, una por HTML, y las marca con @@SERMON@@.
# - Cada pieza empieza en un título "## " del original. Las secciones muy largas del Padrenuestro
#   (y otras) se cortan además en las líneas de CORTES; esas piezas de continuación no tienen título propio.
# - Si el párrafo que sigue al título es el texto bíblico en un solo párrafo ("Ref. texto" o "texto, Ref."),
#   lo parte en dos párrafos (referencia, texto) y pone versiculo "auto".
# - Pasa cada nota a un párrafo propio y quita la línea "__________" (el README pide un <p> por nota).
# - Escribe plan.json (destino, fecha, id, saltar, versiculo, titulo_original, titulo_es) en el mismo orden
#   que las piezas; watson-manifiesto.py lo copia al manifiesto después de "dividir".
#
# Uso: python temp/trabajo/watson-preparar.py
import io, json, os, re

ORIG = "temp/originales/Select Works of Thomas Watson.txt"
SALIDA = "temp/trabajo/watson"
BASE = "siglo/XVII/Thomas Watson"
UT = f"{BASE}/Un Tratado De Teología Práctica"
DM = f"{BASE}/Los Diez Mandamientos"
PN = f"{BASE}/El Padrenuestro"
SS = f"{BASE}/Sermones Selectos"
AC = f"{BASE}/El Arte Del Contentamiento Divino"
TR = f"{BASE}/Tratados"
def romano(n):
    out = ""
    for v, s in ((90, "XC"), (50, "L"), (40, "XL"), (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")):
        while n >= v:
            out += s; n -= v
    return out
ROM = ["0"] + [romano(n) for n in range(1, 100)]

# Zonas del libro: (línea inicial, línea final, destino, fecha). Líneas 1-based del .txt.
ZONAS = [
    (1, 8, BASE, "1855-01-01"),        # noticia biográfica (edición de 1855)
    (11, 3182, UT, "1692-01-01"),      # To the Reader ... Of Love
    (3183, 5468, DM, "1692-01-01"),    # Preface to the Ten Commandments ... Lord's Supper
    (5469, 8612, PN, "1692-01-01"),    # Of Prayer ... Sixth Petition
    (8617, 9629, SS, None),            # Sermones I-VII (la fecha del VII se pone aparte)
    (9630, 10267, AC, "1653-01-01"),   # título de la obra + Fil. iv. 11, Chap. I ... Chap. XV
    (10268, 10**9, TR, None),          # cuatro tratados
]
# Cortes adicionales dentro de secciones largas: línea -> título original de la pieza que empieza ahí.
# El título de la primera parte de cada sección cortada va en TITULO_PARTE1.
CORTES = {
    5783: "Which Art in Heaven",
    6243: "Thy Kingdom Come: The Kingdom of Glory",
    6513: "Thy Kingdom Come: Exhortation to Seek the Kingdom of Heaven",
    6721: "Thy Kingdom Come: Perseverance until We Come to the Kingdom",
    7009: "Thy Will Be Done on Earth as It Is in Heaven: Patient Submission to God's Will",
    7585: "Forgive Us Our Debts: Labouring for the Forgiveness of Sin",
    7827: "As We Forgive Our Debtors",
    8231: "Lead Us Not into Temptation: Uses",
    8305: "But Deliver Us from Evil",
}
TITULO_PARTE1 = {
    5569: "Of the Preface to the Lord's Prayer: Our Father",
    5949: "Of the Second Petition: Thy Kingdom Come; the Kingdom of Grace",
    6847: "Of the Third Petition: Thy Will Be Done",
    7397: "Of the Fifth Petition: Forgive Us Our Debts",
    7909: "Of the Sixth Petition: Lead Us Not into Temptation",
}
FECHAS = {9315: "1662-01-01"}   # Farewell Discourse (Bartolomé, 1662)

LIBRO = r"(?:[1-3I] )?[A-Z][a-z]+\.?"
CAP = r"[ivxlcIVXLC]+\.?,?"
VERS = r"\d[\d, \-]*\.?,?"
REF = rf"{LIBRO} {CAP} ?{VERS}"
RE_REF_TEXTO = re.compile(rf"^({REF})\s+(\S.*)$", re.S)
RE_TEXTO_REF = re.compile(rf"^(\S.*?)[,;]?\s+({REF})$", re.S)

PEQ = {"a", "an", "the", "of", "in", "on", "to", "and", "but", "or", "for", "by", "his", "at", "with", "into", "as", "it", "is"}
def titulo_ingles(t):
    t = re.sub(r"^#+ ", "", t).strip().rstrip(".")
    if t.isupper():
        ps = t.lower().split()
        t = " ".join(p if (i and p in PEQ) else p[:1].upper() + p[1:] for i, p in enumerate(ps))
        t = re.sub(r"'S\b", "'s", t).replace("God's", "God's")
    return t

def parrafos(lineas):
    t = "\n".join(lineas)
    return [p.strip() for p in re.split(r"\n\s*\n", t) if p.strip()]

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

piezas = []
for z0, z1, destino, fecha in ZONAS:
    z1 = min(z1, N)
    inicios = [x for x in titulos2 if z0 <= x <= z1]
    if not inicios or inicios[0] != z0:
        inicios = [z0] + inicios
    inicios = sorted(set(inicios + [c for c in CORTES if z0 <= c <= z1]))
    for k, a in enumerate(inicios):
        b = inicios[k + 1] - 1 if k + 1 < len(inicios) else z1
        piezas.append(dict(ini=a, fin=b, destino=destino, fecha=FECHAS.get(a, fecha)))

# El arte del contentamiento: el título de la obra (es el nombre de la carpeta) se quita, y su texto
# bíblico (Fil. iv. 11) pasa al capítulo I, después del título del capítulo.
texto_obra = None
texto, plan = [], []
ids = {}
for pz in piezas:
    ps = notas_aparte(parrafos(L[pz["ini"] - 1:pz["fin"]]))
    if not ps:
        continue
    if pz["ini"] == 9630:
        texto_obra = ps[1:]
        continue
    if texto_obra and ps[0].startswith("## Chap. I."):
        ps[1:1] = texto_obra
        texto_obra = None
    es_titulo = ps[0].startswith("## ")
    versiculo = None
    if es_titulo and len(ps) > 1 and len(ps[1]) < 400:
        m = RE_REF_TEXTO.match(ps[1])
        if m:
            ps[1:2] = [m.group(1).rstrip(","), m.group(2)]
            versiculo = "auto"
        else:
            m = RE_TEXTO_REF.match(ps[1])
            if m:
                ps[1:2] = [m.group(2).rstrip(","), m.group(1)]
                versiculo = "auto"
    if pz["ini"] in CORTES:
        tit = CORTES[pz["ini"]]
    elif pz["ini"] in TITULO_PARTE1:
        tit = TITULO_PARTE1[pz["ini"]]
    else:
        tit = re.sub(r"^(SERMON|Chap\.) [IVX]+\. ", "", titulo_ingles(ps[0]))
    d = pz["destino"]
    if d == BASE:
        idp, tit = "0", "Biographical Notice of Thomas Watson"
    elif d == UT and pz["ini"] == 11:
        idp = "0"
    else:
        ids[d] = ids.get(d, 0) + 1
        idp = ROM[ids[d]]
    texto.append("@@SERMON@@\n\n" + "\n\n".join(ps))
    plan.append(dict(destino=d, fecha=pz["fecha"], id=idp, saltar=1 if es_titulo else 0, versiculo=versiculo,
                     titulo_original=tit, lineas=[pz["ini"], pz["fin"]], inicio=ps[0][:100]))

os.makedirs(SALIDA, exist_ok=True)
io.open(f"{SALIDA}/original-marcado.txt", "w", encoding="utf-8", newline="\n").write("\n\n".join(texto) + "\n")
io.open(f"{SALIDA}/plan.json", "w", encoding="utf-8", newline="\n").write(json.dumps(plan, ensure_ascii=False, indent=1) + "\n")
print(len(plan), "piezas;", sum(len(t) for t in texto), "caracteres")
for p, t in zip(plan, texto):
    print(f"{p['destino'].split('/')[-1][:14]:14} {p['id']:6} {len(t):7} {'V' if p['versiculo'] else ' '} {p['saltar']} {p['titulo_original'][:70]}")
