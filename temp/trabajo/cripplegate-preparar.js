// Llena los manifiestos de Puritan Sermons (The Morning Exercises at Cripplegate),
// después de "dividir". Asigna a cada bloque su serie, destino, fecha, id (el
// número SERM. del libro; los prefacios llevan el id 0), autor, título original
// y formato del versículo. Los títulos en español se llenan después de traducir.
//
// Uso: node temp/trabajo/cripplegate-preparar.js
// Se puede volver a ejecutar: no toca "titulo" ni "omitir" si ya tienen valor.

const fs = require("fs");
const path = require("path");

const BASE = "siglo/XVII/Varios Autores/Ejercicios Matutinos de Cripplegate";
const SERIES = {
  1: ["1 El Ejercicio Matutino De Cripplegate (1661)", "1661-01-01"],
  2: ["2 Suplemento Al Ejercicio Matutino De Cripplegate (1674)", "1674-01-01"],
  3: ["3 Continuación Del Ejercicio Matutino (1682)", "1682-01-01"],
  4: ["4 Ejercicios Matutinos Casuísticos (1690)", "1690-01-01"],
  5: ["5 El Ejercicio Matutino Metodizado (1660)", "1660-01-01"],
  6: ["6 El Ejercicio Matutino Contra El Papado (1675)", "1675-01-01"],
};
// Serie con la que empieza cada volumen. Un PREF. después de un SERM. abre la serie siguiente.
const SERIE_INICIAL = { 1: 1, 2: 2, 3: 3, 4: 3, 5: 5, 6: 6 };
// Firmantes de los prefacios (sale de la firma al final de cada uno).
const AUTOR_PREFACIO = { 1: "Samuel Annesley", 2: "Samuel Annesley", 3: "Samuel Annesley", 4: "Samuel Annesley", 5: "Thomas Case", 6: "Nathanael Vincent" };

const ROMANOS = [[1000, "M"], [900, "CM"], [500, "D"], [400, "CD"], [100, "C"], [90, "XC"], [50, "L"], [40, "XL"], [10, "X"], [9, "IX"], [5, "V"], [4, "IV"], [1, "I"]];
const aRomano = (n) => ROMANOS.reduce((s, [v, r]) => { while (n >= v) { s += r; n -= v; } return s; }, "");

const MENORES = new Set("a an the of in and to by for or as at on with from into upon nor but than unto".split(" "));
function tituloIngles(t) {
  return t.toLowerCase().split(/(\s+|-)/).map((w, i) => {
    if (/^\s+$|^-$/.test(w)) return w;
    const k = w.replace(/^[“"‘(]+/, "");
    if (i > 0 && MENORES.has(k.replace(/[^a-z]/g, "")) && k === k.replace(/[^a-z’']/g, "")) return w;
    return w.replace(/[a-z]/, (c) => c.toUpperCase());
  }).join("");
}

function nombreAutor(s) {
  return s.replace(/\bREV\.\s*/g, "").replace(/,?\s*\b(M\.\s?A|D\.\s?D|B\.\s?D)\.?/g, "").replace(/\.$/, "").trim()
    .toLowerCase().replace(/\b[a-z]/g, (c) => c.toUpperCase());
}

const RE_VERSICULO = /[—–]\s*(?:[1-3]\s?)?[A-Z][a-z]+\.?\s*\d+(?:[:.]\s*\d+)?[\d,:—–\- ]*\.?\s*$/;

for (let v = 1; v <= 6; v++) {
  const W = path.join("temp/trabajo", `cripplegate-vol${v}`);
  const fm = path.join(W, "manifiesto.json");
  const m = JSON.parse(fs.readFileSync(fm, "utf8"));
  let serie = SERIE_INICIAL[v];
  let vistoSerm = false;
  for (const s of m.sermones) {
    // encabezado_en viene cortado a 160 caracteres; el primer párrafo tiene el encabezado completo
    const [p1, p2 = ""] = fs.readFileSync(path.join(W, "fragmentos", `${s.clave}-f001.en.txt`), "utf8").split(/\n\s*\n/);
    const h = p1.replace(/\s+/g, " ").trim();
    const esPref = /^PREF/.test(h);
    if (esPref && vistoSerm) { serie++; vistoSerm = false; }
    if (!esPref) vistoSerm = true;
    const [carpeta, fecha] = SERIES[serie];
    s.serie = serie;
    s.destino = `${BASE}/${carpeta}`;
    s.fecha = fecha;
    s.saltar_parrafos = 1;
    s.versiculo = RE_VERSICULO.test(p2.trim()) ? "unido" : null;
    if (esPref) {
      s.id = "0";
      s.autor = AUTOR_PREFACIO[serie];
      s.titulo_original = tituloIngles(h.replace(/^PREF\.?\s*\d*\.?\s*/, "").replace(/^MORNING EXERCISE AGAINST POPERY - /, "").replace(/^CASUISTICAL MORNING EXERCISES; /, "").replace(/\.$/, ""));
      if (/EDITOR’S PREFACE/.test(h)) s.omitir = true; // prefacio de Nichols (1844): no se publica
    } else {
      const mm = h.match(/^SERM\.\s*(\d+)\.\s*(.*?)\s*-\s*(REV\..*)$/) || h.match(/^SERM\.\s*(\d+)\.\s*(.*?)\s+(REV\..*)$/);
      if (!mm) { console.log(`v${v} ${s.clave}: encabezado no reconocido: ${h}`); continue; }
      s.id = aRomano(+mm[1]);
      s.autor = nombreAutor(mm[3]);
      s.titulo_original = tituloIngles(mm[2].replace(/^Q\.\s*/, "").replace(/[“”"]/g, "").replace(/\.$/, ""));
    }
  }
  fs.writeFileSync(fm, JSON.stringify(m, null, 1) + "\n");
  for (const s of m.sermones)
    console.log(`v${v} ${s.clave} S${s.serie} ${String(s.id).padEnd(7)} ${(s.versiculo || "-").padEnd(5)} ${s.omitir ? "OMITIR " : ""}${s.autor} | ${s.titulo_original.slice(0, 70)}`);
}
