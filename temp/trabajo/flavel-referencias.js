// Quita los rangos de capítulo entero que e-Sword puso en lugar del versículo original:
// "Mark 9:1-50" (la cita era Marcos 9:24, pero el número de versículo se perdió) queda
// como "Marcos 9". Solo cambia un rango "C:1-N" (N >= 10) del español si el mismo rango
// aparece en el párrafo inglés correspondiente.
// Uso: node temp/trabajo/flavel-referencias.js temp/trabajo/flavel-<obra> [--simular]
"use strict";
const fs = require("fs");
const path = require("path");

const [dir] = process.argv.slice(2).filter((a) => !a.startsWith("--"));
const simular = process.argv.includes("--simular");
if (!dir) { console.error("uso: node temp/trabajo/flavel-referencias.js <trabajo> [--simular]"); process.exit(1); }

const carpeta = path.join(dir, "fragmentos");
const parrafos = (t) => t.replace(/\s+$/, "").split(/\n\s*\n/);
let total = 0, archivos = 0;
for (const f of fs.readdirSync(carpeta).filter((f) => f.endsWith(".es.txt")).sort()) {
  const es = path.join(carpeta, f);
  const en = es.replace(/\.es\.txt$/, ".en.txt");
  if (!fs.existsSync(en)) continue;
  const pEs = parrafos(fs.readFileSync(es, "utf8"));
  const pEn = parrafos(fs.readFileSync(en, "utf8"));
  let cambios = 0;
  const nuevos = pEs.map((p, i) => {
    const ingles = pEn[i] || "";
    return p.replace(/\b(\d+):1-(\d+)\b/g, (m, c, n) => {
      if (+n < 10 || !new RegExp(`\\b${c}:1-${n}\\b`).test(ingles)) return m;
      cambios++;
      return c;
    });
  });
  if (cambios) {
    archivos++; total += cambios;
    if (!simular) fs.writeFileSync(es, nuevos.join("\n\n") + "\n");
  }
}
console.log(`${simular ? "(simulación) " : ""}${total} referencias en ${archivos} fragmentos`);
