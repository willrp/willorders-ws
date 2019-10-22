import pytest
import responses
import re
from flask import json
from unittest.mock import MagicMock

from backend.service import OrderService
from backend.util.response.order import OrderSchema
from backend.util.response.error import ErrorSchema
from backend.errors.not_found_error import NotFoundError
from werkzeug.exceptions import HTTPException
from requests import ConnectionError
from sqlalchemy.exc import DatabaseError, SQLAlchemyError


@pytest.fixture(scope="module")
def response_json():
    return {
        "slug": "slug",
        "user_slug": "user_slug",
        "product_types": 0,
        "items_amount": 0,
        "total": {
            "outlet": 10.55,
            "retail": 20.9,
            "symbol": "£"
        },
        "updated_at": "2019-10-12T00:00:00.000Z"
    }


@pytest.fixture(scope="module")
def willstores_response_json():
    return {
        "products": [
            {
                "id": "id",
                "name": "string",
                "image": "string",
                "price": {
                    "outlet": 10.55,
                    "retail": 20.9,
                    "symbol": "£"
                },
                "discount": 80.5
            }
        ]
    }


@pytest.fixture(scope="function", autouse=True)
def controller_mocker(mocker):
    mocker.patch.object(OrderService, "__init__", return_value=None)


def test_select_by_slug_controller(mocker, login_disabled_app, willstores_ws, response_json, willstores_response_json):
    mock_item = MagicMock()
    mock_item.to_dict.return_value = {"item_id": "id", "amount": 5}
    mock_order = MagicMock()
    mock_order.items = [mock_item]
    mock_order.to_dict.return_value = response_json
    with mocker.patch.object(OrderService, "select_by_slug", return_value=mock_order):
        with responses.RequestsMock() as rsps:
            rsps.add(responses.POST, re.compile(willstores_ws),
                status=200,
                json=willstores_response_json
            )

            with login_disabled_app.test_client() as client:
                response = client.get(
                    "api/order/WILLrogerPEREIRAslugBR"
                )

            data = json.loads(response.data)
            OrderSchema().load(data)
            assert response.status_code == 200
            assert data["slug"] == "slug"
            assert data["user_slug"] == "user_slug"
            assert data["product_types"] == 0
            assert data["items_amount"] == 0
            assert len(data["products"]) == 1


def test_select_by_slug_controller_invalid_slug(login_disabled_app):
    with login_disabled_app.test_client() as client:
        response = client.get(
            "api/order/invalidslug"
        )

    data = json.loads(response.data)
    ErrorSchema().load(data)

    assert response.status_code == 400


@pytest.mark.parametrize(
    "method,http_method,test_url,error,status_code",
    [
        ("select_by_slug", "GET", "api/order/WILLrogerPEREIRAslugBR", HTTPException(), 400),
        ("select_by_slug", "GET", "api/order/WILLrogerPEREIRAslugBR", NotFoundError(), 404),
        ("select_by_slug", "GET", "api/order/WILLrogerPEREIRAslugBR", ConnectionError(), 502),
        ("select_by_slug", "GET", "api/order/WILLrogerPEREIRAslugBR", DatabaseError("statement", "params", "orig"), 400),
        ("select_by_slug", "GET", "api/order/WILLrogerPEREIRAslugBR", SQLAlchemyError(), 504),
        ("select_by_slug", "GET", "api/order/WILLrogerPEREIRAslugBR", Exception(), 500)
    ]
)
def test_select_by_slug_controller_error(mocker, get_request_function, method, http_method, test_url, error, status_code):
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


@pytest.mark.parametrize(
    "test_url, status_code",
    [
        ("api/order/WILLrogerPEREIRAslugBR", 400),
        ("api/order/WILLrogerPEREIRAslugBR", 401),
        ("api/order/WILLrogerPEREIRAslugBR", 500),
        ("api/order/WILLrogerPEREIRAslugBR", 502),
        ("api/order/WILLrogerPEREIRAslugBR", 504),
    ]
)
def test_select_by_slug_controller_http_error(mocker, login_disabled_app, willstores_ws, json_error_recv, test_url, status_code):
    with mocker.patch.object(OrderService, "select_by_slug", return_value=MagicMock(autospec=True)):
        with responses.RequestsMock() as rsps:
            rsps.add(responses.POST, re.compile(willstores_ws),
                status=status_code,
                json=json_error_recv
            )

            with login_disabled_app.test_client() as client:
                response = client.get(
                    test_url
                )

            data = json.loads(response.data)
            ErrorSchema().load(data)

            assert response.status_code == status_code
