import pytest
import requests


@pytest.fixture(scope="session")
def domain_url(flask_app, domain_ip):
    return "http://" + domain_ip + ":8000"


@pytest.fixture(scope="function")
def token_session(jwt_test_token):
    sess = requests.Session()
    sess.headers["Authorization"] = "Bearer %s" % jwt_test_token
    return sess
