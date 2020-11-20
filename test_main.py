from fastapi.testclient import TestClient
from freezegun import freeze_time

from main import app

client = TestClient(app)

TEST_NUMBER = '2456789'
NONEXISTENT_NUMBER = '0000000'


def test_read_main():
    response = client.get('/')
    assert response.status_code == 200


def test_read_css():
    response = client.get('/bootstrap.min.css')
    assert response.status_code == 200


def test_check_number():
    response = client.get(f'/number/{TEST_NUMBER}')
    assert response.status_code == 200
    assert response.json() == {
        'number': '2456789',
        'name': 'Werner Wusel',
        'voted': False,
        'ballot_box_id': None,
        'running_number': None,
        'timestamp': None,
        'user': None,
    }


def test_check_nonexistent_number():
    response = client.get(f'/number/{NONEXISTENT_NUMBER}')
    assert response.status_code == 404


def test_mark_as_has_voted():
    response = client.post(f'/number/{TEST_NUMBER}', json={'ballot_box_id': '11', 'running_number': 7})
    assert response.status_code == 200


def test_mark_as_has_voted_nonexistent_number():
    response = client.post(f'/number/{NONEXISTENT_NUMBER}', json={'ballot_box_id': '11', 'running_number': 7})
    assert response.status_code == 404


def test_mark_as_has_voted_requires_ballot_box_id():
    response = client.post(f'/number/{TEST_NUMBER}', json={'running_number': 7})
    assert response.status_code == 400


def test_mark_as_has_voted_requires_running_number():
    response = client.post(f'/number/{TEST_NUMBER}', json={'ballot_box_id': '11'})
    assert response.status_code == 400


@freeze_time('2021-01-18T10:10:10.123Z')
def test_check_has_voted_number_returns_additional_info():
    client.post(f'/number/{TEST_NUMBER}', json={'ballot_box_id': '11', 'running_number': 7})
    response = client.get(f'/number/{TEST_NUMBER}')
    assert response.status_code == 200
    assert response.json() == {
        'number': '2456789',
        'name': 'Werner Wusel',
        'voted': True,
        'ballot_box_id': '11',
        'running_number': 7,
        'timestamp': '2021-01-18T10:10:10.123Z',
        'user': 'username'
    }


def test_marking_as_has_voted_twice_fails():
    client.post(f'/number/{TEST_NUMBER}', json={'ballot_box_id': '11', 'running_number': 7})
    response = client.post(f'/number/{TEST_NUMBER}', json={'ballot_box_id': '9', 'running_number': 99})
    assert response.status_code == 403
