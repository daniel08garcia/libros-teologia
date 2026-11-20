// Ayudante del flujo de Brooks (copiado de la sesión del vol. 2). Entrega los siguientes N lotes (de hasta 4 fragmentos, en orden) sin .es.txt ni lanzados,
// y los anota en lanzados.txt. Uso: node siguiente.js <vol> <N> [--revisar]
const fs = require("fs");
const path = require("path");
const [vol, N] = [process.argv[2], +process.argv[3]];
const REV = process.argv.includes("--revisar");
const W = path.resolve("C:/www/libros-teologia/temp/trabajo", `brooks-v${vol}`);
const reg = path.join("C:/Users/danie/AppData/Local/Temp/claude/915236ca87cdeb46/28afd549-119e-4e81-aa7f-e14490273c02/scratchpad", `lanzados-v${vol}${REV ? "-rev" : ""}.txt`);
const hechos = new Set(fs.existsSync(reg) ? fs.readFileSync(reg, "utf8").split(/\s+/).filter(Boolean) : []);
const ex = (k, e) => fs.existsSync(path.join(W, "fragmentos", k + e));
const m = JSON.parse(fs.readFileSync(path.join(W, "manifiesto.json"), "utf8"));
const pend = [];
for (const s of m.sermones) for (const f of s.fragmentos) {
  if (hechos.has(f.clave)) continue;
  if (REV ? (!ex(f.clave, ".es.txt") || !ex(f.clave, ".revision.json") || ex(f.clave, ".correcciones.json") || f.revisado) : ex(f.clave, ".es.txt")) continue;
  pend.push(f.clave);
}
const T = REV ? 6 : 4, out = [];
for (let i = 0; i < pend.length && out.length < N; i += T) out.push(pend.slice(i, i + T));
fs.appendFileSync(reg, out.flat().join(" ") + "\n");
for (const l of out) console.log(l.join(" "));
console.error(`${pend.length} pendientes antes de este reparto`);
