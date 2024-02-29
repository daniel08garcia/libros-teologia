const fs = require('fs');
const path = require('path');
const { JSDOM } = require('jsdom');

const directoryPath = './siglo';
const outputFilePath = './index.html';

function createTableOfContents(dir, depth = 0) {
    let files = fs.readdirSync(dir);
    let tableOfContents = '';

    files.forEach(file => {
        const filePath = path.join(dir, file);
        const stats = fs.statSync(filePath);

        if (stats.isDirectory()) {
            // Recursively traverse subdirectories
            tableOfContents += `${' '.repeat(depth * 4)}<li><span class="folder">${file}</span><ul>`;
            tableOfContents += createTableOfContents(filePath, depth + 1);
            tableOfContents += `${' '.repeat(depth * 4)}</ul></li>`;
        } else {
            const fileName = path.basename(file);
            if (fileName.endsWith('.html')) {
                const htmlContent = fs.readFileSync(filePath, 'utf8');
                const { document } = new JSDOM(htmlContent).window;

                const sermonId = document.querySelector('head').getAttribute('data-sermon-id');
                const linkText = sermonId ? `Sermon:${sermonId} ${fileName}` : fileName;

                tableOfContents += `${' '.repeat(depth * 4)}<li><a href="${filePath}">${linkText}</a></li>`;
            } else {
                tableOfContents += `${' '.repeat(depth * 4)}<li><a href="${filePath}">${fileName}</a></li>`;
            }
        }
    });

    return tableOfContents;
}

function generateHTMLTableOfContents() {
    const tableContent = createTableOfContents(directoryPath);

    const htmlContent = `
    <!DOCTYPE html>
    <html>
    <head>
    <title>&Iacute;ndice</title>
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
