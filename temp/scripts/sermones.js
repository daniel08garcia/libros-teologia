#!/usr/bin/env node
/*
 * Herramientas para el flujo de traducción de sermones (ver temp/ai_agent.md).
 *
 *   node temp/scripts/sermones.js candidatos <original>
 *   node temp/scripts/sermones.js dividir    <original> <trabajo> [--multiple] [--patron "<regex>"] [--max 6000] [--forzar]
 *   node temp/scripts/sermones.js estado     <trabajo>
 *   node temp/scripts/sermones.js revisar    <trabajo> [clave...]
 *   node temp/scripts/sermones.js aplicar    <trabajo> [clave...]
 *   node temp/scripts/sermones.js unir       <trabajo>
 *   node temp/scripts/sermones.js html       <trabajo> [--solo s01] [--sobrescribir] [--salida <carpeta>]
 *   node temp/scripts/sermones.js validar    <carpeta|archivo> [--recursivo]
 *   node temp/scripts/sermones.js escanear   <carpeta|archivo> [--todo] [--json casos.json]
 *   node temp/scripts/sermones.js corregir   <decisiones.json> [--simular]
 *
 * Solo depende de Node y de jsdom (ya instalado en el proyecto con `npm install`).
 */
"use strict";
const fs = require("fs");
const path = require("path");

// ----------------------------------------------------------------- utilidades

const RAIZ = (() => {
  let d = __dirname;
  while (!fs.existsSync(path.join(d, "createToC.js"))) {
    const p = path.dirname(d);
    if (p === d) return process.cwd();
    d = p;
  }
  return d;
})();
const GLOSARIO = path.join(__dirname, "falsos-cognados.json");

const leer = (p) =>
  fs.readFileSync(p, "utf8").replace(/^﻿/, "").replace(/\r\n?/g, "\n");
function escribir(p, t) {
  fs.mkdirSync(path.dirname(p), { recursive: true });
  fs.writeFileSync(p, t, "utf8");
}
const leerJSON = (p) => JSON.parse(leer(p));
const escribirJSON = (p, o) => escribir(p, JSON.stringify(o, null, 2) + "\n");
const existe = (p) => fs.existsSync(p);
function fallar(msg) {
  console.error("ERROR: " + msg);
  process.exit(2);
}

/** Párrafos de un texto: separados por línea en blanco (las líneas internas se
 *  unen); si el texto no tiene líneas en blanco, cada línea es un párrafo. */
function parrafosConLinea(texto) {
  const lineas = texto.replace(/\r\n?/g, "\n").split("\n");
  const hayBlancas = /\n[ \t ]*\n/.test(texto.trim());
  const out = [];
  let cur = null;
  lineas.forEach((l, i) => {
    const t = l.replace(/\s*_{5,}\s*/g, " ").replace(/[ \t ]+/g, " ").trim();
    if (!t || /^_{3,}$/.test(t)) {
      cur = null;
      return;
    }
    if (hayBlancas && cur) cur.texto += " " + t;
    else {
      cur = { texto: t, linea: i + 1 };
      out.push(cur);
      if (!hayBlancas) cur = null;
    }
  });
  return out;
}
const parrafos = (t) => parrafosConLinea(t).map((p) => p.texto);
const unirParrafos = (ps) => ps.join("\n\n") + "\n";

/** Minúsculas y sin acentos, conservando la longitud (para buscar con regex). */
const normalizar = (s) =>
  s
    .split("")
    .map((c) => (c.normalize("NFD")[0] || c).toLowerCase()[0] || c)
    .join("")
    .replace(/[’‘]/g, "'");

function aRomano(n) {
  const v = [[1000, "M"], [900, "CM"], [500, "D"], [400, "CD"], [100, "C"],
    [90, "XC"], [50, "L"], [40, "XL"], [10, "X"], [9, "IX"], [5, "V"], [4, "IV"], [1, "I"]];
  let s = "";
  for (const [a, r] of v) while (n >= a) { s += r; n -= a; }
  return s;
}
/** Número de un id (romano o arábigo, como acepta createToC.js). */
const numeroId = (s) => (/^\d+$/.test(s || "") ? parseInt(s, 10) : deRomano(s));
function deRomano(s) {
  if (!/^[IVXLCDM]+$/.test(s || "")) return NaN;
  const val = { I: 1, V: 5, X: 10, L: 50, C: 100, D: 500, M: 1000 };
  let r = 0, prev = 0;
  for (const ch of s.split("").reverse()) {
    const c = val[ch];
    r += c >= prev ? c : -c;
    prev = Math.max(prev, c);
  }
  return aRomano(r) === s ? r : NaN;
}

function argumentos(argv) {
  const conValor = new Set(["max", "patron", "solo", "salida", "json"]);
  const a = { _: [] };
  for (let i = 0; i < argv.length; i++) {
    const x = argv[i];
    if (x.startsWith("--")) {
      const k = x.slice(2);
      if (conValor.has(k)) a[k] = argv[++i];
      else a[k] = true;
    } else a._.push(x);
  }
  return a;
}

function contar(arr) {
  const m = new Map();
  for (const x of arr) m.set(x, (m.get(x) || 0) + 1);
  return m;
}
function diferencia(a, b) {
  const out = [];
  for (const [k, n] of a) for (let i = 0; i < n - (b.get(k) || 0); i++) out.push(k);
  return out;
}
const recortar = (s, i, n = 90) =>
  (i > n ? "…" : "") + s.slice(Math.max(0, i - n), i + n).trim() + (i + n < s.length ? "…" : "");

// --------------------------------------------------------- carga del original

function cargarOriginal(archivo) {
  if (!existe(archivo)) fallar(`no existe ${archivo}`);
  let t = leer(archivo);
  if (/\.html?$/i.test(archivo)) {
    const { JSDOM } = require("jsdom");
    const doc = new JSDOM(t).window.document;
    doc.querySelectorAll("script,style,head").forEach((e) => e.remove());
    const bloques = [];
    doc.body.querySelectorAll("h1,h2,h3,h4,h5,h6,p,li,blockquote,pre").forEach((e) => {
      if (e.querySelector("p,li,blockquote")) return;
      const s = e.textContent.replace(/\s+/g, " ").trim();
      if (s) bloques.push(s);
    });
    t = bloques.join("\n\n");
  }
  return t;
}

// ------------------------------------------------------------------ candidatos

const RE_ENCABEZADO =
  /^(SERMON|DISCOURSE|SECT(ION)?\.?|CHAPTER|CHAP\.|PART|BOOK|LECTURE|TREATISE|ESSAY|LETTER)\b/i;

function cmdCandidatos(a) {
  const [orig] = a._;
  if (!orig) fallar("uso: candidatos <original>");
  const ps = parrafosConLinea(cargarOriginal(orig));
  console.log(`Párrafos: ${ps.length}. Posibles encabezados (línea: texto):\n`);
  let n = 0;
  ps.forEach((p, i) => {
    const t = p.texto;
    if (t.length > 140) return;
    const letras = t.replace(/[^A-Za-z]/g, "");
    const mayus = letras.replace(/[^A-Z]/g, "").length / (letras.length || 1);
    if (RE_ENCABEZADO.test(t) || (letras.length >= 4 && mayus > 0.7)) {
      console.log(`  L${p.linea}  [p${i + 1}]  ${t}`);
      n++;
    }
  });
  console.log(`\n${n} candidatos. Para dividir usa --patron "<regex>" o escribe una línea`);
  console.log(`@@SERMON@@ (sola, con líneas en blanco alrededor) antes de cada sermón en una copia del original.`);
}

// --------------------------------------------------------------------- dividir

/** Agrupa párrafos completos hasta `max` caracteres. Un párrafo nunca se corta:
 *  si él solo pasa del límite, va solo en su propio fragmento. */
function fragmentar(ps, max) {
  const frags = [];
  let cur = [], len = 0;
  const cerrar = () => {
    if (cur.length) frags.push({ parrafos: cur });
    cur = [];
    len = 0;
  };
  for (const p of ps) {
    if (p.length > max) {
      cerrar();
      frags.push({ parrafos: [p], largo: true });
      continue;
    }
    const extra = p.length + (cur.length ? 2 : 0);
    if (len + extra > max) cerrar();
    len += p.length + (cur.length ? 2 : 0);
    cur.push(p);
  }
  cerrar();
  return frags;
}

function cmdDividir(a) {
  const [orig, dir] = a._;
  if (!orig || !dir) fallar("uso: dividir <original> <trabajo> [--multiple] [--patron re] [--max n]");
  const max = parseInt(a.max || "6000", 10);
  const man = path.join(dir, "manifiesto.json");
  if (existe(man) && !a.forzar)
    fallar(`${man} ya existe (hay trabajo previo). Usa otra carpeta o --forzar para empezar de cero.`);
  const ps = parrafos(cargarOriginal(orig));
  let bloques;
  if (!a.multiple) bloques = [ps];
  else {
    bloques = [];
    let cur = [];
    const marcas = ps.some((p) => p === "@@SERMON@@");
    if (!marcas && !a.patron)
      fallar("con --multiple marca cada sermón con @@SERMON@@ o usa --patron. Ejecuta antes: candidatos <original>");
    const re = a.patron ? new RegExp(a.patron) : null;
    for (const p of ps) {
      const inicio = marcas ? p === "@@SERMON@@" : re.test(p);
      if (inicio) {
        if (cur.length) bloques.push(cur);
        cur = marcas ? [] : [p];
      } else cur.push(p);
    }
    if (cur.length) bloques.push(cur);
  }
  if (a.forzar && existe(path.join(dir, "fragmentos")))
    fs.rmSync(path.join(dir, "fragmentos"), { recursive: true });
  const manifiesto = {
    version: 1,
    original: path.resolve(orig),
    multiple: !!a.multiple,
    max,
    creado: new Date().toISOString(),
    comun: { autor: null, fecha: null, destino: null },
    sermones: [],
  };
  bloques.forEach((b, i) => {
    const s = "s" + String(i + 1).padStart(2, "0");
    const frags = fragmentar(b, max);
    const sermon = {
      clave: s,
      encabezado_en: b[0].slice(0, 160),
      omitir: false,
      id: null,
      titulo: null,
      titulo_original: null,
      autor: null,
      fecha: null,
      destino: null,
      saltar_parrafos: 1,
      versiculo: "auto",
      fragmentos: [],
    };
    frags.forEach((f, j) => {
      const clave = `${s}-f${String(j + 1).padStart(3, "0")}`;
      escribir(path.join(dir, "fragmentos", clave + ".en.txt"), unirParrafos(f.parrafos));
      sermon.fragmentos.push({
        clave,
        caracteres: f.parrafos.join("\n\n").length,
        parrafos: f.parrafos.length,
        parrafo_largo: !!f.largo,
        revisado: false,
      });
    });
    manifiesto.sermones.push(sermon);
  });
  escribirJSON(man, manifiesto);
  const total = manifiesto.sermones.reduce((n, s) => n + s.fragmentos.length, 0);
  console.log(`${manifiesto.sermones.length} sermón(es), ${total} fragmento(s) de máx. ${max} caracteres en ${dir}`);
  for (const s of manifiesto.sermones)
    console.log(`  ${s.clave}  ${String(s.fragmentos.length).padStart(3)} frag.  ${s.encabezado_en.slice(0, 90)}`);
}

// ---------------------------------------------------------------------- estado

function cargarManifiesto(dir) {
  const p = path.join(dir, "manifiesto.json");
  if (!existe(p)) fallar(`no existe ${p}; ejecuta primero "dividir"`);
  return leerJSON(p);
}
const guardarManifiesto = (dir, m) => escribirJSON(path.join(dir, "manifiesto.json"), m);
const rutaFrag = (dir, clave, ext) => path.join(dir, "fragmentos", `${clave}.${ext}`);

function cmdEstado(a) {
  const [dir] = a._;
  const m = cargarManifiesto(dir);
  const pend = [], rev = [];
  console.log("sermón  frag  trad  rev   título");
  for (const s of m.sermones) {
    if (s.omitir) { console.log(`${s.clave}    (omitido)`); continue; }
    let t = 0, r = 0;
    for (const f of s.fragmentos) {
      if (existe(rutaFrag(dir, f.clave, "es.txt"))) {
        t++;
        if (f.revisado) r++;
        else rev.push(f.clave);
      } else pend.push(f.clave);
    }
    console.log(`${s.clave}   ${String(s.fragmentos.length).padStart(4)}  ${String(t).padStart(4)}  ${String(r).padStart(4)}   ${s.titulo || "(" + s.encabezado_en.slice(0, 60) + ")"}`);
  }
  console.log(`\nPor traducir (${pend.length}): ${pend.join(" ") || "-"}`);
  console.log(`Por revisar  (${rev.length}): ${rev.join(" ") || "-"}`);
}

// --------------------------------------------------------------------- revisar

const RE_INGLES = /(?<!\p{L})(the|and|of|which|with|that|this|are|was|were|have|been|their|they|unto|thou|thee|hath|shall|would)(?!\p{L})/giu;
/** Párrafo que parece estar en inglés: varias palabras funcionales inglesas distintas. */
const pareceIngles = (p, min = 4) => {
  const m = (p.match(RE_INGLES) || []).map((x) => x.toLowerCase());
  return m.length >= min && new Set(m).size >= 3;
};
const RE_AGREGADO = /^(nota del traductor|n\. del t\.|traducci[oó]n:|aqu[ií] (est[aá]|tienes)|lo siento|i'?m sorry|here is|translation|sure[,!])/i;
const RE_MARKDOWN = /\*\*\p{L}[^*]{0,120}\*\*|__\p{L}[^_]{0,120}__|```/u;
const RE_FORMATO = new RegExp(RE_MARKDOWN.source + "|^#{1,6}\\s|^>\\s|^\\s*[-*]\\s", "u");

function cargarGlosario() {
  return leerJSON(GLOSARIO).map((e) => ({
    ...e,
    reEn: e.en ? new RegExp(e.en, "i") : null,
    reEs: new RegExp(e.es, "gi"),
  }));
}

function numeracion(p) {
  const m = p.match(/^(§\s*\d+|\d+|[IVXLC]+)\.(\s|$)/);
  return m ? m[1].replace(/\s+/g, " ") : null;
}

function revisarPar(enT, esT, glos) {
  const en = parrafos(enT), es = parrafos(esT);
  const E = [], V = [];
  const iguales = en.length === es.length;
  if (!iguales)
    E.push({ tipo: "parrafos", detalle: `El inglés tiene ${en.length} párrafos y el español ${es.length}. Debe ser 1 a 1.` });
  for (const [nombre, re] of [["notas", /\[\d+\]/g], ["secciones", /§\s*\d+/g]]) {
    const ce = contar((enT.match(re) || []).map((x) => x.replace(/\s+/g, " ")));
    const cs = contar((esT.match(re) || []).map((x) => x.replace(/\s+/g, " ")));
    const faltan = diferencia(ce, cs), sobran = diferencia(cs, ce);
    if (faltan.length || sobran.length)
      E.push({ tipo: nombre, detalle: `Faltan: ${faltan.join(" ") || "-"}; sobran: ${sobran.join(" ") || "-"}` });
  }
  const re = enT.length ? esT.length / enT.length : 1;
  if (enT.length > 1500 && (re < 0.85 || re > 1.6))
    E.push({ tipo: "longitud", detalle: `El español mide ${(re * 100).toFixed(0)}% del inglés (normal: 100–140%). Posible omisión o añadido.` });
  es.forEach((p, i) => {
    const n = i + 1;
    if (pareceIngles(p)) E.push({ tipo: "sin_traducir", parrafo: n, detalle: `Posible texto en inglés: ${p.slice(0, 120)}` });
    if (RE_AGREGADO.test(p)) E.push({ tipo: "agregado", parrafo: n, detalle: `Texto que no es traducción: ${p.slice(0, 120)}` });
    if (RE_FORMATO.test(p)) E.push({ tipo: "formato", parrafo: n, detalle: `Formato markdown/listas no permitido: ${p.slice(0, 80)}` });
    if (iguales) {
      const ne = numeracion(en[i]), ns = numeracion(p);
      if (ne && ne !== ns)
        E.push({ tipo: "numeracion", parrafo: n, detalle: `El inglés empieza con "${ne}." y el español con "${ns || p.slice(0, 15)}"` });
      if (en[i].length > 300) {
        const r = p.length / en[i].length;
        if (r < 0.7 || r > 1.9)
          E.push({ tipo: "longitud", parrafo: n, detalle: `Párrafo ${n}: el español mide ${(r * 100).toFixed(0)}% del inglés. Posible omisión o añadido.` });
      }
    }
  });
  const enNorm = iguales ? en.map(normalizar) : null;
  const todoEn = normalizar(enT);
  es.forEach((p, i) => {
    const pn = normalizar(p);
    for (const g of glos) {
      g.reEs.lastIndex = 0;
      const m = g.reEs.exec(pn);
      if (!m) continue;
      const fuente = iguales ? enNorm[i] : todoEn;
      if (g.reEn && !g.reEn.test(fuente)) continue;
      const mi = g.reEn ? fuente.search(g.reEn) : -1;
      V.push({
        parrafo: i + 1,
        termino: g.termino,
        es: recortar(p, m.index),
        en: mi >= 0 ? recortar(iguales ? en[i] : enT.replace(/\s+/g, " "), iguales ? mi : normalizar(enT.replace(/\s+/g, " ")).search(g.reEn)) : null,
        sugerencias: g.sugerencias,
        nota: g.nota,
      });
    }
  });
  return { estructurales: E, vocabulario: V };
}

function clavesObjetivo(m, dir, lista) {
  const todas = m.sermones.filter((s) => !s.omitir).flatMap((s) => s.fragmentos.map((f) => f.clave));
  return lista.length ? lista : todas.filter((c) => existe(rutaFrag(dir, c, "es.txt")));
}

function cmdRevisar(a) {
  const [dir, ...lista] = a._;
  const m = cargarManifiesto(dir);
  const glos = cargarGlosario();
  let tE = 0, tV = 0;
  for (const c of clavesObjetivo(m, dir, lista)) {
    const pe = rutaFrag(dir, c, "es.txt");
    if (!existe(pe)) { console.log(`${c}: sin traducción`); continue; }
    const r = revisarPar(leer(rutaFrag(dir, c, "en.txt")), leer(pe), glos);
    escribirJSON(rutaFrag(dir, c, "revision.json"), { fragmento: c, ...r });
    tE += r.estructurales.length;
    tV += r.vocabulario.length;
    const tipos = [...new Set(r.estructurales.map((e) => e.tipo))].join(",");
    console.log(`${c}: ${r.estructurales.length} estructurales${tipos ? " (" + tipos + ")" : ""}, ${r.vocabulario.length} de vocabulario`);
  }
  console.log(`\nTotal: ${tE} estructurales, ${tV} de vocabulario. Detalle en fragmentos/<clave>.revision.json`);
}

// --------------------------------------------------------------------- aplicar

function cmdAplicar(a) {
  const [dir, ...lista] = a._;
  const m = cargarManifiesto(dir);
  const glos = cargarGlosario();
  const frags = new Map(m.sermones.flatMap((s) => s.fragmentos.map((f) => [f.clave, f])));
  const claves = lista.length ? lista : [...frags.keys()].filter((c) => existe(rutaFrag(dir, c, "correcciones.json")));
  if (!claves.length) console.log("No hay archivos .correcciones.json pendientes.");
  for (const c of claves) {
    const pc = rutaFrag(dir, c, "correcciones.json"), pe = rutaFrag(dir, c, "es.txt");
    if (!existe(pc)) { console.log(`${c}: falta ${path.basename(pc)} (el revisor debe escribir [] si no hay cambios)`); continue; }
    let corr;
    try { corr = leerJSON(pc); } catch (e) { console.log(`${c}: JSON inválido en correcciones: ${e.message}`); continue; }
    if (!Array.isArray(corr)) { console.log(`${c}: las correcciones deben ser un arreglo JSON`); continue; }
    const es = parrafos(leer(pe));
    const fallos = [];
    corr.forEach((k, n) => {
      const i = (k.parrafo || 0) - 1;
      if (typeof k.texto === "string") {
        if (i < 0 || i >= es.length) return fallos.push(`#${n + 1}: párrafo ${k.parrafo} no existe`);
        es[i] = k.texto.trim();
      } else if (typeof k.buscar === "string" && typeof k.reemplazar === "string") {
        let j = es[i] && es[i].includes(k.buscar) ? i : -1;
        if (j < 0) {
          const hall = es.map((p, x) => (p.includes(k.buscar) ? x : -1)).filter((x) => x >= 0);
          if (hall.length === 1) j = hall[0];
        }
        if (j < 0) return fallos.push(`#${n + 1}: no se encontró "${k.buscar.slice(0, 60)}" (párrafo ${k.parrafo})`);
        es[j] = es[j].replace(k.buscar, () => k.reemplazar);
      } else if (!k.ignorar) fallos.push(`#${n + 1}: formato desconocido`);
    });
    escribir(pe, unirParrafos(es));
    fs.renameSync(pc, rutaFrag(dir, c, `correcciones.aplicadas-${Date.now()}.json`));
    const r = revisarPar(leer(rutaFrag(dir, c, "en.txt")), leer(pe), glos);
    escribirJSON(rutaFrag(dir, c, "revision.json"), { fragmento: c, ...r });
    const f = frags.get(c);
    f.revisado = r.estructurales.length === 0 && fallos.length === 0;
    console.log(`${c}: ${corr.length - fallos.length}/${corr.length} correcciones aplicadas; ${r.estructurales.length} estructurales restantes -> ${f.revisado ? "REVISADO" : "PENDIENTE"}`);
    fallos.forEach((x) => console.log("    " + x));
  }
  guardarManifiesto(dir, m);
}

// ------------------------------------------------------------------------ unir

function cmdUnir(a) {
  const [dir] = a._;
  const m = cargarManifiesto(dir);
  for (const s of m.sermones) {
    if (s.omitir) continue;
    const faltan = s.fragmentos.filter((f) => !existe(rutaFrag(dir, f.clave, "es.txt")));
    if (faltan.length) { console.log(`${s.clave}: faltan traducciones (${faltan.map((f) => f.clave).join(" ")})`); continue; }
    const sinRev = s.fragmentos.filter((f) => !f.revisado).map((f) => f.clave);
    const out = [];
    for (const f of s.fragmentos) out.push(...parrafos(leer(rutaFrag(dir, f.clave, "es.txt"))));
    escribir(path.join(dir, "sermones", s.clave + ".es.txt"), unirParrafos(out));
    console.log(`\n${s.clave}: ${out.length} párrafos -> sermones/${s.clave}.es.txt${sinRev.length ? `  (AVISO: ${sinRev.length} fragmento(s) sin revisar: ${sinRev.slice(0, 8).join(" ")}${sinRev.length > 8 ? " …" : ""})` : ""}`);
    out.slice(0, 4).forEach((p, i) => console.log(`   ${i + 1}: ${p.slice(0, 110)}`));
  }
}

// ------------------------------------------------------------------------ html

const ENTIDADES = {
  "á": "aacute", "é": "eacute", "í": "iacute", "ó": "oacute", "ú": "uacute",
  "Á": "Aacute", "É": "Eacute", "Í": "Iacute", "Ó": "Oacute", "Ú": "Uacute",
  "ñ": "ntilde", "Ñ": "Ntilde", "ü": "uuml", "Ü": "Uuml", "¿": "iquest",
  "¡": "iexcl", "«": "laquo", "»": "raquo", "“": "ldquo", "”": "rdquo",
  "‘": "lsquo", "’": "rsquo", "—": "mdash", "–": "ndash", "…": "hellip",
  "§": "sect", "°": "deg", " ": "nbsp", "º": "ordm", "ª": "ordf",
  "è": "egrave", "à": "agrave", "ò": "ograve", "ç": "ccedil", "æ": "aelig", "œ": "oelig",
};
const codificar = (s) =>
  s.replace(/[&<>"]|[^\x00-\x7f]/g, (c) =>
    c === "&" ? "&amp;" : c === "<" ? "&lt;" : c === ">" ? "&gt;" : c === '"' ? "&quot;"
      : ENTIDADES[c] ? `&${ENTIDADES[c]};` : `&#${c.codePointAt(0)};`);

function envolver(texto, ancho) {
  const palabras = texto.split(" ");
  const lineas = [];
  let l = "";
  for (const w of palabras) {
    if (l && l.length + 1 + w.length > ancho) { lineas.push(l); l = w; }
    else l = l ? l + " " + w : w;
  }
  if (l) lineas.push(l);
  return lineas;
}
function bloque(tag, texto, sangria = 4) {
  const pad = " ".repeat(sangria), int = " ".repeat(sangria + 2);
  const una = `${pad}<${tag}>${texto}</${tag}>`;
  if (una.length <= 80) return una;
  return `${pad}<${tag}>\n${envolver(texto, 80 - int.length).map((x) => int + x).join("\n")}\n${pad}</${tag}>`;
}
function vacia(tag, attrs, sangria = 4) {
  const pad = " ".repeat(sangria);
  const una = `${pad}<${tag} ${attrs.map(([k, v]) => `${k}="${v}"`).join(" ")} />`;
  if (una.length <= 80) return una;
  return `${pad}<${tag}\n${attrs.map(([k, v]) => `${pad}  ${k}="${v}"`).join("\n")}\n${pad}/>`;
}
const nombreArchivo = (titulo) => titulo.replace(/[\\/:*?"<>|¿¡]/g, "").replace(/\s+/g, " ").trim() + ".html";

function generarHTML(d) {
  const P = d.prefijo;
  const T = codificar(d.titulo);
  const headAttrs = [
    d.fecha ? ["data-published-date", d.fecha] : null,
    ["data-author", codificar(d.autor)],
    ["data-sermon-id", d.id],
    ["data-sermon-title", T],
    ["data-sermon-title-original", codificar(d.titulo_original)],
  ].filter(Boolean);
  const L = [
    "<!doctype html>",
    '<html lang="es">',
    "  <head",
    ...headAttrs.map(([k, v]) => `    ${k}="${v}"`),
    "  >",
    '    <meta charset="UTF-8" />',
    '    <meta name="viewport" content="width=device-width, initial-scale=1.0" />',
    vacia("meta", [["name", "description"], ["content", T]]),
    bloque("title", T),
    vacia("link", [["rel", "icon"], ["type", "image/x-icon"], ["href", `${P}assets/favicon.ico`]]),
    vacia("link", [["rel", "stylesheet"], ["href", `${P}css/style.css`]]),
    "  </head>",
    "  <body>",
    "    <!-- Cover Page Image -->",
    vacia("img", [["class", "cover-image"], ["src", `${P}assets/portada-1.svg`], ["alt", "Cover Page Image"]]),
    '    <div style="break-after: page"></div>',
    bloque("h1", T),
  ];
  const partes = [L.join("\n")];
  if (d.versiculo) {
    const v = envolver(codificar(d.versiculo.texto) + "<br />", 74).map((x) => "      " + x);
    partes.push(`    <blockquote>\n${v.join("\n")}\n      ${codificar(d.versiculo.referencia)}\n    </blockquote>`);
  }
  for (const p of d.parrafos) {
    const h = p.match(/^(#{2,3})\s+(.*)$/);
    partes.push(h ? bloque("h" + h[1].length, codificar(h[2])) : bloque("p", codificar(p)));
  }
  return partes.join("\n\n") + "\n  </body>\n</html>\n";
}

function idsEnCarpeta(carpeta, excluir) {
  if (!existe(carpeta)) return [];
  return fs.readdirSync(carpeta).filter((f) => f.endsWith(".html") && f !== excluir).map((f) => {
    const m = leer(path.join(carpeta, f)).match(/data-sermon-id="([^"]*)"/);
    return m ? numeroId(m[1]) : NaN;
  }).filter((n) => !isNaN(n));
}

function cmdHtml(a) {
  const [dir] = a._;
  const m = cargarManifiesto(dir);
  const reservados = new Map(); // carpeta -> ids asignados en esta ejecución
  for (const s of m.sermones) {
    if (s.omitir || (a.solo && a.solo !== s.clave)) continue;
    const d = { ...s };
    for (const k of ["autor", "fecha", "destino"]) if (d[k] == null) d[k] = m.comun[k];
    const faltan = ["titulo", "titulo_original", "autor", "destino"].filter((k) => !d[k]);
    if (faltan.length) { console.log(`${s.clave}: faltan en el manifiesto: ${faltan.join(", ")}`); continue; }
    if (d.fecha && !/^\d{4}(-\d{2}){0,2}$/.test(d.fecha)) { console.log(`${s.clave}: fecha inválida "${d.fecha}" (usa AAAA-MM-DD)`); continue; }
    const ps = path.join(dir, "sermones", s.clave + ".es.txt");
    if (!existe(ps)) { console.log(`${s.clave}: falta sermones/${s.clave}.es.txt; ejecuta "unir"`); continue; }
    let cuerpo = parrafos(leer(ps)).slice(d.saltar_parrafos || 0);
    let versiculo = null;
    if (d.versiculo === "auto") {
      versiculo = { referencia: cuerpo[0], texto: cuerpo[1] };
      cuerpo = cuerpo.slice(2);
    } else if (d.versiculo && d.versiculo.texto) versiculo = d.versiculo;
    const destinoAbs = path.resolve(RAIZ, d.destino);
    const rel = path.relative(RAIZ, destinoAbs);
    if (rel.startsWith("..") || !rel.split(path.sep)[0].toLowerCase().startsWith("siglo"))
      { console.log(`${s.clave}: destino debe estar dentro de siglo/ (es "${d.destino}")`); continue; }
    const prefijo = "../".repeat(rel.split(path.sep).length);
    const archivo = nombreArchivo(d.titulo);
    const salida = a.salida ? path.resolve(a.salida) : destinoAbs;
    const pf = path.join(salida, archivo);
    const enDestino = path.join(destinoAbs, archivo);
    const idPrevio = existe(enDestino) ? (leer(enDestino).match(/data-sermon-id="([^"]*)"/) || [])[1] : null;
    if (!d.id && idPrevio) {
      d.id = s.id = idPrevio;
      console.log(`${s.clave}: ${archivo} ya existe en el destino; se conserva su id ${idPrevio}`);
    }
    if (!d.id) {
      const usados = [...idsEnCarpeta(destinoAbs, archivo), ...(reservados.get(destinoAbs) || [])];
      d.id = aRomano((usados.length ? Math.max(...usados) : 0) + 1);
      s.id = d.id;
    }
    if (isNaN(deRomano(d.id))) { console.log(`${s.clave}: id "${d.id}" no es un número romano válido`); continue; }
    reservados.set(destinoAbs, [...(reservados.get(destinoAbs) || []), deRomano(d.id)]);
    if (existe(pf) && !a.sobrescribir) {
      const previo = (leer(pf).match(/data-sermon-id="([^"]*)"/) || [])[1];
      console.log(`${s.clave}: ${archivo} ya existe (id ${previo}). Usa --sobrescribir si es el mismo sermón.`);
      continue;
    }
    escribir(pf, generarHTML({ ...d, prefijo, versiculo, parrafos: cuerpo }));
    const relPf = path.relative(RAIZ, pf);
    s.archivo = (relPf.startsWith("..") ? pf : relPf).split(path.sep).join("/");
    console.log(`${s.clave}: Sermón ${d.id} -> ${s.archivo}`);
    if (versiculo) console.log(`      versículo: ${versiculo.texto.slice(0, 70)} | ${versiculo.referencia}`);
    console.log(`      primer párrafo: ${(cuerpo[0] || "").slice(0, 90)}`);
  }
  guardarManifiesto(dir, m);
}

// --------------------------------------------------------------------- validar

const PERMITIDAS = new Set(["H1", "H2", "H3", "H4", "H5", "P", "BLOCKQUOTE", "Q", "BR", "B", "I", "U", "IMG", "DIV"]);

function archivosHtml(objetivo, recursivo) {
  const st = fs.statSync(objetivo);
  if (st.isFile()) return [objetivo];
  const out = [];
  for (const e of fs.readdirSync(objetivo, { withFileTypes: true })) {
    const p = path.join(objetivo, e.name);
    if (e.isDirectory() && recursivo) out.push(...archivosHtml(p, true));
    else if (e.isFile() && e.name.endsWith(".html")) out.push(p);
  }
  return out;
}

function validarArchivo(archivo, JSDOM) {
  const E = [], A = [];
  const src = leer(archivo);
  const doc = new JSDOM(src).window.document;
  const head = doc.head, body = doc.body;
  if (!/^<!doctype html>/i.test(src.trim())) E.push("falta <!doctype html> al inicio");
  if (doc.documentElement.getAttribute("lang") !== "es") A.push('<html> debería tener lang="es"');
  const ds = head.dataset;
  const id = ds.sermonId;
  if (!id) E.push("falta data-sermon-id (no aparecerá en el índice)");
  else if (/^\d+$/.test(id)) A.push(`data-sermon-id="${id}" usa números arábigos; el proyecto usa romanos (${aRomano(+id)})`);
  else if (isNaN(deRomano(id))) E.push(`data-sermon-id="${id}" no es un número romano válido`);
  for (const k of ["sermonTitle", "sermonTitleOriginal", "author"])
    if (!ds[k]) E.push(`falta data-${k.replace(/[A-Z]/g, (c) => "-" + c.toLowerCase())}`);
  if (!ds.publishedDate) A.push("falta data-published-date");
  else if (!/^\d{4}(-\d{2}){0,2}$/.test(ds.publishedDate)) A.push(`data-published-date="${ds.publishedDate}" no tiene formato AAAA-MM-DD`);
  if (!head.querySelector("meta[charset]")) E.push('falta <meta charset="UTF-8" />');
  const titulo = (doc.title || "").replace(/\s+/g, " ").trim();
  const h1s = body.querySelectorAll("h1");
  if (h1s.length !== 1) E.push(`debe haber exactamente un <h1> (hay ${h1s.length})`);
  const h1 = h1s[0] ? h1s[0].textContent.replace(/\s+/g, " ").trim() : "";
  const desc = (head.querySelector('meta[name="description"]') || { content: "" }).content.replace(/\s+/g, " ").trim();
  const dst = (ds.sermonTitle || "").replace(/\s+/g, " ").trim();
  if (!titulo) E.push("falta <title>");
  if (dst && titulo && dst !== titulo) A.push(`<title> ("${titulo}") distinto de data-sermon-title ("${dst}")`);
  if (h1 && titulo && h1 !== titulo) A.push(`<h1> ("${h1}") distinto de <title>`);
  if (desc && titulo && desc !== titulo) A.push("meta description distinta de <title>");
  const dir = path.dirname(archivo);
  const recursos = [
    ['link[rel="stylesheet"]', "href", "hoja de estilos"],
    ['link[rel="icon"]', "href", "favicon"],
    ["img.cover-image", "src", "portada"],
  ];
  for (const [sel, attr, nombre] of recursos) {
    const el = doc.querySelector(sel);
    if (!el) { E.push(`falta ${nombre} (${sel})`); continue; }
    const v = decodeURI(el.getAttribute(attr) || "");
    if (!existe(path.resolve(dir, v))) E.push(`la ruta de ${nombre} "${v}" no existe (revisa la cantidad de ../)`);
  }
  let imgs = 0, divs = 0;
  for (const el of body.querySelectorAll("*")) {
    const t = el.tagName;
    if (!PERMITIDAS.has(t)) { (t === "EM" || t === "STRONG" ? A : E).push(`etiqueta no permitida <${t.toLowerCase()}>`); continue; }
    if (t === "IMG") {
      imgs++;
      if (!el.classList.contains("cover-image")) E.push("imagen que no es la portada");
    } else if (t === "DIV") {
      divs++;
      if (!/break-after:\s*page/.test(el.getAttribute("style") || "") || el.textContent.trim())
        E.push("<div> no permitido (solo el separador de portada)");
    } else if (el.hasAttribute("style")) E.push(`estilo en línea en <${t.toLowerCase()}>`);
    for (const at of el.getAttributeNames())
      if (!["style", "class", "src", "alt", "title"].includes(at)) A.push(`atributo ${at} en <${t.toLowerCase()}>`);
    if (t === "P" && !el.textContent.trim()) A.push("párrafo <p> vacío");
  }
  if (imgs > 1) E.push(`${imgs} imágenes (solo se permite la portada)`);
  if (divs > 1) E.push(`${divs} <div> (solo se permite uno)`);
  const texto = body.textContent;
  for (const [re, msg] of [[/@@|\[\[PENDIENTE|PENDIENTE\]\]/, "marcadores de trabajo (@@ o PENDIENTE)"],
    [RE_MARKDOWN, "restos de markdown (**negritas** o ```)"], [/\b(i'?m sorry|here is the translation|nota del traductor)\b/i, "texto que no es del sermón"]])
    if (re.test(texto)) E.push(`contiene ${msg}`);
  const ps = [...body.querySelectorAll("p")].map((p) => p.textContent.replace(/\s+/g, " ").trim());
  const ingles = ps.filter((p) => pareceIngles(p, 5));
  if (ingles.length) A.push(`${ingles.length} párrafo(s) posiblemente en inglés, p. ej.: "${ingles[0].slice(0, 70)}"`);
  const uniones = ps.map((p, i) => [p, i]).filter(([p, i]) => i > 3 && /^SERM[OÓ]N\s+[IVXLC]+\b/.test(p));
  if (uniones.length) A.push(`encabezado "SERMÓN …" en el párrafo ${uniones[0][1] + 1}: ¿dos sermones en un archivo?`);
  if (texto.replace(/\s+/g, " ").length < 1500) A.push("texto muy corto: ¿sermón cortado?");
  const base = path.basename(archivo, ".html");
  const letras = (s) => normalizar(s).replace(/[^a-z0-9]/g, "");
  const lb = letras(base.replace(/-+$/, "")), lt = letras(dst);
  if (dst && lb && !lt.startsWith(lb) && !lb.startsWith(lt))
    A.push(`el nombre del archivo no coincide con el título ("${nombreArchivo(dst)}")`);
  return { id, E, A };
}

function cmdValidar(a) {
  const [obj] = a._;
  if (!obj || !existe(obj)) fallar("uso: validar <carpeta|archivo> [--recursivo]");
  const { JSDOM } = require("jsdom");
  const archivos = archivosHtml(obj, !!a.recursivo);
  const porCarpeta = new Map();
  let nE = 0, nA = 0;
  for (const f of archivos) {
    const r = validarArchivo(f, JSDOM);
    const c = path.dirname(f);
    if (!porCarpeta.has(c)) porCarpeta.set(c, []);
    porCarpeta.get(c).push({ f, id: r.id });
    if (r.E.length || r.A.length) {
      console.log(`\n${path.relative(RAIZ, f)}`);
      r.E.forEach((x) => console.log("  ERROR  " + x));
      r.A.forEach((x) => console.log("  aviso  " + x));
    }
    nE += r.E.length;
    nA += r.A.length;
  }
  for (const [c, lista] of porCarpeta) {
    const nums = lista.map((x) => ({ ...x, n: numeroId(x.id) })).filter((x) => !isNaN(x.n));
    const vistos = new Map();
    for (const x of nums) vistos.set(x.n, [...(vistos.get(x.n) || []), path.basename(x.f)]);
    const msgs = [];
    for (const [n, fs_] of vistos) if (fs_.length > 1) msgs.push(`ERROR  id ${aRomano(n)} repetido: ${fs_.join(" | ")}`);
    // Los ids arábigos (p. ej. Spurgeon) son números del original y no tienen que ser consecutivos.
    if (nums.length && nums.every((x) => !/^\d+$/.test(x.id))) {
      const max = Math.max(...nums.map((x) => x.n));
      const faltan = [];
      for (let i = 1; i <= max; i++) if (!vistos.has(i)) faltan.push(aRomano(i));
      if (faltan.length)
        msgs.push(`ERROR  numeración no consecutiva, faltan: ${faltan.slice(0, 25).join(" ")}${faltan.length > 25 ? ` … (${faltan.length})` : ""}`);
    }
    if (msgs.length) {
      console.log(`\nCarpeta ${path.relative(RAIZ, c) || "."} (${nums.length} sermones)`);
      msgs.forEach((x) => console.log("  " + x));
      nE += msgs.filter((x) => x.startsWith("ERROR")).length;
    }
  }
  console.log(`\n${archivos.length} archivo(s) revisados: ${nE} errores, ${nA} avisos.`);
  process.exitCode = nE ? 1 : 0;
}

// -------------------------------------------------------------------- escanear

function cmdEscanear(a) {
  const [obj] = a._;
  if (!obj || !existe(obj)) fallar("uso: escanear <carpeta|archivo> [--todo]");
  // Sin el inglés al lado, solo se usan los términos que casi siempre son error (solo_es).
  const glos = cargarGlosario().filter((g) => a.todo || g.solo_es);
  const archivos = fs.statSync(obj).isFile() ? [obj] : archivosHtml(obj, true).concat(
    fs.readdirSync(obj).filter((f) => f.endsWith(".txt")).map((f) => path.join(obj, f)));
  if (a.json) return escanearJSON(archivos, glos, a.json);
  const totales = new Map();
  for (const f of archivos) {
    let t = leer(f);
    if (f.endsWith(".html")) {
      const { JSDOM } = require("jsdom");
      t = new JSDOM(t).window.document.body.textContent;
    }
    t = t.replace(/\s+/g, " ");
    const tn = normalizar(t);
    const hall = [];
    for (const g of glos) {
      g.reEs.lastIndex = 0;
      let m, n = 0, ej = null;
      while ((m = g.reEs.exec(tn))) { n++; if (!ej) ej = recortar(t, m.index, 60); }
      if (n) { hall.push(`  ${String(n).padStart(4)}  ${g.termino}: ${ej}`); totales.set(g.termino, (totales.get(g.termino) || 0) + n); }
    }
    if (hall.length) console.log(`\n${path.relative(RAIZ, f)}\n${hall.join("\n")}`);
  }
  console.log("\nTotales (sin contexto en inglés; cada caso se debe revisar a mano o con el agente revisor):");
  [...totales].sort((x, y) => y[1] - x[1]).forEach(([k, n]) => console.log(`  ${String(n).padStart(5)}  ${k}`));
}

/** Exporta cada coincidencia con su contexto en español, para que un agente decida. */
function escanearJSON(archivos, glos, salida) {
  const { JSDOM } = require("jsdom");
  const casos = [];
  for (const f of archivos.filter((x) => x.endsWith(".html"))) {
    const doc = new JSDOM(leer(f)).window.document;
    const rel = path.relative(RAIZ, f).split(path.sep).join("/");
    for (const b of doc.body.querySelectorAll("p,blockquote,h2,h3")) {
      const t = b.textContent.replace(/\s+/g, " ").trim();
      const tn = normalizar(t);
      for (const g of glos) {
        g.reEs.lastIndex = 0;
        let m;
        while ((m = g.reEs.exec(tn))) {
          const ini = Math.max(0, t.lastIndexOf(" ", Math.max(0, m.index - 220)));
          const fin = t.indexOf(" ", Math.min(t.length, m.index + m[0].length + 220));
          casos.push({
            id: casos.length + 1,
            archivo: rel,
            termino: g.termino,
            palabra: t.substr(m.index, m[0].length),
            contexto: t.slice(ini, fin < 0 ? t.length : fin).trim(),
          });
        }
      }
    }
  }
  escribirJSON(salida, casos);
  console.log(`${casos.length} casos en ${new Set(casos.map((c) => c.archivo)).size} archivos -> ${salida}`);
}

// -------------------------------------------------------------------- corregir

/** Regex que encuentra `texto` en el HTML aunque esté con entidades o partido en varias líneas. */
function patronHtml(texto) {
  const inv = Object.fromEntries(Object.entries(ENTIDADES).map(([c, n]) => [c, n]));
  const esc = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  return new RegExp(texto.trim().split("").map((c) => {
    if (/\s/.test(c)) return "\\s+";
    const alt = [esc(c), `&#${c.codePointAt(0)};`];
    if (inv[c]) alt.push(`&${inv[c]};`);
    if (c === '"') alt.push("&quot;");
    if (c === "&") alt.push("&amp;");
    if (c === "<") alt.push("&lt;");
    if (c === ">") alt.push("&gt;");
    return alt.length > 1 ? `(?:${alt.join("|")})` : alt[0];
  }).join("").replace(/(\\s\+)+/g, "\\s+"));
}

function cmdCorregir(a) {
  const [archivoDec] = a._;
  if (!archivoDec || !existe(archivoDec)) fallar("uso: corregir <decisiones.json> [--simular]");
  const decisiones = leerJSON(archivoDec).filter((d) => d.buscar && typeof d.reemplazar === "string");
  const porArchivo = new Map();
  for (const d of decisiones) porArchivo.set(d.archivo, [...(porArchivo.get(d.archivo) || []), d]);
  let ok = 0;
  const fallos = [];
  for (const [rel, ds] of porArchivo) {
    const f = path.resolve(RAIZ, rel);
    if (!existe(f) || !fs.statSync(f).isFile()) { fallos.push(`${rel}: no existe`); continue; }
    let src = leer(f);
    const iBody = src.indexOf("<body");
    const cabeza = src.slice(0, iBody), cuerpo0 = src.slice(iBody);
    let cuerpo = cuerpo0;
    const conEntidades = /&[a-z]+acute;|&ntilde;/.test(cuerpo);
    for (const d of ds) {
      const re = patronHtml(d.buscar);
      if (!re.test(cuerpo)) { fallos.push(`${rel} #${d.id}: no se encontró "${d.buscar}"`); continue; }
      const rep = conEntidades ? codificar(d.reemplazar).replace(/&quot;/g, '"')
        : d.reemplazar.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
      cuerpo = cuerpo.replace(re, () => rep);
      ok++;
    }
    if (cuerpo !== cuerpo0 && !a.simular) escribir(f, cabeza + cuerpo);
  }
  console.log(`${ok}/${decisiones.length} correcciones aplicadas en ${porArchivo.size} archivos${a.simular ? " (simulación, sin escribir)" : ""}.`);
  fallos.forEach((x) => console.log("  " + x));
}

// ------------------------------------------------------------------------ main

const comandos = {
  candidatos: cmdCandidatos, dividir: cmdDividir, estado: cmdEstado, revisar: cmdRevisar,
  aplicar: cmdAplicar, unir: cmdUnir, html: cmdHtml, validar: cmdValidar, escanear: cmdEscanear, corregir: cmdCorregir,
};
const [cmd, ...resto] = process.argv.slice(2);
if (!comandos[cmd]) {
  console.log(leer(__filename).split("\n").slice(2, 15).join("\n").replace(/^ \* ?/gm, ""));
  process.exit(cmd ? 2 : 0);
}
comandos[cmd](argumentos(resto));
