import pytest
import responses
import re
from flask import json
from copy import deepcopy

from backend.service import OrderService
from backend.util.response.error import ErrorSchema
from werkzeug.exceptions import HTTPException
from requests import ConnectionError
from sqlalchemy.exc import DatabaseError, SQLAlchemyError


@pytest.fixture(scope="module")
def request_json():
    return {
        "user_slug": "WILLrogerPEREIRAslugBR",
        "item_list": [
            {
                "item_id": "string",
                "amount": 1
            }
        ]
    }


@pytest.fixture(scope="module")
def willstores_response_json():
    return {
        "total": {
            "outlet": 10.55,
            "retail": 20.9,
            "symbol": "£"
        }
    }


@pytest.fixture(scope="function", autouse=True)
def controller_mocker(mocker):
    mocker.patch.object(OrderService, "__init__", return_value=None)


def test_insert_controller(mocker, login_disabled_app, willstores_ws, request_json, willstores_response_json):
    mocker.patch.object(OrderService, "insert", return_value=True)

    with responses.RequestsMock() as rsps:
        rsps.add(responses.POST, re.compile(willstores_ws),
            status=200,
            json=willstores_response_json
        )

        with login_disabled_app.test_client() as client:
            response = client.put(
                "api/order/insert",
                json=request_json
            )

        data = json.loads(response.data)
        assert data == {}
        assert response.status_code == 201


def test_insert_controller_no_json(login_disabled_app):
    with login_disabled_app.test_client() as client:
        response = client.put(
            "api/order/insert"
        )

    data = json.loads(response.data)
    ErrorSchema().load(data)

    assert response.status_code == 400


def test_insert_controller_invalid_json(login_disabled_app, request_json):
    invalid_user_slug = deepcopy(request_json)
    invalid_user_slug.update(user_slug="invalidslug")

    with login_disabled_app.test_client() as client:
        response = client.put(
            "api/order/insert",
            json=invalid_user_slug
        )

    data = json.loads(response.data)
    ErrorSchema().load(data)

    assert response.status_code == 400

    not_unique_item_list = deepcopy(request_json)
    not_unique_item_list.update(item_list=[{"item_id": "string", "amount": 1}, {"item_id": "string", "amount": 2}])

    with login_disabled_app.test_client() as client:
        response = client.put(
            "api/order/insert",
            json=not_unique_item_list
        )

    data = json.loads(response.data)
    ErrorSchema().load(data)

    assert response.status_code == 400

    invalid_item_id = deepcopy(request_json)
    invalid_item_id.update(item_list=[{"item_id": "", "amount": 1}])

    with login_disabled_app.test_client() as client:
        response = client.put(
            "api/order/insert",
            json=invalid_item_id
        )

    data = json.loads(response.data)
    ErrorSchema().load(data)

    assert response.status_code == 400

    invalid_amount = deepcopy(request_json)
    invalid_amount.update(item_list=[{"item_id": "string", "amount": 0}])

    with login_disabled_app.test_client() as client:
        response = client.put(
            "api/order/insert",
            json=invalid_amount
        )

    data = json.loads(response.data)
    ErrorSchema().load(data)

    assert response.status_code == 400


@pytest.mark.parametrize(
    "method,http_method,test_url,error,status_code",
    [
        ("insert", "PUT", "api/order/insert", HTTPException(), 400),
        ("insert", "PUT", "api/order/insert", ConnectionError(), 502),
        ("insert", "PUT", "api/order/insert", DatabaseError("statement", "params", "orig"), 400),
        ("insert", "PUT", "api/order/insert", SQLAlchemyError(), 504),
        ("insert", "PUT", "api/order/insert", Exception(), 500)
    ]
)
def test_insert_controller_error(mocker, get_request_function, willstores_ws, request_json, willstores_response_json, method, http_method, test_url, error, status_code):
    mocker.patch.object(OrderService, method, side_effect=error)

    with responses.RequestsMock() as rsps:
        rsps.add(responses.POST, re.compile(willstores_ws),
            status=200,
            json=willstores_response_json
        )

        make_request = get_request_function(http_method)

        response = make_request(
            test_url,
            json=request_json
        )

        data = json.loads(response.data)
        ErrorSchema().load(data)

        assert response.status_code == status_code


@pytest.mark.parametrize(
    "test_url, status_code",
    [
        ("api/order/insert", 400),
        ("api/order/insert", 401),
        ("api/order/insert", 500),
        ("api/order/insert", 502),
        ("api/order/insert", 504),
    ]
)
def test_insert_controller_http_error(mocker, login_disabled_app, willstores_ws, request_json, json_error_recv, test_url, status_code):
    mocker.patch.object(OrderService, "insert", return_value=True)

    with responses.RequestsMock() as rsps:
        rsps.add(responses.POST, re.compile(willstores_ws),
            status=status_code,
            json=json_error_recv
        )

        with login_disabled_app.test_client() as client:
            response = client.put(
                test_url,
                json=request_json
            )

        data = json.loads(response.data)
        ErrorSchema().load(data)

        assert response.status_code == status_code
