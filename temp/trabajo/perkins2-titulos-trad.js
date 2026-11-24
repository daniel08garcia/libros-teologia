// Pone "titulo" (y, donde corresponde, "versiculo" y "saltar_parrafos") en el manifiesto de Perkins vol. 2
// después de "sermones.js unir". Mismo esquema que perkins1-titulos-trad.js:
// - El título sale del primer párrafo traducido ("## TÍTULO."), sin «CAP. N.» ni numeración inicial,
//   en mayúscula inicial por palabra, o de TITULOS. Las epístolas (id 0) se llaman «Epístola Dedicatoria».
// - Las continuaciones (saltar_parrafos 0) heredan el título de la anterior con «(Parte N)».
// - SALTAR: piezas cuyo encabezado ocupa dos párrafos (portadas de los libros II y III de los Casos).
// Uso: node temp/trabajo/perkins2-titulos-trad.js [--simular]
const fs = require("fs");
const path = require("path");

const simular = process.argv.includes("--simular");
const W = path.resolve("C:/www/libros-teologia/temp/trabajo/perkins-v2");
const rm = path.join(W, "manifiesto.json");
const m = JSON.parse(fs.readFileSync(rm, "utf8"));

const TITULOS = {
  s14: "Libro Segundo: Del Hombre En Relación Con Dios",
  s30: "Libro Tercero: Del Hombre En Relación Con El Hombre",
  s39: "Capítulo I", s42: "Capítulo II", s45: "Capítulo III", s50: "Capítulo IV", s54: "Capítulo V", s59: "Capítulo VI",
  s58: "Epístola Dedicatoria Del Suplemento",
  s71: "La Explicación Del Texto",
  s72: "La Vanidad De Los Pensamientos Naturales Del Hombre",
  s96: "El Orden De La Predestinación En La Mente De Dios",
  s102: "De La Profecía Y De La Predicación De La Palabra",
  s110: "De La Pronunciación Del Sermón",
  s83: "Catálogo De Las Obras Falsas, Dudosas O Corrompidas De Los Padres",
  s115: "Tablas De La Armonía De Los Tiempos",
};
const SALTAR = { s14: 2, s30: 2 };
const VERSICULOS = { s71: ["Gén. 8. 21", 2] };

const tc = (t) => t.toLocaleLowerCase("es")
  .replace(/(^|[\s¿¡("«“—-])(\p{L})/gu, (_, a, b) => a + b.toLocaleUpperCase("es"))
  .replace(/\b(Ii|Iii|Iv|Vi|Vii|Viii|Ix|Xi|Xii|Xiii|Xiv|Xv|Xvi)\b/g, (x) => x.toUpperCase());

const parrafos = (k) => fs.readFileSync(path.join(W, "sermones", `${k}.es.txt`), "utf8")
  .split(/\n\s*\n/).map((x) => x.replace(/\s+/g, " ").trim()).filter(Boolean);

let base = null, parte = 0, inicio = null;
for (const s of m.sermones) {
  const ps = parrafos(s.clave);
  let t;
  if (s.saltar_parrafos === 0 && s.id !== "0" && !TITULOS[s.clave]) {
    parte++;
    if (parte === 2) inicio.titulo = `${base} (Parte 1)`;
    t = `${base} (Parte ${parte})`;
  } else {
    if (TITULOS[s.clave]) t = TITULOS[s.clave];
    else if (s.id === "0") t = "Epístola Dedicatoria";
    else {
      if (!ps[0].startsWith("## ")) throw new Error(`${s.clave}: sin título "## " y sin título fijado`);
      t = tc(ps[0].replace(/^##\s*/, "").replace(/^CAP\. [IVXL]+\.\s*/i, "").replace(/^(?:[IVXL]+|\d+)\.\s+/, "")
        .replace(/[.:,;\s]+$/, ""));
      if (!t) throw new Error(`${s.clave}: título vacío`);
    }
    base = t; parte = 1; inicio = s;
  }
  if (SALTAR[s.clave]) s.saltar_parrafos = SALTAR[s.clave];
  const v = VERSICULOS[s.clave];
  if (v) {
    s.versiculo = { referencia: v[0], texto: ps[v[1] - 1].replace(/^«|»$/g, "") };
    s.saltar_parrafos = 2;
  }
  s.titulo = t;
}
for (const s of m.sermones)
  console.log(`${s.clave} ${s.destino.split("/").pop().slice(0, 16).padEnd(16)} [${s.id}] ${s.titulo}${s.versiculo ? `  «${s.versiculo.texto.slice(0, 40)}» ${s.versiculo.referencia}` : ""}`);
const vistos = {};
for (const s of m.sermones) { const c = s.destino + "|" + s.titulo; if (vistos[c]) console.log(`!! título repetido en la misma obra: ${s.titulo}`); vistos[c] = 1; }
if (!simular) fs.writeFileSync(rm, JSON.stringify(m, null, 1) + "\n");
