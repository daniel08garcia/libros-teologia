# Títulos ## / ### del volumen 4 de Brooks (ver temp/ocr_agent.md, paso 7: Títulos).
# Funciones de brooks3-titulos.py; la lista de abajo es propia de este volumen.
# Uso: python temp/trabajo/brooks4-titulos.py [--aplicar]   (haz antes una copia de texto/)
import io,re,sys
T='c:/www/libros-teologia/temp/trabajo/ocr-brooks-v4/texto/'
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

# ================= THE CROWN AND GLORY OF CHRISTIANITY =================
entero(4,r"^THE\s+CROWN AND GLORY",'##')
# Doctrina y sus cuatro partes
poner(40,r"^Doct\. That real holiness",'##','Doct.',quitar=r"^Doct\.\s*")
insertar(41,r"^I\. First, What is this holiness",'###',"I. What this holiness is: sixfold.")
insertar(50,r"^II\. I come now to the second thing",'###',"II. The truth of the proposition, that 'without men are holy, they can never be happy:' ten arguments.")
insertar(80,r"^III\. I come now to the reasons",'###',"III. Reasons: five.")
insertar(83,r"^IV\. Use 1\.",'##',"IV. Use 1. Conviction.")
insertar(98,r"^Use 2\.",'##',"Use 2. Trial and examination.")
insertar(106,r"^But methinks I hear some of you saying",'###',"How we shall know whether we have real holiness or no: sixteen marks.")
insertar(153,r"^Use 3\.",'##',"Use 3. Exhortation.")
insertar(154,r"^I\. For the first, I shall propound",'###',"Motives: fifteen.")
insertar(195,r"^Well, then, if you are in good earnest",'###',"Counsels: six negative.")
insertar(215,r"^II\. Secondly, As there are several things",'###',"Counsels: ten positive.")
OBJ={1:"We have no power to make ourselves holy.",
     2:"But hereafter may be time enough to look after holiness.",
     3:"But if we should thus press and pursue after holiness, then we must take our farewell of all joy and comfort.",
     4:"We see that no persons on earth are exposed to such troubles, dangers, afflictions, and persecutions, as those who follow after holiness.",
     5:"If we should labour after holiness, then we must resolve to be poor, and mean, and beggarly in the world.",
     6:"Should we pursue after holiness, it would be a disgrace to us who are high, and great, and rich, and honourable in the earth.",
     7:"Should we pursue after holiness, we shall be sure to be reviled, slandered, and reproached on all hands."}
for n,k in [(244,1),(249,2),(252,3),(264,4),(303,5),(310,6),(320,7)]:
    poner(n,r"^Object\. %d\. "%k,'###','Object. %d.'%k,titulo=OBJ[k],quitar=r"^Object\. %d\.\s*"%k)
# Segunda parte de la exhortación: a los santificados
insertar(326,r"^And so I shall come now to the second part of the exhortation",'##',"To shew forth the reality and power of holiness.")
insertar(337,r"^\(1\.\) First, Consider that notwithstanding",'###',"Eight proofs of little holiness.")
insertar(343,r"^\(2\.\) Secondly, To provoke you",'###',"Seventeen provocations to increased holiness.")
insertar(377,r"^I shall, therefore, in the second place come to the reasons",'###',"Five arguments for degrees of glory.")
insertar(382,r"^Now I have nothing further to do upon this point",'###',"Two objections.")
insertar(387,r"^And so I come to the second thing proposed",'###',"Eight means, helps, and directions.")
insertar(395,r"^First, Premise this with me",'###',"Holiness of God: eight characteristics.")
insertar(401,r"^And so I come to the third thing proposed",'###',"Signs or evidences of increasing holiness: twelve signs.")
insertar(415,r"^And so I come now to the last use of this doctrine",'##',"Comfort and consolation to all who have real holiness: twelve considerations.")
insertar(431,r"^And now I have nothing to do but to lay down some positions",'##',"Positions concerning holiness.")
POS=[(431,r"^1\. And the first position","1. Wherever real holiness is, it will appear."),
     (432,r"^2\. The second position","2. Holiness rises by degrees."),
     (432,r"^3\. The third position","3. There is a great deal of preciousness in the least degree of holiness."),
     (434,r"^4\. The fourth position","4. All saints are not alike holy."),
     (435,r"^5\. The fifth position","5. A Christian may be more eminently holy at one time than at another."),
     (437,r"^6\. The sixth position","6. There will come a time when in this world holiness shall be more general."),
     (438,r"^\[7\.\] The seventh and last proposition","[7.] There are some special times and seasons wherein God calls aloud for holiness.")]
for n,rx,t in POS: insertar(n,rx,'###',t)
# p. 238: "I. The precious promises..." no es un título impreso aparte (su "II." va dentro de un párrafo)
d=pag(238); i=buscar(238,r"^## I\. The precious promises"); ORDEN.append((238,'(## quitado de "I. The precious promises")'))
if APLICAR: d['pars'][i]=d['pars'][i][3:]

for n,c in ORDEN: print('p%04d'%n,c[:150])
print(len(ORDEN),'títulos')
if APLICAR: guardar()
