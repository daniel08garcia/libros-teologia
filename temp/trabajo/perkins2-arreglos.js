// Arreglos globales de Perkins vol. 2, después de "sermones.js aplicar" y antes de "unir".
// - Une los párrafos que el OCR partió a media frase (en el inglés y en el español a la vez),
//   dentro de un fragmento (UNIR) y entre dos fragmentos seguidos de la misma pieza (CRUZAR).
//   Si el primero termina en «pala-» la palabra se suelda sin espacio.
// - Separa los títulos «### …» que quedaron pegados al final de un párrafo (SEPARAR).
// - Quita restos del OCR al principio de un párrafo (QUITAR_INICIO).
// - Pasa a mayúscula inicial normal las capitulares del original («EN el primer…» -> «En el primer…»).
// Uso: node temp/trabajo/perkins2-arreglos.js [--simular]
const fs = require("fs");
const path = require("path");
const F = "C:/www/libros-teologia/temp/trabajo/perkins-v2/fragmentos";
const simular = process.argv.includes("--simular");
const P = (t) => t.split(/\n\s*\n/).map((x) => x.trim()).filter(Boolean);
const leer = (k, l) => P(fs.readFileSync(path.join(F, `${k}.${l}.txt`), "utf8"));
const escribir = (k, l, ps) => simular || fs.writeFileSync(path.join(F, `${k}.${l}.txt`), ps.join("\n\n") + "\n");

// [clave, n]: une el párrafo n con el n+1 (1-based)
const UNIR = [
  ["s11-f003", 1], ["s40-f010", 3], ["s41-f002", 5], ["s42-f006", 2], ["s52-f005", 1], ["s63-f005", 5],
  ["s63-f010", 1], ["s65-f001", 3], ["s69-f002", 3], ["s83-f008", 69], ["s89-f001", 8], ["s96-f006", 3],
  ["s97-f006", 3], ["s99-f008", 7],
];
// [clave, n, regex del inglés, regex del español]: quita ese resto al principio del párrafo n (antes de unir)
const QUITAR_INICIO = [["s69-f002", 4, /^A (?=the duty)/, null]];
// [clave A, clave B, arreglo del español]: el último párrafo de A sigue en el primero de B
const CRUZAR = [
  ["s27-f005", "s27-f006", (a, b) => `${a.replace(/el após-$/, "el apóstol:")} ${b.replace(/^…?stle,?\s*/, "")}`],
];
// [clave, n]: el párrafo n lleva pegado un «### título» que debe ir en su propio párrafo
const SEPARAR = [["s93-f007", 6]];

const cache = {};
const get = (k) => (cache[k] ||= { en: leer(k, "en"), es: leer(k, "es") });
const juntar = (a, b) => (/\p{Ll}-$/u.test(a) ? a.slice(0, -1) + b : `${a} ${b}`);
const check = (k) => {
  const d = get(k);
  if (d.en.length !== d.es.length) throw new Error(`${k}: ${d.en.length} párrafos en inglés, ${d.es.length} en español`);
  return d;
};

for (const [k, n, ren, res] of QUITAR_INICIO) {
  const d = check(k);
  for (const [ps, re] of [[d.en, ren], [d.es, res]]) {
    if (!re) continue;
    if (!re.test(ps[n - 1])) { console.log(`!! ${k} ¶${n}: no empieza con ${re}`); continue; }
    ps[n - 1] = ps[n - 1].replace(re, "");
  }
}
for (const [k, n] of SEPARAR.sort((a, b) => b[1] - a[1])) {
  const d = check(k);
  for (const ps of [d.en, d.es]) {
    const i = ps[n - 1].indexOf(" ### ");
    if (i < 0) throw new Error(`${k} ¶${n}: no tiene « ### »`);
    ps.splice(n - 1, 1, ps[n - 1].slice(0, i).trim(), ps[n - 1].slice(i + 1).trim());
  }
  console.log(`${k} ¶${n}: título separado -> «${d.es[n]}»`);
}
for (const [k, n] of UNIR.sort((a, b) => a[0].localeCompare(b[0]) || b[1] - a[1])) {
  const d = check(k);
  const i = n - 1;
  console.log(`${k} ¶${n}: …${d.es[i].slice(-40)} || ${d.es[i + 1].slice(0, 40)}…`);
  const guion = /\p{Ll}-$/u.test(d.en[i]);
  d.en.splice(i, 2, juntar(d.en[i], d.en[i + 1]));
  d.es.splice(i, 2, guion && /\p{Ll}-$/u.test(d.es[i]) ? d.es[i].slice(0, -1) + d.es[i + 1] : `${d.es[i]} ${d.es[i + 1]}`);
}
for (const [a, b, fes] of CRUZAR) {
  const A = check(a), B = check(b);
  const la = A.en.length - 1;
  if (/^\[\d+\]/.test(A.en[la])) throw new Error(`${a}: el último párrafo es una nota`);
  if (B.en.length < 2) throw new Error(`${b}: quedaría vacío`);
  A.en[la] = juntar(A.en[la], B.en.shift());
  A.es[la] = fes(A.es[la], B.es.shift());
  console.log(`${a} + ${b}: «…${A.es[la].slice(-120, -60)}…»`);
}
for (const [k, d] of Object.entries(cache)) { escribir(k, "en", d.en); escribir(k, "es", d.es); }

// Capitulares: dos o más mayúsculas seguidas de minúscula al principio de un párrafo.
let cap = 0;
for (const f of fs.readdirSync(F).filter((x) => x.endsWith(".es.txt"))) {
  const k = f.slice(0, -7);
  const ps = leer(k, "es");
  let cambio = false;
  const nuevos = ps.map((p) => p.replace(/^(\p{Lu})(\p{Lu}+)(?=[\s,;:.]+\p{Ll})/u, (m, a, b) => {
    if (/^[IVXLCDM]+$/.test(m) || m.length > 12) return m;
    cambio = true; cap++;
    return a + b.toLocaleLowerCase("es");
  }));
  if (cambio) escribir(k, "es", nuevos);
}
console.log(`capitulares corregidas: ${cap}`);
