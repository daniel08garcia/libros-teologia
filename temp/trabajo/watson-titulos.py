# Títulos de Select Works of Thomas Watson (ocr-watson). Sin --aplicar solo lista los cambios.
import re, sys, glob, os
T = 'temp/trabajo/ocr-watson/texto/'
aplicar = '--aplicar' in sys.argv
cambios = []

def leer(n): return open(T + 'p%04d.txt' % n, encoding='utf-8').read()
def escribir(n, s):
    if aplicar: open(T + 'p%04d.txt' % n, 'w', encoding='utf-8').write(s)

def reemplazar(n, viejo, nuevo):
    s = leer(n)
    assert s.count(viejo) == 1, (n, viejo, s.count(viejo))
    cambios.append('p%04d: %r -> %r' % (n, viejo[:70], nuevo[:70]))
    escribir(n, s.replace(viejo, nuevo))

# 1. Portadas partidas en tres renglones
reemplazar(11, '## BIOGRAPHICAL NOTICE\n\nOf\n\n## THOMAS WATSON.', '## BIOGRAPHICAL NOTICE OF THOMAS WATSON.')
reemplazar(15, '## A BODY\n\nOf\n\n## PRACTICAL DIVINITY.', '## A BODY OF PRACTICAL DIVINITY.')

# 2. Sermones: el número impreso más el título del índice (p. 10)
sermones = {623: ('I', 'On Christian Prudence and Innocency.'), 635: ('II', 'On becoming a New Creature.'),
            644: ('III', 'On the Evil Tongue.'), 651: ('IV', 'Not being Weary in Well-doing.'),
            654: ('V', 'On knowing good and doing it.'), 660: ('VI', 'Christ is all in all.'),
            670: ('VII', 'Farewell Discourse on his ejection.')}
for n, (num, tit) in sermones.items():
    reemplazar(n, '## SERMON %s.' % num, '## SERMON %s. %s' % (num, tit))

# 3. "Sect." del tratado de contentamiento: todos como ###
for f in sorted(glob.glob(T + 'p07[0-3]*.txt')):
    n = int(os.path.basename(f)[1:5]); s = leer(n); s2 = s
    s2 = re.sub(r'(?m)^(?:## )?(Sect\.? [IVX0-9]+\.)', r'### \1', s2)
    if s2 != s:
        for a, b in zip(s.splitlines(), s2.splitlines()):
            if a != b: cambios.append('p%04d: %r -> %r' % (n, a[:60], b[:60]))
        escribir(n, s2)

# 4. Bajar a ### los ## que no son obra, tema ni capítulo
vistos = set()
for f in sorted(glob.glob(T + 'p*.txt')):
    n = int(os.path.basename(f)[1:5]); s = leer(n) if not aplicar else open(f, encoding='utf-8').read()
    lineas = s.split('\n'); cambio = False
    for i, l in enumerate(lineas):
        if not l.startswith('## '): continue
        t = l[3:]
        bajar = False
        if re.match(r'(?i)(Exod|Mark|Luke|Mat|James)\.? ', t): bajar = True          # texto bíblico de cada lección
        elif re.match(r'(Use |Rule |Fourthly|6th Subtilty|2d Branch|1\. Of my discharge|Rules for the well)', t): bajar = True
        elif t.isupper() and t in vistos and n > 200 and n != 364: bajar = True   # p. 364: «Of Faith» es otro tema (índice, p. 350)                     # tema repetido: nueva lección
        if t.isupper(): vistos.add(t)
        if bajar:
            lineas[i] = '### ' + t; cambio = True
            cambios.append('p%04d: ## -> ### %s' % (n, t[:70]))
    if cambio: escribir(n, '\n'.join(lineas))

# 5. «&c.» leído como «§c.»
for n in (239, 241):
    reemplazar(n, '§c.', '&c.')

# 6. Párrafo entero marcado como título por error
reemplazar(511, '## 3d. Consideration,', '3d. Consideration,')

print('\n'.join(cambios)); print(len(cambios), 'cambios', '(aplicados)' if aplicar else '(sin aplicar; usa --aplicar)')
