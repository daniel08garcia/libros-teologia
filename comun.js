// Funciones que comparten crearBusqueda.js y crearVectores.js.
const fs = require("fs");
const path = require("path");

const RAIZ = __dirname;
const MIN_PALABRAS = 4; // los párrafos más cortos ("I.", "Amén.") no se indexan

// Catálogo que createToC.js escribe dentro de index.html
function leerCatalogo() {
  const html = fs.readFileSync(path.join(RAIZ, "index.html"), "utf8");
  const m = html.match(
    /<script id="catalogo" type="application\/json">([\s\S]*?)<\/script>/,
  );
  if (!m)
    throw new Error(
      "index.html no tiene el catálogo; ejecuta antes node createToC.js",
    );
  return JSON.parse(m[1]);
}

// Párrafos de un texto: <p> y <blockquote> (sin contar los <p> dentro de un <blockquote>).
// "n" numera todos los bloques, también los cortos que no se indexan; indice/indice.js
// usa la misma regla en el navegador para encontrar el párrafo n.
function parrafos(doc) {
  const out = [];
  let n = 0;
  for (const el of doc.body.querySelectorAll("p, blockquote")) {
    if (el.parentElement.closest("blockquote")) continue;
    n++;
    const texto = el.textContent.replace(/\s+/g, " ").trim();
    if (texto.split(" ").length >= MIN_PALABRAS) out.push({ n, texto });
  }
  return out;
}

// Enlace al párrafo con un fragmento de texto (#:~:text=inicio,fin): el navegador
// baja hasta él y lo resalta. En un fragmento, el guion y la coma tienen significado propio.
const fragmento = (s) => encodeURIComponent(s).replace(/-/g, "%2D");
function enlace(href, texto) {
  const w = texto.split(" ");
  if (w.length <= 12) return `${href}#:~:text=${fragmento(texto)}`;
  return `${href}#:~:text=${fragmento(w.slice(0, 6).join(" "))},${fragmento(w.slice(-6).join(" "))}`;
}

module.exports = { RAIZ, leerCatalogo, parrafos, enlace };
