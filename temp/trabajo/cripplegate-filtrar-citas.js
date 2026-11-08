// Separa las correcciones del revisor que solo acercan una cita bíblica a la
// redacción de la RV1960 "de memoria" (motivo con RV/Reina/1960), salvo que el
// motivo indique un error de sentido u omisión. Las separadas se guardan en
// <clave>.correcciones.citas-descartadas.json (no se pierden) y el archivo de
// correcciones queda solo con las demás.
//
// Uso: node temp/trabajo/cripplegate-filtrar-citas.js <carpeta de trabajo> [--simular]
const fs = require("fs");
const path = require("path");

const dir = process.argv[2];
const simular = process.argv.includes("--simular");
if (!dir) { console.error("uso: node temp/trabajo/cripplegate-filtrar-citas.js <trabajo> [--simular]"); process.exit(1); }
const F = path.join(dir, "fragmentos");

const ES_CITA = /RV|Reina|1960/i;
const ES_SENTIDO = /omit|falt|sentido|negaci|invert|pronombre|agreg|restaur/i;

let total = 0, quitadas = 0, archivos = 0;
for (const f of fs.readdirSync(F).filter((x) => x.endsWith(".correcciones.json"))) {
  const ruta = path.join(F, f);
  const lista = JSON.parse(fs.readFileSync(ruta, "utf8"));
  const quedan = [], fuera = [];
  for (const c of lista) {
    total++;
    const m = c.motivo || "";
    (ES_CITA.test(m) && !ES_SENTIDO.test(m) ? fuera : quedan).push(c);
  }
  if (!fuera.length) continue;
  archivos++; quitadas += fuera.length;
  if (simular) continue;
  fs.writeFileSync(ruta, JSON.stringify(quedan, null, 1) + "\n");
  const desc = ruta.replace(/\.correcciones\.json$/, ".correcciones.citas-descartadas.json");
  const previas = fs.existsSync(desc) ? JSON.parse(fs.readFileSync(desc, "utf8")) : [];
  fs.writeFileSync(desc, JSON.stringify([...previas, ...fuera], null, 1) + "\n");
}
console.log(`${simular ? "[simulación] " : ""}${quitadas} de ${total} correcciones separadas (citas RV1960 de memoria) en ${archivos} archivo(s).`);
