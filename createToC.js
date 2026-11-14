// Genera index.html a partir de los textos de siglo/.
//
//   node createToC.js && npx --yes prettier@3.3.3 --write index.html
//
// Lee los datos del <head> de cada HTML (data-sermon-id, data-sermon-title, etc.),
// agrupa los textos en obras y escribe el catálogo dentro de indice/plantilla.html.
// El diseño vive en indice/ (plantilla.html, indice.css, indice.js) y los datos
// editables de autores, series y obras en indice/autores.json.
//
// Estructura de carpetas: siglo/<siglo>/<Autor>/[<Serie>/]<Obra>/<texto>.html
//   - Los textos sueltos en la carpeta del autor forman una obra: si es uno solo,
//     la obra toma su título; si comparten título (con I, II, III...), ese título;
//     si no, "Sermones".
//   - Una carpeta "N Título (año)" es el volumen N de la serie que la contiene.
//   - Los archivos sin data-sermon-id (o vacíos) no aparecen en el índice.
const fs = require("fs");
const path = require("path");
const { JSDOM } = require("jsdom");

const RAIZ = __dirname;
const CONFIG = JSON.parse(fs.readFileSync(path.join(RAIZ, "indice", "autores.json"), "utf8"));
const AUTORES = CONFIG.autores || {};
const SERIES = CONFIG.series || {};
const OBRAS = CONFIG.obras || {};

// Número romano o arábigo → número ("XIV" → 14, "110" → 110, "0" → 0)
function numero(s) {
  if (!/^[IVXLCDM]+$/.test(s)) return parseInt(s, 10);
  const v = { I: 1, V: 5, X: 10, L: 50, C: 100, D: 500, M: 1000 };
  let r = 0, prev = 0;
  for (const ch of [...s].reverse()) {
    r += v[ch] >= prev ? v[ch] : -v[ch];
    prev = v[ch];
  }
  return r;
}

const esc = (s) =>
  String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);

// Identificador para enlazar a la ficha de una obra (index.html#obra-...)
const slug = (s) =>
  s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase()
    .replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");

function listar(dir, out = []) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) listar(p, out);
    else if (e.name.endsWith(".html")) out.push(p);
  }
  return out;
}

// ── 1. Leer los textos ──
const textos = [];
for (const archivo of listar(path.join(RAIZ, "siglo"))) {
  const partes = path.relative(RAIZ, archivo).split(path.sep); // siglo, XVII, Autor, ...carpetas, archivo
  const html = fs.readFileSync(archivo, "utf8");
  if (!html.trim()) continue;
  const doc = new JSDOM(html).window.document;
  const head = doc.querySelector("head");
  const id = head?.dataset.sermonId;
  if (!id) continue;
  textos.push({
    siglo: partes[1],
    carpeta: partes[2],
    dirs: partes.slice(3, -1),
    titulo: head.dataset.sermonTitle || partes.at(-1).replace(/\.html$/, ""),
    original: head.dataset.sermonTitleOriginal || "",
    autor: head.dataset.author || "",
    fecha: head.dataset.publishedDate || "",
    id,
    orden: numero(id),
    palabras: (doc.body?.textContent || "").split(/\s+/).filter(Boolean).length,
    href: partes.map(encodeURIComponent).join("/"),
  });
}

// ── 2. Agrupar en obras ──
const sueltos = {};
for (const t of textos) if (!t.dirs.length) (sueltos[t.carpeta] ??= []).push(t);

const obras = new Map();
for (const t of textos) {
  let serie = "", titulo, volumen = "";
  if (t.dirs.length) {
    if (t.dirs.length > 1) serie = SERIES[t.dirs[0]] || t.dirs[0];
    titulo = t.dirs.at(-1);
    const m = titulo.match(/^(\d+)\s+(.*?)(?:\s*\((\d{4})\))?$/);
    if (m) [volumen, titulo] = [m[1], m[2]];
    const ajuste = OBRAS[[t.carpeta, ...t.dirs].join("/")];
    if (ajuste?.titulo) titulo = ajuste.titulo;
    if (ajuste?.volumen) volumen = String(ajuste.volumen);
  } else {
    const grupo = sueltos[t.carpeta];
    const base = new Set(grupo.map((g) => g.titulo.replace(/\s+[IVX]+$/, "")));
    titulo = grupo.length === 1 ? t.titulo : base.size === 1 ? [...base][0] : "Sermones";
  }
  const clave = [t.siglo, t.carpeta, serie, volumen, titulo].join("|");
  if (!obras.has(clave)) {
    const a = AUTORES[t.carpeta] || {};
    obras.set(clave, {
      id: "",
      siglo: t.siglo,
      carpeta: t.carpeta,
      autor: a.nombre || t.carpeta,
      color: a.color || "",
      serie, titulo, volumen,
      textos: [],
    });
  }
  obras.get(clave).textos.push(t);
}

const lista = [...obras.values()].map((o) => {
  o.textos.sort((a, b) => a.orden - b.orden);
  const anios = o.textos.map((t) => t.fecha.slice(0, 4)).filter(Boolean).sort();
  o.anio = anios.length ? (anios[0] === anios.at(-1) ? anios[0] : `${anios[0]}–${anios.at(-1)}`) : "";
  o.textos = o.textos.map((t) => ({
    n: t.id,
    t: t.titulo,
    o: t.original,
    a: AUTORES[t.carpeta]?.coleccion ? t.autor : "",
    h: t.href,
    m: Math.max(1, Math.round(t.palabras / 200)),
  }));
  return o;
});
lista.sort((a, b) =>
  numero(a.siglo) - numero(b.siglo) ||
  a.autor.localeCompare(b.autor, "es") ||
  a.serie.localeCompare(b.serie, "es") ||
  (+a.volumen || 0) - (+b.volumen || 0) ||
  a.titulo.localeCompare(b.titulo, "es"));

// Identificadores únicos para los enlaces a cada ficha
const usados = new Set();
for (const o of lista) {
  let id = slug([o.autor, o.serie, o.volumen && "vol " + o.volumen, o.titulo].filter(Boolean).join(" "));
  for (let k = 2; usados.has(id); k++) id = id.replace(/-\d+$/, "") + "-" + k;
  usados.add(id);
  o.id = id;
}

// ── 3. Autores ──
const autores = [...new Set(lista.map((o) => o.carpeta))].map((carpeta) => {
  const a = AUTORES[carpeta] || {};
  const suyas = lista.filter((o) => o.carpeta === carpeta);
  return {
    carpeta,
    nombre: a.nombre || carpeta,
    vida: a.vida || "",
    coleccion: !!a.coleccion,
    monograma: a.monograma || "",
    siglo: suyas[0].siglo,
    obras: suyas.length,
    textos: suyas.reduce((s, o) => s + o.textos.length, 0),
    predicadores: a.coleccion
      ? new Set(textos.filter((t) => t.carpeta === carpeta).map((t) => t.autor)).size
      : 0,
  };
}).sort((a, b) => numero(a.siglo) - numero(b.siglo) || a.nombre.localeCompare(b.nombre, "es"));

const catalogo = { obras: lista, autores, total: textos.length };

// ── 4. Escribir index.html ──
// Lista simple para buscadores y para quien navegue sin JavaScript.
const sinJs = lista.map((o) =>
  `<li>${esc(o.autor)}, <i>${esc(o.serie ? o.serie + ": " : "")}${esc(o.titulo)}</i> (siglo ${o.siglo})<ul>` +
  o.textos.map((t) => `<li><a href="${esc(t.h)}">${esc(t.t)}</a></li>`).join("") +
  `</ul></li>`).join("");

const plantilla = fs.readFileSync(path.join(RAIZ, "indice", "plantilla.html"), "utf8");
if (!plantilla.includes("<!--CATALOGO-->")) throw new Error("Falta <!--CATALOGO--> en indice/plantilla.html");
const json = JSON.stringify(catalogo).replace(/</g, "\\u003c");
const salida = plantilla.replace("<!--CATALOGO-->", () =>
  `<noscript><section class="sin-js"><h2>Índice</h2><ul>${sinJs}</ul></section></noscript>\n` +
  `<script id="catalogo" type="application/json">${json}</script>`);
fs.writeFileSync(path.join(RAIZ, "index.html"), salida);

const siglos = new Set(lista.map((o) => o.siglo)).size;
console.log(`index.html generado: ${textos.length} textos, ${lista.length} obras, ${autores.length} autores, ${siglos} siglos.`);
const sinDatos = autores.filter((a) => !AUTORES[a.carpeta]).map((a) => a.carpeta);
if (sinDatos.length) console.log(`Autores sin datos en indice/autores.json (se muestran sin años de vida): ${sinDatos.join(", ")}`);
