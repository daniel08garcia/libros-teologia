// Genera temp/trabajo/edwards-vol1/original-marcado.txt a partir de original-utf8.txt
// (el original de CCEL convertido de ISO-8859-1 con iconv).
// - Cada bloque es una obra del índice del usuario; se separan con @@SERMON@@.
// - Los apéndices de las Memorias (No. I-VI) se mueven junto a la Vida, antes del Sermón de Despedida.
// - Se quita la copia duplicada del Discurso I (y el Discurso II truncado que la precede), L118672-L123540.
// - Se omiten los índices de CCEL (desde "END OF THE FIRST VOLUME").
const fs = require("fs");
const dir = "temp/trabajo/edwards-vol1";
const L = fs.readFileSync(`${dir}/original-utf8.txt`, "utf8").split(/\r?\n/);
const r = (a, b) => L.slice(a - 1, b).join("\n");
const bloques = [
  [[1, 76]], // portada, advertencia, contenido (omitir)
  [[77, 21306], [22667, 26361]], // Memorias + apéndices
  [[21307, 22666]], // Sermón de despedida
  [[26362, 39911]], // Libertad de la voluntad
  [[39912, 43935]], // Fin de la creación
  [[43936, 47054]], // Verdadera virtud
  [[47055, 60092]], // Pecado original
  [[60093, 75875]], // Afectos religiosos
  [[75876, 78743]], // Narración fiel
  [[78744, 87511]], // Algunos pensamientos
  [[87512, 94790]], // Investigación humilde
  [[94791, 101388]], // Tergiversaciones corregidas
  [[101389, 113673]], // Historia de la redención
  [[113674, 113887]], // Cinco discursos (prefacio)
  [[113888, 118671]], // Discurso I (primera copia; la segunda está duplicada)
  [[123541, 124869]], // Discurso II
  [[124870, 125446]], // Discurso III
  [[125447, 127075]], // Discurso IV
  [[127076, 128453]], // Discurso V
  [[128454, 128671]], // Preguntas teológicas
];
const out = bloques.map((b) => b.map(([a, z]) => r(a, z)).join("\n\n")).join("\n\n@@SERMON@@\n\n");
fs.writeFileSync(`${dir}/original-marcado.txt`, out + "\n", "utf8");
console.log("bloques:", bloques.length);
