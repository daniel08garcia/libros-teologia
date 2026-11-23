# Correcciones de tipografía antigua en Perkins vol. 1 (después de "limpiar"): ſ, Anf., Te, verf., Pfal., whe, fro,
# palabras revisadas de perkins1-analiza.py, y notas que solo son un número de división del margen (con su llamada).
# Uso: python perkins1-corrige.py <trabajo>/texto   (haz antes una copia de texto/)
import re, glob, sys, collections
D = sys.argv[1]
SUST = [  # (patrón, reemplazo) con límites de palabra
 ("ſ", "s"),
 (r"\bAnfwer\b", "Answer"), (r"\bAnfw\b", "Answ"), (r"\bAnf\b", "Ans"),
 (r"\bTe\b", "Ye"), (r"\b([Vv])erf\.", r"\1ers."), (r"\bPfal", "Psal"), (r"\bPfa\b", "Psa"),
 (r"\bwhe\b", "when"), (r"\bthe the\b", "then the"), (r"\bserue the\. Our", "serue them. Our"),
 (r"\bfitting in heauen", "sitting in heauen"), (r"\bthe fence of", "the sence of"),
 (r"\btreble &", "tremble &"), (r"\binted not", "intend not"), (r"\bthou haft\b", "thou hast"), (r"\bLord haft\b", "Lord hast"),
]
# palabras sueltas f->s y tildes sin desarrollar (lista revisada a mano)
PAL = dict(muft="must", fo="so", fome="some", Thefe="These", finnes="sinnes", againft="against", moft="most",
  fin=None, defire="desire", faying="saying", iuft="iust", reft="rest", laftly="lastly", cafe="case", feeing="seeing",
  feruants="seruants", Gofpell="Gospell", fundry="sundry", ficke="sicke", loft="lost", finned="sinned", pleafe="please",
  forts="sorts", perswafion="perswasion", defires="desires", curfed="cursed", arifeth="ariseth", ftandeth="standeth",
  ferueth="serueth", ceafe="cease", preferued="preserued", Vniuft="Vniust", ferued="serued", feauenth="seauenth",
  perfecution="persecution", phyficke="physicke", thankfgiuing="thanksgiuing", feeth="seeth", Ephef="Ephes",
  fetteth="setteth", perfecute="persecute", fakes="sakes", thankf="thanks",
  secod="second", theselues="themselues", Secodly="Secondly", repentace="repentance", commadement="commandement",
  comandement="commandement", cosider="consider", stad="stand", cosidered="considered", actios="actions", cofort="comfort",
  cofcience="conscience", couenat="couenant", cotrary="contrary", codition="condition", commaded="commanded", repet="repent",
  remeber="remember", cotent="content", excellet="excellent", assurace="assurance", prouidece="prouidence", Teple="Temple",
  codemnation="condemnation", strog="strong", accout="account", willig="willing", cotinually="continually",
  reuerece="reuerence", comunion="communion", Comit="Commit", comit="commit", couersation="conuersation", natios="nations",
  temptatios="temptations", essece="essence", remebred="remembred", Coucell="Councell", warrat="warrant",
  corruptios="corruptions", comand="command", hudred="hundred", copany="company", couenient="conuenient",
  conueniet="conuenient", propouded="propounded", inheritace="inheritance", copared="compared", comended="commended",
  coparison="comparison", sermos="sermons", garmets="garments", tormets="torments", opinios="opinions",
  cotaines="containes", appearace="appearance", comands="commands", teder="tender", cocealed="concealed",
  comitteth="committeth", cotemne="contemne", consideratios="considerations", comission="commission", negligece="negligence")
PAL = {k: v for k, v in PAL.items() if v}
RE_PAL = re.compile(r"\b(" + "|".join(sorted(PAL, key=len, reverse=True)) + r")\b")
RE_SOLO = re.compile(r"^\[(\d+)\]\s*(\(?[0-9]+\.?\)?|\(?[IVXL]+\.?\)?|§|Vse\.? ?\d*\.?|Duties,? ?\d*\.?|\d+\. Duties\.?)\s*$")
cambios = collections.Counter(); quitadas = []
for f in sorted(glob.glob(D + "/p*.txt")):
    t = open(f, encoding="utf-8").read(); o = t
    for a, b in SUST:
        t, n = re.subn(a, b, t); cambios[a] += n
    t = re.sub(r"\bfro\b(?<!and fro)", lambda m: "from", t)  # fro -> from
    def pal(m): cambios[m.group(1)] += 1; return PAL[m.group(1)]
    t = RE_PAL.sub(pal, t)
    if "---NOTAS---" in t:
        cuerpo, notas = t.split("---NOTAS---", 1)
        nuevas = []
        for l in notas.strip("\n").split("\n"):
            m = RE_SOLO.match(l.strip())
            if m:
                cuerpo = cuerpo.replace("[%s]" % m.group(1), "", 1); quitadas.append((f[-9:-4], l.strip()))
            else: nuevas.append(l)
        t = cuerpo.rstrip("\n") + ("\n---NOTAS---\n" + "\n".join(nuevas) + "\n" if any(x.strip() for x in nuevas) else "\n")
    if t != o: open(f, "w", encoding="utf-8", newline="\n").write(t)  # sin newline, Windows escribe CRLF
print({k: v for k, v in cambios.items() if v})
print("notas solo-número quitadas:", len(quitadas)); [print("  ", q) for q in quitadas[:15]]
