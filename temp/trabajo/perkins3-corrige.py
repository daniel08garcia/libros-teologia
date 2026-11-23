# Correcciones de tipografía antigua en Perkins vol. 3 (copia de perkins2-corrige.py; notas que solo son una etiqueta de división: Use., Quest., Answ., Object., 10 Ground.) (después de "limpiar"): ſ, Anf., Te, verf., Pfal., whe, fro,
# palabras revisadas de perkins1-analiza.py, y notas que solo son un número de división del margen (con su llamada).
# Uso: python perkins3-corrige.py <trabajo>/texto   (haz antes una copia de texto/)
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
PAL = dict(becaufe="because", Thefe="These", fome="some", alfo="also", againft="against", thofe="those", fay="say",
  fecondly="secondly", anfwer="answer", fee="see", moft="most", confider="consider", perfon="person", Laftly="Lastly",
  laftly="lastly", Chriftian="Christian", Chriftians="Christians", juftice="justice", Iuftice="Iustice", fhew="shew",
  fhewes="shewes", purpofe="purpose", juft="just", ftand="stand", ftands="stands", Befides="Besides", befide="beside",
  fometimes="sometimes", fometime="sometime", ferve="serve", foules="soules", houfe="house", elfe="else", fhalt="shalt",
  fins="sins", manifeft="manifest", reafons="reasons", reafonable="reasonable", courfe="course", forts="sorts",
  obfervation="observation", abfolute="absolute", circumftances="circumstances", honeft="honest", Iofeph="Ioseph",
  Ephef="Ephes", Magiftrates="Magistrates", feverall="severall", fixt="sixt", higheft="highest", treatife="treatise",
  abolifh="abolish", fixth="sixth", efteemed="esteemed", fundrie="sundrie", whileft="whilest", afide="aside",
  propofition="proposition", defiring="desiring", refisted="resisted", fitteth="sitteth", defolation="desolation",
  Prefident="President", Hof="Hos", ferm="serm", caufe="cause",
  comitted="committed", comonly="commonly", copany="company", chaging="changing")
PAL = {k: v for k, v in PAL.items() if v}
# vol. 3 (lista de perkins1-analiza.py revisada a mano)
PAL.update(muft='must', thefe='these', finnes='sinnes', cafe='case', confideration='consideration', fundry='sundry', perfecution='persecution', mifery='misery', feemes='seemes', confisteth='consisteth', referved='reserved', difobedience='disobedience', Genef='Genes', fearching='searching', infomuch='insomuch', Thef='Thes', forcerie='sorcerie', feeing='seeing', feeth='seeth')
RE_PAL = re.compile(r"\b(" + "|".join(sorted(PAL, key=len, reverse=True)) + r")\b")
RE_SOLO = re.compile(r"^\[(\d+)\]\s*(\(?[0-9]+\.?\)?|\(?[IVXL]+\.?\)?|§|(?:\d+\.? ?)?(?:[VU]se|Quest|Q|Answ?|Anf|Obje[cf]t|Obiect|Obj|Ob|Ground|Doct|Reason|Rule|Duties),?\.? ?\d*\.?)\s*$")
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
