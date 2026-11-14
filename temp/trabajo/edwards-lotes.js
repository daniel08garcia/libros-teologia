// Lotes de traducción o revisión para The Works of Jonathan Edwards (una carpeta de trabajo por volumen).
// Imprime un prompt listo por lote y marca sus claves como lanzadas en <trabajo>/lanzados.json,
// para que la siguiente llamada no las repita mientras el agente trabaja.
//
//   node temp/trabajo/edwards-lotes.js <trabajo> [--n 20] [--max 5]            lotes de traducción
//   node temp/trabajo/edwards-lotes.js <trabajo> --revisar [--n 20] [--max 7]  lotes de revisión
//   node temp/trabajo/edwards-lotes.js <trabajo> --resumen                     avance, sin lanzar nada
//   node temp/trabajo/edwards-lotes.js <trabajo> --liberar                     olvida las claves lanzadas que no terminaron
//
// Traducción: pendiente = sin .es.txt. Revisión: pendiente = con .revision.json, sin .correcciones.json
// y sin "revisado" (solo fragmentos sin errores estructurales; "revisar" los marca).
// Un lote no mezcla obras.
const fs = require("fs");
const path = require("path");

const args = process.argv.slice(2);
const W = path.resolve(args[0] || "");
const opt = (k, d) => (args.includes("--" + k) ? +args[args.indexOf("--" + k) + 1] : d);
const REVISAR = args.includes("--revisar");
const N = opt("n", 20);
const MAX = opt("max", REVISAR ? 7 : 5);
const F = path.join(W, "fragmentos");
const ex = (k, ext) => fs.existsSync(path.join(F, k + ext));
const m = JSON.parse(fs.readFileSync(path.join(W, "manifiesto.json"), "utf8"));
const rutaLanz = path.join(W, "lanzados.json");
const lanz = fs.existsSync(rutaLanz) ? JSON.parse(fs.readFileSync(rutaLanz, "utf8")) : { traducir: [], revisar: [] };
const RAIZ = path.resolve(__dirname, "..", "..");
const INSTR = path.join(RAIZ, "temp", "trabajo", REVISAR ? "edwards-revisor.md" : "edwards-traductor.md");

const conErrores = (k) => {
  if (!ex(k, ".revision.json")) return false;
  const r = JSON.parse(fs.readFileSync(path.join(F, k + ".revision.json"), "utf8"));
  return (r.estructurales || []).length > 0;
};
const pendiente = (f) => REVISAR
  ? !f.revisado && ex(f.clave, ".es.txt") && ex(f.clave, ".revision.json") && !ex(f.clave, ".correcciones.json") && !conErrores(f.clave)
  : !ex(f.clave, ".es.txt");
const terminado = (k, modo) => (modo === "traducir" ? ex(k, ".es.txt") : ex(k, ".correcciones.json"));

if (args.includes("--liberar")) {
  for (const modo of ["traducir", "revisar"]) lanz[modo] = [];
  fs.writeFileSync(rutaLanz, JSON.stringify(lanz) + "\n");
  console.log("lanzados.json vaciado");
  process.exit(0);
}

const modo = REVISAR ? "revisar" : "traducir";
const yaLanz = new Set(lanz[modo]);
let totalPend = 0, totalTrad = 0, totalFr = 0, totalRev = 0;
const lotes = [];
for (const s of m.sermones) {
  if (s.omitir) continue;
  const tit = s.titulo_en_corto || s.encabezado_en.replace(/\s+/g, " ").slice(0, 60);
  const pend = s.fragmentos.map((f, i) => ({ ...f, i: i + 1 })).filter(pendiente);
  totalFr += s.fragmentos.length;
  totalTrad += s.fragmentos.filter((f) => ex(f.clave, ".es.txt")).length;
  totalRev += s.fragmentos.filter((f) => f.revisado).length;
  totalPend += pend.length;
  const libres = pend.filter((f) => !yaLanz.has(f.clave));
  for (let k = 0; k < libres.length; k += MAX) lotes.push({ s, tit, fr: libres.slice(k, k + MAX) });
}
console.error(`fragmentos: ${totalFr}; traducidos: ${totalTrad}; revisados: ${totalRev}; pendientes de ${modo}: ${totalPend}; lanzados sin terminar: ${[...yaLanz].filter((k) => !terminado(k, modo)).length}; lotes libres: ${lotes.length}`);
if (args.includes("--resumen")) process.exit(0);

const elegidos = lotes.slice(0, N);
for (const { s, tit, fr } of elegidos) {
  const lista = REVISAR ? fr.map((f) => f.clave).join(", ") : fr.map((f) => `${f.clave} (${f.parrafos})`).join(", ");
  const rango = `${fr[0].i}${fr.length > 1 ? "–" + fr[fr.length - 1].i : ""} de ${s.fragmentos.length}`;
  console.log(`Lee y sigue las instrucciones de ${INSTR}. Carpeta: ${F}. Obra: "${tit}" (Jonathan Edwards), fragmentos ${rango}. ${REVISAR ? "Revisa" : "Traduce"}: ${lista}. Tu respuesta final debe ser solo las líneas OK, sin resumen ni notas.`);
  lanz[modo].push(...fr.map((f) => f.clave));
}
lanz[modo] = lanz[modo].filter((k) => !terminado(k, modo));
fs.writeFileSync(rutaLanz, JSON.stringify(lanz) + "\n");
