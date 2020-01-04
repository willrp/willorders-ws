import pytest
import responses
import re
from flask import json
from unittest.mock import MagicMock
from copy import deepcopy
from json import JSONDecodeError

from backend.service import OrderService
from backend.util.response.user_orders import UserOrdersSchema
from backend.util.response.error import ErrorSchema
from werkzeug.exceptions import HTTPException
from requests import ConnectionError
from sqlalchemy.exc import DatabaseError, DataError, SQLAlchemyError
from backend.errors.no_content_error import NoContentError


@pytest.fixture(scope="module")
def request_json():
    return {
        "page": "1",
        "page_size": "5",
        "datespan": {
            "start": "2019-10-20",
            "end": "2019-10-24"
        }
    }


@pytest.fixture(scope="module")
def response_json():
    return {
        "slug": "slug",
        "product_types": 0,
        "items_amount": 0,
        "updated_at": "2019-10-12T00:00:00.000Z"
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


def test_select_by_user_slug_controller(mocker, login_disabled_app, willstores_ws, request_json, response_json, willstores_response_json):
    mock_order = MagicMock()
    mock_order.to_dict.return_value = response_json
    with mocker.patch.object(OrderService, "select_by_user_slug", return_value={"orders": [mock_order, mock_order], "total": 0, "pages": 0}):
        with responses.RequestsMock() as rsps:
            rsps.add(responses.POST, re.compile(willstores_ws),
                status=200,
                json=willstores_response_json
            )

            with login_disabled_app.test_client() as client:
                response = client.post(
                    "api/order/user/WILLrogerPEREIRAslugBR"
                )

            data = json.loads(response.data)
            UserOrdersSchema().load(data)
            assert response.status_code == 200
            assert len(data["orders"]) == 2
            assert data["total"] == 0
            assert data["pages"] == 0

            for order in data["orders"]:
                assert order["slug"] == "slug"
                assert order["product_types"] == 0
                assert order["items_amount"] == 0
                assert order["total"]["outlet"] == 10.55
                assert order["total"]["retail"] == 20.9
                assert order["total"]["symbol"] == "£"

    with mocker.patch.object(OrderService, "select_by_user_slug", return_value={"orders": [mock_order], "total": 0, "pages": 0}):
        with responses.RequestsMock() as rsps:
            rsps.add(responses.POST, re.compile(willstores_ws),
                status=200,
                json=willstores_response_json
            )

            with login_disabled_app.test_client() as client:
                response = client.post(
                    "api/order/user/WILLrogerPEREIRAslugBR",
                    json=request_json
                )

            data = json.loads(response.data)
            UserOrdersSchema().load(data)
            assert response.status_code == 200
            assert len(data["orders"]) == 1
            assert data["total"] == 0
            assert data["pages"] == 0

            for order in data["orders"]:
                assert order["slug"] == "slug"
                assert order["product_types"] == 0
                assert order["items_amount"] == 0
                assert order["total"]["outlet"] == 10.55
                assert order["total"]["retail"] == 20.9
                assert order["total"]["symbol"] == "£"


def test_select_by_user_slug_controller_invalid_slug(login_disabled_app):
    with login_disabled_app.test_client() as client:
        response = client.post(
            "api/order/user/invalidslug"
        )

    data = json.loads(response.data)
    ErrorSchema().load(data)

    assert response.status_code == 400


def test_select_by_user_slug_controller_invalid_json(login_disabled_app, request_json):
    invalid_page = deepcopy(request_json)
    invalid_page.update(page=-1)

    with login_disabled_app.test_client() as client:
        response = client.post(
            "api/order/user/WILLrogerPEREIRAslugBR",
            json=invalid_page
        )

    data = json.loads(response.data)
    ErrorSchema().load(data)

    assert response.status_code == 400

    toosmall_page_size = deepcopy(request_json)
    toosmall_page_size.update(page_size=0)

    with login_disabled_app.test_client() as client:
        response = client.post(
            "api/order/user/WILLrogerPEREIRAslugBR",
            json=toosmall_page_size
        )

    data = json.loads(response.data)
    ErrorSchema().load(data)

    assert response.status_code == 400

    toobig_page_size = deepcopy(request_json)
    toobig_page_size.update(page_size=999)

    with login_disabled_app.test_client() as client:
        response = client.post(
            "api/order/user/WILLrogerPEREIRAslugBR",
            json=toobig_page_size
        )

    data = json.loads(response.data)
    ErrorSchema().load(data)

    assert response.status_code == 400

    switched_datespan = deepcopy(request_json)
    switched_datespan.update(datespan={"start": "2019-10-25", "end": "2019-10-23"})   

    with login_disabled_app.test_client() as client:
        response = client.post(
            "api/order/user/WILLrogerPEREIRAslugBR",
            json=switched_datespan
        )

    data = json.loads(response.data)
    ErrorSchema().load(data)

    assert response.status_code == 400

    overflow_datespan = deepcopy(request_json)
    overflow_datespan.update(datespan={"start": "2019-13-20", "end": "2019-10-33"})

    with login_disabled_app.test_client() as client:
        response = client.post(
            "api/order/user/WILLrogerPEREIRAslugBR",
            json=overflow_datespan
        )

    data = json.loads(response.data)
    ErrorSchema().load(data)

    assert response.status_code == 400


@pytest.mark.parametrize(
    "method,http_method,test_url,error,status_code",
    [
        ("select_by_user_slug", "POST", "api/order/user/WILLrogerPEREIRAslugBR", NoContentError(), 204),
        ("select_by_user_slug", "POST", "api/order/user/WILLrogerPEREIRAslugBR", HTTPException(), 400),
        ("select_by_user_slug", "POST", "api/order/user/WILLrogerPEREIRAslugBR", ConnectionError(), 502),
        ("select_by_user_slug", "POST", "api/order/user/WILLrogerPEREIRAslugBR", DataError("statement", "params", "DETAIL:  orig\n"), 400),
        ("select_by_user_slug", "POST", "api/order/user/WILLrogerPEREIRAslugBR", DatabaseError("statement", "params", "orig"), 400),
        ("select_by_user_slug", "POST", "api/order/user/WILLrogerPEREIRAslugBR", SQLAlchemyError(), 504),
        ("select_by_user_slug", "POST", "api/order/user/WILLrogerPEREIRAslugBR", Exception(), 500)
    ]
)
def test_select_by_user_slug_controller_error(mocker, get_request_function, method, http_method, test_url, error, status_code):
    with mocker.patch.object(OrderService, method, side_effect=error):
        make_request = get_request_function(http_method)

        response = make_request(
            test_url
        )

        if status_code == 204:
            with pytest.raises(JSONDecodeError):
                json.loads(response.data)
        else:
            data = json.loads(response.data)
            ErrorSchema().load(data)

        assert response.status_code == status_code


@pytest.mark.parametrize(
    "test_url, status_code",
    [
        ("api/order/user/WILLrogerPEREIRAslugBR", 400),
        ("api/order/user/WILLrogerPEREIRAslugBR", 401),
        ("api/order/user/WILLrogerPEREIRAslugBR", 500),
        ("api/order/user/WILLrogerPEREIRAslugBR", 502),
        ("api/order/user/WILLrogerPEREIRAslugBR", 504),
    ]
)
def test_select_by_user_slug_controller_http_error(mocker, login_disabled_app, willstores_ws, json_error_recv, test_url, status_code):
    with mocker.patch.object(OrderService, "select_by_user_slug", return_value={"orders": [MagicMock()], "total": 0, "pages": 0}):
        with responses.RequestsMock() as rsps:
            rsps.add(responses.POST, re.compile(willstores_ws),
                status=status_code,
                json=json_error_recv
            )

            with login_disabled_app.test_client() as client:
                response = client.post(
                    test_url
                )

            data = json.loads(response.data)
            ErrorSchema().load(data)

            assert response.status_code == status_code
