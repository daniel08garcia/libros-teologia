// Unifica las comillas de las traducciones de Flavel: «…» en el primer nivel y “…” dentro.
// Uso: node temp/trabajo/flavel-comillas.js temp/trabajo/flavel-<obra> [--simular]
// Trabaja sobre fragmentos/*.es.txt. Las comillas rectas (") se toman como de apertura
// si van al inicio o después de espacio, paréntesis o raya. Un párrafo con comillas
// desequilibradas se deja igual y se informa. Las comillas simples ‘ ’ no se tocan
// (’ también es apóstrofo).
"use strict";
const fs = require("fs");
const path = require("path");

const [dir] = process.argv.slice(2).filter((a) => !a.startsWith("--"));
const simular = process.argv.includes("--simular");
if (!dir) { console.error("uso: node temp/trabajo/flavel-comillas.js <trabajo> [--simular]"); process.exit(1); }

function normalizar(p) {
  let prof = 0, out = "";
  for (let i = 0; i < p.length; i++) {
    const c = p[i];
    let abre = null;
    if (c === "«" || c === "“") abre = true;
    else if (c === "»" || c === "”") abre = false;
    else if (c === '"') abre = i === 0 || /[\s(\[—–«“]/.test(p[i - 1]);
    if (abre === null) { out += c; continue; }
    if (abre) { prof++; out += prof === 1 ? "«" : "“"; }
    else { if (prof === 0) return null; out += prof === 1 ? "»" : "”"; prof--; }
  }
  return prof === 0 ? out : null;
}

const carpeta = path.join(dir, "fragmentos");
let cambiados = 0, parrafos = 0;
for (const f of fs.readdirSync(carpeta).filter((f) => f.endsWith(".es.txt")).sort()) {
  const ruta = path.join(carpeta, f);
  const ps = fs.readFileSync(ruta, "utf8").replace(/\s+$/, "").split(/\n\s*\n/);
  let toco = false;
  const nuevos = ps.map((p, i) => {
    const n = normalizar(p);
    if (n === null) { console.log(`${f} párrafo ${i + 1}: comillas desequilibradas, se deja igual`); return p; }
    if (n !== p) { toco = true; parrafos++; }
    return n;
  });
  if (toco) { cambiados++; if (!simular) fs.writeFileSync(ruta, nuevos.join("\n\n") + "\n"); }
}
console.log(`${simular ? "(simulación) " : ""}${parrafos} párrafos en ${cambiados} fragmentos`);
