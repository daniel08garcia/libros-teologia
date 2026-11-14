// Genera el índice de búsqueda por palabras en pagefind/ (no se versiona).
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
const { RAIZ, leerCatalogo, parrafos, enlace } = require("./comun");

const SALIDA = path.join(RAIZ, "pagefind");

async function main() {
  const catalogo = leerCatalogo();
  const pagefind = await import("pagefind");
  const { index, errors } = await pagefind.createIndex({ forceLanguage: "es" });
  if (errors.length) throw new Error(errors.join("\n"));

  let total = 0,
    textos = 0;
  for (const o of catalogo.obras) {
    for (const t of o.textos) {
      const archivo = path.join(RAIZ, decodeURIComponent(t.h));
      const doc = new JSDOM(fs.readFileSync(archivo, "utf8")).window.document;
      const registros = parrafos(doc).map(({ n, texto }) =>
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
      for (const r of await Promise.all(registros))
        if (r.errors?.length) throw new Error(`${t.h}: ${r.errors.join(", ")}`);
      total += registros.length;
      textos++;
    }
  }

  fs.rmSync(SALIDA, { recursive: true, force: true });
  const w = await index.writeFiles({ outputPath: SALIDA });
  if (w.errors.length) throw new Error(w.errors.join("\n"));
  await pagefind.close();
  console.log(
    `Índice de búsqueda generado en pagefind/: ${total} párrafos de ${textos} textos.`,
  );
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
