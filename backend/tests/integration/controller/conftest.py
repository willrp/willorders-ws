import pytest
from flask.testing import FlaskClient
from werkzeug.datastructures import Headers

from backend import create_app


@pytest.fixture(scope="session")
def token_app(flask_app, jwt_test_token):
    class FlaskTokenClient(FlaskClient):
        def __init__(self, *args, **kwargs):
            super(FlaskTokenClient, self).__init__(*args, **kwargs)

        def open(self, *args, **kwargs):
            headers = kwargs.pop("headers", Headers())
            headers.extend(Headers({"Authorization": "Bearer %s" % jwt_test_token}))
            kwargs["headers"] = headers
            return super().open(*args, **kwargs)

    app = create_app(flask_env="test")
    app.config = flask_app.config
    app.test_client_class = FlaskTokenClient
    return app
