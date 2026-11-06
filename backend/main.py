import json
import os
from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

app = FastAPI(title='Ludoteca API')
DSN = os.environ.get('DATABASE_URL', 'postgresql://ludoteca@127.0.0.1:55439/ludoteca')

@contextmanager
def database():
    try:
        with psycopg.connect(DSN, row_factory=dict_row, connect_timeout=5) as conn:
            yield conn
    except psycopg.OperationalError:
        raise HTTPException(503, 'No se pudo conectar con PostgreSQL.')

BASE = '''SELECT j.*, s.windows, s.mac, s.linux, s.website,
 e.positive, e.negative, e.peak_ccu, e.metacritic_score,
 ARRAY(SELECT g.nombre FROM juego_genero jg JOIN generos g USING(id_genero) WHERE jg.app_id=j.app_id ORDER BY g.nombre) genres,
 ARRAY(SELECT d.nombre FROM juego_desarrollador jd JOIN desarrolladores d USING(id_desarrollador) WHERE jd.app_id=j.app_id ORDER BY d.nombre) developers
 FROM juegos j LEFT JOIN soporte_plataformas s USING(app_id)
 LEFT JOIN estadisticas_rendimiento e USING(app_id)'''

def game(row):
    row['app_id'] = str(row['app_id'])
    row['price_status'] = 'unknown' if row['price'] is None else 'free' if row['price'] == 0 else 'paid'
    for key in ('screenshots', 'movies'):
        try:
            value = json.loads(row.get(key) or '[]')
            row[key] = value if isinstance(value, list) else []
        except (ValueError, TypeError):
            row[key] = []
    return row

@app.get('/api/health')
def health():
    with database() as conn:
        conn.execute('SELECT 1')
    return {'status': 'ok'}

@app.get('/api/genres')
def genres():
    with database() as conn:
        return [r['nombre'] for r in conn.execute('SELECT nombre FROM generos WHERE nombre IS NOT NULL ORDER BY nombre')]

@app.get('/api/games')
def games(q: str = Query('', max_length=200), genre: str = '', kind: str = '', page: int = Query(1, ge=1), limit: int = Query(24, ge=1, le=100)):
    clauses, args = [], []
    if q:
        clauses.append("j.name ILIKE %s")
        args.append('%' + q.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_') + '%')
    if genre:
        clauses.append('EXISTS (SELECT 1 FROM juego_genero jg JOIN generos g USING(id_genero) WHERE jg.app_id=j.app_id AND g.nombre=%s)')
        args.append(genre)
    if kind:
        if kind not in ('free', 'paid'):
            raise HTTPException(422, 'Filtro de precio inválido.')
        clauses.append('j.price = 0' if kind == 'free' else 'j.price > 0')
    where = ' WHERE ' + ' AND '.join(clauses) if clauses else ''
    with database() as conn:
        total = conn.execute('SELECT count(*) total FROM juegos j' + where, args).fetchone()['total']
        rows = conn.execute(BASE + where + ' ORDER BY peak_ccu DESC NULLS LAST, j.name, j.app_id LIMIT %s OFFSET %s', args + [limit, (page-1)*limit]).fetchall()
    return {'items': [game(r) for r in rows], 'total': total, 'page': page, 'limit': limit}

@app.get('/api/games/{app_id}')
def detail(app_id: int):
    with database() as conn:
        row = conn.execute(BASE + ' WHERE j.app_id=%s', [app_id]).fetchone()
        if not row:
            raise HTTPException(404, 'Juego no encontrado.')
        extra = conn.execute('''SELECT publishers, categories, tags, supported_languages, full_audio_languages,
        achievements, dlc_count, estimated_owners, average_playtime_forever FROM steam_games WHERE app_id=%s LIMIT 1''', [app_id]).fetchone()
        if extra:
            row.update(extra)
            for key in ('publishers', 'categories', 'tags', 'supported_languages', 'full_audio_languages'):
                try:
                    row[key] = json.loads(row[key] or '[]')
                except (ValueError, TypeError):
                    row[key] = []
    return game(row)

class GameInput(BaseModel):
    app_id: int = Field(gt=0)
    name: str = Field(min_length=1, max_length=500)
    release_date: str = Field(default='', max_length=100)
    price: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    short_description: str = Field(default='', max_length=10000)
    detailed_description: str = Field(default='', max_length=100000)
    header_image: str = Field(default='', max_length=2000)
    genres: list[str] = Field(default_factory=list, max_length=50)
    developers: list[str] = Field(default_factory=list, max_length=50)
    windows: bool = False
    mac: bool = False
    linux: bool = False
    website: str = Field(default='', max_length=2000)
    positive: int | None = Field(default=None, ge=0)
    negative: int | None = Field(default=None, ge=0)
    peak_ccu: int | None = Field(default=None, ge=0)
    metacritic_score: float | None = Field(default=None, ge=0, le=100, allow_inf_nan=False)

def save(data, creating):
    if not data.name.strip():
        raise HTTPException(422, 'El nombre es obligatorio.')
    with database() as conn:
        # Serialize modifications, including duplicate checks, within the transaction.
        conn.execute('SELECT pg_advisory_xact_lock(%s)', [data.app_id])
        exists = conn.execute('SELECT 1 FROM juegos WHERE app_id=%s', [data.app_id]).fetchone()
        if creating and exists:
            raise HTTPException(409, 'Ya existe un juego con ese App ID.')
        if not creating and not exists:
            raise HTTPException(404, 'Juego no encontrado.')
        conn.execute('''INSERT INTO juegos(app_id,name,release_date,price,short_description,detailed_description,header_image)
        VALUES(%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(app_id) DO UPDATE SET
        name=excluded.name,release_date=excluded.release_date,price=excluded.price,
        short_description=excluded.short_description,detailed_description=excluded.detailed_description,header_image=excluded.header_image''',
        [data.app_id,data.name.strip(),data.release_date,data.price,data.short_description,data.detailed_description,data.header_image])
        for table, relation, column, values in [('generos','juego_genero','id_genero',data.genres),('desarrolladores','juego_desarrollador','id_desarrollador',data.developers)]:
            conn.execute(f'DELETE FROM {relation} WHERE app_id=%s', [data.app_id])
            for name in dict.fromkeys(v.strip() for v in values if v.strip()):
                row = conn.execute(f'SELECT {column} FROM {table} WHERE nombre=%s LIMIT 1', [name]).fetchone()
                identifier = row[column] if row else conn.execute(f'INSERT INTO {table}(nombre) VALUES(%s) RETURNING {column}', [name]).fetchone()[column]
                conn.execute(f'INSERT INTO {relation}(app_id,{column}) VALUES(%s,%s)', [data.app_id,identifier])
        conn.execute('''INSERT INTO soporte_plataformas VALUES(%s,%s,%s,%s,%s) ON CONFLICT(app_id) DO UPDATE SET
        windows=excluded.windows,mac=excluded.mac,linux=excluded.linux,website=excluded.website''', [data.app_id,data.windows,data.mac,data.linux,data.website])
        conn.execute('''INSERT INTO estadisticas_rendimiento VALUES(%s,%s,%s,%s,%s) ON CONFLICT(app_id) DO UPDATE SET
        positive=excluded.positive,negative=excluded.negative,peak_ccu=excluded.peak_ccu,metacritic_score=excluded.metacritic_score''', [data.app_id,data.positive,data.negative,data.peak_ccu,data.metacritic_score])
    return detail(data.app_id)

@app.post('/api/games', status_code=201)
def create(data: GameInput):
    return save(data, True)

@app.put('/api/games/{app_id}')
def update(app_id: int, data: GameInput):
    if app_id != data.app_id:
        raise HTTPException(422, 'El App ID no coincide.')
    return save(data, False)
