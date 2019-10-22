from flask import json

from backend.util.response.error import ErrorSchema


def test_basic_api_wrong_method(flask_app):
    with flask_app.test_client() as client:
        response = client.patch(
            "/start"
        )

    data = json.loads(response.data)
    ErrorSchema().load(data)
    assert response.status_code == 404


def test_basic_wrong_method(flask_app):
    with flask_app.test_client() as client:
        response = client.patch(
            "/api/order/123"
        )

    assert response.data.decode("utf-8").find("{}") != -1
    assert response.status_code == 405
