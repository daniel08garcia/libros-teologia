# Títulos ## / ### del volumen 6 de Brooks (ver temp/ocr_agent.md, paso 7: Títulos).
# Funciones de brooks3-titulos.py; la lista de abajo es propia de este volumen.
# Uso: python temp/trabajo/brooks6-titulos.py [--aplicar]   (haz antes una copia de texto/)
import io,re,sys
T='c:/www/libros-teologia/temp/trabajo/ocr-brooks-v6/texto/'
APLICAR='--aplicar' in sys.argv
PAGS={}; ORDEN=[]
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
    """Primera oración: termina en . ? ! seguido de espacio y mayúscula o comilla, o fin.
    Se saltan abreviaturas (Tim., xii., viz., &c.) y exclamaciones cortas."""
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
def poner(n,rx,nivel,etiqueta,titulo=None,quitar=None,titulo_si_falla=None):
    """Quita la etiqueta del párrafo; el título es etiqueta + frase inicial (o titulo / titulo_si_falla)."""
    d=pag(n); i=buscar(n,rx); p=d['pars'][i]
    q=re.search(quitar or re.escape(etiqueta),p); assert q,(n,etiqueta,p[:80])
    antes,resto=p[:q.start()].strip(),p[q.end():].strip()
    f=None
    if titulo is None: f,r=frase(resto)
    if f: cab='%s %s %s'%(nivel,etiqueta,f); nuevo=(antes+' '+r).strip()
    else:
        cab=('%s %s %s'%(nivel,etiqueta,titulo or titulo_si_falla or '')).strip(); nuevo=(antes+' '+resto).strip()
    ORDEN.append((n,cab))
    if APLICAR:
        if nuevo: d['pars'][i]=nuevo
        else: del d['pars'][i]
        d['pars'].insert(i,cab)
def insertar(n,rx,nivel,titulo):
    """Título nuevo (del índice) antes del párrafo; el párrafo no se toca."""
    d=pag(n); i=buscar(n,rx)
    ORDEN.append((n,nivel+' '+titulo))
    if APLICAR: d['pars'].insert(i,nivel+' '+titulo)
def entero(n,rx,nivel):
    """Todo el párrafo (corto) pasa a ser título (o cambia de nivel)."""
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

# ================= I. LONDON'S LAMENTATIONS =================
entero(8,r"^LONDON'S LAMENTATIONS\.$",'##')
insertar(24,r"^\(1\.\) First, That great afflictions",'###',"Fire, as a symbol in Scripture.")
insertar(29,r"^Now here give me leave to say",'###',"Ends of God in inflicting judgments.")
insertar(42,r"^Quest\. But pray, sir, what are those high and holy ends",'###',"Ends of God in inflicting judgments on his own people.")
insertar(58,r"^But you will say, What sins were there",'###',"Seven sins among the professing people in London, that ought to work them to justify the Lord.")
insertar(65,r"^\[2\.\] Secondly, That though sin in the general",'###',"The several sins that bring the fiery judgment upon cities and countries.")
insertar(137,r"^Now that you may the better see and acknowledge",'###',"Various specialities concerning the judgment of fire on London.")
insertar(160,r"^Use 2\. The second use",'###',"Use 2. Considerations to work to lamentation.")
insertar(173,r"^Now that I may be a little serviceable",'###',"Thirteen supports to bear up their hearts who have lost all, or much, of what they had in this world.")
insertar(206,r"^\[1\.\] First, The fire of hell is frequently mentioned",'###',"Four arguments to prove that it is very probable that there is material fire in hell, and objections met.")
insertar(223,r"^Quest\. But, sir, pray what are those duties",'###',"Sixteen duties incumbent upon those who have been burned up.")
insertar(313,r"^I come now to those duties",'###',"Eight duties incumbent upon those whose habitations are still standing.")
# ================= II. THE GLORIOUS DAY OF THE SAINTS' APPEARANCE =================
entero(320,r"^THE GLORIOUS DAY",'##')
d=pag(321); i=buscar(321,r"^## Note\.$"); ORDEN.append((321,'## NOTE.'))
if APLICAR: d['pars'][i]='## NOTE.'
# ================= III. GOD'S DELIGHT =================
entero(342,r"^GOD'S DELIGHT",'##')
d=pag(343); i=buscar(343,r"^## \* GOD'S DELIGHT"); ORDEN.append((343,'(## quitado de la portada citada en la NOTE)'))
if APLICAR: d['pars'][i]=d['pars'][i][3:]
# ================= IV. HYPOCRITES DETECTED =================
entero(371,r"^HYPOCRITES DETECTED",'##')
juntar(377,r"^## A SERMON$",'##')
# ================= VI. A HEAVENLY CORDIAL: máximas =================
ROM=['I','II','III','IV','V','VI','VII','VIII','IX','X','XI','XII']
for k,(n,lab) in enumerate([(417,'1'),(419,'II'),(419,'III'),(419,'IV'),(420,'V'),(420,'VI'),(421,'VII'),(421,'VIII'),(421,'IX'),(436,'X'),(437,'XI'),(438,'XII')]):
    d=pag(n); i=buscar(n,r"^%s\. The [a-z]+ divine maxim"%lab); p=d['pars'][i]
    m=re.search(r"viz\., (?:That )?(.+?[.;:])(?=\s|$)",p)
    t=m.group(1).rstrip(';:') if m else ''
    t=re.sub(r"\[\d+\]","",t)
    if len(t)>150: t=t[:150].rsplit(',',1)[0]
    if k==11: t='God knows how to distinguish his people from others, when the pestilence rages in the midst of them'
    if k==3: t='No man knows divine love or hatred by outward dispensation'
    if k==6: t='When the people of God cannot prevail for a whole land, they shall prevail for their own personal preservation'
    t=t[0].upper()+t[1:]
    if not t.endswith('.'): t+='.'
    insertar(n,r"^%s\. The [a-z]+ divine maxim"%lab,'###',"%s. %s"%(ROM[k],t))
# ================= VII. THE LEGACY OF A DYING MOTHER =================
entero(441,r"^THE LEGACY",'##')
d=pag(458); i=buscar(458,r"^## A TRUE RELATION$")
t='## A TRUE RELATION OF SOME OF THE EXPERIENCES OF MRS SUSANNA BELL,'
ORDEN.append((458,t))
if APLICAR: d['pars'][i:i+3]=[t]

for n,c in ORDEN: print('p%04d'%n,c[:160])
print(len(ORDEN),'títulos')
if APLICAR: guardar()
