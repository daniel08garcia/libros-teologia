// Normaliza los .es.txt de una carpeta de trabajo de Edwards antes de la revisión:
//  1. Comillas: « » “ ” → "  y  ‘ ’ → '  (el original usa comillas rectas).
//  2. Referencias bíblicas: si el párrafo inglés cita "Rom. viii. 28" y el español dice "8:28",
//     se devuelve a "viii. 28" (solo cuando el capítulo y el versículo coinciden con una cita del inglés).
// Uso: node temp/trabajo/edwards-normalizar.js <trabajo> [--simular]
const fs = require("fs");
const path = require("path");

const dir = process.argv[2];
const simular = process.argv.includes("--simular");
if (!dir) { console.error("uso: node temp/trabajo/edwards-normalizar.js <trabajo> [--simular]"); process.exit(1); }
const F = path.join(dir, "fragmentos");

const romano = (n) => {
  const v = [[100, "c"], [90, "xc"], [50, "l"], [40, "xl"], [10, "x"], [9, "ix"], [5, "v"], [4, "iv"], [1, "i"]];
  let s = "";
  for (const [a, r] of v) while (n >= a) { s += r; n -= a; }
  return s;
};
const deRomano = (s) => {
  const val = { i: 1, v: 5, x: 10, l: 50, c: 100 };
  let r = 0, prev = 0;
  for (const ch of s.split("").reverse()) { const c = val[ch]; r += c >= prev ? c : -c; prev = Math.max(prev, c); }
  return romano(r) === s ? r : NaN;
};
const parrafos = (t) => t.replace(/\r\n?/g, "\n").split(/\n[ \t]*\n/).map((p) => p.trim()).filter(Boolean);

let archivos = 0, comillas = 0, refs = 0;
for (const f of fs.readdirSync(F).filter((x) => x.endsWith(".es.txt"))) {
  const pes = path.join(F, f), pen = pes.replace(/\.es\.txt$/, ".en.txt");
  if (!fs.existsSync(pen)) continue;
  const es = parrafos(fs.readFileSync(pes, "utf8"));
  const en = parrafos(fs.readFileSync(pen, "utf8"));
  let cambio = false;
  const out = es.map((p, i) => {
    let q = p.replace(/[«“”»]/g, '"').replace(/[‘’]/g, "'");
    if (q !== p) { comillas += (p.match(/[«“”»‘’]/g) || []).length; }
    // pares capítulo/versículo en romanos del párrafo inglés correspondiente
    const pares = new Set();
    for (const m of (en[i] || "").matchAll(/\b([ivxlc]+)\.\s*(\d+)/g)) {
      const c = deRomano(m[1]);
      if (!isNaN(c)) pares.add(`${c}:${m[2]}`);
    }
    if (pares.size) {
      q = q.replace(/\b(\d{1,3}):(\d{1,3})\b/g, (all, c, v) => {
        if (!pares.has(`${+c}:${v}`)) return all;
        refs++;
        return `${romano(+c)}. ${v}`;
      });
    }
    if (q !== p) cambio = true;
    return q;
  });
  if (!cambio) continue;
  archivos++;
  if (!simular) fs.writeFileSync(pes, out.join("\n\n") + "\n", "utf8");
}
console.log(`${simular ? "[simulación] " : ""}${archivos} archivo(s); ${comillas} comillas normalizadas; ${refs} referencias devueltas a romanos.`);
