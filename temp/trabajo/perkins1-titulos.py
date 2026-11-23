# Títulos (## / ###) de The Works of William Perkins, vol. 1 (ver temp/ocr_agent.md, paso 7).
# Uso: python perkins1-titulos.py <trabajo> [--aplicar]   (sin --aplicar solo lista los cambios)
import re, sys, os, shutil

T = sys.argv[1]
APLICAR = '--aplicar' in sys.argv
D = os.path.join(T, 'texto')
cambios = {}


def leer(p):
    f = os.path.join(D, 'p%04d.txt' % p)
    return open(f, encoding='utf-8').read() if os.path.exists(f) else ''


def get(p):
    return cambios.get(p) or leer(p)


def put(p, s, motivo):
    if s != get(p):
        cambios[p] = s
        print('p%04d %s' % (p, motivo))


# 1. Portadillas: los renglones del título pasan a un solo "## " (el resto de la portadilla queda como texto)
PORTADAS = {
    7: (4, "THE FOVNDATION OF CHRISTIAN RELIGION, GATHERED INTO SIXE PRINCIPLES."),
    18: (4, "A GOLDEN CHAINE: OR, THE DESCRIPTION OF THEOLOGIE."),
    133: (5, "AN EXPOSITION OF THE SYMBOLE, OR CREED OF THE APOSTLES."),
    339: (4, "AN EXPOSITION OF THE LORDS PRAYER."),
    370: (8, "A TREATISE TENDING VNTO A DECLARATION, WHETHER A MAN BE IN THE ESTATE OF DAMNATION, OR IN THE ESTATE OF GRACE: AND IF HE BE IN the first, how he may in time come out of it: if in the second, how he may discerne it, and persevere in the same to the end."),
    436: (4, "A CASE OF CONSCIENCE, THE GREATEST THAT EVER WAS: HOW A MAN MAY KNOW WHETHER HE be the childe of God, or no."),
    454: (5, "A DIRECTION FOR THE GOVERNEMENT OF THE TONGVE according to Gods word."),
    468: (4, "TWO TREATISES: 1. Of the nature and practise of Repentance. 2. Of the combate of the flesh and spirit."),
    490: (5, "HOW TO LIVE, AND THAT WELL: IN ALL ESTATES AND TIMES. Specially, When helpes and comforts faile."),
    502: (5, "A SALVE FOR A SICKE MAN: OR, A TREATISE CONTAINING THE NATVRE, DIFFERENCES, AND KINDS OF DEATH; AS ALSO THE RIGHT MANNER OF DYING WELL."),
    530: (7, "A DISCOVRSE OF CONSCIENCE. WHEREIN IS SET DOWNE THE nature, properties, and differences thereof: as also the way to get and keepe a good Conscience."),
    568: (8, "A REFORMED CATHOLIKE, OR, A DECLARATION SHEWING HOW NEERE WE MAY COME TO THE PRESENT CHVRCH OF ROME IN SVNDRY points of Religion: and wherein wee must for euer depart from them."),
    640: (5, "A DECLARATION OF THE TRVE MANNER OF KNOWING CHRIST CRVCIFIED."),
    650: (7, "A GRAINE OF MVSTERD-SEEDE: OR, THE LEAST MEASVRE OF GRACE THAT IS OR CAN BE effectuall to saluation."),
    660: (5, "THE TRVE GAINE: MORE IN WORTH THEN ALL THE GOODS IN THE WORLD."),
    684: (9, "A WARNING AGAINST THE IDOLATRY OF THE LAST TIMES, AND AN INSTRVCTION TOVCHING RELIGIOVS OR DIVINE WORSHIP."),
    732: (5, "A TREATISE OF GODS FREE-GRACE, AND MANS FREE-WILL."),
    762: (6, "A TREATISE OF the Vocations, OR Callings of men, with the sorts and kinds of them, and the right vse thereof."),
}


def norm(s):
    return re.sub(r'[^a-z]', '', s.lower().replace('vv', 'w'))


for p, (n, tit) in PORTADAS.items():
    if get(p).startswith('## '):   # ya aplicado
        continue
    lineas = get(p).split('\n')
    idx = [i for i, l in enumerate(lineas) if l.strip()][:n]
    viejo = ' '.join(lineas[i] for i in idx)
    v, t = norm(viejo), norm(tit)
    if not (v == t or norm('A ' + viejo) == t or v == 'a' + t or v.replace('aa', 'a', 1) == t):
        print('  OJO p%04d no coincide: «%s» / «%s»' % (p, viejo, tit))
    resto = [l for i, l in enumerate(lineas) if i > idx[-1]]
    put(p, '## ' + tit + '\n\n' + '\n'.join(resto).lstrip('\n'), 'portadilla: ' + tit[:50])

# 2. Arreglos sueltos
put(429, re.sub(r'\n+## A DECLA-\s*$', '\n', get(429)), 'quita el título partido "A DECLA-" (está entero en p0430)')
put(438, get(438).replace('## Chvrch.', 'Chvrch.'), '"Chvrch." no es título')
if not get(662).startswith('## PHIL'):
    put(662, '## PHIL. 3. verse 7.\n\n' + get(662), 'texto del sermón como título')
s = get(371)
if '## TO THE RIGHT WORSHIPFVLL' in s:
    put(371, s[s.index('## TO THE RIGHT WORSHIPFVLL'):], 'quita el índice de la obra (sus números de página no sirven)')

# 3. Secciones del Credo, tomadas del índice del libro: (página, nº de párrafo, título)
CREDO = [(138, 7, 'Faith.'), (144, 3, 'God.'), (146, 2, 'The three persons.'), (148, 2, 'The Father.'),
         (152, 2, 'Gods omnipotencie.'), (155, 3, 'The creation.'), (161, 5, 'The creation of heauen.'),
         (163, 2, 'The creation of Angels.'), (166, 4, 'The creation of Man.'), (170, 3, 'Gods prouidence.'),
         (175, 7, 'Adams fall, and originall sinne.'), (180, 1, 'The couenant of grace.'), (181, 6, 'The title, Iesus.'),
         (184, 3, 'The title, Christ.'), (187, 3, 'The title, Sonne.'), (191, 1, 'The title, Lord.'),
         (192, 2, 'The incarnation of Christ.'), (201, 3, 'Christs humiliation.'), (221, 2, 'Christs execution.'),
         (233, 3, 'Christs sacrifice.'), (237, 1, 'Christs triumph.'), (244, 1, 'Christs buriall.'),
         (247, 3, 'The descension of Christ.'), (250, 1, 'Christs exaltation.'), (251, 2, 'Christs resurrection.'),
         (261, 2, 'Christs ascension.'), (267, 3, 'Christs sitting at the right hand of God.'),
         (269, 1, 'Christs intercession.'), (275, 2, 'The last iudgement.'), (284, 4, 'The holy Ghost.'),
         (293, 2, 'The Church.'), (294, 1, 'Predestination.'), (314, 2, 'The mysticall vnion.'),
         (324, 5, 'The communion of Saints.'), (328, 3, 'The forgiuenesse of sinnes.'),
         (330, 2, 'The resurrection of the bodie.'), (334, 2, 'Life euerlasting.')]
for p, k, tit in CREDO:
    s = get(p)
    if '## ' + tit in s:
        continue
    cuerpo, sep, notas = s.partition('---NOTAS---')
    pars = cuerpo.rstrip('\n').split('\n\n')
    if pars[k].startswith('[[sigue]]') or pars[k].startswith('#'):
        print('  OJO p%04d párrafo %d no sirve para el título %s' % (p, k, tit))
        continue
    pars.insert(k, '## ' + tit)
    put(p, '\n\n'.join(pars) + '\n' + (sep + notas if sep else ''), 'Credo: ' + tit)

# 4. Une un título con el siguiente: "CHAP. I." + subtítulo, "I. COM." + mandamiento,
#    referencia bíblica corta + texto, y títulos partidos en dos renglones (el primero sin puntuación final)
CORTO = r'(?:CHAP\.?\s*[IVXL]+\.?|[IVXL]+\.? COM\.|[^\n]{0,30}\d+[.,]?(?:\s*verse\s*[\d, ]+\.?)?|[^\n]*[^.:;,!?\n])'
RE_UNIR = re.compile(r'^## (' + CORTO + r')\n\n## (?!CHAP)([^\n]+)$', re.M)
for p in range(2, 795):
    s = get(p)
    o = s
    for _ in range(3):
        s = RE_UNIR.sub(lambda m: '## ' + m.group(1).rstrip() + ' ' + m.group(2), s)
    if s != o:
        put(p, s, 'une títulos')

# 5. Números romanos sueltos como título (proposiciones numeradas): pasan al comienzo del párrafo siguiente
for p in list(range(373, 396)) + [423, 424, 659]:
    s = get(p)
    o = s
    s = re.sub(r'^## ([IVXL]+\.?)\n\n(?!#)', lambda m: m.group(1) + (' ' if m.group(1).endswith('.') else '. '), s, flags=re.M)
    if s != o:
        put(p, s, 'numeral romano al párrafo')


# 6. Niveles: subdivisiones a ###
def bajar(p, pred, motivo):
    s = get(p)
    o = s
    s = re.sub(r'^## ([^\n]+)$', lambda m: ('### ' if pred(m.group(1)) else '## ') + m.group(1), s, flags=re.M)
    if s != o:
        put(p, s, motivo)


for p in range(23, 130):   # A Golden Chaine: capítulos ##, lo demás ###
    bajar(p, lambda t: not t.startswith('CHAP'), 'Golden Chaine ###')
PET = re.compile(r'^(Our Father|Father\.|Which art|Hallowed be|Thy Kingdome|Thy will|In earth|Giue vs|Forgiue vs|'
                 r'As we forgiue|Leade vs|For thine|Amen\.|Of the vse|Of the circumstances|Of Gods hearing)')
for p in range(346, 364):  # Padrenuestro: peticiones ##, sus partes ###
    bajar(p, lambda t: not PET.match(t), 'Padrenuestro ###')
for p in range(413, 420):
    bajar(p, lambda t: re.match(r'The (first|second|third|fourth) [Aa]rgument|The [Pp]roofe', t), 'argumentos ###')
for p in (444, 450):
    bajar(p, lambda t: t.startswith('Assertion'), 'aserciones ###')
for p in range(474, 478):
    bajar(p, lambda t: 'COM.' in t or t.startswith('Sinnes directly'), 'mandamientos ###')
for p in range(481, 484):
    bajar(p, lambda t: re.match(r'[IV]+\. Case', t), 'casos ###')
for p in range(573, 630):  # A Reformed Catholike: puntos ##, sus partes ###
    bajar(p, lambda t: not re.search(r'point', t), 'Reformed Catholike ###')
for p in range(652, 658):
    bajar(p, lambda t: t.startswith('The Exposition'), 'Graine ###')
for p in range(365, 368):
    bajar(p, lambda t: t.lower().startswith('the exposition'), 'exposiciones ###')

# 7. Casos vistos al revisar la lista: capítulos cuyo subtítulo quedó sin "## ", un título en tres renglones,
#    y las subdivisiones numeradas de The Foundation
for p in (36, 37, 38):
    put(p, re.sub(r'^## (CHAP\. [XVIL]+\.)\n\n(?!#)([^\n]+)$', r'## \1 \2', get(p), flags=re.M), 'une CHAP con su subtítulo')
put(398, get(398).replace('## A DIALOGVE OF THE STATE OF\n## A CHRISTIAN MAN, GATHERED HERE\n',
                          '## A DIALOGVE OF THE STATE OF A CHRISTIAN MAN, GATHERED HERE '), 'título en tres renglones')
for p in (10, 11):
    bajar(p, lambda t: re.match(r'\d\. |Proofes out', t), 'Foundation ###')

print('\npáginas cambiadas:', len(cambios))
if APLICAR:
    bak = os.path.join(T, 'texto-bak-antes-titulos')
    if not os.path.exists(bak):
        shutil.copytree(D, bak)
    for p, s in cambios.items():
        open(os.path.join(D, 'p%04d.txt' % p), 'w', encoding='utf-8', newline='\n').write(s)
    print('aplicado; copia en', bak)
