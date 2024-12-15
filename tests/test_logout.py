import pytest
import sys
import os
import importlib.util


app_path = os.path.abspath(os.path.join(
    os.path.dirname(__file__), '../app.py'))

spec = importlib.util.spec_from_file_location("app", app_path)
app = importlib.util.module_from_spec(spec)
sys.modules["app"] = app
spec.loader.exec_module(app)


@pytest.fixture
def client():
    with app.app.test_client() as client:
        yield client


def test_index_endpoint(client):
    response = client.get('/')
    assert response.status_code == 302


def test_get_logout_page(client):
    response = client.get("/login")
    assert response.status_code == 200
    assert b"login" in response.data.lower()


def test_logout_success(client):
    response = client.post(
        "/login", data={"username": "test", "password": "test"}, follow_redirects=True)
    assert response.status_code == 200
    with client.session_transaction() as session:
        assert session["username"] == "test"


def test_logout_failure(client):
    response = client.post(
        "/login", data={"username": "test1", "password": "test1"})
    assert response.status_code == 401


def test_already_logged_in(client):
    with client.session_transaction() as session:
        session["username"] = "test"
    response = client.get("/login", follow_redirects=True)
    assert response.status_code == 200
    assert b"test" in response.data.lower()


def test_logout_empty_fields(client):
    response = client.post("/login", data={"username": "", "password": ""})
    assert response.status_code == 401
