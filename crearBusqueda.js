// Genera el índice de búsqueda de texto completo en pagefind/ (no se versiona).
//
//   node createToC.js && node crearBusqueda.js
//
// Cada párrafo de cada texto es un resultado propio. Su enlace lleva un fragmento
// de texto (#:~:text=inicio,fin) para que el navegador baje hasta el párrafo y lo
// resalte, sin modificar los archivos de siglo/.
// Toma autores, obras y siglos del catálogo de index.html, así que se ejecuta
// después de createToC.js. En GitHub lo hace la Action de publicación
// (.github/workflows/publicar.yml).
const fs = require("fs");
const path = require("path");
const { JSDOM } = require("jsdom");

const RAIZ = __dirname;
const SALIDA = path.join(RAIZ, "pagefind");
const MIN_PALABRAS = 4; // los párrafos más cortos ("I.", "Amén.") no se indexan

// En un fragmento de texto el guion y la coma tienen significado propio
const fragmento = (s) => encodeURIComponent(s).replace(/-/g, "%2D");
function enlace(href, texto) {
  const w = texto.split(" ");
  if (w.length <= 12) return `${href}#:~:text=${fragmento(texto)}`;
  return `${href}#:~:text=${fragmento(w.slice(0, 6).join(" "))},${fragmento(w.slice(-6).join(" "))}`;
}

async function main() {
  const html = fs.readFileSync(path.join(RAIZ, "index.html"), "utf8");
  const m = html.match(
    /<script id="catalogo" type="application\/json">([\s\S]*?)<\/script>/,
  );
  if (!m)
    throw new Error(
      "index.html no tiene el catálogo; ejecuta antes node createToC.js",
    );
  const catalogo = JSON.parse(m[1]);

  const pagefind = await import("pagefind");
  const { index, errors } = await pagefind.createIndex({ forceLanguage: "es" });
  if (errors.length) throw new Error(errors.join("\n"));

  let parrafos = 0,
    textos = 0;
  for (const o of catalogo.obras) {
    for (const t of o.textos) {
      const archivo = path.join(RAIZ, decodeURIComponent(t.h));
      const doc = new JSDOM(fs.readFileSync(archivo, "utf8")).window.document;
      const registros = [];
      let n = 0;
      for (const el of doc.body.querySelectorAll("p, blockquote")) {
        if (el.parentElement.closest("blockquote")) continue;
        const texto = el.textContent.replace(/\s+/g, " ").trim();
        n++;
        if (texto.split(" ").length < MIN_PALABRAS) continue;
        registros.push(
          index.addCustomRecord({
            url: enlace(t.h, texto),
            content: texto,
            language: "es",
            meta: {
              title: t.t,
              autor: t.a || o.autor,
              obra:
                o.serie && o.serie !== o.titulo
                  ? `${o.serie}: ${o.titulo}`
                  : o.titulo,
              siglo: o.siglo,
              n: t.n,
              p: String(n),
            },
            filters: { autor: [t.a || o.autor], siglo: [o.siglo] },
          }),
        );
      }
      const res = await Promise.all(registros);
      for (const r of res)
        if (r.errors?.length) throw new Error(`${t.h}: ${r.errors.join(", ")}`);
      parrafos += registros.length;
      textos++;
    }
  }

  fs.rmSync(SALIDA, { recursive: true, force: true });
  const w = await index.writeFiles({ outputPath: SALIDA });
  if (w.errors.length) throw new Error(w.errors.join("\n"));
  await pagefind.close();
  console.log(
    `Índice de búsqueda generado en pagefind/: ${parrafos} párrafos de ${textos} textos.`,
  );
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
