// Prepara los originales de John Flavel a partir de temp/originales/writings-of-john-flavel.txt
// (compilación de e-Sword con muchas copias repetidas). Uso:
//   node temp/trabajo/flavel-preparar.js corazon
// Escribe temp/trabajo/flavel-<obra>/original-marcado.txt, listo para
//   node temp/scripts/sermones.js dividir <ese archivo> temp/trabajo/flavel-<obra> --multiple
"use strict";
const fs = require("fs");
const path = require("path");

const RAIZ = path.resolve(__dirname, "..", "..");
const ORIGINAL = path.join(RAIZ, "temp", "originales", "writings-of-john-flavel.txt");

/** Capítulos del archivo ("CHAPTER n: ...") como listas de párrafos con las líneas unidas. */
function capitulos() {
  const lineas = fs.readFileSync(ORIGINAL, "utf8").replace(/\r/g, "").split("\n");
  const C = {};
  let cur = null;
  for (let i = 0; i < lineas.length; i++) {
    const m = lineas[i].match(/^  CHAPTER (\d+): /);
    if (m) { cur = +m[1]; C[cur] = []; i++; continue; }
    if (cur && !/^={20,}$/.test(lineas[i])) C[cur].push(lineas[i]);
  }
  const P = {};
  for (const n in C)
    P[n] = C[n].join("\n").split(/\n\s*\n/).map((p) => p.replace(/\s+/g, " ").trim()).filter(Boolean);
  return P;
}

// ------------------------------------------------------------ Keeping the Heart
// El libro completo está en los capítulos 28, 29 y 30 (04.01a-c); los capítulos 31-61
// repiten ese mismo texto. El 30 se corta a mitad del motivo 9; el final sale del 33.
// Cada capítulo: [primer párrafo (1 = primero del libro), título inglés]. Los números
// son posiciones en el texto unido 28+29+30+cierre del 33.
const CORAZON = [
  [1, "Proverbs 4:23, The Text Explained"],
  [11, "Duties Included in Keeping the Heart"],
  [23, "Reasons Why this Should be the Great Business of Life"],
  [37, "Keeping the Heart in the Time of Prosperity"],
  [54, "Keeping the Heart in the Time of Adversity"],
  [66, "Keeping the Heart in the Time of Zion's Troubles"],
  [76, "Keeping the Heart in Time of Danger and Public Distraction"],
  [94, "Keeping the Heart in the Time of Outward Wants"],
  [114, "Keeping the Heart in the Time of Duty"],
  [126, "Keeping the Heart When We Receive Injuries and Abuses"],
  [137, "Keeping the Heart When We Meet With Great Trials"],
  [145, "Keeping the Heart When the Hour of Temptation Comes"],
  [153, "Keeping the Heart in the Time of Doubting and Spiritual Darkness"],
  [172, "Keeping the Heart When Sufferings for Religion are Laid on Us"],
  [180, "Keeping the Heart When Sickness Warns of Death Approaching"],
  [191, "A Special Warning to Hypocrites and Formal Professors"],
  [201, "A Special Encouragement to the People of God"],
  [203, "Ten Motives Exhorting to a Hearty Engagement in Keeping the Heart"],
];
// Párrafos que se quitan: encabezados resumidos con ". . ." que repiten el párrafo
// siguiente, el "I proceed," duplicado y la línea de motivos repetida.
const CORAZON_QUITAR = [36, 53, 65, 75, 93, 113, 136, 144, 152, 171, 179, 204];

function corazon(P) {
  const base = [...P[28], ...P[29], ...P[30]];
  const i = P[33].findIndex((p) => p.startsWith("9. If the people of God would diligently keep"));
  if (i < 0 || !base[base.length - 1].startsWith("9. If the people of God")) throw new Error("no se encontró el cierre");
  const libro = [...base.slice(0, -1), ...P[33].slice(i)];
  if (libro.length !== 217) throw new Error(`se esperaban 217 párrafos y hay ${libro.length}`);

  // El primer párrafo trae pegados el título, el versículo y el comienzo del texto.
  const m = libro[0].match(/^Proverbs 4:23, The Text Explained (“KEEP THY HEART.*?”)—Proverbs 4:23\. THE (heart of man.*)$/);
  if (!m) throw new Error("primer párrafo inesperado");
  const versiculo = m[1].replace(/“(.)(.*)”/, (_, a, b) => "“" + a + b.toLowerCase() + "”");
  libro[0] = `The ${m[2]}`;
  libro[190] = libro[190].replace(/: \. \. \.$/, ":"); // "I now proceed to improve and apply the subject: . . ."

  const salida = [];
  CORAZON.forEach(([ini, titulo], k) => {
    const fin = k + 1 < CORAZON.length ? CORAZON[k + 1][0] : libro.length + 1;
    salida.push("@@SERMON@@", titulo);
    if (k === 0) salida.push("Proverbs 4:23.", versiculo);
    for (let n = ini; n < fin; n++) if (!CORAZON_QUITAR.includes(n)) salida.push(libro[n - 1]);
  });
  return salida;
}

// ------------------------------------------------------- The Mystery of Providence
// Edición de Banner of Truth (1963): capítulos 85 (introducción del autor) a 100.
// El 96 y el 99 ("cont'd") continúan los capítulos 10 y 12; el 98 termina con un
// párrafo cortado que el 99 repite completo. El 101 (Publisher's Note) no es de Flavel.
const PROVIDENCIA = [
  "The Work of Providence for the Saints",
  "Our Birth and Upbringing",
  "The Work of Conversion",
  "Our Employment",
  "Family Affairs",
  "Preservation of the Saints from Evil",
  "The Work of Sanctification",
  "The Duty of Meditation on Providence",
  "How to Meditate on the Providence of God",
  "The Advantages of Meditating on Providence",
  "Practical Implications for the Saints",
  "Practical Problems in Connection with Providence",
  "The Advantages of Recording our Experiences of Providence",
];

function providencia(P) {
  const p98 = P[98].slice();
  const cortado = p98.pop();
  if (!/rises u$/.test(cortado) || !P[99][1].startsWith(cortado.slice(0, 80))) throw new Error("unión 98/99 inesperada");
  const libro = [...P[85], ...P[86], ...P[87], ...P[88], ...P[89], ...P[90], ...P[91], ...P[92], ...P[93],
    ...P[94], ...P[95], ...P[96], ...P[97], ...p98, ...P[99], ...P[100]].filter((p) => p !== "cont’d");

  const salida = [];
  const m = libro[0].match(/^Author’s Introduction (I will cry unto God most high; unto God that performeth all things for me) \(Psalms 57:2\) (The greatness .*)$/);
  if (!m) throw new Error("introducción inesperada");
  salida.push("@@SERMON@@", "Author’s Introduction", "Psalms 57:2.", `‘${m[1]}.’`, m[2]);
  let cap = 0;
  for (const p of libro.slice(1)) {
    const c = p.match(/^Chapter (\d+) (.*)$/);
    if (c) {
      const n = +c[1], titulo = PROVIDENCIA[n - 1];
      if (n !== cap + 1 || !c[2].startsWith(titulo)) throw new Error(`capítulo inesperado: ${p.slice(0, 80)}`);
      cap = n;
      salida.push("@@SERMON@@", titulo);
      const resto = c[2].slice(titulo.length).trim();
      if (resto) salida.push(resto);
      continue;
    }
    salida.push(p);
  }
  if (cap !== 13) throw new Error(`se esperaban 13 capítulos y hay ${cap}`);
  return salida;
}

// --------------------------------------------------------- Communion with Christ
// Líneas 9825-11162 del archivo (dentro del capítulo 26, después de las obras de
// Samuel Shaw). Un solo tratado, sin capítulos ni texto bíblico.
function comunion() {
  const lineas = fs.readFileSync(ORIGINAL, "utf8").replace(/\r/g, "").split("\n").slice(9824, 11161);
  const ps = lineas.join("\n").split(/\n\s*\n/).map((p) => p.replace(/\s+/g, " ").trim()).filter(Boolean)
    .filter((p) => !/^={20,}$/.test(p));
  if (ps[0] !== "COMMUNION WITH CHRIST, BY THE REV. JOHN FLAVEL.") throw new Error("inicio inesperado");
  // "“ Make me…" → "“Make me…": espacio sobrante después de la comilla de apertura.
  return ["@@SERMON@@", "Communion with Christ", ...ps.slice(1).map((p) => p.replace(/“ /g, "“"))];
}

// ----------------------------------------------------------- The Method of Grace
// Capítulos 63-83: 21 sermones (edición abreviada). Cada uno empieza con el título,
// a veces un subtítulo, y el versículo entre comillas seguido de la referencia (y a
// veces del comienzo del texto en el mismo párrafo).
const RE_VERSICULO = /^"(.+)"\s+((?:[123] )?[A-Z][a-z]+(?: of Solomon)? \d+:\d+(?:-\d+)?)\.?\s*(.*)$/;

function gracia(P) {
  const salida = [];
  for (let n = 63; n <= 83; n++) {
    const ps = P[n].slice();
    const titulo = ps.shift();
    let sub = null;
    if (!ps[0].startsWith('"')) sub = ps.shift();
    let v = ps.shift();
    if (n === 78) v = `${v} ${ps.shift()}`; // el versículo viene partido en dos párrafos
    const m = v.match(RE_VERSICULO);
    if (!m) throw new Error(`capítulo ${n}: versículo inesperado: ${v.slice(0, 120)}`);
    let ref = m[2];
    if (n === 81) ref = ref.replace("1 John 11:6", "1 John 2:6"); // errata del original
    salida.push("@@SERMON@@", titulo, `${ref}.`, `“${m[1]}”`);
    if (sub) salida.push(sub);
    if (m[3]) salida.push(m[3]);
    salida.push(...ps);
  }
  return salida;
}

// ------------------------------------------------------------ The Fountain of Life
// 42 sermones repartidos entre los capítulos "S." (102-173) en orden alfabético, varios
// en dos o tres copias casi idénticas. Los sermones 1-9 traen número; el resto va en el
// orden del libro: oficios de Cristo, humillación, muerte, siete palabras y exaltación.
// Copias elegidas: las más completas (la 133 omite párrafos de la 137) y, para 6-9,
// las del mismo formato que 10-42.
const FUENTE = [137, 135, 131, 132, 117, 140, 150, 148, 155, 160, 147, 141, 103, 152, 143, 145, 144,
  149, 107, 108, 163, 168, 156, 161, 109, 165, 146, 158, 159, 142, 162, 167, 157, 153, 166, 164,
  172, 106, 173, 138, 139, 105];
const RE_REF = String.raw`(?:[123] )?[A-Z][a-z]+(?: of Solomon)? \d+:\d+(?:[-–]\d+)?(?:, etc\.)?`;
const sinRaya = (p) => p.replace(/^_{5,}\s*/, "").replace(/\s*_{5,}$/, "");

/** Separa el encabezado de los sermones 1-5 (formatos distintos en cada copia). */
function encabezadoAntiguo(n, ps) {
  const f = (re, p) => { const m = p.match(re); if (!m) throw new Error(`sermón ${n}: encabezado inesperado: ${p.slice(0, 100)}`); return m; };
  switch (n) {
    case 1: { const m = f(/^(1 Corinthians 2:2) (For I determined .*)$/, ps[3]);
      return { titulo: "Opens the Excellency of the Subject", ref: m[1], verso: m[2], resto: ps.slice(4) }; }
    case 2: if (ps[2] !== "Proverbs 8:30.") throw new Error("sermón 2");
      return { titulo: "Sets forth Christ in his Essential and Primeval Glory", ref: "Proverbs 8:30", verso: ps[3], resto: ps.slice(4) };
    case 3: f(/Isaiah 53:12\.$/, ps[1]);
      return { titulo: "Opens the Covenant of Redemption betwixt the Father and the Redeemer", ref: "Isaiah 53:12", verso: ps[2], resto: ps.slice(3) };
    case 4: { const m = f(/John 3:16\. (For GOD so loved .*)$/, ps[1]);
      return { titulo: "Opens the Admirable Love of God in Giving his own Son for us", ref: "John 3:16", verso: m[1].replace(/GOD/g, "God").replace(/SON/g, "Son"), resto: ps.slice(2) }; }
    case 5: { const m = f(/John 1:14\. (And the Word was made Flesh, and dwelt among us) ?, &c/, ps[0]);
      return { titulo: "Of Christ’s Wonderful Person", ref: "John 1:14", verso: `${m[1]}, &c.`, resto: ps.slice(1) }; }
  }
}

function fuente(P) {
  const salida = [];
  FUENTE.forEach((cap, i) => {
    let ps = P[cap].map(sinRaya).filter((p) => p && !/^Source: https?:/.test(p));
    if (cap === 109) {
      // El capítulo trae el sermón completo dos veces seguidas.
      const k = ps.findIndex((p, j) => j > 0 && p === ps[0]);
      if (k < 0) throw new Error("109: no se encontró la repetición");
      ps = ps.slice(0, k);
    }
    let e;
    if (i < 5) e = encabezadoAntiguo(i + 1, ps);
    else {
      const unido = ps[0].match(new RegExp(String.raw`^(.*?)\s+"(.+)"\s+(${RE_REF})\.?\s*(.*)$`));
      if (unido) e = { titulo: unido[1], verso: unido[2], ref: unido[3], resto: [unido[4], ...ps.slice(1)] };
      else {
        const m = ps[1].match(new RegExp(String.raw`^"(.+)"\s+(${RE_REF})\.?\s*(.*)$`));
        if (!m) throw new Error(`capítulo ${cap}: versículo inesperado: ${ps[1].slice(0, 100)}`);
        e = { titulo: ps[0], verso: m[1], ref: m[2], resto: [m[3], ...ps.slice(2)] };
      }
    }
    let ref = e.ref.replace(/^Php /, "Philippians ");
    if (cap === 106) ref = ref.replace("John 9:40-41", "John 19:40-42"); // errata: el entierro es Juan 19:40-42
    salida.push("@@SERMON@@", e.titulo, ref.endsWith(".") ? ref : `${ref}.`, `“${e.verso}”`, ...e.resto.filter(Boolean));
  });
  return salida;
}

// --------------------------------------------------------------- Piezas menores
// Para la carpeta "Tratados": Reply to Hyper-Calvinism (113), Evil Effects of Unbelief
// (112), las preguntas sueltas de la exposición del Catecismo Menor (en orden de
// pregunta, como un solo texto con un subtítulo por pregunta) y Life of Flavel (115).
// Vindication (103) ya está en Fountain of Life (sermón 13); Christian View of Death
// (110) es un extracto de Keeping the Heart.
const CATECISMO = [
  [171, "Of the Chief End of Man"], [170, "Of the Rule of Faith"], [169, "What the Scriptures Principally Teach"],
  [124, "Of God’s Holiness"], [125, "Of Three Persons in the Godhead"], [123, "Of Divine Providence"],
  [119, "Of Christ’s Incarnation"], [127, "Of the Manner of Christ’s Incarnation"],
  [121, "Of Christ’s Prophetical Office"], [120, "Of Christ’s Kingly Office"], [118, "Of Christ’s Humiliation"],
];
const PREFIJO_CAT = /^(Westminster Shorter Catechism Project )?(An Exposition of the Assembly’s Shorter Catechism by John Flavel )?/;

function menores(P) {
  const salida = [];
  // Reply to Baptist Hyper-Calvinism: cuatro párrafos de encabezado.
  if (!/^\(Excerpt\)$/.test(P[113][3])) throw new Error("113: encabezado inesperado");
  salida.push("@@SERMON@@", "A Reply to Baptist Hyper-Calvinism", ...P[113].slice(4));
  // Evil Effects of Unbelief: el título y el versículo vienen juntos; la referencia, con el texto.
  const v = P[112][0].match(/^Evil Effects of Unbelief by John Flavel (“.*”)$/);
  const r = P[112][1].match(/^(Mark 4:40\.) (.*)$/);
  if (!v || !r) throw new Error("112: encabezado inesperado");
  salida.push("@@SERMON@@", "Evil Effects of Unbelief", r[1], v[1], r[2], ...P[112].slice(2));
  // Catecismo: un subtítulo por pregunta (se marca con "## " después de traducir).
  salida.push("@@SERMON@@", "An Exposition of the Assembly’s Shorter Catechism");
  for (const [cap, titulo] of CATECISMO) {
    const ps = P[cap].map((p, i) => (i === 0 ? p.replace(PREFIJO_CAT, "") : p));
    const sinTitulo = ps[0].replace(/^Of [^.?]*?(\.|(?= Q\.))\s*/, "");
    salida.push(titulo, ...(sinTitulo ? [sinTitulo] : []), ...ps.slice(1));
  }
  // Life of Flavel: biografía anónima que precede sus obras.
  const vida = P[115].filter((p) => !/www\.ccel\.org/.test(p));
  salida.push("@@SERMON@@", "The Life of the late Rev. Mr. John Flavel, Minister of Dartmouth", ...vida.slice(1));
  return salida;
}

// ----------------------------------------------------------------- Samuel Shaw
// El tomo de 1830 (ed. William Vint) que trae el archivo empieza con tres obras de
// Samuel Shaw (1635-1696): Immanuel (líneas 2875-8023: memorias del autor, prefacio y
// ocho capítulos), On Communion with God (8024-8917) y The Angelical Life (8918-9824).
function lineasComoParrafos(a, b) {
  return fs.readFileSync(ORIGINAL, "utf8").replace(/\r/g, "").split("\n").slice(a - 1, b)
    .filter((l) => !/^(={20,}|  CHAPTER )/.test(l)).join("\n")
    .split(/\n\s*\n/).map((p) => p.replace(/\s+/g, " ").trim()).filter(Boolean);
}

function shawEmanuel() {
  const pre = lineasComoParrafos(2875, 3902);
  if (!/^IMMANUEL:/.test(pre[0]) || !/^Memoirs OF THE AUTHOR\. /.test(pre[2]) || pre[23] !== "PREFACE.")
    throw new Error("Immanuel: memorias o prefacio inesperados");
  const memorias = pre[2].replace(/^Memoirs OF THE AUTHOR\. /, "").replace("at Repton, in Derbyshire, in 1695", "at Repton, in Derbyshire, in 1635");
  // id 0: memorias y prefacio ("PREFACE." se marca con "## " después de traducir).
  const salida = ["@@SERMON@@", "Memoirs of the Author and Preface", memorias, ...pre.slice(3)];
  const caps = lineasComoParrafos(3903, 8023);
  let n = 0;
  for (const p of caps) {
    const m = p.match(/^CHAP\. ?[IVX]+\.? ?(.*)$/);
    if (m) { n++; salida.push("@@SERMON@@", `Chapter ${n}`); if (m[1]) salida.push(m[1]); continue; }
    salida.push(p);
  }
  if (n !== 8) throw new Error(`Immanuel: se esperaban 8 capítulos y hay ${n}`);
  return salida;
}

function shawTratados() {
  const com = lineasComoParrafos(8024, 8917);
  const ang = lineasComoParrafos(8918, 9824);
  if (com[1] !== "1 John 1:3." || ang[1] !== "Matthew 22:30." || !/^ever\. THE ANGELICAL LIFE/.test(ang[0]))
    throw new Error("Shaw: encabezados inesperados");
  com[com.length - 1] += " ever."; // la última palabra quedó pegada al título siguiente
  const v = ang[2].match(/^’— “ (Are as the angels of God in heaven\.) (.*)$/);
  if (!v) throw new Error("Angelical Life: versículo inesperado");
  return [
    "@@SERMON@@", "On Communion with God", "1 John 1:3.", "“Our fellowship is with the Father, and with his Son Jesus Christ.”", ...com.slice(3),
    "@@SERMON@@", "The Angelical Life", "Matthew 22:30.", `“${v[1]}”`, v[2], ...ang.slice(3),
  ];
}

// -------------------------------------------------------------- Ziekentroost
// Capítulo 111 (líneas 53449-53854): The Consolation of the Sick, de Cornelis van Hille
// (1571). e-Sword metió las referencias del margen en medio de las frases, muchas con un
// rango de capítulo entero ("1 Peter 1:1-25," antes de "1 Peter 1:24"). Aquí se marcan
// entre corchetes para que el traductor las ponga al final de su cita, se quitan los
// rangos de capítulo entero y se corrigen las erratas.
const ZK_TEXTO = [
  ["out of this belly", "out of his belly"], ["but, but after", "but after"], ["his Luke 10:34 precious blood or our sins", "his Luke 10:34 precious blood for our sins"],
  ["unto Goad who", "unto God who"], ["law of Cod", "law of God"], ["He that hearth my", "He that heareth my"],
  ["them that live him", "them that love him"], ["strenghten", "strengthen"], ["coming up of the Lord", "coming of the Lord"],
  ["true man 17,3 to be", "true man John 17:3 to be"], ["Where I John 12, am there shall also my servant be: Again, He that heareth my 26 Word",
    "Where I am there shall also my servant be: John 12:26 Again, He that heareth my Word"],
  ["ye sorrow 1 Thess. not even", "ye sorrow not even"], ["Tit.2:24", "Titus 2:14"], ["Acts 7:26", "Acts 17:26"],
  ["Romans 5:18 much more", "Romans 5:10 much more"], ["the Matthew 3:3 kingdom", "the John 3:3 kingdom"],
  ["Therefore we Hebrews 2:4 conclude", "Habakkuk 2:4 Therefore we conclude"], ["1 Corinthians 12:1-31, face", "face"],
  ["1 Corinthians 12:12", "1 Corinthians 13:12"], ["Psalms 34:1, Psalms 34:4", "Psalms 84:1, Psalms 84:4"],
];
const ZK_REF = /(?:[123] )?(?:[A-Z][a-z]+|Php) \d+:\d+(?:-\d+)?/g;

function ziekentroost() {
  let ps = lineasComoParrafos(53449, 53854);
  if (!/^The Consolation of the Sick/.test(ps[0]) || !/love of$/.test(ps[9]) || !/^Christ\? Shall/.test(ps[10]))
    throw new Error("Ziekentroost: estructura inesperada");
  ps.splice(9, 2, `${ps[9]} ${ps[10]}`); // salto de página a mitad de frase
  ps = ps.map((p) => {
    for (const [a, b] of ZK_TEXTO) p = p.split(a).join(b);
    // Rangos "C:1-N": en la frase ("in Psalms 42:1-11") quedan como capítulo; si no, se quitan.
    // Si el párrafo no trae otra cita de ese capítulo, queda el capítulo solo ("Job 19").
    p = p.replace("together with them in 2 Corinthians 5:1-21, the clouds", "together with them in the clouds 2 Corinthians 5:1-21");
    const original = p;
    p = p.replace(/(\bin )?((?:[123] )?(?:[A-Z][a-z]+|Php) (\d+)):1-(\d+)(,?)/g, (m, enLaFrase, libroCap, c, n, coma) => {
      if (+n < 10) return m;
      if (enLaFrase) return `${enLaFrase}${libroCap.replace(/^Psalms/, "Psalm")}${coma}`;
      const otra = new RegExp(`${libroCap}:(?!1-${n}\\b)\\d`).test(original);
      return otra ? "" : `[${libroCap}] `;
    });
    p = p.replace(ZK_REF, (r) => `[${r.replace(/^Php /, "Philippians ")}]`)
      .replace(/\](?:\s*,)?\s*\[/g, "; ") // referencias seguidas en un solo corchete
      .replace(/ {2,}/g, " ").replace(/ ,/g, ",");
    return p;
  });
  const resto = ps.slice(1);
  return ["@@SERMON@@", "The Consolation of the Sick",
    "## Which is an Instruction in Faith, and the Way of Salvation to prepare Believers to die willingly", ...resto];
}

const OBRAS = { corazon, providencia, comunion, gracia, fuente, menores, "shaw-emanuel": shawEmanuel, "shaw-tratados": shawTratados, ziekentroost };

const obra = process.argv[2];
if (!OBRAS[obra]) {
  console.error(`uso: node temp/trabajo/flavel-preparar.js <${Object.keys(OBRAS).join("|")}>`);
  process.exit(1);
}
const ps = OBRAS[obra](capitulos());
const dir = path.join(RAIZ, "temp", "trabajo", obra.startsWith("shaw") || obra === "ziekentroost" ? obra : `flavel-${obra}`);
fs.mkdirSync(dir, { recursive: true });
fs.writeFileSync(path.join(dir, "original-marcado.txt"), ps.join("\n\n") + "\n");
console.log(`${ps.filter((p) => p === "@@SERMON@@").length} capítulos, ${ps.length} párrafos -> ${path.relative(RAIZ, dir)}/original-marcado.txt`);
