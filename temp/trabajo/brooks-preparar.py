# Prepara un volumen de Brooks (transcrito con ocr.py) para la traducción con sermones.js.
# - Corta el original en piezas (una por archivo HTML) y las marca con @@SERMON@@.
# - Pasa cada nota a un párrafo propio y quita la línea "__________" (el README pide un <p> por nota).
# - En la primera artimaña de cada grupo, pone el encabezado del grupo (##) después del de la
#   artimaña (###), para que "saltar_parrafos: 1" quite solo el título de la artimaña.
# - Escribe plan.json con destino, fecha, id, saltar_parrafos, versiculo y titulo_original de cada pieza,
#   en el mismo orden; brooks-manifiesto.py lo copia al manifiesto después de "dividir".
#
# Uso: python temp/trabajo/brooks-preparar.py 1
import io, json, re, sys

VOL = sys.argv[1] if len(sys.argv) > 1 else "1"
ORIG = f"temp/originales/The Complete Works of Thomas Brooks (vol.{VOL}).txt"
SALIDA = f"temp/trabajo/brooks-v{VOL}"
BASE = "siglo/XVII/Thomas Brooks"
ROM = ["0","I","II","III","IV","V","VI","VII","VIII","IX","X","XI","XII","XIII","XIV","XV","XVI","XVII","XVIII","XIX","XX",
       "XXI","XXII","XXIII","XXIV","XXV","XXVI","XXVII","XXVIII","XXIX","XXX","XXXI","XXXII","XXXIII","XXXIV","XXXV",
       "XXXVI","XXXVII","XXXVIII","XXXIX","XL","XLI","XLII","XLIII","XLIV","XLV"]

# Piezas del volumen 1: (línea inicial, línea final inclusive, datos). Líneas 1-based del .txt.
# grupo=(ini, fin): líneas del encabezado del grupo que se mueven después del primer párrafo.
def pieza(a, b, **d): return {"ini": a, "fin": b, **d}

PR = f"{BASE}/Remedios Preciosos Contra Las Artimañas De Satanás"
AG = f"{BASE}/Manzanas De Oro"
MC = f"{BASE}/El Cristiano Mudo Bajo La Vara"
SP = f"{BASE}/Una Sarta De Perlas"

def artimañas(inicios, fin, grupo, id0):
    out = []
    for k, a in enumerate(inicios):
        b = (inicios[k + 1] - 1) if k + 1 < len(inicios) else fin
        d = dict(destino=PR, fecha="1652-01-01", id=ROM[id0 + k], saltar=1)
        if k == 0: d["grupo"] = grupo
        out.append(pieza(a, b, **d))
    return out

V1 = [
    pieza(44, 179, destino=BASE, fecha="1866-01-01", id="0", saltar=1, titulo_original="Memoir of Thomas Brooks"),
    # Precious Remedies Against Satan's Devices (1652)
    pieza(785, 879, destino=PR, fecha="1652-01-01", id="0", saltar=0, titulo_original="The Epistle Dedicatory and A Word to the Reader"),
    pieza(880, 934, destino=PR, fecha="1652-01-01", id="I", saltar=1, versiculo="unido", titulo_original="The Words Opened and the Point Proved"),
    *artimañas([939, 990, 1030, 1084, 1128, 1166, 1233, 1268, 1318, 1399, 1428, 1487], 1514, (935, 938), 2),
    *artimañas([1521, 1587, 1621, 1657, 1687, 1721, 1744, 1781], 1800, (1515, 1520), 14),
    *artimañas([1808, 1848, 1885, 1919, 1986, 2023, 2053, 2088], 2132, (1801, 1807), 22),
    *artimañas([2135, 2183], 2352, (2133, 2134), 30),
    *artimañas([2357, 2415, 2431, 2461, 2484], 2495, (2353, 2356), 32),
    pieza(2496, 2535, destino=PR, fecha="1652-01-01", id="XXXVII", saltar=1),
    pieza(2536, 2581, destino=PR, fecha="1652-01-01", id="XXXVIII", saltar=1),
    pieza(2582, 2602, destino=PR, fecha="1652-01-01", id="XXXIX", saltar=1),
    pieza(2603, 2690, destino=PR, fecha="1652-01-01", id="XL", saltar=1),
    # Apples of Gold (1657)
    pieza(2691, 2820, destino=AG, fecha="1657-01-01", id="0", saltar=1),
    pieza(2821, 3103, destino=AG, fecha="1657-01-01", id="I", saltar=1),
    *[pieza(a, b, destino=AG, fecha="1657-01-01", id=ROM[i + 2], saltar=1)
      for i, (a, b) in enumerate([(3104, 3246), (3247, 3350), (3351, 3568), (3569, 3617), (3618, 3791), (3792, 4316), (4317, 4564), (4565, 4612)])],
    pieza(4613, 4687, destino=AG, fecha="1657-01-01", id="X", saltar=1),
    # The Mute Christian under the Smarting Rod (1659)
    pieza(4688, 4775, destino=MC, fecha="1659-01-01", id="0", saltar=1),
    pieza(4776, 4838, destino=MC, fecha="1659-01-01", id="I", saltar=1),
    *[pieza(a, b, destino=MC, fecha="1659-01-01", id=ROM[i + 2], saltar=1)
      for i, (a, b) in enumerate([(4839, 4935), (4936, 4991), (4992, 5073), (5074, 5245), (5246, 5287), (5288, 5350), (5351, 5398),
                                  (5399, 5427), (5428, 5454), (5455, 5479), (5480, 5533), (5534, 5589), (5590, 5651), (5652, 5674), (5675, 5761)])],
    # A String of Pearls (1657)
    pieza(5762, 5865, destino=SP, fecha="1657-01-01", id="0", saltar=1),
    pieza(5866, 5949, destino=SP, fecha="1657-01-01", id="I", saltar=1),
    *[pieza(a, b, destino=SP, fecha="1657-01-01", id=ROM[i + 2], saltar=1)
      for i, (a, b) in enumerate([(5950, 5982), (5983, 6020), (6021, 6050), (6051, 6076), (6077, 6119), (6120, 10**9)])],
]
# Volumen 2
ARK = f"{BASE}/Un Arca Para Todos Los Noés De Dios"
PK = f"{BASE}/La Llave Secreta Del Cielo"
HE = f"{BASE}/El Cielo En La Tierra"

def serie(destino, fecha, id0, rangos, saltar=1, grupo=None):
    out = []
    for k, (a, b) in enumerate(rangos):
        d = dict(destino=destino, fecha=fecha, id=ROM[id0 + k], saltar=saltar)
        if k == 0 and grupo: d["grupo"] = grupo
        out.append(pieza(a, b, **d))
    return out

V2 = [
    # An Ark for all God's Noahs (1662)
    pieza(1, 81, destino=ARK, fecha="1662-01-01", id="0", saltar=1, titulo_original="An Ark for All God's Noahs: The Epistle Dedicatory"),
    pieza(82, 384, destino=ARK, fecha="1662-01-01", id="I", saltar=1, versiculo="unido", titulo_original="A Matchless Portion: What a Portion God Is"),
    pieza(385, 416, destino=ARK, fecha="1662-01-01", id="II", saltar=1, titulo_original="Grounds of Title unto God as a Portion"),
    # III. Improvement: un archivo por cada uso (1.)–(14.); el encabezado del grupo va en el primero
    *serie(ARK, "1662-01-01", 3, [(423, 504), (505, 538), (539, 549), (550, 558), (559, 571), (572, 579), (580, 587),
                                  (588, 598), (599, 622), (623, 630), (631, 679), (680, 686), (687, 700), (701, 736)], grupo=(417, 422)),
    pieza(737, 832, destino=ARK, fecha="1662-01-01", id="XVII", saltar=1, titulo_original="How Shall We Know Whether God Be Our Portion?"),
    pieza(833, 956, destino=ARK, fecha="1662-01-01", id="XVIII", saltar=0, titulo_original="Exhortation to Evidence and to Get God as Our Portion"),
    *serie(ARK, "1662-01-01", 19, [(957, 984), (985, 998), (999, 1091)]),
    # The Privy Key of Heaven (1665)
    pieza(1092, 1365, destino=PK, fecha="1665-01-01", id="0", saltar=1, titulo_original="The Privy Key of Heaven: The Epistle Dedicatory and To the Reader"),
    pieza(1366, 1554, destino=PK, fecha="1665-01-01", id="I", saltar=1, versiculo="unido", titulo_original="The Privy Key of Heaven; or, A Discourse of Closet Prayer"),
    pieza(1555, 1738, destino=PK, fecha="1665-01-01", id="II", saltar=0, titulo_original="Further Reasons for Closet Prayer"),
    *serie(PK, "1665-01-01", 3, [(1739, 1802), (1803, 1909), (1910, 2088), (2089, 2107), (2108, 2119), (2120, 2193)]),
    pieza(2194, 2403, destino=PK, fecha="1665-01-01", id="IX", saltar=0, titulo_original="Counsel for the Better Carrying On of Closet Prayer"),
    pieza(2404, 2634, destino=PK, fecha="1665-01-01", id="X", saltar=0, titulo_original="Means, Rules, and Directions for Closet Prayer"),
    # Heaven on Earth (1654)
    pieza(2635, 2854, destino=HE, fecha="1654-01-01", id="0", saltar=1, titulo_original="Heaven on Earth: The Epistles and the Preface"),
    pieza(2855, 2993, destino=HE, fecha="1654-01-01", id="I", saltar=1, titulo_original="Heaven on Earth: Chapter I"),
    pieza(2994, 3129, destino=HE, fecha="1654-01-01", id="II", saltar=1, titulo_original="Heaven on Earth: Chapter II"),
    pieza(3130, 3451, destino=HE, fecha="1654-01-01", id="III", saltar=0, titulo_original="Heaven on Earth: Chapter II, The Seventh Proposition"),
    pieza(3452, 3667, destino=HE, fecha="1654-01-01", id="IV", saltar=1, titulo_original="Heaven on Earth: Chapter III"),
    pieza(3668, 3849, destino=HE, fecha="1654-01-01", id="V", saltar=1, titulo_original="Heaven on Earth: Chapter IV"),
    pieza(3850, 4005, destino=HE, fecha="1654-01-01", id="VI", saltar=1, titulo_original="Heaven on Earth: Chapter V"),
    *[pieza(a, b, destino=HE, fecha="1654-01-01", id=ROM[7 + i], saltar=0, titulo_original=t)
      for i, (a, b, t) in enumerate([
          (4006, 4101, "Heaven on Earth: Chapter V, The Things that Accompany Salvation: Knowledge"),
          (4102, 4211, "Heaven on Earth: Chapter V, Faith that Accompanies Salvation"),
          (4212, 4301, "Heaven on Earth: Chapter V, Repentance and Obedience that Accompany Salvation"),
          (4302, 4413, "Heaven on Earth: Chapter V, Love that Accompanies Salvation"),
          (4414, 4880, "Heaven on Earth: Chapter V, Prayer, Perseverance, and Hope that Accompany Salvation")])],
    pieza(4881, 4975, destino=HE, fecha="1654-01-01", id="XII", saltar=1, titulo_original="Heaven on Earth: Chapter VI"),
    pieza(4976, 10**9, destino=HE, fecha="1654-01-01", id="XIII", saltar=1, titulo_original="Heaven on Earth: Chapter VII"),
]
# Volumen 3. Las piezas que abarcan varias subdivisiones conservan su primer encabezado (saltar=0);
# el título del HTML se pone en el manifiesto.
UR = f"{BASE}/Las Inescrutables Riquezas De Cristo"
CJ = f"{BASE}/Un Cofre De Joyas"
def tramos(destino, fecha, id0, rangos, saltar=0):
    return [pieza(a, b, destino=destino, fecha=fecha, id=ROM[id0 + k], saltar=saltar, titulo_original=t)
            for k, (a, b, t) in enumerate(rangos)]

V3 = [
    # The Unsearchable Riches of Christ (1655)
    pieza(1, 105, destino=UR, fecha="1655-01-01", id="0", saltar=1, titulo_original="The Unsearchable Riches of Christ: The Epistle Dedicatory"),
    pieza(106, 375, destino=UR, fecha="1655-01-01", id="I", saltar=1, versiculo="unido",
          titulo_original="The Unsearchable Riches of Christ: The First Doctrine, Eighteen Properties of an Humble Soul"),
    *tramos(UR, "1655-01-01", 2, [
        (376, 534, "The First Doctrine: Reasons, Uses, and Motives to Humility"),
        (535, 730, "The First Doctrine: Directions to Keep Us Humble; The Dangerous Nature of Pride"),
        (731, 866, "The Second Doctrine: Twelve Things by Which Souls Weak in Grace Are Discovered"),
        (867, 1131, "The Second Doctrine: Twelve Supports and Comforts to Uphold Weak Christians"),
        (1132, 1467, "The Second Doctrine: Six Duties That Lie upon Weak Saints"),
        (1468, 1590, "The Second Doctrine: The Duties of Strong Saints to the Weak"),
        (1591, 1934, "The Third Doctrine: The Lord Gives the Best Gifts to His Best Beloved Ones"),
        (1935, 2155, "The Fourth Doctrine: Gifts and Graces Should Be Exercised and Improved"),
        (2156, 2287, "The Fourth Doctrine: The Use of the Point"),
        (2288, 2462, "The Fifth Doctrine: The Lord Jesus Christ Is Very Rich"),
        (2463, 2646, "The Fifth Doctrine: Use 1, To Labour to Be Spiritually Rich"),
        (2647, 2868, "The Fifth Doctrine: Use 1, Propositions concerning Spiritual Riches"),
        (2869, 3125, "The Fifth Doctrine: Further Uses"),
        (3126, 3365, "The Sixth Doctrine: Ministers Must Preach Jesus Christ"),
        (3366, 3511, "The Last Doctrine: The Office of a Faithful Minister Is an Honourable Office")]),
    # A Cabinet of Jewels (1669)
    pieza(3512, 3623, destino=CJ, fecha="1669-01-01", id="0", saltar=1, titulo_original="A Cabinet of Jewels: The Epistle Dedicatory"),
    pieza(3624, 3725, destino=CJ, fecha="1669-01-01", id="I", saltar=1, titulo_original="A Cabinet of Jewels: Chapter I, Maxims 1-7"),
    *tramos(CJ, "1669-01-01", 2, [
        (3726, 4031, "A Cabinet of Jewels: Chapter I, Maxims 8-18"),
        (4032, 4122, "A Cabinet of Jewels: Chapter II, Evidences of Saving Grace (I-II)"),
        (4123, 4238, "A Cabinet of Jewels: Chapter II, The Obedience of Faith"),
        (4239, 4266, "A Cabinet of Jewels: Chapter II, Evidences IV-V"),
        (4267, 4402, "A Cabinet of Jewels: Chapter II, True Desires of Grace Is Grace"),
        (4403, 4552, "A Cabinet of Jewels: Chapter III, Saving Repentance"),
        (4553, 4675, "A Cabinet of Jewels: Chapter III, The Properties of Right Turning from Sin"),
        (4676, 4815, "A Cabinet of Jewels: Chapter IV, How Far an Hypocrite Cannot Go"),
        (4816, 10**9, "A Cabinet of Jewels: Chapter V, The Use of Evidences")]),
]
# Volumen 4: The Crown and Glory of Christianity (1662), 58 sermones sobre Heb. xii. 14, en una sola obra.
# Las secciones largas (marcas, motivos, objeción 4, provocaciones) se cortan en sus puntos numerados.
CG = f"{BASE}/La Corona Y Gloria Del Cristianismo"
V4 = [
    pieza(1, 220, destino=CG, fecha="1662-01-01", id="0", saltar=1, titulo_original="The Crown and Glory of Christianity: The Epistle Dedicatory"),
    pieza(221, 324, destino=CG, fecha="1662-01-01", id="I", saltar=1, versiculo="unido",
          titulo_original="The Crown and Glory of Christianity: The Text Opened; What Holiness Is"),
    *tramos(CG, "1662-01-01", 2, [
        (325, 384, "Without Holiness No Happiness: Arguments 1-6"),
        (385, 508, "Without Holiness No Happiness: Arguments 7-10"),
        (509, 594, "The Reasons of the Point; Use 1, Conviction"),
        (595, 657, "Use 2, Trial: Marks of Real Holiness 1-5"),
        (658, 709, "Use 2, Trial: Marks of Real Holiness 6-13"),
        (710, 826, "Use 2, Trial: Marks of Real Holiness 14-16"),
        (827, 878, "Use 3, Exhortation: Motives to Holiness 1-4"),
        (879, 908, "Use 3, Exhortation: Motives to Holiness 5-11"),
        (909, 1019, "Use 3, Exhortation: Motives to Holiness 12-15"),
        (1020, 1128, "Six Negative Counsels"),
        (1129, 1292, "Ten Positive Counsels"),
        (1293, 1397, "Objections 1-3"),
        (1398, 1433, "Objection 4: Persecution, Answers 1-4"),
        (1434, 1588, "Objection 4: Persecution, Answers 5-12"),
        (1589, 1698, "Objections 5-7"),
        (1699, 1788, "The Reality and Power of Holiness; Eight Proofs of Little Holiness"),
        (1789, 1810, "Provocations to Increased Holiness 1-6"),
        (1811, 1900, "Provocations to Increased Holiness 7-17"),
        (1901, 2025, "Degrees of Glory; Two Objections; Eight Means"),
        (2026, 2114, "The Holiness of God; Signs of Increasing Holiness"),
        (2115, 2176, "Comfort to All Who Have Real Holiness"),
        (2177, 10**9, "Positions concerning Holiness")]),
]
# Volumen 5: The Golden Key (1675), Paradise Opened (1675) y A Word in Season (1675). La tercera
# alegación (431k), la décima (254k) y las doce maneras (218k) se cortan por sus subdivisiones.
GK = f"{BASE}/La Llave De Oro Para Abrir Tesoros Escondidos"
PO = f"{BASE}/El Paraíso Abierto"
WS = f"{BASE}/Una Palabra A Tiempo"
V5 = [
    pieza(1, 176, destino=GK, fecha="1675-01-01", id="0", saltar=1, titulo_original="The Golden Key: The Epistle Dedicatory and To the Reader"),
    pieza(177, 465, destino=GK, fecha="1675-01-01", id="I", saltar=1,
          titulo_original="The Golden Key: The First Question, Remedies against Cherishing Any Secret Sin"),
    *tramos(GK, "1675-01-01", 2, [
        (466, 593, "The Golden Key: The Second and Third Questions"),
        (594, 680, "The Golden Key: The First and Second Pleas"),
        (681, 836, "The Third Plea: The Obedience of Christ and His Death on the Cross"),
        (837, 934, "The Third Plea: The Sufferings of Christ in His Soul"),
        (935, 1034, "The Third Plea: Uses of the Sufferings of Christ"),
        (1035, 1088, "The Third Plea: If There Be a Hell"),
        (1089, 1198, "The Third Plea: The Eternal Deity of Christ"),
        (1199, 1446, "The Third Plea: Christ Is God-Man"),
        (1447, 1502, "The Fourth Plea: From the Sufferings of Christ"),
        (1503, 1540, "The Fifth Plea: From the Imputed Righteousness of Christ"),
        (1541, 1607, "The Fifth Plea: Comforts from the Imputed Righteousness of Christ"),
        (1608, 1641, "The Sixth and Seventh Pleas")]),
    pieza(1642, 1840, destino=PO, fecha="1675-01-01", id="0", saltar=1, titulo_original="Paradise Opened: The Epistle Dedicatory"),
    pieza(1841, 1922, destino=PO, fecha="1675-01-01", id="I", saltar=1,
          titulo_original="Paradise Opened: The Eighth Plea, the Covenant of Grace; Seven Premises"),
    *tramos(PO, "1675-01-01", 2, [
        (1923, 2052, "Paradise Opened: The Covenant of Grace; the Ninth Plea"),
        (2053, 2144, "The Tenth Plea: The Covenant of Redemption Proved from Scripture"),
        (2145, 2188, "The Tenth Plea: Propositions concerning the Covenant of Redemption"),
        (2189, 2250, "The Tenth Plea: The Articles of the Covenant of Redemption"),
        (2251, 2341, "The Tenth Plea: Uses of the Covenant of Redemption"),
        (2342, 2405, "The Eleventh Plea: From the Book of Life")]),
    pieza(2406, 2595, destino=WS, fecha="1675-01-01", id="0", saltar=1, titulo_original="A Word in Season: A General Epistle to All Suffering Saints"),
    pieza(2596, 2652, destino=WS, fecha="1675-01-01", id="I", saltar=1, titulo_original="A Word in Season: Some Words of Counsel to a Dear Friend"),
    pieza(2653, 2708, destino=WS, fecha="1675-01-01", id="II", saltar=1, versiculo="unido",
          titulo_original="A Word in Season: The Signal Presence of God with His People; Six Kinds of His Presence"),
    *tramos(WS, "1675-01-01", 3, [
        (2709, 2786, "A Word in Season: Ways in Which the Lord Manifests His Signal Presence (1-11)"),
        (2787, 2836, "A Word in Season: If God Be with Us, Who Can Be against Us? (1-14)"),
        (2837, 2948, "A Word in Season: If God Be with Us, Who Can Be against Us? (15-17)"),
        (2949, 3015, "A Word in Season: Ten Reasons Why God Will Be Present with His People"),
        (3016, 3103, "A Word in Season: The Application of This Truth"),
        (3104, 3228, "A Word in Season: Things to Be Shunned and Practised")]),
]
# Volumen 6: London's Lamentations (1670, ~1M caracteres, cortada por sus puntos numerados) y seis
# obras breves (un sermón con su epístola cada una).
LL = f"{BASE}/Las Lamentaciones De Londres"
GD = f"{BASE}/El Glorioso Día De La Aparición De Los Santos"
DP = f"{BASE}/El Deleite De Dios En El Progreso De Los Rectos"
HD = f"{BASE}/Los Hipócritas Descubiertos"
BL = f"{BASE}/El Último Día Del Creyente Es Su Mejor Día"
HC = f"{BASE}/Un Cordial Celestial"
LM = f"{BASE}/El Legado De Una Madre Moribunda"
V6 = [
    pieza(1, 71, destino=LL, fecha="1670-01-01", id="0", saltar=1, titulo_original="London's Lamentations: The Epistle Dedicatory"),
    pieza(72, 197, destino=LL, fecha="1670-01-01", id="I", saltar=1, versiculo="unido",
          titulo_original="London's Lamentations: The Text Opened; Fire as a Symbol; Ends of God in Judgments"),
    *tramos(LL, "1670-01-01", 2, [
        (198, 263, "Ends of God in Judgments on His Own People"),
        (264, 360, "Seven Sins among the Professing People; Sins That Bring the Fiery Judgment (1-2)"),
        (361, 430, "Sins That Bring the Fiery Judgment (3-6)"),
        (431, 498, "Sins That Bring the Fiery Judgment (7-8)"),
        (499, 749, "Sins That Bring the Fiery Judgment (9-13)"),
        (750, 849, "Use 1: To See the Hand of the Lord in the Fire"),
        (850, 904, "Use 2: Lamentation and Mourning"),
        (905, 1002, "Thirteen Supports for Those Who Have Lost All (1-7)"),
        (1003, 1118, "Thirteen Supports for Those Who Have Lost All (8-13)"),
        (1119, 1223, "Material Fire in Hell"),
        (1224, 1333, "Sixteen Duties of Those Who Have Been Burned Up (1-2)"),
        (1334, 1389, "Sixteen Duties of Those Who Have Been Burned Up (3-8)"),
        (1390, 1535, "Sixteen Duties of Those Who Have Been Burned Up (9)"),
        (1536, 1649, "Sixteen Duties of Those Who Have Been Burned Up (10-15)"),
        (1650, 1976, "The Sixteenth Duty: To Sanctify the Sabbath"),
        (1977, 2027, "Eight Duties of Those Whose Habitations Are Still Standing")]),
    pieza(2028, 2067, destino=GD, fecha="1648-01-01", id="0", saltar=1, titulo_original="The Glorious Day of the Saints' Appearance: The Epistle Dedicatory"),
    pieza(2068, 2199, destino=GD, fecha="1648-01-01", id="I", saltar=1, versiculo="unido", titulo_original="Christ Is the Life of Believers"),
    pieza(2200, 2241, destino=DP, fecha="1649-01-01", id="0", saltar=1, titulo_original="God's Delight in the Progress of the Upright: The Epistle Dedicatory"),
    pieza(2242, 2474, destino=DP, fecha="1649-01-01", id="I", saltar=1, versiculo="unido", titulo_original="God's Delight in the Progress of the Upright"),
    pieza(2475, 2537, destino=HD, fecha="1650-01-01", id="0", saltar=1, titulo_original="Hypocrites Detected: The Epistle Dedicatory"),
    pieza(2538, 2631, destino=HD, fecha="1650-01-01", id="I", saltar=1, versiculo="unido",
          titulo_original="A Sermon Preached before the Parliament on Their Day of Thanksgiving for Their Victory over the Scots"),
    pieza(2632, 2697, destino=BL, fecha="1652-01-01", id="0", saltar=1, titulo_original="A Believer's Last Day Is His Best Day: The Epistle Dedicatory"),
    pieza(2698, 2823, destino=BL, fecha="1652-01-01", id="I", saltar=1, titulo_original="A Saint's Last Day Is His Best Day"),
    pieza(2824, 3054, destino=HC, fecha="1665-01-01", id="I", saltar=1, titulo_original="A Heavenly Cordial"),
    pieza(3055, 3122, destino=LM, fecha="1673-01-01", id="0", saltar=1, titulo_original="The Legacy of a Dying Mother: The Epistle Dedicatory"),
    pieza(3123, 10**9, destino=LM, fecha="1673-01-01", id="I", saltar=1, titulo_original="A True Relation of Some of the Experiences of Mrs Susanna Bell"),
]
PIEZAS = {"1": V1, "2": V2, "3": V3, "4": V4, "5": V5, "6": V6}[VOL]

def parrafos(lineas):
    t = "\n".join(lineas)
    return [p.strip() for p in re.split(r"\n\s*\n", t) if p.strip()]

def notas_aparte(ps):
    out = []
    for p in ps:
        if p.startswith("__________"):
            out.extend(l.strip() for l in p.split("\n")[1:] if l.strip())
        else:
            out.append(p)
    return out

L = io.open(ORIG, encoding="utf-8").read().split("\n")
todas = []
for pz in PIEZAS:
    fin = min(pz["fin"], len(L))
    if "grupo" in pz:
        g0, g1 = pz["grupo"]
        cab = parrafos(L[g0 - 1:g1])
        ps = notas_aparte(parrafos(L[pz["ini"] - 1:fin]))
        ps = ps[:1] + cab + ps[1:]
    else:
        ps = notas_aparte(parrafos(L[pz["ini"] - 1:fin]))
    todas.append(ps)

# Reparto de notas: cuando un capítulo largo se corta en varias piezas, su bloque de notas queda
# en la última. Cada nota se mueve, al final, a la pieza donde está su llamada [n] en el texto.
RE_NOTA = re.compile(r"^\[(\d+)\]")
llamada = {}
for i, ps in enumerate(todas):
    for p in ps:
        if RE_NOTA.match(p): continue
        for n in re.findall(r"\[(\d+)\]", p): llamada.setdefault(n, i)
nuevas = [[] for _ in todas]
recibidas = [[] for _ in todas]
movidas = 0
for i, ps in enumerate(todas):
    for p in ps:
        m = RE_NOTA.match(p)
        j = llamada.get(m.group(1), i) if m else i
        if j != i: recibidas[j].append(p); movidas += 1
        else: nuevas[i].append(p)
todas = [a + sorted(b, key=lambda p: int(RE_NOTA.match(p).group(1))) for a, b in zip(nuevas, recibidas)]
print("notas movidas a la pieza de su llamada:", movidas)

texto, plan = [], []
for pz, ps in zip(PIEZAS, todas):
    texto.append("@@SERMON@@\n\n" + "\n\n".join(ps))
    plan.append(dict({k: pz.get(k) for k in ("destino", "fecha", "id", "saltar", "versiculo", "titulo_original")}, inicio=ps[0][:100]))

import os
os.makedirs(SALIDA, exist_ok=True)
io.open(f"{SALIDA}/original-marcado.txt", "w", encoding="utf-8", newline="\n").write("\n\n".join(texto) + "\n")
io.open(f"{SALIDA}/plan.json", "w", encoding="utf-8", newline="\n").write(json.dumps(plan, ensure_ascii=False, indent=1) + "\n")
print(len(PIEZAS), "piezas;", sum(len(t) for t in texto), "caracteres")
for p in plan: print(f"{p['destino'].split('/')[-1][:22]:22} {p['id']:8} {p['inicio'][:80]}")
