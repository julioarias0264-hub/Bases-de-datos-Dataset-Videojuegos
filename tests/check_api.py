"""Integration checks against the restored DB; writes are rolled back."""
from contextlib import contextmanager
import psycopg
from psycopg.rows import dict_row
from fastapi.testclient import TestClient
import backend.main as api

with psycopg.connect(api.DSN, row_factory=dict_row) as conn:
    @contextmanager
    def isolated_database():
        yield conn
    api.database = isolated_database
    client = TestClient(api.app)
    assert client.get('/api/health').status_code == 200
    catalog = client.get('/api/games').json()
    assert catalog['total'] > 100000 and len(catalog['items']) == 24, catalog
    first = catalog['items'][0]['app_id']
    detail = client.get('/api/games/' + first)
    assert detail.status_code == 200, detail.text
    assert isinstance(detail.json()['genres'], list)
    assert isinstance(detail.json()['screenshots'], list)
    free = client.get('/api/games?kind=free').json()
    assert all(g['price'] == 0 for g in free['items'])
    genre = client.get('/api/genres').json()[0]
    assert all(genre in g['genres'] for g in client.get('/api/games', params={'genre': genre}).json()['items'])
    assert client.get('/api/games?page=0').status_code == 422
    assert client.get('/api/games?kind=invalid').status_code == 422
    assert client.get('/api/games/999999999999').status_code == 404
    assert client.get('/api/games', params={'q':"' OR 1=1 --"}).json()['total'] == 0
    test_id = 900000000001
    assert not conn.execute('SELECT 1 FROM juegos WHERE app_id=%s',[test_id]).fetchone()
    payload = {'app_id':test_id,'name':'Prueba temporal ludoteca','price':0,'genres':[genre], 'developers':[], 'windows':True,'positive':0}
    response = client.post('/api/games',json=payload)
    assert response.status_code == 201, response.text
    assert client.post('/api/games',json=payload).status_code == 409
    payload['name']='Prueba editada'
    response=client.put(f'/api/games/{test_id}',json=payload)
    assert response.status_code == 200 and response.json()['name']=='Prueba editada', response.text
    assert client.get('/api/games',params={'q':'Prueba editada'}).json()['total']==1
    payload['price']=-1
    assert client.put(f'/api/games/{test_id}',json=payload).status_code == 422
    conn.rollback()
    print(f'OK: {catalog["total"]:,} juegos. Catálogo, filtros, detalle, validaciones, alta y edición. Escrituras revertidas.')
