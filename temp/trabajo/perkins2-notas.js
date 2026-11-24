// Perkins vol. 2, después de "unir": el OCR dejó las notas al margen al final del capítulo, y al dividir
// un capítulo largo en partes, las notas quedaron en una parte distinta de la que tiene sus llamadas.
// Este script mueve cada párrafo de nota «[n] …» al final de la pieza (de la misma obra) que tiene la
// llamada [n], en sermones/<clave>.es.txt. Uso: node temp/trabajo/perkins2-notas.js [--simular]
const fs = require("fs");
const path = require("path");
const arg = process.argv.slice(2).find((x) => !x.startsWith("--"));
const W = arg ? path.resolve(arg) : "C:/www/libros-teologia/temp/trabajo/perkins-v2";
const simular = process.argv.includes("--simular");
const m = JSON.parse(fs.readFileSync(path.join(W, "manifiesto.json"), "utf8"));
const P = (t) => t.split(/\n\s*\n/).map((x) => x.trim()).filter(Boolean);
const ruta = (k) => path.join(W, "sermones", `${k}.es.txt`);
const esNota = (p) => /^\[\d+\]/.test(p);
const D = {};
for (const s of m.sermones) D[s.clave] = { obra: s.destino, ps: P(fs.readFileSync(ruta(s.clave), "utf8")) };
// dónde se llama cada nota, por obra
const llamada = {};
for (const [k, d] of Object.entries(D))
  for (const p of d.ps) for (const c of p.replace(/^\[\d+\]/, "").matchAll(/\[(\d+)\]/g)) {
    const key = d.obra + "|" + c[1];
    if (!(key in llamada)) llamada[key] = k;
  }
const mover = {}; let n = 0;
for (const [k, d] of Object.entries(D)) {
  d.ps = d.ps.filter((p) => {
    if (!esNota(p)) return true;
    const num = p.match(/^\[(\d+)\]/)[1];
    const destino = llamada[d.obra + "|" + num];
    if (!destino || destino === k) return true;
    (mover[destino] ||= []).push(p); n++;
    return false;
  });
}
const cambiadas = new Set(Object.keys(mover));
for (const [k, d] of Object.entries(D)) if (d.ps.length !== P(fs.readFileSync(ruta(k), "utf8")).length) cambiadas.add(k);
for (const [k, notas] of Object.entries(mover)) {
  D[k].ps.push(...notas.sort((a, b) => +a.match(/\d+/)[0] - +b.match(/\d+/)[0]));
  console.log(`${k}: recibe ${notas.length} notas (${notas[0].match(/\d+/)[0]}…${notas[notas.length - 1].match(/\d+/)[0]})`);
}
console.log(`notas movidas: ${n}`);
console.log(`piezas cambiadas: ${[...cambiadas].sort().join(" ")}`);
if (!simular) for (const [k, d] of Object.entries(D)) fs.writeFileSync(ruta(k), d.ps.join("\n\n") + "\n");
