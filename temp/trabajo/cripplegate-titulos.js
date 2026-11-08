// Pone "titulo" en los manifiestos de una serie a partir del primer párrafo del
// sermón unido (sermones/sNN.es.txt): quita "SERM. N. " / "PREF. N. " y " - REV. NOMBRE",
// y pasa a mayúscula inicial cada palabra (estilo de los títulos ya publicados).
// Uso: node temp/trabajo/cripplegate-titulos.js <serie> [--simular]
// Los títulos corregidos a mano van en AJUSTES ("volN/sNN": "Título").
const fs = require("fs");
const path = require("path");

const AJUSTES = {
  "vol1/s34": "En Qué Sentido Es El Amor Al Mundo Incompatible Con El Amor A Dios",
  "vol1/s35": "Ahora Es El Tiempo, O Instrucciones Para Aprovechar En El Presente La Temporada De La Gracia",
  "vol2/s08": "¿Cómo Puede Demostrarse Que Es Deber Indispensable De Todo Cristiano Participar De La Cena Del Señor?",
  "vol2/s09": "Un Ayuno Religioso: Se Afirma, Describe Y Persuade Su Deber",
  "vol2/s24": "Cómo Podemos Disponer Nuestros Corazones Para Soportar Las Reprensiones",
  "vol2/s25": "¿En Qué Se Manifiesta La Bienaventuranza Del Perdón, Y Cómo Puede Obtenerse?",
  "vol3/s01": "Al Lector",
  "vol3/s08": "¿Qué Pueden Hacer Mejor Los Padres Piadosos Para La Conversión De Aquellos Hijos Cuya Maldad Es Ocasionada Por Una Severidad O Una Indulgencia Pecaminosas?",
  "vol3/s14": "¿Cómo Puede Nuestra Creencia En El Gobierno De Dios Sobre El Mundo Sostenernos En Todas Las Turbaciones Mundanas?",
  "vol3/s19": "¿Cómo Podemos Aprovechar Piadosamente Aquellas Doctrinas Y Providencias Que Trascienden Nuestro Entendimiento?",
  "vol4/s04": "¿Cómo Puede Una Persona Piadosa, De La Cual Dios Esconde Su Rostro, Confiar En El Señor Como Su Dios?",
  "vol4/s07": "Al Lector",
  "vol4/s08": "¿Cómo Podemos Dar A Cristo Razón Satisfactoria De Por Qué Asistimos Al Ministerio De La Palabra?",
  "vol4/s09": "En Qué Y Por Qué La Condenación De Quienes Perecen Bajo El Evangelio Será Más Insoportable Que La De Sodoma O De Los Peores Paganos En El Día Del Juicio",
  "vol4/s15": "¿Cómo Puede Demostrarse Convincentemente Que Quienes Consideran Fácil Creer Carecen Aún De Fe Salvadora?",
  "vol4/s21": "¿Cómo Puede Curarse Eficazmente Un Temple Tibio, En Nosotros Mismos Y Unos En Otros?",
  "vol5/s30": "Al Lector",
  "vol6/s02": "Los Protestantes Se Separaron Con Justos Fundamentos De La Iglesia De Roma",
  "vol6/s13": "La Doctrina De La Iglesia De Roma Que Prohíbe Casarse Es Una Doctrina Malvada",
  "vol6/s14": "La Doctrina Papal Que Niega La Posibilidad De La Certeza De La Salvación Es Falsa, Y Tiende Peligrosamente A Destruir La Verdadera Paz Y El Consuelo De Las Almas",
  "vol5/s01":"A Los Muy Honorables",
  "vol5/s17": "La Satisfacción De Cristo Examinada",
  "vol5/s23": "Arrepentimiento Del Que No Hay Que Arrepentirse, Claramente Afirmado Y Explicado En La Práctica",
  "vol4/s25": "¿Qué Arrepentimiento De Los Pecados Nacionales Requiere Dios, Si Es Que Alguna Vez Esperamos Misericordias Nacionales?",
  "vol2/s27": "¿Qué Dones De Gracia Han De Ejercitarse Principalmente Para Una Preparación Efectiva Para La Venida De Cristo Por Muerte Y Juicio?",
};

const serie = +process.argv[2];
const simular = process.argv.includes("--simular");
if (!serie) { console.error("uso: node temp/trabajo/cripplegate-titulos.js <serie> [--simular]"); process.exit(1); }

const tc = (t) => t.toLocaleLowerCase("es").replace(/(^|[\s¿¡("«“—-])(\p{L})/gu, (_, a, b) => a + b.toLocaleUpperCase("es"));

for (let v = 1; v <= 6; v++) {
  const W = path.resolve("temp/trabajo", `cripplegate-vol${v}`);
  const rm = path.join(W, "manifiesto.json");
  const m = JSON.parse(fs.readFileSync(rm, "utf8"));
  let cambios = 0;
  for (const s of m.sermones) {
    if (s.serie !== serie || s.omitir) continue;
    const ra = path.join(W, "sermones", `${s.clave}.es.txt`);
    if (!fs.existsSync(ra)) { console.log(`vol${v}/${s.clave}: falta ${ra} (ejecuta "unir")`); continue; }
    const p1 = fs.readFileSync(ra, "utf8").split(/\n\s*\n/)[0].replace(/\s+/g, " ").trim();
    let t = p1.replace(/^(SERM|PREF)\.\s*\d+\.\s*/i, "").replace(/\s+[-—–]\s+REV\.?\s.*$/i, "").replace(/[.\s]+$/, "");
    t = AJUSTES[`vol${v}/${s.clave}`] || tc(t);
    console.log(`vol${v}/${s.clave} [${s.id}] ${t}`);
    if (s.titulo !== t) { s.titulo = t; cambios++; }
  }
  if (cambios && !simular) fs.writeFileSync(rm, JSON.stringify(m, null, 2) + "\n");
}
