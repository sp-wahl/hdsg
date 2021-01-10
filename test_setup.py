from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy_utils import database_exists, create_database

from database import Base
from main import app
from setup import import_users, import_voters

client = TestClient(app)

TEST_NUMBER = '1234567'
NONEXISTENT_NUMBER = '0000000'


class DBTestHelper:
    def __init__(self, tmppath: Path):
        self.connection_str = f'sqlite:///{tmppath.absolute()}/test.db'
        self._session = None

    def __enter__(self):
        if self._session:
            return self._session
        if not database_exists(self.connection_str):
            create_database(self.connection_str)
        engine = create_engine(self.connection_str)

        Base.metadata.create_all(engine)

        self._session = Session(engine)
        return self._session

    def __exit__(self, type, value, traceback):
        self._session.close()
        self._session = None


@pytest.fixture(autouse=True)
def fake_db(monkeypatch, tmp_path):
    monkeypatch.setattr('main.DBHelper', lambda: DBTestHelper(tmp_path))
    monkeypatch.setattr('setup.DBHelper', lambda: DBTestHelper(tmp_path))


def get_token(username: str, password: str):
    response = client.post('/token', data={'username': username, 'password': password})
    return response.json()['access_token']


def get_auth_header(username: str, password: str):
    token = get_token(username, password)
    return {'Authorization': f'Bearer {token}'}


def test_add_user():
    import_users(Path(__file__).parent / 'users_example.csv')
    response = client.get(f'/number/{NONEXISTENT_NUMBER}', headers=get_auth_header('team_1', 'team_1password'))
    assert response.status_code == 404


def test_add_voter():
    import_users(Path(__file__).parent / 'users_example.csv')
    import_voters(Path(__file__).parent / 'voters_example.csv')
    response = client.get(f'/number/{TEST_NUMBER}', headers=get_auth_header('team_1', 'team_1password'))
    assert response.status_code == 200
    assert response.json() == {
        'number': '1234567',
        'name': 'Der Vor Name Der Nachname',
        'voted': False,
        'notes': None,
        'ballot_box_id': None,
        'running_number': None,
        'timestamp': None,
        'user_id': None,
    }
