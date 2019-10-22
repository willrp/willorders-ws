import pytest

from backend import create_app


@pytest.fixture(scope="session")
def login_disabled_app(flask_app):
    test_app = create_app(flask_env="test")
    test_app.config = flask_app.config
    test_app.config["LOGIN_DISABLED"] = True
    yield test_app


@pytest.fixture(scope="session")
def get_request_function(login_disabled_app):
    def decision_function(http_method):
        if http_method == "GET":
            return login_disabled_app.test_client().get
        elif http_method == "PUT":
            return login_disabled_app.test_client().put
        elif http_method == "DELETE":
            return login_disabled_app.test_client().delete
        else:
            return login_disabled_app.test_client().post

    return decision_function


@pytest.fixture(scope="session")
def json_error_recv():
    return {"error": "error message"}


@pytest.fixture(scope="session")
def willstores_ws(flask_app):
    return flask_app.config["WILLSTORES_WS"]
