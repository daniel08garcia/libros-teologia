// Pone "titulo" en el manifiesto de Watson después de "sermones.js unir". Los títulos salen del
// primer párrafo traducido ("## TÍTULO."), en mayúscula inicial por palabra, sin "SERMÓN N.",
// "Cap. N." ni "Uso N.", o de TITULOS (las piezas en que se cortaron las peticiones del Padrenuestro).
// Uso: node temp/trabajo/watson-titulos-trad.js [--simular]
const fs = require("fs");
const path = require("path");

const simular = process.argv.includes("--simular");
const W = path.resolve("temp/trabajo/watson");
const rm = path.join(W, "manifiesto.json");
const m = JSON.parse(fs.readFileSync(rm, "utf8"));

const TITULOS = {
  s01: "Vida De Thomas Watson",
  s68: "Cuán Eficaz Es La Palabra Leída Y Predicada",
  s100: "La Naturaleza Del Contentamiento",
  s107: "Cómo Puede Un Cristiano Saber Si Ha Aprendido Este Arte Divino",
  s108: "Un Directorio Cristiano, O Reglas Para El Contentamiento",
  s109: "Consuelo Para El Cristiano Contento",
  s72: "El Prefacio Del Padrenuestro: Padre Nuestro",
  s73: "Que Estás En Los Cielos",
  s74: "La Primera Petición: Santificado Sea Tu Nombre",
  s75: "La Segunda Petición: Venga Tu Reino; El Reino De La Gracia",
  s76: "Venga Tu Reino: El Reino De La Gloria",
  s77: "Venga Tu Reino: Exhortación A Buscar El Reino De Los Cielos",
  s78: "Venga Tu Reino: La Perseverancia Hasta Llegar Al Reino",
  s79: "La Tercera Petición: Hágase Tu Voluntad",
  s80: "Hágase Tu Voluntad En La Tierra: La Sumisión Paciente",
  s81: "La Cuarta Petición: El Pan Nuestro De Cada Día",
  s82: "La Quinta Petición: Perdónanos Nuestras Deudas",
  s83: "Perdónanos Nuestras Deudas: Procurar El Perdón Del Pecado",
  s84: "Como También Nosotros Perdonamos A Nuestros Deudores",
  s85: "La Sexta Petición: No Nos Metas En Tentación",
  s86: "No Nos Metas En Tentación: Usos",
  s87: "Mas Líbranos Del Mal",
};

const tc = (t) => t.toLocaleLowerCase("es")
  .replace(/(^|[\s¿¡("«“—-])(\p{L})/gu, (_, a, b) => a + b.toLocaleUpperCase("es"));

for (const s of m.sermones) {
  const p1 = fs.readFileSync(path.join(W, "sermones", `${s.clave}.es.txt`), "utf8")
    .split(/\n\s*\n/)[0].replace(/\s+/g, " ").trim();
  let t = TITULOS[s.clave];
  if (!t) {
    if (!p1.startsWith("## ")) throw new Error(`${s.clave}: sin título "## " y sin título fijado`);
    t = tc(p1.replace(/^##\s*/, "")
      .replace(/^(SERMÓN|Cap\.) [IVXL]+\.\s*/, "")
      .replace(/^Uso [IVX]+\.\s*/, "")
      .replace(/[.\s]+$/, ""));
  }
  console.log(`${s.clave} ${s.destino.split("/").pop().slice(0, 16).padEnd(16)} [${s.id}] ${t}`);
  s.titulo = t;
}
if (!simular) fs.writeFileSync(rm, JSON.stringify(m, null, 1) + "\n");
