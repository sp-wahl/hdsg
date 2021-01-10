from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from freezegun import freeze_time
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy_utils import database_exists, create_database

from database import Base, User, get_password_hash, Voter
from main import app

client = TestClient(app)

TEST_NUMBER = '2456789'
NONEXISTENT_NUMBER = '0000000'


class DBTestHelper:
    def __init__(self, tmppath:Path):
        self.connection_str = f'sqlite:///{tmppath.absolute()}/test.db'
        self._session = None

    def __enter__(self):
        if self._session:
            return self._session
        do_init = False
        if not database_exists(self.connection_str):
            do_init = True
            create_database(self.connection_str)
        engine = create_engine(self.connection_str)

        Base.metadata.create_all(engine)

        self._session = Session(engine)

        if do_init:
            user = User()
            user.username = "user"
            user.hashed_password = get_password_hash("password")
            self._session.add_all([user])

            voter = Voter()
            voter.number = '2456789'
            voter.name = 'Werner Wusel'
            voter.voted = False
            self._session.add_all([voter])

            self._session.commit()
        return self._session

    def __exit__(self, type, value, traceback):
        self._session.close()
        self._session = None


@pytest.fixture(autouse=True)
def fake_db(monkeypatch, tmp_path):
    monkeypatch.setattr('main.DBHelper', lambda: DBTestHelper(tmp_path))


def get_token():
    response = client.post('/token', data={'username': 'user', 'password': 'password'})
    return response.json()['access_token']


def get_auth_header():
    token = get_token()
    return {'Authorization': f'Bearer {token}'}


def test_read_main():
    response = client.get('/')
    assert response.status_code == 200


def test_read_css():
    response = client.get('/bootstrap.min.css')
    assert response.status_code == 200


def test_check_number():
    response = client.get(f'/number/{TEST_NUMBER}', headers=get_auth_header())
    assert response.status_code == 200
    assert response.json() == {
        'number': '2456789',
        'name': 'Werner Wusel',
        'voted': False,
        'notes': None,
        'ballot_box_id': None,
        'running_number': None,
        'timestamp': None,
        'user_id': None,
    }


def test_check_number_needs_authentication():
    response = client.get(f'/number/{TEST_NUMBER}')
    assert response.status_code == 401


def test_check_nonexistent_number():
    response = client.get(f'/number/{NONEXISTENT_NUMBER}', headers=get_auth_header())
    assert response.status_code == 404


def test_mark_as_has_voted():
    response = client.post(f'/number/{TEST_NUMBER}', json={'ballot_box_id': '11', 'running_number': 7},
                           headers=get_auth_header())
    assert response.status_code == 200


def test_mark_as_has_voted_needs_authentication():
    response = client.post(f'/number/{TEST_NUMBER}', json={'ballot_box_id': '11', 'running_number': 7})
    assert response.status_code == 401


def test_mark_as_has_voted_nonexistent_number():
    response = client.post(f'/number/{NONEXISTENT_NUMBER}', json={'ballot_box_id': '11', 'running_number': 7},
                           headers=get_auth_header())
    assert response.status_code == 404


def test_mark_as_has_voted_requires_ballot_box_id():
    response = client.post(f'/number/{TEST_NUMBER}', json={'running_number': 7}, headers=get_auth_header())
    assert response.status_code == 422


def test_mark_as_has_voted_requires_running_number():
    response = client.post(f'/number/{TEST_NUMBER}', json={'ballot_box_id': '11'}, headers=get_auth_header())
    assert response.status_code == 422


@freeze_time('2021-01-18T10:10:10.123Z')
def test_check_has_voted_number_returns_additional_info():
    client.post(f'/number/{TEST_NUMBER}', json={'ballot_box_id': '11', 'running_number': 7}, headers=get_auth_header())
    response = client.get(f'/number/{TEST_NUMBER}', headers=get_auth_header())
    assert response.status_code == 200
    json = response.json()
    assert json == {
        'number': '2456789',
        'name': 'Werner Wusel',
        'notes': None,
        'voted': True,
        'ballot_box_id': '11',
        'running_number': 7,
        'timestamp': '2021-01-18T10:10:10.123000+00:00',
        'user_id': 'user'
    }


@freeze_time('2021-01-18T10:10:10.123Z')
def test_stats():
    client.post(f'/number/{TEST_NUMBER}', json={'ballot_box_id': '11', 'running_number': 7}, headers=get_auth_header())
    response = client.get(f'/stats', headers=get_auth_header())
    assert response.status_code == 200
    json = response.json()
    assert json == {
        'marked_as_voted': {
            '2021-01-18T10': 1
        }
    }


def test_stats_need_authentication():
    response = client.get(f'/stats')
    assert response.status_code == 401


def test_marking_as_has_voted_twice_fails():
    auth_header = get_auth_header()
    client.post(f'/number/{TEST_NUMBER}', json={'ballot_box_id': '11', 'running_number': 7}, headers=auth_header)
    response = client.post(f'/number/{TEST_NUMBER}', json={'ballot_box_id': '9', 'running_number': 99},
                           headers=auth_header)
    assert response.status_code == 403


def test_login():
    response = client.post('/token', data={'username': 'user', 'password': 'password'})
    assert response.status_code == 200
    response_json = response.json()
    assert 'access_token' in response_json
    assert response_json['token_type'] == 'bearer'
