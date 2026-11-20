// Cambia las citas entre comillas simples ('…') de las traducciones por comillas angulares («…»),
// el estilo de la biblioteca. No toca apóstrofos dentro de palabras (Fuller's) ni pares que contienen
// un apóstrofo inglés. Uso: node temp/trabajo/brooks-comillas.js <vol> [--simular]
const fs = require("fs");
const path = require("path");
const vol = process.argv[2];
const simular = process.argv.includes("--simular");
const F = path.resolve("temp/trabajo", `brooks-v${vol}`, "fragmentos");
const RE = /(^|[\s(\[—–¿¡«“-])'([^'\n]{1,600}?)'(?=[\s.,;:?!)\]—–»”-]|$)/gm;
let total = 0, archivos = 0;
for (const f of fs.readdirSync(F).filter((x) => x.endsWith(".es.txt"))) {
  const r = path.join(F, f);
  const t = fs.readFileSync(r, "utf8");
  let n = 0;
  const u = t.replace(RE, (all, a, b) => {
    if (/\p{L}'\p{L}/u.test(b)) return all; // apóstrofo inglés dentro: no es una cita
    n++;
    return `${a}«${b}»`;
  });
  if (!n) continue;
  total += n; archivos++;
  if (simular && archivos <= 3) console.log(f, u.match(/«[^»]{0,60}»/g).slice(0, 3).join(" | "));
  if (!simular) fs.writeFileSync(r, u);
}
console.log(`${simular ? "[simulación] " : ""}${total} citas en ${archivos} archivos`);
