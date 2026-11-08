// Lista los lotes de traducción pendientes de una serie de Puritan Sermons.
// Cada lote tiene hasta 4 fragmentos seguidos del mismo sermón (no mezcla sermones).
// Uso: node temp/trabajo/cripplegate-lotes.js <serie> [--max 4] [--revisar]
// Con --revisar lista los fragmentos traducidos que esperan al revisor
// (tienen .es.txt y .revision.json, pero no .correcciones.json ni "revisado").
const fs = require("fs");
const path = require("path");

const serie = +process.argv[2];
const iMax = process.argv.indexOf("--max");
const MAX = iMax > 0 ? +process.argv[iMax + 1] : 4;
const REVISAR = process.argv.includes("--revisar");
const ex = (W, k, ext) => fs.existsSync(path.join(W, "fragmentos", k + ext));
if (!serie) { console.error("uso: node temp/trabajo/cripplegate-lotes.js <serie> [--max 4]"); process.exit(1); }

let n = 0, frags = 0;
for (let v = 1; v <= 6; v++) {
  const W = path.resolve("temp/trabajo", `cripplegate-vol${v}`);
  const m = JSON.parse(fs.readFileSync(path.join(W, "manifiesto.json"), "utf8"));
  for (const s of m.sermones) {
    if (s.serie !== serie || s.omitir) continue;
    const pend = s.fragmentos
      .map((f, i) => ({ ...f, i: i + 1 }))
      .filter((f) => REVISAR
        ? !f.revisado && ex(W, f.clave, ".es.txt") && ex(W, f.clave, ".revision.json") && !ex(W, f.clave, ".correcciones.json")
        : !ex(W, f.clave, ".es.txt"));
    for (let k = 0; k < pend.length; k += MAX) {
      const lote = pend.slice(k, k + MAX);
      n++; frags += lote.length;
      const enc = s.encabezado_en.replace(/\s+/g, " ").slice(0, 110);
      console.log(`${path.join(W, "fragmentos")}\t${s.autor}\t${s.fragmentos.length}\t${enc}\t${lote.map((f) => `${f.clave}:${f.parrafos}:${f.i}`).join(" ")}`);
    }
  }
}
console.error(`serie ${serie}: ${n} lotes, ${frags} fragmentos pendientes${REVISAR ? " de revisión" : ""}`);
