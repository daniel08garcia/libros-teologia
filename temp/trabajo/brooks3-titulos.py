# Títulos ## / ### del volumen 3 de Brooks (ver temp/ocr_agent.md, paso 7: Títulos).
# Funciones de brooks2-titulos.py (limpias) más insertar(); la lista de abajo es propia de este volumen.
# Uso: python temp/trabajo/brooks3-titulos.py [--aplicar]   (haz antes una copia de texto/)
import io,re,sys
T='c:/www/libros-teologia/temp/trabajo/ocr-brooks-v3/texto/'
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

# ================= I. THE UNSEARCHABLE RICHES OF CHRIST =================
entero(7,r"^THE UNSEARCHABLE RICHES OF CHRIST\.$",'##')
# Primera doctrina
insertar(14,r"^I\. I shall begin with the first observation",'##',"The first doctrine.—Those that are lowest in their own esteem are highest in God's esteem.")
insertar(14,r"^I\. For the first, That this is so",'###',"I. The point proved.")
insertar(16,r"^II\. The second thing that I am to do",'###',"II. Eighteen properties of an humble soul.")
insertar(32,r"^III\. I come now to the next thing",'###',"III. Five reasons of the point.")
insertar(35,r"^IV\. The uses of it",'###',"IV. Uses of it.")
insertar(36,r"^First, To lay down some motives",'###',"Eight motives to provoke persons to be humble.")
insertar(42,r"^I shall now come to some helps and directions",'###',"Nine directions and helps to keep us humble and low in our own eyes.")
insertar(47,r"^\[1\.\] And the first is this, Of all sins pride",'###',"The dangerous nature of pride held forth in nine propositions: also, six ways wherein pride shews itself.")
# Segunda doctrina
insertar(54,r"^II\. I shall now proceed to a second observation",'##',"The second doctrine.—All saints are not of an equal size and growth in grace and holiness.")
insertar(55,r"^I\. I shall begin with the first, To decipher",'###',"I. Twelve things by which souls weak in grace are discovered and deciphered.")
insertar(66,r"^II\. The second thing that I propounded",'###',"II. Twelve supports and comforts to uphold weak Christians.")
# Si la frase lleva llamada de nota, el título es la frase sin la llamada y el párrafo queda entero.
SUP={1:"That the weakest Christians have as much interest and propriety in Christ, and all the fundamental good that comes by Christ, as the strongest saints.",
     2:"That God doth with an eye of love reflect upon the least good that is in them, or done by them.",
     4:"That the Lord will graciously preserve and strengthen those weak graces that are in you.",
     7:"The least measure of grace is as true an earnest and pledge of greater measures of grace and of glory, as the greatest measure of grace is.",
     8:"That the least good that is done by the weakest saint shall not be despised by Christ, but highly esteemed and rewarded.",
     10:"That your persons stand not before God in your own righteousness, but in the righteousness of the Lord Jesus.",
     11:"Your sins shall never provoke Christ, nor prevail with Christ so far, as to give you a bill of divorce."}
for k,n in enumerate([66,67,68,69,70,71,72,73,74,75,76]):
    poner(n,r"^Support %d\. "%(k+1),'###','Support %d.'%(k+1),quitar=r"^Support %d\.\s*"%(k+1),titulo_si_falla=SUP.get(k+1))
entero(78,r"^## Support 12\.",'###')
insertar(81,r"^III\. The third thing propounded",'###',"III. Six duties that lie upon weak saints.")
DUT=['To be thankful for that little grace they have.',None,None,'Not to turn aside from the ways of God because of any hardships or difficulties.','Observe how Christ keeps your wills and affections.','Take heed of making sense and feeling a judge of your condition.']
poner(81,r"^1\. To be thankful",'###','1.',quitar=r"^1\.\s*",titulo_si_falla=DUT[0])
entero(88,r"^## 2\. Live up",'###')
entero(91,r"^## 3\. Be sure",'###')
poner(97,r"^4\. To persuade weak saints",'###','4.',titulo=DUT[3],quitar=r"^4\.\s*")
poner(99,r"^5\. You that are weak saints",'###','5.',quitar=r"^5\.\s*")
poner(100,r"^6\. Sixthly, Take heed",'###','6.',titulo=DUT[5],quitar=r"^6\.\s*")
entero(101,r"^## IV\. The duties of strong saints",'###')
# Tercera doctrina
insertar(109,r"^The word grace being thus opened",'##',"The third doctrine.—That the Lord gives the best gifts to his best beloved ones.")
insertar(109,r"^For the first, What are those best gifts",'###',"I. What those best gifts are that Christ bestows upon his dearest ones.")
entero(116,r"^## II\. The difference between",'###')
entero(117,r"^## III\. The excellency of those gifts",'###')
entero(119,r"^## IV\. The reasons why God gives",'###')
insertar(123,r"^We shall make some short but sweet uses",'###',"Eight inferences or uses made of this point.")
insertar(128,r"^But now some poor sinners may say",'###',"A word to sinners.")
# Cuarta doctrina
insertar(130,r"^1\. The first observation that I shall speak to",'##',"The fourth doctrine.—That the gifts and graces that God bestows upon his people should be improved, employed, and exercised by his people.")
insertar(131,r"^I\. For the first, There are these twelve reasons",'###',"I. Twelve reasons why gracious souls should exercise and improve their gifts and graces.")
insertar(142,r"^The special ends that the gifts and graces",'###',"II. Three special ends that the gifts and graces that God has bestowed upon believers should be exercised and improved to.")
insertar(146,r"^We shall come now to make some use",'###',"The use of this point: to stir up all Christians to make a blessed improvement of their gifts and graces.")
poner(153,r"^Quest\. When may a soul",'###','Quest.',quitar=r"^Quest\.\s*")
# Quinta doctrina
insertar(156,r"^'The unsearchable riches of Christ\.'",'##',"The fifth doctrine.—That the Lord Jesus Christ is very rich.")
insertar(156,r"^I\. For the first, that the Lord Jesus Christ is very rich\.",'###',"I. This point opened and proved by eight arguments.")
entero(161,r"^II\. The grounds and reasons why",'###')
entero(163,r"^III\. The excellency of the riches of Christ",'###')
entero(167,r"^## IV\. The uses of this point\.",'###')
insertar(167,r"^And the first use that we shall make",'###',"Use 1. To exhort Christians to labour to be spiritually rich.")
for n,k in [(198,2),(199,3),(200,4),(200,5),(201,6),(205,8),(206,9)]:
    poner(n,r"^Use %d\. "%k,'###','Use %d.'%k,quitar=r"^Use %d\.\s*"%k,titulo_si_falla={2:'Do not join anything with Christ in the great work of your redemption and salvation.',9:'Strive more and more to clear up your interest in Christ.'}.get(k))
poner(204,r"^Use\. 7\. ",'###','Use 7.',titulo='If Christ be so rich, then trust to Christ.',quitar=r"^Use\. 7\.\s*")
insertar(208,r"^Before I close up this discourse",'###',"A word to sinners.")
insertar(209,r"^\[1\.\] And the first principle is this",'###',"Nine directions to poor souls that would fain get an interest in Christ.")
# Sexta doctrina
insertar(213,r"^Unto me, who am less than the least",'##',"The sixth doctrine.—That it is the great duty of preachers or ministers to preach Jesus Christ to the people.")
insertar(214,r"^II\. But to come to the reasons",'###',"Five reasons why ministers must preach Christ to the people.")
entero(216,r"^II\. How ministers are to preach Christ",'###')
insertar(226,r"^I hope it will not be counted presumption",'###',"Three rules or directions to be observed by such as would preach Christ aright to the people.")
# Última doctrina
insertar(229,r"^Unto me, who am less than the least",'##',"The last doctrine.—That the office of a faithful minister is an honourable office.")
insertar(230,r"^\[1\.\] First, The several names and titles",'###',"I. Seven things speak them out to be honourable.")
entero(232,r"^2\. What honour that is which is justly due",'###')
poner(235,r"^Use\. And now let me make",'###','Use.',titulo='A short use.',quitar=r"^Use\.\s*")
insertar(236,r"^But you will say to me, How shall we honour them",'###',"Quest. How must Christians honour their faithful ministers?")
insertar(237,r"^But to draw to a close",'###',"The use of all.")

# ================= II. A CABINET OF JEWELS =================
for n,rx in [(255,"first"),(257,"second"),(258,"third"),(259,"fourth"),(260,"fifth"),(265,"sixth"),(292,"ninth"),(292,"tenth"),(294,"eleventh"),(300,"twelfth"),(303,"thirteenth"),(305,"fourteenth"),(306,"fifteenth"),(307,"sixteenth"),(308,"seventeenth"),(311,"eighteenth")]:
    entero(n,r"^## The %s maxim"%rx,'###')
entero(267,r"^The seventh maxim or consideration\.$",'###')
entero(270,r"^The eighth maxim, or consideration\.$",'###')
# Capítulo II: divisiones I.–VI.
CII={1:"In regard of sin, and a Christian's actings about it.",2:"The constant bent of a man's heart set for God, for grace, for holiness.",
     4:"A gracious heart is an uniform heart.",5:"A gracious heart sets himself most against his darling sin.",6:"True desires of grace is grace."}
for n,k,r,ord_ in [(312,1,'I','First'),(337,2,'II','Secondly'),(341,3,'III','Thirdly'),(360,4,'IV','Fourthly'),(362,5,'V','Fifthly'),(366,6,'VI','Sixthly')]:
    if k==3: poner(n,r"^III\. Thirdly",'###','III.',titulo='If your obedience be the obedience of faith, then your estate is good.',quitar=r"^III\.\s*")
    else: poner(n,r"^%s\. %s"%(r,ord_),'###','%s.'%r,titulo=CII[k],quitar=r"^%s\.\s*"%r)
# Capítulo III: pregunta y respuestas con título impreso
poner(422,r"^Quest\. But what are the properties or qualifications of that right turning",'###','Quest.',titulo='What are the properties of that right turning from sin which brings sinners within the compass of the promise of forgiveness?',quitar=r"^Quest\.\s*")
entero(423,r"^The second answer\.$",'###')
entero(434,r"^## The third answer\.$",'###')
entero(440,r"^The fourth answer\.$",'###')

for n,c in ORDEN: print('p%04d'%n,c[:150])
print(len(ORDEN),'títulos')
if APLICAR: guardar()
