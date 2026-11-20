# Títulos ## / ### del volumen 1 de Brooks (ver temp/ocr_agent.md, paso 7: Títulos).
# Ejemplo para otros libros: las funciones poner/entero/juntar/serie sirven tal cual; la lista de páginas
# y etiquetas de abajo es propia de este volumen. Sin --aplicar solo muestra los títulos propuestos.
# Uso: python temp/trabajo/brooks-titulos.py [--aplicar]   (haz antes una copia de texto/)
# Ya se aplicó en ocr-brooks-v1 (2026-11-19): volver a ejecutarlo ahí falla porque las etiquetas ya se movieron.
import io,re,sys
T='c:/www/libros-teologia/temp/trabajo/ocr-brooks-v1/texto/'
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
IDX=[l.strip() for l in io.open('c:/www/libros-teologia/temp/trabajo/ocr-brooks-v1/indice.txt',encoding='utf-8').read().split('\n') if l.strip()]
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
    t=re.sub(r"^#+ ","",d['pars'][i])+' '+d['pars'][i+1]
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

# PRECIOUS REMEDIES
poner(90,r"^I\. For the proof",'##','I.',titulo='The point proved.',quitar=r"^I\.\s*")
poner(91,r"^II\. Now, the second",'##','II.',titulo='The several devices that Satan hath to draw souls to sin.',quitar=r"^II\.\s*")
for j,(n,k) in enumerate([(91,1),(95,2),(98,3),(103,4),(106,5),(110,6),(117,7),(120,8),(126,9),(133,10),(135,11),(140,12)]): dev(n,k,j)
entero(142,r"^The second thing to be shewed is",'##')
for j,(n,k) in enumerate([(142,1),(149,2),(153,3),(156,4),(160,5),(163,6),(165,7),(168,8)]): dev(n,k,12+j)
entero(170,r"^III\. The third thing",'##')
for j,(n,k) in enumerate([(170,1),(174,2),(176,3),(178,4),(183,5),(186,6),(189,7)]): dev(n,k,20+j)
DEVT.insert(27,'By persuading them that their estate is not good, their hearts are not upright with God.')
dev(192,8,27)
juntar(196,r"^## IV\. The fourth",'##')
DEVT[28:]=['By working them to make it their business to seek how to greaten themselves, to enrich themselves, to secure themselves.','By engaging them against the people of the Most High.']
for j,(n,k) in enumerate([(196,1),(201,2)]): dev(n,k,28+j)
juntar(218,r"^AN APPENDIX$",'##')
for n,k in [(218,1),(223,2),(225,3),(227,4),(227,5)]:
    poner(n,r"^Device \(%d\)"%k,'###','Device (%d).'%k,intro=True,quitar=r"Device \(%d\)\.\s*"%k)
entero(228,r"^Here followeth seven characters",'##')
entero(231,r"^Propositions concerning Satan",'##')
entero(235,r"^Now I shall come to the reasons of the point",'##')
entero(236,r"^The use of the point\.",'##')

# APPLES OF GOLD
def tit_idx(rx):
    out={}
    for l in IDX:
        m=re.match(rx,l)
        if m:
            s=re.sub(r",? (from )?\d[\d\- ,]*$","",m.group(2)).strip()
            s=re.sub(r"[,.;]?\s*(also |wherein )?[Aa]nswered .*$|\. (This objection|Four|Eight).*$","",s).rstrip(' ,;')
            s=re.sub(r",? &c\.?$","",s).rstrip(' ,')
            out[int(m.group(1))]=s if s.endswith(('.','?')) else s+'.'
    return out
MOT=tit_idx(r"^(\d+)\. (.*(?:honour to be good|gave himself|rich in spiritual experiences|only time that you are sure|dregs of his wrath|reward in heaven|affected and taken|black temptations|excellency of souls|reckoning).*)$")
OBJ=tit_idx(r"^Obj\. (\d+)\. (.*)$")
AOG=tit_idx(r"^(\d) Obj\. (.*)$")
print('reasons',serie(257,272,r"Reason \(?(?P<num>\d+)\)?\.",'###',''))
poner(278,r"^Evil 1\.",'###','Evil 1.',titulo='Pride.',quitar=r"^Evil 1\.\s*")
poner(279,r"^Evil 2\.",'###','Evil 2.',titulo='Sensual pleasures and delights.',quitar=r"^Evil 2\.\s*")
print('evils',serie(278,283,r"Evil (?P<num>\d+)\.",'###','Evil %d.'))
print('motives',serie(283,299,r"Motive \((?P<num>\d+)\)\.",'###','',MOT))
poner(299,r"^Quest\. But here an apt question",'###','Quest.',titulo='Whether in the great day of account, the sins of saints shall be brought into the judgment of discussion and discovery, or no?',quitar=r"^Quest\.\s*")
print('objs AoG',serie(340,354,r"Obj(?:ect(?:ion)?)?\.? \(?(?P<num>\d+)\)?\.",'###','',AOG))
# MUTE CHRISTIAN
poner(374,r"^I\. For the first",'##','I.',quitar=r"^I\.\s*")
entero(377,r"^II\. Quest\. 2\.",'##')
poner(385,r"^III\. The third thing",'##','III.',quitar=r"^III\.\s*")
poner(391,r"^IV\. Why must Christians",'##','IV.',quitar=r"^IV\.\s*",titulo_si_falla='Why Christians must be mute and silent under their greatest afflictions.')
poner(399,r"^V\. You see, beloved",'##','V.',titulo='Use.',quitar=r"^V\.\s*")
print('reasons MC',serie(391,399,r"Reason (?P<num>\d+)\.",'###','Reason %d.'))
print('objs MC',serie(400,478,r"Obj(?:ect(?:ion)?)?\.? \(?(?P<num>\d+)\)?\.",'###','',OBJ))
for n,rx in [(466,r"^Quest\. But what are the reasons")]:
    poner(n,rx,'###','Quest.',quitar=r"^Quest\.\s*",titulo_si_falla='What are the reasons that God doth so delay and put off his people?')
# STRING OF PEARLS
SPT={'IV':'They shall have the best and choicest presence of God and Christ in heaven.','V':'They shall enjoy perfection of grace in heaven.'}
for n,num in [(489,'I'),(493,'II'),(497,'III'),(501,'IV'),(503,'V'),(506,'VI'),(511,'VII')]:
    poner(n,r"^%s\. "%num,'##',num+'.',quitar=r"^%s\.\s*"%num,titulo_si_falla=SPT.get(num))
print('reasons SP',serie(514,519,r"Reason (?P<num>\d+)\.",'###','Reason %d.'))
if APLICAR: guardar()
