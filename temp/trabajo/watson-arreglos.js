// Arreglos globales de la traducción de Watson, después de "aplicar" y antes de "unir".
// - "1.º. Texto" -> "1.º Texto" (los traductores pusieron punto después del ordinal).
// - Correcciones puntuales (referencias del OCR, nombres, glosas agregadas, puntos perdidos).
// - Une los párrafos que el OCR partió a media frase (en el inglés y en el español a la vez).
// Uso: node temp/trabajo/watson-arreglos.js [--simular]
const fs = require("fs");
const path = require("path");
const F = "C:/www/libros-teologia/temp/trabajo/watson/fragmentos";
const simular = process.argv.includes("--simular");
const P = (t) => t.split(/\n\s*\n/).map((x) => x.trim()).filter(Boolean);
const leer = (k, l) => fs.readFileSync(path.join(F, `${k}.${l}.txt`), "utf8");
const escribir = (k, l, ps) => simular || fs.writeFileSync(path.join(F, `${k}.${l}.txt`), ps.join("\n\n") + "\n");

const PUNTUALES = [
  ["s54-f004", "Gén. i. 25.:", "Gén. l. 25:"],          // OCR: "Gen. i. 25" por "l. 25" (Gén. 50:25)
  ["s72-f018", "Barac", "Baruc"],                        // Jer. xlv. 5: Baruc (el original dice "Barak")
  ["s47-f001", "alchymy (una aleación)", "alquimia"],    // glosa agregada; alquimia = latón
  ["s83-f007", "no demoren", "no demoren."],             // el OCR perdió el punto
];
// Párrafos partidos a media frase: [clave, n] une el párrafo n con el n+1 (1-based).
const UNIR = [["s102-f001", 2], ["s74-f001", 5], ["s88-f005", 1], ["s94-f012", 2], ["s94-f016", 7]];

let ord = 0;
for (const f of fs.readdirSync(F).filter((x) => x.endsWith(".es.txt"))) {
  const k = f.slice(0, -7), t = leer(k, "es");
  const n = (t.match(/\.º\. /g) || []).length;
  if (!n) continue;
  ord += n;
  simular || fs.writeFileSync(path.join(F, f), t.replace(/\.º\. /g, ".º "));
}
console.log(`ordinales "º." corregidos: ${ord}`);

for (const [k, a, b] of PUNTUALES) {
  const t = leer(k, "es");
  const veces = t.split(a).length - 1;
  if (veces !== 1) { console.log(`!! ${k}: "${a}" aparece ${veces} veces`); continue; }
  simular || fs.writeFileSync(path.join(F, `${k}.es.txt`), t.replace(a, b));
  console.log(`${k}: ${a} -> ${b}`);
}

for (const [k, n] of UNIR) {
  const en = P(leer(k, "en")), es = P(leer(k, "es"));
  if (en.length !== es.length) { console.log(`!! ${k}: ${en.length} párrafos en inglés, ${es.length} en español`); continue; }
  console.log(`${k} ¶${n}: …${es[n - 1].slice(-40)} || ${es[n].slice(0, 40)}…`);
  for (const ps of [en, es]) ps.splice(n - 1, 2, `${ps[n - 1]} ${ps[n]}`);
  escribir(k, "en", en); escribir(k, "es", es);
}
