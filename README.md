# Ludoteca

Prototipo de catálogo de juegos de Steam, construido con React y Vite para presentar un avance. Utiliza una muestra local del dataset de Hubert Sidorowicz; no está conectado a la base de datos ni a una API.

## Ejecutar

```bash
npm install
npm run dev
```

Para compilar: `npm run build`. Los datos están en `src/games.json`; el siguiente paso es sustituirlos por consultas al backend. La moneda de los precios no está verificada y los precios pueden haber cambiado. Las imágenes se cargan desde Steam y requieren conexión.

Fuente: https://www.kaggle.com/datasets/hubertsidorowicz/steam-games-dataset-daily-updates
