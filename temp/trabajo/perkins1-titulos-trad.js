// Pone "titulo" (y, donde corresponde, "versiculo" y "saltar_parrafos") en el manifiesto de Perkins vol. 1
// después de "sermones.js unir".
// - El título sale del primer párrafo traducido ("## TÍTULO."), sin "CAP. N.", en mayúscula inicial por
//   palabra, o de TITULOS. Las epístolas y avisos (id 0) llevan el título de PREFACIOS.
// - Las piezas que son continuación (saltar_parrafos 0) heredan el título de la anterior con «(Parte N)»,
//   y la primera parte recibe «(Parte 1)».
// - VERSICULOS: el texto bíblico del encabezado va en el <blockquote> de la pieza.
// - SUBTITULO: piezas cuyo segundo párrafo es el subtítulo del capítulo («## CAP. I.» + «De los medios…»):
//   el título sale del subtítulo y se saltan los dos párrafos.
// Uso: node temp/trabajo/perkins1-titulos-trad.js [--simular]
const fs = require("fs");
const path = require("path");

const simular = process.argv.includes("--simular");
const W = path.resolve("C:/www/libros-teologia/temp/trabajo/perkins-v1");
const rm = path.join(W, "manifiesto.json");
const m = JSON.parse(fs.readFileSync(rm, "utf8"));

const PREFACIOS = {
  s01: "A Todos Los Ignorantes Que Desean Ser Instruidos",
  s04: "Al Lector Cristiano",
  s139: "Al Lector Piadoso",
  s146: "Al Lector", s159: "Al Lector", s175: "Al Lector", s210: "Al Lector",
};
const TITULOS = {
  s02: "Los Fundamentos De La Religión Cristiana, Reunidos En Seis Principios",
  s03: "Exposición De Los Principios",
  s63: "Un Excelente Tratado Para Consolar A Los Turbados Acerca De Su Predestinación",
  s65: "Creo En Dios",
  s78: "El Título «Jesús»", s79: "El Título «Cristo»", s80: "El Título «Hijo»", s81: "El Título «Señor»",
  s83: "La Humillación De Cristo",
  s98: "La Predestinación",
  s108: "Padre Nuestro Que Estás En Los Cielos",
  s118: "Como También Nosotros Perdonamos A Nuestros Deudores",
  s120: "Porque Tuyo Es El Reino, Y El Poder, Y La Gloria",
  s125: "Un Cántico Reunido De Los Salmos",
  s127: "Proposiciones Que Declaran Hasta Dónde Puede Avanzar Un Réprobo En La Profesión Del Evangelio",
  s128: "El Estado Del Cristiano En Esta Vida",
  s130: "Diálogo Sobre El Estado Del Hombre Cristiano",
  s133: "Diálogo De Los Conflictos Entre Satanás Y Un Cristiano",
  s138: "Declaración De Ciertas Deserciones Espirituales",
  s140: "La Primera Epístola De Juan En Forma De Diálogo: Cap. I",
  s141: "La Primera Epístola De Juan En Forma De Diálogo: Cap. II",
  s142: "La Primera Epístola De Juan En Forma De Diálogo: Cap. III",
  s143: "La Primera Epístola De Juan En Forma De Diálogo: Cap. IV",
  s144: "La Primera Epístola De Juan En Forma De Diálogo: Cap. V",
  s145: "Breve Discurso Tomado De Los Escritos De Jerónimo Zanchi",
  s174: "El Combate De La Carne Y El Espíritu",
  s176: "Cómo Vivir, Y Vivir Bien",
  s178: "Un Bálsamo Para El Enfermo",
  s183: "De Los Deberes De La Conciencia",
  s186: "Del Deber Del Hombre Respecto A La Conciencia",
  s188: "Introducción Y Del Libre Albedrío",
  s189: "Del Pecado Original",
  s209: "Advertencia A Los Favorecedores De La Religión Romana",
  s211: "Declaración De La Verdadera Manera De Conocer A Cristo Crucificado",
  s213: "Un Grano De Mostaza, O La Menor Medida De Gracia Eficaz Para La Salvación",
  s215: "La Verdadera Ganancia",
  s219: "Hijitos, Guardaos De Los Ídolos",
  s225: "La Libre Gracia De Dios Y El Libre Albedrío Del Hombre",
  s229: "Las Vocaciones O Llamamientos De Los Hombres",
};
const VERSICULOS = {
  s176: ["Hab. 2. 4", "El justo por su fe vivirá."],
  s178: ["Ecl. 7. 3", "El día de la muerte es mejor que el día en que uno nace."],
  s188: ["Apoc. 18. 4", 2],
  s215: ["Fil. 3. 7", 2],
  s219: ["1 Juan 5. 21", "Hijitos, guardaos de los ídolos."],
  s225: ["Mat. 23. 37, 38", 2],
  s229: ["1 Cor. 7. 20", 2],
};
const SUBTITULO = ["s147", "s148", "s185"];

const tc = (t) => t.toLocaleLowerCase("es")
  .replace(/(^|[\s¿¡("«“—-])(\p{L})/gu, (_, a, b) => a + b.toLocaleUpperCase("es"))
  .replace(/\b(Cap|Ii|Iii|Iv|Vi|Vii|Viii|Ix|Xi|Xii|Xiii|Xiv|Xv|Xvi|Xvii|Xviii|Xix|Xx|Xxi)\b/g,
    (x) => (x === "Cap" ? x : x.toUpperCase()));

const parrafos = (k) => fs.readFileSync(path.join(W, "sermones", `${k}.es.txt`), "utf8")
  .split(/\n\s*\n/).map((x) => x.replace(/\s+/g, " ").trim()).filter(Boolean);

let base = null, parte = 0, inicio = null;
const porClave = {};
for (const s of m.sermones) {
  porClave[s.clave] = s;
  const ps = parrafos(s.clave);
  let t;
  if (s.saltar_parrafos === 0 && s.id !== "0") {
    // continuación de la pieza anterior
    parte++;
    if (parte === 2) inicio.titulo = `${base} (Parte 1)`;
    t = `${base} (Parte ${parte})`;
  } else {
    if (s.id === "0") t = PREFACIOS[s.clave] || "Epístola Dedicatoria";
    else if (TITULOS[s.clave]) t = TITULOS[s.clave];
    else if (SUBTITULO.includes(s.clave)) { t = tc(ps[1].replace(/[.\s]+$/, "")); s.saltar_parrafos = 2; }
    else {
      if (!ps[0].startsWith("## ")) throw new Error(`${s.clave}: sin título "## " y sin título fijado`);
      t = tc(ps[0].replace(/^##\s*/, "").replace(/^CAP\. [IVXL]+\.\s*/i, "").replace(/[.:,\s]+$/, ""));
    }
    // Un católico reformado: «El tercer punto: Certeza…», «El punto 16. De la fe…» -> solo el tema
    if (/Un Católico Reformado$/.test(s.destino)) t = t.replace(/^El (?:\S+ )?Punto(?: \S+)?[.:] /, "");
    base = t; parte = 1; inicio = s;
  }
  const v = VERSICULOS[s.clave];
  if (v) {
    const texto = typeof v[1] === "number" ? ps[v[1] - 1].replace(/^«|»$/g, "").replace(/^Jerusalén/, "¡Jerusalén") : v[1];
    s.versiculo = { referencia: v[0], texto };
    s.saltar_parrafos = typeof v[1] === "number" ? 2 : 1;
  }
  s.titulo = t;
}
for (const s of m.sermones)
  console.log(`${s.clave} ${s.destino.split("/").pop().slice(0, 16).padEnd(16)} [${s.id}] ${s.titulo}${s.versiculo ? `  «${s.versiculo.texto.slice(0, 40)}» ${s.versiculo.referencia}` : ""}`);
if (!simular) fs.writeFileSync(rm, JSON.stringify(m, null, 1) + "\n");
