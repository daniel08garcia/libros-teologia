// Búsqueda por sentido: calcula los vectores de cada párrafo y arma semantica/.
//
//   node createToC.js && node crearVectores.js            calcula los que falten y arma semantica/
//   node crearVectores.js --limpiar                        además borra de vectores/ los que ya no se usan
//
// Cada texto guarda sus vectores en vectores/<huella>.bin, donde la huella depende
// del contenido de sus párrafos: mover o renombrar un sermón no obliga a recalcular,
// y solo se calculan los textos nuevos o modificados. vectores/ sí se versiona.
// semantica/ (lo que descarga el navegador) se arma de nuevo cada vez y no se versiona.
//
// Modelo: multilingual-e5-small (los párrafos llevan el prefijo "passage: "; las
// consultas, "query: "). Cada vector se guarda en int8 con su escala en float32.
const fs = require("fs");
const path = require("path");
const crypto = require("crypto");
const { JSDOM } = require("jsdom");
const { RAIZ, leerCatalogo, parrafos } = require("./comun");

const MODELO = "Xenova/multilingual-e5-small";
const DIM = 384;
const LOTE = 16;
const DIR_VECTORES = path.join(RAIZ, "vectores");
const SALIDA = path.join(RAIZ, "semantica");

// Archivo de un texto: N escalas float32 seguidas de N×384 valores int8
function guardar(archivo, vectores) {
  const n = vectores.length;
  const buf = Buffer.alloc(n * 4 + n * DIM);
  vectores.forEach((v, i) => {
    let max = 0;
    for (const x of v) max = Math.max(max, Math.abs(x));
    const escala = max / 127 || 1;
    buf.writeFloatLE(escala, i * 4);
    for (let j = 0; j < DIM; j++)
      buf.writeInt8(Math.round(v[j] / escala), n * 4 + i * DIM + j);
  });
  fs.writeFileSync(archivo, buf);
}

async function main() {
  const limpiar = process.argv.includes("--limpiar");
  const catalogo = leerCatalogo();
  fs.mkdirSync(DIR_VECTORES, { recursive: true });

  // 1. Párrafos y huella de cada texto
  const textos = [];
  for (const o of catalogo.obras)
    for (const t of o.textos) {
      const doc = new JSDOM(
        fs.readFileSync(path.join(RAIZ, decodeURIComponent(t.h)), "utf8"),
      ).window.document;
      const ps = parrafos(doc);
      const huella = crypto
        .createHash("sha1")
        .update(MODELO + "\n" + ps.map((p) => p.texto).join("\n"))
        .digest("hex")
        .slice(0, 20);
      textos.push({
        o,
        t,
        ps,
        archivo: path.join(DIR_VECTORES, huella + ".bin"),
      });
    }

  // 2. Calcular los que falten, por grupos de textos (si se interrumpe, lo hecho queda guardado)
  const faltan = textos.filter((x) => x.ps.length && !fs.existsSync(x.archivo));
  if (faltan.length) {
    const total = faltan.reduce((s, x) => s + x.ps.length, 0);
    console.log(
      `Calculando vectores de ${faltan.length} textos (${total} párrafos)…`,
    );
    const { pipeline } = await import("@huggingface/transformers");
    const extraer = await pipeline("feature-extraction", MODELO, {
      dtype: "fp32",
    });
    const t0 = Date.now();
    let hechos = 0;
    for (let g = 0; g < faltan.length; g += 12) {
      const grupo = faltan.slice(g, g + 12);
      // Párrafos de parecida longitud en el mismo lote: menos relleno, más rápido
      const items = grupo.flatMap((x, ti) =>
        x.ps.map((p, pi) => ({ ti, pi, texto: "passage: " + p.texto })),
      );
      items.sort((a, b) => a.texto.length - b.texto.length);
      const vectores = grupo.map((x) => new Array(x.ps.length));
      for (let i = 0; i < items.length; i += LOTE) {
        const lote = items.slice(i, i + LOTE);
        const salida = await extraer(
          lote.map((x) => x.texto),
          { pooling: "mean", normalize: true },
        );
        const datos = salida.tolist();
        lote.forEach((x, k) => (vectores[x.ti][x.pi] = datos[k]));
      }
      grupo.forEach((x, ti) => guardar(x.archivo, vectores[ti]));
      hechos += items.length;
      const seg = (Date.now() - t0) / 1000;
      const resta = ((total - hechos) / (hechos / seg) / 60).toFixed(0);
      console.log(
        `  ${hechos}/${total} párrafos · ${(hechos / seg).toFixed(1)} por segundo · faltan ~${resta} min`,
      );
    }
  }

  // 3. Armar semantica/: meta.json y vectores.bin (todas las escalas y luego todos los vectores)
  // p: por cada párrafo, [índice del texto, número de párrafo, palabras]
  const meta = { modelo: MODELO, dim: DIM, textos: [], p: [] };
  const escalas = [],
    cuerpos = [];
  textos.forEach((x, ti) => {
    const obra =
      x.o.serie && x.o.serie !== x.o.titulo
        ? `${x.o.serie}: ${x.o.titulo}`
        : x.o.titulo;
    meta.textos.push({
      h: x.t.h,
      t: x.t.t,
      a: x.t.a || x.o.autor,
      o: obra,
      s: x.o.siglo,
    });
    if (!x.ps.length) return;
    const buf = fs.readFileSync(x.archivo);
    const n = x.ps.length;
    if (buf.length !== n * (4 + DIM))
      throw new Error(`${x.archivo} no corresponde a ${x.t.h}`);
    escalas.push(buf.subarray(0, n * 4));
    cuerpos.push(buf.subarray(n * 4));
    for (const p of x.ps) meta.p.push(ti, p.n, p.texto.split(" ").length);
  });
  fs.rmSync(SALIDA, { recursive: true, force: true });
  fs.mkdirSync(SALIDA);
  fs.writeFileSync(path.join(SALIDA, "meta.json"), JSON.stringify(meta));
  fs.writeFileSync(
    path.join(SALIDA, "vectores.bin"),
    Buffer.concat([...escalas, ...cuerpos]),
  );
  const n = meta.p.length / 3;
  console.log(
    `Búsqueda por sentido armada en semantica/: ${n} párrafos de ${textos.length} textos (${((n * (4 + DIM)) / 1e6).toFixed(1)} MB).`,
  );

  // 4. Vectores que ya no corresponden a ningún texto
  const usados = new Set(textos.map((x) => path.basename(x.archivo)));
  const sobran = fs
    .readdirSync(DIR_VECTORES)
    .filter((f) => f.endsWith(".bin") && !usados.has(f));
  if (sobran.length && limpiar) {
    for (const f of sobran) fs.rmSync(path.join(DIR_VECTORES, f));
    console.log(
      `Se borraron ${sobran.length} archivos de vectores/ que ya no se usan.`,
    );
  } else if (sobran.length) {
    console.log(
      `Hay ${sobran.length} archivos en vectores/ que ya no se usan (textos editados o borrados). Para quitarlos: node crearVectores.js --limpiar`,
    );
  }
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
