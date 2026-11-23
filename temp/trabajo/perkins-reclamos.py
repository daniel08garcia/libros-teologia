# Quita los reclamos copiados al final de página (la palabra suelta del pie que anuncia la página siguiente) y las
# palabras cortadas con guion que el agente completó en las dos páginas («expound ‖ pound them»).
# Usa la misma regla que el control «palabra repetida en el corte» de ocr.py validar.
# Uso: python perkins-reclamos.py <trabajo> [--aplicar] [--excepto 32,426] (o en <trabajo>/reclamos-excepto.txt)   (sin --aplicar solo lista)
import re, sys, os, glob, shutil

T = sys.argv[1]
APLICAR = '--aplicar' in sys.argv
EXCEPTO = set()
if '--excepto' in sys.argv:
    EXCEPTO = set(int(x) for x in sys.argv[sys.argv.index('--excepto') + 1].split(','))
D = os.path.join(T, 'texto')
# excepciones guardadas en la carpeta de trabajo (repeticiones legítimas ya revisadas), para no olvidarlas
if os.path.exists(os.path.join(T, 'reclamos-excepto.txt')):
    EXCEPTO |= set(int(x) for x in re.findall(r'\d+', open(os.path.join(T, 'reclamos-excepto.txt')).read()))
SEP = '---NOTAS---'


def leer(f):
    return open(f, encoding='utf-8').read()


cambios = {}
for f in sorted(glob.glob(D + '/p*.txt')):
    n = int(f[-8:-4])
    previa = os.path.join(D, 'p%04d.txt' % (n - 1))
    if n in EXCEPTO or not os.path.exists(previa):
        continue
    cuerpo = leer(f).split(SEP)[0]
    tp = cambios.get(n - 1) or leer(previa)
    cp, sep, notas = tp.partition(SEP)
    cp = cp.rstrip()
    # la anterior termina cortada («doubt-») y esta repite la palabra entera («doubtlesse»): se quita «doubt» de aquí
    if cp.endswith('-') and '[[capa]]' not in cuerpo and not cuerpo.lstrip().startswith('#'):
        fin = re.findall(r'[A-Za-z]+', cp[-40:])
        ta = cambios.get(n) or leer(f)
        m = re.match(r'^(\s*(?:\[\[sigue\]\]\n)?)([A-Za-z]+)', ta)
        if fin and m and len(fin[-1]) >= 2 and len(m.group(2)) > len(fin[-1]) and m.group(2).lower().startswith(fin[-1].lower()):
            cambios[n] = ta[:m.start(2)] + ta[m.start(2) + len(fin[-1]):]
            print('p%04d «%s-» ‖ «%s» -> «%s»' % (n, fin[-1], m.group(2), m.group(2)[len(fin[-1]):]))
        continue
    if '[[capa]]' in cp or '[[capa]]' in cuerpo or cp.endswith('-') or cuerpo.lstrip().startswith('#'):
        continue
    fin = re.findall(r'[A-Za-z]+', cp[-60:])
    ini = re.findall(r'[A-Za-z]+', re.sub(r'^\s*\[\[sigue\]\]', '', cuerpo)[:60])
    if not (fin and ini):
        continue
    a, b = fin[-1].lower(), ini[0].lower()
    igual = a == b or (len(a) >= 4 and len(b) > len(a) and b.startswith(a))
    partida = len(b) >= 4 and len(a) > len(b) and a.endswith(b)
    if not (igual or partida):
        continue
    m = re.search(r'(\s*)(\S+)$', cp)
    tok = m.group(2)
    mt = re.match(r'^([^A-Za-z]*)([A-Za-z]+)([^\[]*)((?:\[\d+\])?)$', tok)
    if not mt or mt.group(2).lower() != a:
        print('  OJO p%04d: no entiendo el final «%s»' % (n - 1, tok))
        continue
    llamada = mt.group(4)
    base = cp[:m.start()]
    if igual:   # reclamo: se quita la palabra (la llamada de nota, si la hay, pasa a la palabra anterior)
        nuevo = base + llamada
    else:       # palabra partida completada: se deja la primera parte con guion, como en el impreso
        if llamada:
            print('  OJO p%04d: palabra partida con llamada «%s»' % (n - 1, tok))
            continue
        nuevo = base + ' ' + mt.group(1) + mt.group(2)[:len(mt.group(2)) - len(b)] + '-'
    cambios[n - 1] = nuevo.rstrip() + '\n' + (sep + notas if sep else '')
    print('p%04d «%s» ‖ «%s» -> «%s»' % (n - 1, cp[-35:].replace('\n', ' '), cuerpo.replace('[[sigue]]\n', '')[:25].replace('\n', ' '),
                                        nuevo[-30:].replace('\n', ' ')))

print('\npáginas cambiadas:', len(cambios))
if APLICAR:
    bak = os.path.join(T, 'texto-bak-antes-reclamos')
    if not os.path.exists(bak):
        shutil.copytree(D, bak)
    for p, s in cambios.items():
        open(os.path.join(D, 'p%04d.txt' % p), 'w', encoding='utf-8', newline='\n').write(s)
    print('aplicado; copia en', bak)
