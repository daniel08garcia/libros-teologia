// Búsqueda por sentido (Web Worker de módulo). Lo usa indice/indice.js.
//
// Carga el modelo multilingual-e5-small (una sola vez; el navegador lo guarda en caché)
// y los vectores de semantica/ que arma crearVectores.js. Para cada consulta calcula su
// vector y lo compara con el de cada párrafo; devuelve los más parecidos.
//
// Mensajes que recibe:  { tipo: "cargar", base } · { tipo: "buscar", id, texto, siglo, autor, max }
// Mensajes que envía:   { tipo: "progreso", fraccion } · { tipo: "listo", textos } ·
//                       { tipo: "resultados", id, lista: [{ ti, n, s }] } · { tipo: "error", mensaje }
import {
  pipeline,
  env,
} from "https://cdn.jsdelivr.net/npm/@huggingface/transformers@3.8.1";

env.allowLocalModels = false;
const MIN_PALABRAS = 12;

let extraer = null;
let meta = null;
let escalas = null; // Float32Array, una por párrafo
let vectores = null; // Int8Array, 384 por párrafo
let carga = null;

// Progreso combinado de varios archivos que se descargan a la vez. El total parte del
// tamaño esperado (modelo + vectores), para que la barra no retroceda cuando aparece
// un archivo grande después de los pequeños.
const archivos = new Map();
const ESPERADO = 136e6;
let ultimo = 0;
function avisar() {
  let cargado = 0,
    total = 0;
  for (const [c, t] of archivos.values()) {
    cargado += c;
    total += t;
  }
  ultimo = Math.max(ultimo, Math.min(1, cargado / Math.max(total, ESPERADO)));
  postMessage({ tipo: "progreso", fraccion: ultimo });
}

async function descargar(url, clave) {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`No se pudo descargar ${url} (${r.status})`);
  const total = +r.headers.get("content-length") || 0;
  if (!r.body || !total) return new Uint8Array(await r.arrayBuffer());
  const datos = new Uint8Array(total);
  const lector = r.body.getReader();
  let pos = 0;
  for (;;) {
    const { done, value } = await lector.read();
    if (done) break;
    datos.set(value, pos);
    pos += value.length;
    archivos.set(clave, [pos, total]);
    avisar();
  }
  return datos.subarray(0, pos);
}

function cargar(base) {
  carga ??= (async () => {
    const modelo = pipeline(
      "feature-extraction",
      "Xenova/multilingual-e5-small",
      {
        dtype: "q8",
        progress_callback: (p) => {
          if (p.status === "progress" && p.total) {
            archivos.set(p.file, [p.loaded, p.total]);
            avisar();
          }
        },
      },
    );
    const m = fetch(base + "semantica/meta.json").then((r) => r.json());
    const v = descargar(base + "semantica/vectores.bin", "vectores");
    [extraer, meta] = await Promise.all([modelo, m]);
    const bin = await v;
    const n = meta.p.length / 3;
    escalas = new Float32Array(
      bin.buffer.slice(bin.byteOffset, bin.byteOffset + n * 4),
    );
    vectores = new Int8Array(bin.buffer, bin.byteOffset + n * 4, n * meta.dim);
  })();
  return carga;
}

async function buscar({ id, texto, siglo, autor, max = 60 }) {
  const salida = await extraer("query: " + texto, {
    pooling: "mean",
    normalize: true,
  });
  const q = salida.data;
  const dim = meta.dim,
    n = escalas.length,
    p = meta.p,
    textos = meta.textos;
  const puntos = new Float32Array(n).fill(-Infinity);
  for (let i = 0; i < n; i++) {
    // Los párrafos muy cortos (encabezados como "PREGUNTA. ¿Cómo podemos saberlo?")
    // se parecen a casi cualquier consulta; aquí se buscan pasajes.
    if (p[3 * i + 2] < MIN_PALABRAS) continue;
    const t = textos[p[3 * i]];
    if ((siglo && t.s !== siglo) || (autor && t.a !== autor)) continue;
    let s = 0;
    for (let j = 0, o = i * dim; j < dim; j++) s += q[j] * vectores[o + j];
    puntos[i] = s * escalas[i];
  }
  // Los "max" mejores
  const orden = Array.from({ length: n }, (_, i) => i).filter(
    (i) => puntos[i] > -Infinity,
  );
  orden.sort((a, b) => puntos[b] - puntos[a]);
  const lista = orden
    .slice(0, max)
    .map((i) => ({ ti: p[3 * i], n: p[3 * i + 1], s: puntos[i] }));
  postMessage({ tipo: "resultados", id, lista });
}

onmessage = async ({ data }) => {
  try {
    if (data.tipo === "cargar") {
      await cargar(data.base);
      postMessage({ tipo: "listo", textos: meta.textos });
    } else if (data.tipo === "buscar") {
      await cargar(data.base);
      await buscar(data);
    }
  } catch (e) {
    postMessage({
      tipo: "error",
      mensaje: String(e?.message || e),
      id: data.id,
    });
  }
};
