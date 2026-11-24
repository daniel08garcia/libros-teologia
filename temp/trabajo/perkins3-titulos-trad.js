// Pone "titulo" (y, donde corresponde, "versiculo" y "saltar_parrafos") en el manifiesto de Perkins vol. 3
// después de "sermones.js unir". Mismo esquema que perkins2-titulos-trad.js:
// - El título sale del primer párrafo traducido ("## TÍTULO."), sin «CAP. N.» ni numeración inicial,
//   en mayúscula inicial por palabra, o de TITULOS. Las epístolas (id 0) se llaman «Epístola Dedicatoria».
// - Las continuaciones (saltar_parrafos 0) heredan el título de la anterior con «(Parte N)».
// - SALTAR: piezas cuyo encabezado ocupa dos párrafos (portadas de los libros II y III de los Casos).
// Uso: node temp/trabajo/perkins3-titulos-trad.js [--simular]
const fs = require("fs");
const path = require("path");

const simular = process.argv.includes("--simular");
const W = path.resolve("C:/www/libros-teologia/temp/trabajo/perkins-v3");
const rm = path.join(W, "manifiesto.json");
const m = JSON.parse(fs.readFileSync(rm, "utf8"));

const TITULOS = {
  s02: "Mateo 5", s12: "Mateo 6", s21: "Mateo 7",
  s29: "Hebreos 11", s47: "Hebreos 12",
  s49: "Análisis General De La Visión", s50: "Apocalipsis 1", s55: "Apocalipsis 2", s61: "Apocalipsis 3",
  s66: "Vista General Del Combate", s67: "El Combate Explicado",
  s72: "Exhortación Al Arrepentimiento",
  s75: "Primer Tratado De Los Deberes Y Dignidades Del Ministerio",
  s76: "Epístola Dedicatoria Del Segundo Tratado",
  s77: "Segundo Tratado De Los Deberes Y Dignidades Del Ministerio",
  s80: "Diálogo Entre El Cristiano Y El Mundano",
  s82: "Breve Vista De Toda La Epístola", s83: "Exposición De La Epístola De Judas", s94: "Posdata Del Editor",
  s96: "Discurso De La Brujería", s109: "Del Rechazo O La Negativa Del Contrato", s103: "Una Resolución Para El Hombre Del Campo",
};
const SALTAR = {};
// [referencia, párrafo del versículo (1-based), saltar_parrafos]
const VERSICULOS = { s96: ["Éx. 22. 18", 3, 3] };

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
    s.saltar_parrafos = v[2] || 2;
  }
  s.titulo = t;
}
for (const s of m.sermones)
  console.log(`${s.clave} ${s.destino.split("/").pop().slice(0, 16).padEnd(16)} [${s.id}] ${s.titulo}${s.versiculo ? `  «${s.versiculo.texto.slice(0, 40)}» ${s.versiculo.referencia}` : ""}`);
const vistos = {};
for (const s of m.sermones) { const c = s.destino + "|" + s.titulo; if (vistos[c]) console.log(`!! título repetido en la misma obra: ${s.titulo}`); vistos[c] = 1; }
if (!simular) fs.writeFileSync(rm, JSON.stringify(m, null, 1) + "\n");
