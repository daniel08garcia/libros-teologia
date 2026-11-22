// Entrega los siguientes N lotes de Watson (6 fragmentos para traducir o revisar, en orden)
// que no estén hechos ni ya lanzados, y los anota en temp/trabajo/watson/lanzados[-rev].txt.
// Uso: node temp/trabajo/watson-siguiente.js <N> [--revisar]
const fs = require("fs");
const path = require("path");
const N = +process.argv[2];
const REV = process.argv.includes("--revisar");
const W = path.resolve("C:/www/libros-teologia/temp/trabajo/watson");
const reg = path.join(W, `lanzados${REV ? "-rev" : ""}.txt`);
const hechos = new Set(fs.existsSync(reg) ? fs.readFileSync(reg, "utf8").split(/\s+/).filter(Boolean) : []);
const ex = (k, e) => fs.existsSync(path.join(W, "fragmentos", k + e));
const m = JSON.parse(fs.readFileSync(path.join(W, "manifiesto.json"), "utf8"));
const pend = [];
for (const s of m.sermones) {
  if (s.omitir) continue;
  for (const f of s.fragmentos) {
    if (hechos.has(f.clave)) continue;
    if (REV ? (!ex(f.clave, ".es.txt") || !ex(f.clave, ".revision.json") || ex(f.clave, ".correcciones.json") || f.revisado) : ex(f.clave, ".es.txt")) continue;
    pend.push(f.clave);
  }
}
const T = REV ? 10 : 6, out = [];
for (let i = 0; i < pend.length && out.length < N; i += T) out.push(pend.slice(i, i + T));
if (out.length) fs.appendFileSync(reg, out.flat().join(" ") + "\n");
for (const l of out) console.log(l.join(" "));
console.error(`${pend.length} pendientes antes de este reparto`);
