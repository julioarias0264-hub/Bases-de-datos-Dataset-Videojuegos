# Ludoteca

Catálogo de Steam con React + Vite, FastAPI y PostgreSQL 18. El frontend consulta la base restaurada; `src/games.json` se conserva únicamente como muestra histórica.

## Desarrollo local

Desde `/home/jules/ludoteca`:

```bash
# Si PostgreSQL no está iniciado:
/usr/lib/postgresql/18/bin/pg_ctl -D "$PWD/.postgres" -l "$PWD/.postgres/server.log" -o '-p 55439 -k /tmp -h 127.0.0.1' start

# Terminal 1: API
.venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000

# Terminal 2: frontend
npm run dev -- --host 127.0.0.1
```

Abrir http://127.0.0.1:5173/Bases-de-datos-Dataset-Videojuegos/ . Documentación interactiva de la API: http://127.0.0.1:8000/docs .

La instancia está aislada del PostgreSQL del sistema y escucha únicamente en localhost. Usa el usuario `ludoteca`, base `ludoteca`, puerto `55439`. `DATABASE_URL` permite configurar otra conexión. Los datos de la instancia y el entorno Python están excluidos de Git.

## Instalación en otra máquina

Requiere PostgreSQL 18, Python compatible con FastAPI y Node.js:

```bash
uv venv .venv
uv pip install --python .venv/bin/python -r backend/requirements.txt
npm ci
```

Crear una base vacía y restaurar `respaldo_steam_custom.backup` con `pg_restore --no-owner --no-privileges --exit-on-error`. Configurar `DATABASE_URL` antes de iniciar FastAPI. No restaurar sobre una base con información existente.

## Funcionalidad

- Búsqueda por nombre, filtros por género y precio, y páginas de 24 juegos.
- Fichas con desarrolladores, plataformas, reseñas, Metacritic, pico de jugadores, idiomas, editoras, etiquetas, logros, DLC, capturas y videos disponibles.
- Registro y edición de juegos, relaciones con géneros y desarrolladores, plataformas y estadísticas, en una transacción.
- Los atributos adicionales de la tabla original `steam_games` son de consulta; las modificaciones se guardan en las siete tablas normalizadas. Las capturas y los videos existentes se conservan al editar.
- La descripción HTML del dataset se muestra como texto para evitar ejecutar contenido del respaldo.

Los precios proceden del respaldo y su moneda no está verificada; no representan precios actuales. Imágenes y videos requieren acceso a los servidores de Steam. No todos los juegos incluyen todos los campos.

## Comprobaciones

```bash
npm run build
uv pip install --python .venv/bin/python httpx
.venv/bin/python -m tests.check_api
```

Las pruebas de integración requieren la base restaurada; sus escrituras se revierten al terminar.

## Publicación

El proxy de Vite funciona durante el desarrollo. Para producción, servir la API bajo `/Bases-de-datos-Dataset-Videojuegos/api` mediante un proxy inverso, o configurar `VITE_API_URL` al compilar y el origen permitido en el servidor. GitHub Pages por sí solo no ejecuta FastAPI ni PostgreSQL. Esta versión está preparada para uso local; no exponer sus operaciones de escritura públicamente sin autenticación.

Fuente original: https://www.kaggle.com/datasets/hubertsidorowicz/steam-games-dataset-daily-updates
