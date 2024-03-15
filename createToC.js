const fs = require("fs");
const path = require("path");
const { JSDOM } = require("jsdom");

const directoryPath = "./siglo";
const outputFilePath = "./index.html";

function createTableOfContents(dir, depth = 0) {
  let files = fs.readdirSync(dir);
  let tableOfContents = "";

  files.forEach((file) => {
    const filePath = path.join(dir, file);
    const stats = fs.statSync(filePath);

    if (stats.isDirectory()) {
      // Recursively traverse subdirectories
      tableOfContents += `<li>${file}<ul>`;
      tableOfContents += createTableOfContents(filePath, depth + 1);
      tableOfContents += `</ul></li>`;
    } else {
      const fileName = path.basename(file);
      if (fileName.endsWith(".html")) {
        const htmlContent = fs.readFileSync(filePath, "utf8");
        const { document } = new JSDOM(htmlContent).window;

        const sermonId = document
          .querySelector("head")
          .getAttribute("data-sermon-id");
        const linkText = sermonId ? `Sermon:${sermonId} ${fileName}` : fileName;

        tableOfContents += `<li><a href="${filePath}">${linkText}</a></li>`;
      } else {
        tableOfContents += `<li><a href="${filePath}">${fileName}</a></li>`;
      }
    }
  });

  return tableOfContents;
}

function generateHTMLTableOfContents() {
  const tableContent = createTableOfContents(directoryPath);

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
    ${tableContent}
    </ul>
    </body>
    </html>
    `;

  fs.writeFileSync(outputFilePath, htmlContent);
}

generateHTMLTableOfContents();
