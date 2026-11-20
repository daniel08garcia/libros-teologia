// Lista los lotes pendientes de un volumen de Brooks.
// Traducción: hasta --max (4) fragmentos seguidos del mismo sermón, sin mezclar sermones.
// Con --revisar: fragmentos traducidos que esperan al revisor (tienen .es.txt y .revision.json,
// pero no .correcciones.json ni "revisado"), en lotes de hasta --max (6) del mismo sermón.
// Uso: node temp/trabajo/brooks-lotes.js <vol> [--max N] [--revisar] [--excluir s01-f001,s01-f002]
const fs = require("fs");
const path = require("path");

const vol = process.argv[2];
const arg = (n) => { const i = process.argv.indexOf(n); return i > 0 ? process.argv[i + 1] : null; };
const REVISAR = process.argv.includes("--revisar");
const MAX = +(arg("--max") || (REVISAR ? 6 : 4));
const EXCL = new Set((arg("--excluir") || "").split(",").filter(Boolean));
const W = path.resolve("temp/trabajo", `brooks-v${vol}`);
const ex = (k, ext) => fs.existsSync(path.join(W, "fragmentos", k + ext));
const m = JSON.parse(fs.readFileSync(path.join(W, "manifiesto.json"), "utf8"));

let n = 0, frags = 0;
for (const s of m.sermones) {
  if (s.omitir) continue;
  const pend = s.fragmentos.filter((f) => !EXCL.has(f.clave) && (REVISAR
    ? !f.revisado && ex(f.clave, ".es.txt") && ex(f.clave, ".revision.json") && !ex(f.clave, ".correcciones.json")
    : !ex(f.clave, ".es.txt")));
  for (let k = 0; k < pend.length; k += MAX) {
    const lote = pend.slice(k, k + MAX);
    n++; frags += lote.length;
    console.log(lote.map((f) => f.clave).join(" "));
  }
}
console.error(`vol ${vol}: ${n} lotes, ${frags} fragmentos pendientes${REVISAR ? " de revisión" : ""}`);
