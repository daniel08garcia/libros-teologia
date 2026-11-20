# Títulos ## / ### del volumen 2 de Brooks (ver temp/ocr_agent.md, paso 7: Títulos).
# Funciones copiadas de brooks-titulos.py; la lista de abajo es propia de este volumen.
# Uso: python temp/trabajo/brooks2-titulos.py [--aplicar]   (haz antes una copia de texto/)
import io,re,sys
T='c:/www/libros-teologia/temp/trabajo/ocr-brooks-v2/texto/'
APLICAR='--aplicar' in sys.argv
PAGS={}
def pag(n):
    if n not in PAGS:
        t=io.open(T+'p%04d.txt'%n,encoding='utf-8').read()
        sigue=t.startswith('[[sigue]]')
        if sigue: t=t[len('[[sigue]]'):].lstrip('\n')
        notas=None
        if '---NOTAS---' in t: t,notas=t.split('---NOTAS---',1)
        PAGS[n]={'sigue':sigue,'pars':[p.strip() for p in re.split(r'\n\s*\n',t.strip()) if p.strip()],'notas':notas}
    return PAGS[n]
def guardar():
    for n,d in PAGS.items():
        s=('[[sigue]]\n' if d['sigue'] else '')+'\n\n'.join(d['pars'])+'\n'
        if d['notas'] is not None: s+='---NOTAS---'+d['notas']
        io.open(T+'p%04d.txt'%n,'w',encoding='utf-8',newline='\n').write(s)
def buscar(n,rx):
    d=pag(n)
    hs=[i for i,p in enumerate(d['pars']) if re.search(rx,p)]
    assert len(hs)==1,(n,rx,hs)
    return hs[0]
def frase(s, limite=160):
    """Primera oración (el enunciado en cursiva del autor): termina en . ? ! seguido de espacio y mayúscula
    o comilla, o fin. Se saltan abreviaturas (Tim., xii., viz., &c.) y exclamaciones cortas (Sir !, Oh!)."""
    for m in re.finditer(r"[.?!](['’\"]?)(?=\s+['‘\"(]?[A-Z]|\s*$)", s):
        f = s[:m.end()].strip()
        prev = re.search(r"(\S+)[.?!]['’\"]?$", f)
        tok = prev.group(1) if prev else ""
        if len(f) < 30: continue
        if m.group(0)[0] == "." and (re.fullmatch(r"[ivxlcdmIVXLCDM]+|\d+|[A-Z][a-z]{0,4}|&c|viz|i\.e|e\.g|ch|cf|ver", tok) or tok.endswith(",")):
            continue
        if len(f) > limite or re.search(r"\[\d+\]", f): return None, s
        return f, s[m.end():].strip()
    return None, s
ORDEN=[]
def poner(n,rx,nivel,etiqueta,titulo=None,intro=False,quitar=None):
    """Busca en la página n el párrafo que casa con rx; quita la etiqueta (regex quitar) del párrafo;
    el título es etiqueta + frase inicial (o 'titulo' si se da o si la frase no sirve).
    intro=True: el título va antes del párrafo anterior ("... is,"), que puede estar en la página previa."""
    d=pag(n); i=buscar(n,rx); p=d['pars'][i]
    q=re.search(quitar or re.escape(etiqueta),p); assert q,(n,etiqueta,p[:80])
    antes,resto=p[:q.start()].strip(),p[q.end():].strip()
    f=None
    if titulo is None and not antes:
        f,r=frase(resto)
    if f: cab='%s %s %s'%(nivel,etiqueta,f); nuevo=r
    else: cab=('%s %s %s'%(nivel,etiqueta,titulo or '')).strip(); nuevo=(antes+' '+resto).strip() if antes else resto
    dest_n,dest_i=n,i
    if intro and not antes:
        if i>0: dest_i=i-1
        else:
            dest_n=n-1; dest_i=len(pag(n-1)['pars'])-1
        assert re.search(r"is,?\s*$|is,$",pag(dest_n)['pars'][dest_i]) or True
    ORDEN.append((n,cab,(pag(dest_n)['pars'][dest_i] if intro and not antes else '')[-60:]))
    if APLICAR:
        if nuevo: d['pars'][i]=nuevo
        else: del d['pars'][i]
        pag(dest_n)['pars'].insert(dest_i,cab)
def nivel3(n,rx):
    """convierte un título ## existente en ###"""
    d=pag(n); i=buscar(n,rx); assert d['pars'][i].startswith('## ')
    ORDEN.append((n,'#'+d['pars'][i],''))
    if APLICAR: d['pars'][i]='#'+d['pars'][i]

# ---- reinicio de la lista PR con fallback del índice ----
ORDEN.clear(); PAGS.clear()
IDX=[l.strip() for l in io.open('c:/www/libros-teologia/temp/trabajo/ocr-brooks-v2/indice.txt',encoding='utf-8').read().split('\n') if l.strip()]
def idx_dev():
    out=[]
    for l in IDX:
        m=re.search(r"device[^,]*?(?:,[^,]*?)*? is, (.+?)\. (One|Two|Three|Four|Five|Six|Seven|Eight|Nine|Ten)\b",l)
        if m and 'remed' in l: out.append(m.group(1)[0].upper()+m.group(1)[1:]+'.')
    return out
DEVT=idx_dev()
def dev(n,k,parte_i):
    poner(n,r"Device \(?%d\.?\)?\.?"%k,'###','Device (%d).'%k,intro=True,
          quitar=r"Device \(?%d\.?\)?\.?\s*"%k,titulo_si_falla=(DEVT[parte_i] if parte_i < len(DEVT) else None))
# redefinir poner con fallback
_poner=poner
def poner(n,rx,nivel,etiqueta,titulo=None,intro=False,quitar=None,titulo_si_falla=None):
    d=pag(n); i=buscar(n,rx); p=d['pars'][i]
    q=re.search(quitar or re.escape(etiqueta),p); assert q,(n,etiqueta,p[:80])
    antes,resto=p[:q.start()].strip(),p[q.end():].strip()
    f=None
    if titulo is None:
        f,r=frase(resto)
    if f: cab='%s %s %s'%(nivel,etiqueta,f); nuevo=(antes+' '+(resto if intro else r)).strip()
    else:
        cab=('%s %s %s'%(nivel,etiqueta,titulo or titulo_si_falla or '')).strip(); nuevo=(antes+' '+resto).strip()
    dest_n,dest_i=n,i
    if intro and not antes:
        if i>0: dest_i=i-1
        else: dest_n=n-1; dest_i=len(pag(n-1)['pars'])-1
    ORDEN.append((n,cab))
    if APLICAR:
        if nuevo: d['pars'][i]=nuevo
        else: del d['pars'][i]
        pag(dest_n)['pars'].insert(dest_i,cab)
def entero(n,rx,nivel,prefijo_quitar=None):
    """todo el párrafo (corto) pasa a ser título"""
    d=pag(n); i=buscar(n,rx); p=re.sub(r"^#+ ","",d['pars'][i])
    assert len(p)<260,(n,p[:80])
    ORDEN.append((n,nivel+' '+p))
    if APLICAR: d['pars'][i]=nivel+' '+p
def juntar(n,rx,nivel):
    """el párrafo y el siguiente forman el título"""
    d=pag(n); i=buscar(n,rx)
    t=re.sub(r"^#+ ","",d['pars'][i])+' '+re.sub(r"^#+ ","",d['pars'][i+1])
    ORDEN.append((n,nivel+' '+t))
    if APLICAR: d['pars'][i:i+2]=[nivel+' '+t]
def serie(desde,hasta,rxlab,nivel,etq,titulos=None):
    """todas las etiquetas (Reason 3., Obj. 2., ...) que empiezan párrafo entre las páginas dadas"""
    vistos=[]
    for n in range(desde,hasta+1):
        for p in list(pag(n)['pars']):
            m=re.match(r"^(#+ )?"+rxlab,p)
            if not m: continue
            num=m.group('num'); vistos.append(int(num))
            if m.group(1):  # ya era título
                d=pag(n); i=d['pars'].index(p)
                ORDEN.append((n,nivel+' '+p[len(m.group(1)):]))
                if APLICAR: d['pars'][i]=nivel+' '+p[len(m.group(1)):]
                continue
            et=m.group(0)[len(m.group(1) or ''):].strip()
            tt=(titulos or {}).get(int(num))
            poner(n,'^'+re.escape(p[:40]),nivel,et,quitar=r"^"+rxlab+r"\s*",titulo_si_falla=tt)
    return vistos


# ---------------- AN ARK FOR ALL GOD'S NOAHS ----------------
entero(7,r"^AN ARK FOR ALL GOD'S NOAHS",'##')
poner(18,r"^I\. For the first, What a portion",'##','I.',quitar=r"^I\.\s*")
ATR=['Present.','Immense.','All-sufficient.','Absolute, needful, and necessary.','Pure and universal.','Glorious, happy, and blessed.','Peculiar.','Universal.','Safe and secure.','Suitable.','Incomprehensible.','Inexhaustible.','Soul-satisfying.','Permanent, indefinite, never-failing, everlasting.','Incomparable.']
for k,n in enumerate([18,19,21,23,24,27,28,29,32,33,34,36,38,41,43]):
    poner(n,r"^\(%d\.\) "%(k+1),'###','(%d.)'%(k+1),titulo=ATR[k],quitar=r"^\(%d\.\)\s*"%(k+1))
poner(45,r"^II\. Upon what grounds",'##','II.',quitar=r"^II\.\s*",titulo_si_falla='Grounds of title unto God as a portion.')
GR=['Free favour and love of God.','Covenant of grace.','Marriage-union.']
for k,n in enumerate([45,46,46]):
    poner(n,r"^\(%d\.\) "%(k+1),'###','(%d.)'%(k+1),titulo=GR[k],quitar=r"^\(%d\.\)\s*"%(k+1))
poner(47,r"^III\. I shall come now",'##','III.',titulo='Improvement of the truth that God is a portion.',quitar=r"^III\.\s*")
IMP=['Fret not on account of prosperity of the wicked.','Be content with present condition.','Those mistaken who judge saints to be unhappy.','Set not affections on earthly portions.','Be cheerful under all crosses and troubles.','Away with all expedients and compliances.','Glory in God as a portion.','Shall want nothing good.','Away with inordinate cares.','All is the believer\'s.','God no hurtful portion.','Let the saints think of God as their portion.','Be not afraid to die.','Make it fully out that God is your portion.']
poner(47,r"^\[1\.\] First, Let not the saints",'###','(1.)',titulo=IMP[0],quitar=r"^\[1\.\]\s*")
poner(53,r"^\(2\) Secondly, If the saints",'###','(2.)',titulo=IMP[1],quitar=r"^\(2\)\s*")
for k,n in enumerate([58,60,62,64,65,66,68,72,73,77,79,80]):
    j=k+3
    poner(n,r"^\(%d\.\) "%j,'###','(%d.)'%j,titulo=IMP[j-1],quitar=r"^\(%d\.\)\s*"%j)
poner(88,r"^Quest\. But you will say, How shall we know",'###','Quest.',titulo='How shall we know whether God be our portion?',quitar=r"^Quest\.\s*")
for n,k in [(125,1),(128,2),(130,3)]:
    poner(n,r"^Obj\. %d\. "%k,'###','Obj. %d.'%k,quitar=r"^Obj\. %d\.\s*"%k,titulo_si_falla=None)

# ---------------- THE PRIVY KEY OF HEAVEN ----------------
juntar(170,r"^## THE PRIVY KEY OF HEAVEN;",'##')
ARG=['The most eminent saints have done it.','Christ did it.','A distinction from hypocrites.','Can thus more fully unbosom ourselves.','Secret duties shall have open rewards.','God most manifests himself in private.','Life is the only time for it.','The great prevalency of it.','The most soul-enriching of duties.','Take many things together.','Christ much delighted by.','Believers only get God\'s secrets.','The Christian\'s meat and drink in difficulties.','God is omnipresent.','Private prayer neglected brings neglect to public prayer.','The times call aloud for it.','The near relations to the Lord call for it.','God hath given special marks of favour in secret prayer.','Satan, a great enemy to it.','Believers, those from whom private prayer may be looked for.']
for k,n in enumerate([172,175,177,178,179,180,183,183,189,190,191,191,196,197,198,199,200,201,202,203]):
    poner(n,r"^\[%d\.\] "%(k+1),'###','[%d.]'%(k+1),titulo=ARG[k],quitar=r"^\[%d\.\]\s*"%(k+1))
poner(208,r"^Objection\. But many will be ready",'###','Obj. 1.',quitar=r"^Objection\.\s*")
for n,rx,et in [(216,r"^Obj\. 2\. ",'Obj. 2.'),(227,r"^Obj\. 3\. ",'Obj. 3.'),(241,r"^Obj\. 4\. ",'Obj. 4.'),(243,r"^Objection 5\. ",'Objection 5.'),(244,r"^Obj\. 6\. ",'Obj. 6.')]:
    poner(n,rx,'###',et,quitar=rx+r"?\s*")

# ---------------- HEAVEN ON EARTH ----------------
juntar(321,r"^## THE PREFACE,$",'##')
if APLICAR:
    d=pag(419); i=buscar(419,r"^## Shewing the several ways"); d['pars'][i]=d['pars'][i][3:]
ORDEN.append((419,'(subtítulo del capítulo V pasa a párrafo normal)'))
if APLICAR: guardar()
