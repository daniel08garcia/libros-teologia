// Arreglos globales de Perkins vol. 1, después de "sermones.js aplicar" y antes de "unir".
// - Quita las notas de imprenta de las tablas plegadas («Place this Table betweene fol. …»),
//   en el inglés y en el español a la vez (los párrafos que solo son esa nota se borran).
// - Une los párrafos que el OCR partió a media frase (en el inglés y en el español a la vez).
// - Pasa a mayúscula inicial normal las capitulares del original («EN el primer…» -> «En el primer…»).
// Uso: node temp/trabajo/perkins1-arreglos.js [--simular]
const fs = require("fs");
const path = require("path");
const F = "C:/www/libros-teologia/temp/trabajo/perkins-v1/fragmentos";
const simular = process.argv.includes("--simular");
const P = (t) => t.split(/\n\s*\n/).map((x) => x.trim()).filter(Boolean);
const leer = (k, l) => P(fs.readFileSync(path.join(F, `${k}.${l}.txt`), "utf8"));
const escribir = (k, l, ps) => simular || fs.writeFileSync(path.join(F, `${k}.${l}.txt`), ps.join("\n\n") + "\n");

// [clave, párrafo (1-based), prefijo inglés, prefijo español]; prefijo null = borrar el párrafo entero
const TABLAS = [
  ["s36-f002", 36, "Place this Table betwixt the Fol.72. and 73. ", "Colóquese esta tabla entre los folios 72 y 73. "],
  ["s37-f003", 1, "Place this Table betweene fol. 74. and 75. ", "Colóquese esta tabla entre los folios 74 y 75: "],
  ["s57-f002", 15, "Place this Table betweene Fol. 106. and 107. ", "Colóquese esta tabla entre los folios 106 y 107. "],
  ["s54-f002", 6, null, null],
  ["s64-f002", 10, null, null],
];
// Párrafos partidos a media frase: [clave, n] une el párrafo n con el n+1 (1-based).
const UNIR = [
  ["s66-f003", 1], ["s92-f008", 1], ["s107-f001", 29], ["s202-f002", 1], ["s214-f001", 16],
  ["s214-f001", 8], ["s218-f001", 7], ["s223-f004", 1], ["s228-f001", 6],
];

// Las tablas y las uniones de una misma clave se aplican de la última a la primera,
// para que los números de párrafo de las anteriores no se muevan.
const ops = [
  ...TABLAS.map(([k, n, en, es]) => ({ k, n, tipo: "tabla", en, es })),
  ...UNIR.map(([k, n]) => ({ k, n, tipo: "unir" })),
].sort((a, b) => a.k.localeCompare(b.k) || b.n - a.n);

const cache = {};
const get = (k) => (cache[k] ||= { en: leer(k, "en"), es: leer(k, "es") });
for (const o of ops) {
  const d = get(o.k);
  if (d.en.length !== d.es.length) { console.log(`!! ${o.k}: ${d.en.length} párrafos en inglés, ${d.es.length} en español`); continue; }
  const i = o.n - 1;
  if (o.tipo === "tabla") {
    if (o.en === null) {
      if (!/^Place this Table/.test(d.en[i])) { console.log(`!! ${o.k} ¶${o.n}: no es la nota de la tabla`); continue; }
      console.log(`${o.k} ¶${o.n}: se borra «${d.es[i]}»`);
      d.en.splice(i, 1); d.es.splice(i, 1);
    } else {
      if (!d.en[i].startsWith(o.en) || !d.es[i].startsWith(o.es)) { console.log(`!! ${o.k} ¶${o.n}: el prefijo no coincide`); continue; }
      d.en[i] = d.en[i].slice(o.en.length); d.es[i] = d.es[i].slice(o.es.length);
      d.es[i] = d.es[i][0].toLocaleUpperCase("es") + d.es[i].slice(1);
      console.log(`${o.k} ¶${o.n}: nota de tabla quitada -> «${d.es[i].slice(0, 50)}…»`);
    }
  } else {
    console.log(`${o.k} ¶${o.n}: …${d.es[i].slice(-40)} || ${d.es[i + 1].slice(0, 40)}…`);
    for (const ps of [d.en, d.es]) ps.splice(i, 2, `${ps[i]} ${ps[i + 1]}`);
  }
}
for (const [k, d] of Object.entries(cache)) { escribir(k, "en", d.en); escribir(k, "es", d.es); }

// Capitulares: dos o más mayúsculas seguidas de minúscula al principio de un párrafo («EN el…», «THE…» no).
let cap = 0;
for (const f of fs.readdirSync(F).filter((x) => x.endsWith(".es.txt"))) {
  const k = f.slice(0, -7);
  const ps = leer(k, "es");
  let cambio = false;
  const nuevos = ps.map((p) => p.replace(/^(\p{Lu})(\p{Lu}+)(?=[\s,;:.]+\p{Ll})/u, (m, a, b) => {
    if (/^[IVXLCDM]+$/.test(m) || m.length > 12) return m;          // números romanos y siglas
    cambio = true; cap++;
    return a + b.toLocaleLowerCase("es");
  }));
  if (cambio) escribir(k, "es", nuevos);
}
console.log(`capitulares corregidas: ${cap}`);
