import pytest
import json
from flask_restplus import Api, Resource

from backend import create_app
from backend.controller import auth_required
from backend.util.response.error import ErrorSchema


def make_protected_app():
    app = create_app(flask_env="test")
    api = Api(app)

    @api.route("/protected")
    class Protected(Resource):
        @auth_required()
        def get(self):
            return "Test access granted"

    return app


def test_auth_required_decorator_bearer_token(jwt_test_token):
    protected_app = make_protected_app()
    authorization_send = {"Authorization": "Bearer %s" % jwt_test_token}

    with protected_app.test_client() as client:
        response = client.get(
            "/protected",
            headers=authorization_send
        )

    data = response.data

    assert data.decode("utf-8").find("Test access granted") != -1
    assert response.status_code == 200


def test_auth_required_decorator_unauthorized(jwt_test_token):
    protected_app = make_protected_app()

    with protected_app.test_client() as client:
        response = client.get(
            "/protected"
        )

    data = json.loads(response.data)
    ErrorSchema().load(data)

    assert data["error"].find("Unauthorized") != -1
    assert response.status_code == 401


def test_auth_required_decorator_login_disabled():
    protected_app = make_protected_app()

    protected_app.config["LOGIN_DISABLED"] = True
    with protected_app.test_client() as client:
        response = client.get(
            "/protected"
        )

    data = response.data

    assert data.decode("utf-8").find("Test access granted") != -1
    assert response.status_code == 200


@pytest.mark.parametrize(
    "token, info",
    [
        ("BadToken", "Invalid token"),
        ("Bearer", "Invalid token"),
        ("Bearer invalid.token", "Unauthorized"),
    ]
)
def test_auth_required_decorator_invalid_token(token, info):
    protected_app = make_protected_app()
    authorization_send = {"Authorization": token}

    with protected_app.test_client() as client:
        response = client.get(
            "/protected",
            headers=authorization_send
        )

    data = json.loads(response.data)
    ErrorSchema().load(data)

    assert data["error"].find(info) != -1
    assert response.status_code == 401
