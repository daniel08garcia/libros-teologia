// Agrupa en lotes para el revisor los fragmentos de una serie que ya tienen
// .es.txt y .revision.json pero aún no tienen .correcciones.json ni "revisado".
// Solo incluye sermones con todos sus fragmentos traducidos.
// Uso: node temp/trabajo/cripplegate-lotes-revision.js <serie> [--max 15] [--parrafos 110]
const fs = require("fs");
const path = require("path");

const serie = +process.argv[2];
const arg = (n, d) => { const i = process.argv.indexOf(n); return i > 0 ? +process.argv[i + 1] : d; };
const MAX = arg("--max", 15), PAR = arg("--parrafos", 110);
if (!serie) { console.error("uso: node temp/trabajo/cripplegate-lotes-revision.js <serie>"); process.exit(1); }

for (let v = 1; v <= 6; v++) {
  const W = path.resolve("temp/trabajo", `cripplegate-vol${v}`);
  const m = JSON.parse(fs.readFileSync(path.join(W, "manifiesto.json"), "utf8"));
  const ex = (k, e) => fs.existsSync(path.join(W, "fragmentos", k + e));
  const lotes = []; let cur = [], par = 0;
  for (const s of m.sermones) {
    if (s.serie !== serie || s.omitir) continue;
    if (!s.fragmentos.every((f) => ex(f.clave, ".es.txt"))) continue;
    for (const f of s.fragmentos) {
      if (f.revisado || ex(f.clave, ".correcciones.json") || !ex(f.clave, ".revision.json")) continue;
      if (cur.length && (cur.length >= MAX || par + f.parrafos > PAR)) { lotes.push(cur); cur = []; par = 0; }
      cur.push(f.clave); par += f.parrafos;
    }
  }
  if (cur.length) lotes.push(cur);
  for (const l of lotes) console.log(`vol${v}\t${l.length}\t${l.join(", ")}`);
}
