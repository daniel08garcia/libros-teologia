# Directrices de Contribución

¡Gracias por considerar contribuir a nuestro proyecto! Para mantener la consistencia y la calidad del código, hemos establecido algunas directrices que te pedimos que sigas al contribuir al código HTML en este repositorio.

## Etiquetas HTML Permitidas

Cuando trabajes en archivos HTML en este proyecto, asegúrate de utilizar solo las siguientes etiquetas:

- `<h1>`, `<h2>`, `<h3>`, `<h4>`, `<h5>`: para títulos y encabezados.
- `<p>`: para párrafos.
- `<q>`: para citas cortas en línea.
- `<blockquote>`: para citas de bloque.
- `<u>`, `<i>`, `<b>`: para resaltar texto.

## Ejemplo de Uso Correcto

```html
<!DOCTYPE html>
<html lang="es">
  <head
    data-published-date="[Fecha de publicación en formato AAAA-MM-DD]"
    data-author="[Nombre del autor]"
    data-sermon-id="[Numero de sermon, si aplica]"
    data-sermon-title="[Titulo en español]"
    data-sermon-title-original="[Titulo original]"
  >
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta name="description" content="[Descripci&oacute;n/Titulo en español]" />
    <title>Ejemplo</title>
    <link rel="stylesheet" href="../../../css/style.css" />
  </head>
  <body>
    <!-- Cover Page Image -->
    <img
      class="cover-image"
      src="../../../assets/portada-1.svg"
      alt="Cover Page Image"
    />
    <div style="break-after: page"></div>

    <h1>Título Principal</h1>
    <p>Este es un párrafo de ejemplo.</p>
    <blockquote title="3 Juan 1:1">
      <p>Esta es una cita de bloque.</p>
    </blockquote>
    <p>
      Este es otro párrafo.
      <q title="3 Juan 1:1">Esta es una cita en línea.</q>
    </p>
  </body>
</html>
```

## Citas de la Biblia

Si incluyes citas de la Biblia en tus traducciones, utiliza la versión Reina Valera 1960 para mantener la consistencia en todo el proyecto.

## Estilos

Por favor, evita integrar estilos en línea en tus elementos HTML. Mantener el código sin estilos permite que cualquier persona pueda personalizar el texto según sus preferencias de lectura sin interferencias visuales no deseadas.

Por ejemplo, algunos lectores pueden preferir un tamaño de fuente más grande, un espaciado diferente o un esquema de color específico. Al mantener el estilo separado del contenido, permitimos una mayor flexibilidad para que los usuarios adapten la experiencia de lectura a sus necesidades individuales.

## Ayuda Adicional

Si tienes alguna pregunta sobre estas directrices o necesitas ayuda adicional, no dudes en abrir un issue o ponerte en contacto con el equipo de desarrollo.
