# Correspondencia con el reporte

Referencia: `Proyecto Base de Datos.pdf`, sección 2, Diccionario de Datos.

| Tabla / columna | Presentación en la ficha |
| --- | --- |
| juegos.app_id | App ID |
| juegos.name | Título de la ficha |
| juegos.release_date | Lanzamiento |
| juegos.price | Precio bajo el título; cero se presenta como Gratis |
| juegos.short_description | Descripción breve |
| juegos.detailed_description | Descripción completa, abierta inicialmente |
| juegos.header_image | Imagen de portada |
| juegos.screenshots | Capturas de pantalla |
| juegos.movies | Videos y tráileres |
| desarrolladores.nombre | Desarrollador |
| generos.nombre | Géneros |
| estadisticas_rendimiento.positive | Reseñas positivas |
| estadisticas_rendimiento.negative | Reseñas negativas |
| estadisticas_rendimiento.peak_ccu | Pico de jugadores simultáneos |
| estadisticas_rendimiento.metacritic_score | Metacritic |
| soporte_plataformas.windows | Windows: Compatible / No compatible |
| soporte_plataformas.mac | macOS: Compatible / No compatible |
| soporte_plataformas.linux | Linux: Compatible / No compatible |
| soporte_plataformas.website | Enlace Sitio oficial |

Las claves de desarrolladores y géneros y las tablas puente se usan internamente para relacionar registros; la ficha muestra sus nombres. El App ID identifica el juego y vincula las relaciones uno a uno.

## Diferencias a tener en cuenta

- El reporte llama al campo largo `detailed_description`, no `large_description`.
- Idiomas, audio, editoras, etiquetas, logros, DLC y propietarios estimados pertenecen a `steam_games`, fuera de las siete tablas del diccionario. Se conservan en un apartado plegado de datos adicionales.
- El reporte describe `screenshots` como URLs separadas por comas. El respaldo almacena una lista serializada como JSON dentro de TEXT. `movies` también contiene metadatos JSON de videos. La interfaz interpreta el formato real sin cambiar el respaldo.
- Portada y capturas se presentan como imágenes, y el sitio web y videos como enlaces/reproductores; no como sus cadenas de URL.
- El formulario permite editar las dos descripciones y los campos principales. No incluye edición de capturas y videos: los existentes se conservan al guardar.
- Esta revisión comprueba la correspondencia de campos de la ficha. No equivale a completar las consultas analíticas, vistas y disparadores del resto de la entrega.

## Ayudas de procedencia en la interfaz

Las etiquetas subrayadas con puntos muestran su origen al pasar el cursor o enfocarlas con Tab. Escape cierra la ayuda. La ficha y el formulario incluyen la tabla y columna, el App ID del juego y las relaciones mediante tablas puente cuando corresponden. Los filtros describen el campo consultado, sin atribuirlo a un registro concreto.

Otras diferencias de representación:

- `price = 0` se muestra como Gratis; `NULL` se distingue como precio no disponible. No se conoce la moneda del respaldo.
- `metacritic_score = 0` y `NULL` se presentan como Sin puntuación; no se interpretan como una calificación crítica válida.
- Los BOOLEAN de plataformas se presentan individualmente como Compatible / No compatible; NULL permanece como No disponible.
- `release_date` es TEXT según el reporte y el respaldo; se muestra el valor original, sin asumir que todos los registros sean fechas válidas.
- Las descripciones conservan el texto y separaciones básicas, pero no ejecutan el HTML del dataset.
- Los identificadores de género y desarrollador son claves internas. Las ayudas muestran la ruta de relación y el App ID del juego, no un supuesto ID individual deducido del nombre.
