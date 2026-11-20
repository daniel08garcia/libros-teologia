# Títulos ## / ### del volumen 5 de Brooks (ver temp/ocr_agent.md, paso 7: Títulos).
# Funciones de brooks3-titulos.py; la lista de abajo es propia de este volumen.
# Uso: python temp/trabajo/brooks5-titulos.py [--aplicar]   (haz antes una copia de texto/)
import io,re,sys
T='c:/www/libros-teologia/temp/trabajo/ocr-brooks-v5/texto/'
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

# ================= I. THE GOLDEN KEY =================
entero(3,r"^THE GOLDEN KEY",'##')
insertar(18,r"^The first question or case is this",'###',"The first question.—What are the special remedies, means, or helps against cherishing or keeping up of any special or peculiar sin?")
insertar(49,r"^The second question or case is this",'###',"The second question.—What is that faith that gives a man an interest in Christ?")
insertar(52,r"^The third question, or case is this",'###',"The third question.—Whether the sins of the saints shall be brought into the judgment of discussion and discovery in the great day, or no?")
PLEAS=[(61,"I","The first plea: Christ by his own blood has balanced and made up all reckonings."),
       (70,"II","The second plea: Christ has been the believer's surety, and paid his debts."),
       (75,"III","The third plea: from the active obedience of Christ."),
       (200,"IV","The fourth plea: from the sufferings of Christ."),
       (218,"V","The fifth plea: from the imputed righteousness of Christ."),
       (251,"VI","The sixth plea: from Christ considered as a common head."),
       (257,"VII","The seventh plea: from the suretyship of Christ."),
       (285,"VIII","The eighth plea: from the covenant of grace."),
       (326,"IX","The ninth plea: from evangelical obedience."),
       (328,"X","The tenth plea: from the covenant of redemption between God and Christ."),
       (402,"XI","The eleventh and last plea: from the book of life.")]
for n,r,t in PLEAS:
    insertar(n,r"^%s\. "%r,'###',"%s. %s"%(r,t))
# ================= II. PARADISE OPENED (## ya puestos por los agentes) =================
# ================= III. A WORD IN SEASON =================
insertar(414,r"^## NOTE\.",'##',"A WORD IN SEASON.")
juntar(455,r"^## THE SIGNAL PRESENCE OF GOD",'##')
insertar(456,r"^1\. First, There is a general presence",'###',"Six kinds of the presence of God.")
insertar(462,r"^\(1\.\) First, The Lord does manifest",'###',"Twelve ways in which the Lord manifests his signal presence with his people.")
insertar(525,r"^But you will say, What are the reasons",'###',"Ten reasons why God will be signally present with his people in their greatest troubles.")
insertar(545,r"^We shall now come to the application",'###',"The application of this truth.")
insertar(558,r"^The next use is a use of exhortation",'###',"Use of exhortation.")
insertar(569,r"^1\. First, There are some things that you must carefully shun",'###',"Things to be shunned, if you would enjoy the presence of God in your troubles.")
insertar(577,r"^2\. Secondly, As there are many things to be avoided",'###',"Things to be put in practice, if you would enjoy the presence of God in your troubles.")
poner(594,r"^Question\. But how may a person",'###','Question.',titulo='How may a person that has lost this gracious presence of God recover it again?',quitar=r"^Question\.\s*")

for n,c in ORDEN: print('p%04d'%n,c[:150])
print(len(ORDEN),'títulos')
if APLICAR: guardar()
