const fs = require("fs");
const path = require("path");
const { JSDOM } = require("jsdom");

// Function to convert Roman numerals to Arabic numbers
function romanToArabic(roman) {
  const romanNumerals = { I: 1, V: 5, X: 10, L: 50, C: 100, D: 500, M: 1000 };
  let result = 0;
  let current,
    previous = 0;
  for (const char of roman.split("").reverse()) {
    current = romanNumerals[char];
    if (current >= previous) {
      result += current;
    } else {
      result -= current;
    }
    previous = current;
  }
  return result;
}

// Function to determine if a string is a Roman numeral
function isRoman(num) {
  return /^[IVXLCDM]+$/.test(num);
}

// Function to extract metadata from an HTML file using jsdom
async function extractMetadata(filePath) {
  const htmlContent = fs.readFileSync(filePath, "utf8");
  const dom = new JSDOM(htmlContent);
  const headElement = dom.window.document.querySelector("head");
  const sermonId = headElement.dataset.sermonId || "undefined";
  return sermonId;
}

// Function to recursively read directory and create a nested structure
async function readDirectory(dir, baseDir) {
  let structure = { type: "directory", name: path.basename(dir), children: [] };
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  for (const entry of entries) {
    if (entry.isDirectory()) {
      const subDirectoryStructure = await readDirectory(
        path.join(dir, entry.name),
        baseDir
      );
      structure.children.push(subDirectoryStructure);
    } else if (entry.isFile() && path.extname(entry.name) === ".html") {
      const fileInfo = {
        type: "file",
        name: entry.name,
        path: path.join(dir, entry.name),
        relativePath: path.relative(baseDir, path.join(dir, entry.name)),
        sermonId: await extractMetadata(path.join(dir, entry.name)),
      };
      structure.children.push(fileInfo);
    }
  }
  // Sort files and directories based on sermonId if available
  structure.children.sort((a, b) => {
    if (a.type === "file" && b.type === "file") {
      const numA = isRoman(a.sermonId)
        ? romanToArabic(a.sermonId)
        : parseInt(a.sermonId);
      const numB = isRoman(b.sermonId)
        ? romanToArabic(b.sermonId)
        : parseInt(b.sermonId);
      return numA - numB;
    }
    return 0; // Keep directories in their read order
  });
  return structure;
}

function addHeaderAndFoother(unsortoredList) {
  const htmlContent = `
  <!DOCTYPE html>
  <html lang="es">
  <head>
  <title>&Iacute;ndice</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <meta name="description" content="Colección de textos teológicos traducidos al español">
  <link rel="icon" type="image/x-icon" href="assets/favicon.ico" />
  <link rel="stylesheet" href="css/style.css" />
  </head>
  <body>
  <h1>&Iacute;ndice</h1>
  <ul>
  ${unsortoredList}
  </ul>
  </body>
  </html>
  `;
  return htmlContent;
}

// Function to generate HTML list from the directory structure
function generateHTMLList(structure) {
  if (structure.type === "directory") {
    const content = structure.children
      .map((child) => generateHTMLList(child))
      .join("");
    return `<li>${structure.name}<ul>${content}</ul></li>`;
  } else if (structure.type === "file" && structure.sermonId !== "undefined") {
    return `<li><a href="siglo/${structure.relativePath}"> <b class="sermon-id-index"> Sermon:${structure.sermonId} </b>  ${structure.name} </a></li>`;
  }
  return "";
}

// Main function to generate the HTML table of contents
async function generateTableOfContents() {
  const baseDir = path.join(__dirname, "Siglo");
  const directoryStructure = await readDirectory(baseDir, baseDir);
  const htmlList = generateHTMLList(directoryStructure);

  // Generate HTML content
  //const htmlContent = `<ul>${htmlList}</ul>`;

  // Write to an HTML file
  fs.writeFileSync("index.html", addHeaderAndFoother(htmlList));
  console.log("Table of contents generated.");
}

generateTableOfContents().catch(console.error);
