# Títulos (## / ###) de The Works of William Perkins, vol. 3 (ver temp/ocr_agent.md, paso 7). Modelo: perkins2-titulos.py.
# Uso: python perkins3-titulos.py <trabajo> [--aplicar]   (sin --aplicar solo lista los cambios)
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


PAGINAS = [p for p in range(3, 1025) if os.path.exists(os.path.join(D, 'p%04d.txt' % p))]

# 0. Renglones "## " seguidos (sin línea en blanco) son un solo título partido: se unen, salvo que el segundo sea otro título
SIG = r'(?!CHAP|Sect|[IVX]+\.? Question|Verse|VERSE|Vers|[Vv]\. ?\d)'
RE_PEGADOS = re.compile(r'^## ([^\n]+)\n## ' + SIG, re.M)
for p in PAGINAS:
    s = get(p)
    o = s
    for _ in range(12):
        s = RE_PEGADOS.sub(lambda m: '## ' + m.group(1).rstrip() + ' ', s)
    s = re.sub(r'^(## [^\n]+)\n## ', r'\1\n\n## ', s, flags=re.M)
    if s != o:
        put(p, s, 'une renglones seguidos del título')

# 1. Portadillas: los renglones del título pasan a un solo "## " (el resto queda como texto)
PORTADAS = {
    3: (4, "A Godly and Learned EXPOSITION VPON Christs Sermon in the Mount."),
    282: (6, "TO THE NOBLE AND VERTVOVS GENTLEMEN, Sir Iohn Sheaffield, Knight: AND Mr. Oliver St. Iohn:"),
    284: (5, "A COMMENTARIE UPON THE ELEVENTH CHAPTER OF THE EPISTLE to the Hebrewes."),
    490: (7, "A godly and learned EXPOSITION OR COMMENTARIE VPON THE THREE FIRST CHAPTERS OF the Revelation."),
    665: (7, "THE COMBAT BETWEENE Christ and the Devill displayed: OR, A COMMENTARIE UPON The Temptations of Christ."),
    713: (6, "A faithfull and plaine EXPOSITION VPON THE TWO FIRST VERSES OF The second Chapter of Zephaniah."),
    734: (7, "OF THE CALLING OF THE MINISTERIE. Two Treatises: DESCRIBING THE DVTIES and Dignities of that calling."),
    749: (8, "THE SECOND TREATISE OF THE DVTIES AND DIGNITIES OF The Ministerie."),
    773: (4, "A Fruitfull DIALOGVE CONCERNING The end of the World."),
    789: (4, "A Godly and Learned EXPOSITION UPON The whole Epistle of Iude."),
    923: (6, "A DISCOURSE OF THE DAMNED ART OF Witchcraft."),
    977: (4, "A RESOLVTION TO The Countrey-man."),
    994: (3, "OECONOMIE: Or, Houshold-Government."),
}


def norm(s):
    return re.sub(r'[^a-z]', '', s.lower().replace('vv', 'w'))


for p, (n, tit) in PORTADAS.items():
    if get(p).startswith('## '):
        continue
    lineas = get(p).split('\n')
    idx = [i for i, l in enumerate(lineas) if l.strip()][:n]
    viejo = ' '.join(lineas[i] for i in idx)
    if norm(viejo) != norm(tit):
        print('  OJO p%04d no coincide: «%s» / «%s»' % (p, viejo, tit))
        continue
    resto = [l for i, l in enumerate(lineas) if i > idx[-1]]
    put(p, '## ' + tit + '\n\n' + '\n'.join(resto).lstrip('\n'), 'portadilla: ' + tit[:50])

# 2. Arreglos sueltos
reemplazar(554, '\n\n## CHAP. 2.\n', '\n', 'reclamo «CHAP. 2.» (el título está en p0555)')
put(738, re.sub(r'(## A TREATISE OF THE DVTIES AND DIGNITIES)\n+(of the Ministerie\.)', r'\1 \2', get(738)), 'título sigue en el renglón')

# 3. Título partido entre dos páginas: la página empieza con "## x" y la anterior termina en un título sin puntuación final
for p in PAGINAS:
    s = get(p)
    m = re.match(r'## ([^\n]+)\n', s)
    if not m or not os.path.exists(os.path.join(D, 'p%04d.txt' % (p - 1))):
        continue
    prev = get(p - 1)
    cuerpo, sep, notas = prev.partition('---NOTAS---')
    ult = cuerpo.rstrip('\n').split('\n')[-1]
    if ult.startswith('## ') and not re.search(r'[.:;?!)\]]$', ult.strip()) and not m.group(1).startswith(('CHAP', 'Sect', 'Verse', 'VERSE')):
        put(p - 1, cuerpo.rstrip('\n') + ' ' + m.group(1) + '\n' + (sep + notas if sep else ''), 'título partido (sigue en la página siguiente)')
        put(p, s[m.end():].lstrip('\n'), 'título partido (movido a la página anterior)')

# 4. Lemas del comentario («Through faith]», «Prepared the Arke,]») y rótulos de párrafo: no son títulos
for p in PAGINAS:
    s = get(p)
    o = s
    s = re.sub(r'^## (\[?[^\n]*\])$', r'\1', s, flags=re.M)
    if s != o:
        put(p, s, 'lema, no título')

# 5. Une un título con el siguiente: «CHAP. I.» + subtítulo, «Sect. 1.» + subtítulo, «VERSE 2.» + texto del versículo,
#    «Abels Faith.» + «Verse 2.», referencia corta + texto, títulos partidos (el primero sin puntuación final)
SIG2 = r'(?!CHAP|Sect\b|Sect\.|[Vv](?:ers)?\.? ?\d|Verse|VERSE)'
CORTO = (r'(?:CHAP\.?\s*[IVXL0-9]+\.?|Sect\.? ?[0-9IVX]+\.?|VERSE ?[0-9IVX]+\.?|Verse ?[0-9IVX]+\.?|Vers\. ?\d+\.?'
         r'|[^\n]{0,40}Faith\.|Beleevers under the Macchabees\.|[A-Z]+\.? ?[0-9IVX]+\. ?[0-9IVX]+\.'
         r'|[^\n]*[^.:;!?\]\n])')   # un título que termina en coma sigue en el siguiente («Of the Master of the Family,»)
RE_UNIR = re.compile(r'^## (' + CORTO + r')\n\n## ' + SIG2 + r'([^\n]+)$', re.M)
for p in PAGINAS:
    s = get(p)
    o = s
    for _ in range(4):
        s = RE_UNIR.sub(lambda m: '## ' + m.group(1).rstrip() + ' ' + m.group(2), s)
    if s != o:
        put(p, s, 'une títulos')

# 6. Niveles: obras, dedicatorias, partes y capítulos ##; versículos, secciones y lo demás ###
ARRIBA = re.compile(
    r'^(CHAP|TO |To the|AN ADVERTISEMENT|A GENERALL|A briefe view|THE COMBAT BETWEENE CHRIST|A COMMENTARIE VPON PART'
    r'|THE PVBLISHERS|A DISCOURSE OF WITCHCRAFT|A TREATISE OF THE DVTIES|THE SECOND TREATISE OF THE DVTIES'
    r'|A Fruitfull DIALOGVE Betweene|A Conclusion|A short SURVEY|A RESOLVTION TO THE COVNTREY)')
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
