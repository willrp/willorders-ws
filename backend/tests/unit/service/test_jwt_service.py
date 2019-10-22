import pytest

from backend.service import JWTService
from backend.errors.access_error import InvalidTokenError, UnauthorizedError


@pytest.fixture(scope="function")
def service(monkeypatch):
    with monkeypatch.context() as m:
        m.setenv("ACCESS_TOKEN", "TEST")
        service = JWTService()
        return service


def test_jwt_service_verify_header(service):
    assert service.verify_header(auth_header="Bearer TEST") is True


def test_jwt_service_verify_header_error_token_formation(service):
    with pytest.raises(InvalidTokenError):
        service.verify_header(auth_header="BadToken")


def test_jwt_service_verify_header_error_token_type(service):
    with pytest.raises(InvalidTokenError):
        service.verify_header(auth_header="Bearer")


def test_jwt_service_verify_header_error_unauthorized(service):
    with pytest.raises(UnauthorizedError):
        service.verify_header(auth_header="Bearer NOTTEST")
