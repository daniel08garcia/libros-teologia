# Títulos (## / ###) de The Works of William Perkins, vol. 2 (ver temp/ocr_agent.md, paso 7).
# Uso: python perkins2-titulos.py <trabajo> [--aplicar]   (sin --aplicar solo lista los cambios)
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


def reemplazar(p, viejo, nuevo, motivo):
    s = get(p)
    if nuevo in s and viejo not in s:
        return
    if viejo not in s:
        print('  OJO p%04d no encuentro: %r' % (p, viejo[:60]))
        return
    put(p, s.replace(viejo, nuevo, 1), motivo)


PAGINAS = range(8, 739)

# 0. Renglones "## " seguidos (sin línea en blanco) son un solo título partido en la imagen: se unen,
#    salvo que el segundo sea otro título (CHAP., Sect., Question, libro)
SIG = r'(?!CHAP|Sect|[IVX]+\.? Question|THE (?:SECOND|THIRD) BOOKE)'
RE_PEGADOS = re.compile(r'^## ([^\n]+)\n## ' + SIG, re.M)
for p in PAGINAS:
    s = get(p)
    o = s
    for _ in range(4):
        s = RE_PEGADOS.sub(lambda m: '## ' + m.group(1).rstrip() + ' ', s)
    s = re.sub(r'^(## [^\n]+)\n## ', r'\1\n\n## ', s, flags=re.M)   # los que quedan, separados
    if s != o:
        put(p, s, 'une renglones seguidos del título')

# 1. Portadillas: los renglones del título pasan a un solo "## " (el resto de la portadilla queda como texto)
PORTADAS = {
    8: (5, "THE WHOLE TREATISE OF The Cases of Conscience, Distinguished into three Bookes."),
    165: (6, "A COMMENTARIE OR EXPOSITION VPON THE FIVE FIRST CHAPTERS of the Epistle to the GALATIANS."),
    356: (8, "THE SVPPLEMENT, OR, CONTINVATION OF THE COMMENTARIE VPON THE SIXTH CHAPTER."),
    445: (5, "ΕΠΙΕΙΚΕΙΑ, OR A TREATISE OF CHRISTIAN EQVITY AND MODERATION."),
    465: (3, "A TREATISE OF Mans Imaginations."),
    496: (5, "WILLIAM PERKINS HIS PROBLEME OF The forged Catholicisme, or Vniversalitie of the Romish Religion."),
    616: (6, "A CHRISTIAN AND PLAINE TREATISE OF THE MANNER AND ORDER OF PREDESTINATION, AND OF the largenesse of Gods Grace."),
    655: (4, "THE ART OF PROPHECYING OR, A Treatise Concerning The Sacred And Onely True Manner And Methode Of Preaching."),
    686: (3, "DIGEST OR HARMONIE OF the bookes of the old and new Testament."),
}


def norm(s):
    return re.sub(r'[^a-z]', '', s.lower().replace('vv', 'w'))


for p, (n, tit) in PORTADAS.items():
    if get(p).startswith('## '):   # ya aplicado
        continue
    lineas = get(p).split('\n')
    idx = [i for i, l in enumerate(lineas) if l.strip()][:n]
    viejo = ' '.join(lineas[i] for i in idx)
    if norm(viejo) != norm(tit):
        print('  OJO p%04d no coincide: «%s» / «%s»' % (p, viejo, tit))
    resto = [l for i, l in enumerate(lineas) if i > idx[-1]]
    put(p, '## ' + tit + '\n\n' + '\n'.join(resto).lstrip('\n'), 'portadilla: ' + tit[:50])

# 2. Arreglos sueltos vistos en la lista de títulos
reemplazar(24, '## Of the first maine Question,\n\n## [ilegible]\n', '## Of the first maine Question touching man.\n',
           'subtítulo de CHAP. V (leído en la imagen)')
if not get(468).startswith('## Gen. 8'):
    put(468, '## Gen. 8. verse 21.\n\nAnd the Lord said in his heart, I will henceforth curse the earth no more for mans cause: '
             'for the Imagination of mans heart is evill even from his youth.\n\n' + get(468), 'texto del tratado (faltaba)')
s = get(467)   # índice de la obra: sus números de página no sirven
if '## The Contents of this Treatise.' in s:
    put(467, s[:s.index('## The Contents of this Treatise.')].rstrip('\n') + '\n', 'quita el índice de la obra')
# título partido entre dos páginas
reemplazar(499, '\n\n## 2. A Catalogue of the counterfeit, doubtfull,\n', '\n', 'título partido (sigue en p0500)')
reemplazar(500, '## or corrupted workes', '## 2. A Catalogue of the counterfeit, doubtfull, or corrupted workes', 'título partido')
# dedicatorias y títulos en varios renglones que terminan en coma o dos puntos
reemplazar(657, '## TO THE FAITHFVLL MINISTERS OF THE GOSPELL: AND TO ALL THAT ARE\n\ndesirous of',
           '## TO THE FAITHFVLL MINISTERS OF THE GOSPELL: AND TO ALL THAT ARE desirous of', 'título sigue en el párrafo')
reemplazar(617, '## To the Right Worshipfull\n\nSir Peter', '## To the Right Worshipfull Sir Peter', 'dedicatoria en un título')
# no son títulos: versículo del comentario, columnas de una tabla, rótulos de párrafo
reemplazar(328, '## 9. A little leaven', '9. A little leaven', 'versículo, no título')
reemplazar(520, '## The places and heads of the controversies', 'The places and heads of the controversies', 'introduce una lista')
for p in range(500, 519):   # rótulos dentro de cada Padre del catálogo
    put(p, re.sub(r'^## ((?:These workes|Suspected|Doubted|In (?:his|the) )[^\n]*)$', r'\1', get(p), flags=re.M),
        'rótulos del catálogo, no títulos')
for p in (522,):
    put(p, re.sub(r'^## (Vulgar Edit\.|The Vulgar Edition)$', r'\1', get(p), flags=re.M), 'rótulos de la tabla de la Vulgata')
for p in PAGINAS:
    s = get(p)
    o = s
    s = re.sub(r'^## (Testimonies\.)$', r'\1', s, flags=re.M)
    s = re.sub(r'^## (Answer\.(?: I\.)?)\n\n(?!#)', r'\1 ', s, flags=re.M)   # Predestinación: "Answer." al párrafo
    if s != o:
        put(p, s, 'rótulo de párrafo, no título')

# 3. Une un título con el siguiente: "CHAP. I." + subtítulo, "I. Question." + la pregunta, "Sect. 1." + subtítulo,
#    y títulos partidos en dos renglones (el primero sin puntuación final). No une las entradas del
#    catálogo de los Padres (pp. 500-518), que no llevan puntuación.
CORTO = (r'(?:CHAP\.?\s*[IVXL]+\.?|[IVX]+\.? Question[.:]?(?: touching Baptisme\.)?|Sect\.? ?[0-9I]+\.?'
         r'|[^\n]*[^.:;,!?\n])')
RE_UNIR = re.compile(r'^## (' + CORTO + r')\n\n## ' + SIG + r'([^\n]+)$', re.M)
RE_UNIR_ETIQ = re.compile(r'^## (CHAP\.?\s*[IVXL]+\.?|[IVX]+\.? Question[.:]?(?: touching Baptisme\.)?|Sect\.? ?[0-9I]+\.?)'
                          r'\n\n## ' + SIG + r'([^\n]+)$', re.M)
for p in PAGINAS:
    s = get(p)
    o = s
    r = RE_UNIR_ETIQ if 500 <= p <= 518 else RE_UNIR
    for _ in range(4):
        s = r.sub(lambda m: '## ' + m.group(1).rstrip() + ' ' + m.group(2), s)
    if s != o:
        put(p, s, 'une títulos')

# 4. Niveles: obras, partes, dedicatorias y capítulos ##; lo demás ###
ARRIBA = re.compile(
    r'^(CHAP|THE (SECOND|THIRD) BOOKE|TO |To the|THE EPISTLE OF|MASTER PERKINS|An admonition|The Proem|THE ORDER'
    r'|A Corolary|The Probleme|The explanation of the Probleme|Preparatives|I\. The authoritie|2\. A Catalogue'
    r'|III\. The causes|The Demonstration of the Probleme|Additions|The Consequent|Gen\. 8|The Argument)')
TITULOS_OBRA = {t for _, t in PORTADAS.values()}
for p in PAGINAS:
    s = get(p)
    o = s
    s = re.sub(r'^##+ ([^\n]+)$',
               lambda m: ('## ' if ARRIBA.match(m.group(1)) or m.group(1) in TITULOS_OBRA else '### ') + m.group(1),
               s, flags=re.M)
    if s != o:
        put(p, s, 'niveles')

print('\npáginas cambiadas:', len(cambios))
if APLICAR:
    bak = os.path.join(T, 'texto-bak-antes-titulos')
    if not os.path.exists(bak):
        shutil.copytree(D, bak)
    for p, s in cambios.items():
        open(os.path.join(D, 'p%04d.txt' % p), 'w', encoding='utf-8', newline='\n').write(s)
    print('aplicado; copia en', bak)
