import copy
import pytest
from fastapi.testclient import TestClient

from src import app as app_module

client = TestClient(app_module.app)
# keep original state for reset
_original_activities = copy.deepcopy(app_module.activities)


@pytest.fixture(autouse=True)
def reset_activities():
    # arrange: restore activities dict before each test
    app_module.activities.clear()
    app_module.activities.update(copy.deepcopy(_original_activities))


def test_root_redirect():
    # act
    response = client.get("/")
    # assert
    # uvicorn/static may serve index directly (200) or issue a redirect
    assert response.status_code in (200, 302, 307)
    if response.status_code in (302, 307):
        assert response.headers["location"].endswith("/static/index.html")


def test_get_activities():
    # act
    response = client.get("/activities")
    # assert
    assert response.status_code == 200
    assert set(response.json()) == set(_original_activities)


def test_signup_success():
    # act
    response = client.post("/activities/Chess Club/signup?email=test@x")
    # assert
    assert response.status_code == 200
    assert "Signed up" in response.json()["message"]
    assert "test@x" in app_module.activities["Chess Club"]["participants"]


def test_signup_already_exists():
    # act
    existing = _original_activities["Chess Club"]["participants"][0]
    response = client.post(f"/activities/Chess Club/signup?email={existing}")
    # assert
    assert response.status_code == 400
    assert "already" in response.json()["detail"].lower()


def test_signup_missing_activity():
    # act
    response = client.post("/activities/Nonexistent/signup?email=test@x")
    # assert
    assert response.status_code == 404


def test_remove_participant_success():
    # arrange
    target = _original_activities["Chess Club"]["participants"][0]
    # act
    response = client.delete(f"/activities/Chess Club/participants?email={target}")
    # assert
    assert response.status_code == 200
    assert target not in app_module.activities["Chess Club"]["participants"]


def test_remove_participant_not_found():
    # act
    response = client.delete("/activities/Chess Club/participants?email=not@here")
    # assert
    assert response.status_code == 404


def test_remove_from_nonexistent():
    # act
    response = client.delete("/activities/Nope/participants?email=some@x")
    # assert
    assert response.status_code == 404
