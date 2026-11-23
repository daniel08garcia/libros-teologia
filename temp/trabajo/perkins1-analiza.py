# Busca en las transcripciones de una edición antigua las palabras raras que se vuelven frecuentes al cambiar f por s
# (ſ leída como f) o al insertar m/n tras vocal (tilde sin desarrollar). Uso: python perkins1-analiza.py <trabajo>/texto
# Revisa la lista a mano y pasa las seguras a perkins1-corrige.py (Perkins vol. 1: 55 f/s y 81 m/n).
import re, glob, collections, sys
D = sys.argv[1]
textos = {f: open(f, encoding='utf-8').read() for f in sorted(glob.glob(D + '/p*.txt'))}
cnt = collections.Counter()
for t in textos.values():
    cnt.update(re.findall(r"[A-Za-z]+", t))
low = collections.Counter()
for w, c in cnt.items(): low[w.lower()] += c
# f -> s
fs = []
for w, c in cnt.items():
    if 'f' not in w.lower() or c > 3: continue
    for i, ch in enumerate(w):
        if ch in 'fF':
            v = w[:i] + ('s' if ch == 'f' else 'S') + w[i+1:]
            if low[v.lower()] >= 10 * max(1, low[w.lower()]) and low[v.lower()] >= 10:
                fs.append((w, c, v, low[v.lower()])); break
print("== f->s candidatos:", len(fs))
for x in sorted(fs, key=lambda x: -x[3])[:80]: print("  ", x)
# m/n insertion
mn = []
for w, c in cnt.items():
    if c > 3 or len(w) < 3: continue
    best = None
    for i in range(1, len(w)):
        if w[i-1].lower() in 'aeiou':
            for ins in 'mn':
                v = w[:i] + ins + w[i:]
                if low[v.lower()] >= 8 and low[v.lower()] >= 10 * max(1, low[w.lower()]):
                    if not best or low[v.lower()] > best[3]: best = (w, c, v, low[v.lower()])
    if best: mn.append(best)
print("== m/n candidatos:", len(mn))
for x in sorted(mn, key=lambda x: -x[3])[:80]: print("  ", x)
