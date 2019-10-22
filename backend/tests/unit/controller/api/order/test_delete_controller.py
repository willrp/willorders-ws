import pytest
from flask import json

from backend.service import OrderService
from backend.util.response.error import ErrorSchema
from backend.errors.not_found_error import NotFoundError
from werkzeug.exceptions import HTTPException
from requests import ConnectionError
from sqlalchemy.exc import DatabaseError, SQLAlchemyError


@pytest.fixture(scope="function", autouse=True)
def controller_mocker(mocker):
    mocker.patch.object(OrderService, "__init__", return_value=None)


def test_delete_controller(mocker, login_disabled_app):
    with mocker.patch.object(OrderService, "delete", return_value=True):
        with login_disabled_app.test_client() as client:
            response = client.delete(
                "api/order/delete/WILLrogerPEREIRAslugBR"
            )

            data = json.loads(response.data)
            assert data == {}
            assert response.status_code == 200


def test_delete_controller_invalid_slug(login_disabled_app):
    with login_disabled_app.test_client() as client:
        response = client.delete(
            "api/order/delete/invalidslug"
        )

    data = json.loads(response.data)
    ErrorSchema().load(data)

    assert response.status_code == 400


@pytest.mark.parametrize(
    "method,http_method,test_url,error,status_code",
    [
        ("delete", "DELETE", "api/order/delete/WILLrogerPEREIRAslugBR", HTTPException(), 400),
        ("delete", "DELETE", "api/order/delete/WILLrogerPEREIRAslugBR", NotFoundError(), 404),
        ("delete", "DELETE", "api/order/delete/WILLrogerPEREIRAslugBR", ConnectionError(), 502),
        ("delete", "DELETE", "api/order/delete/WILLrogerPEREIRAslugBR", DatabaseError("statement", "params", "orig"), 400),
        ("delete", "DELETE", "api/order/delete/WILLrogerPEREIRAslugBR", SQLAlchemyError(), 504),
        ("delete", "DELETE", "api/order/delete/WILLrogerPEREIRAslugBR", Exception(), 500)
    ]
)
def test_delete_controller_error(mocker, get_request_function, method, http_method, test_url, error, status_code):
    with mocker.patch.object(OrderService, method, side_effect=error):
        make_request = get_request_function(http_method)

        response = make_request(
            test_url
        )

        data = json.loads(response.data)

        if status_code == 404:
            assert data == {}
        else:
            ErrorSchema().load(data)

        assert response.status_code == status_code
