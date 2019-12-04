import pytest
from flask import json
from uuid import uuid4
from datetime import date, timedelta
from json import JSONDecodeError

from backend.tests.factories import OrderFactory, ProductFactory, OrderProductFactory
from backend.util.response.user_orders import UserOrdersSchema
from backend.util.response.error import ErrorSchema
from backend.util.slug import uuid_to_slug


@pytest.fixture(scope="function", autouse=True)
def factory_session(db_perm_session):
    OrderFactory._meta.sqlalchemy_session = db_perm_session
    ProductFactory._meta.sqlalchemy_session = db_perm_session
    OrderProductFactory._meta.sqlalchemy_session = db_perm_session


def test_select_by_user_controller(token_app, db_perm_session, prod_list):
    user_slug = uuid_to_slug(uuid4())
    prod_id_list = [p.meta["id"] for p in prod_list]
    product_list = [ProductFactory.create(es_id=es_id) for es_id in prod_id_list]
    db_perm_session.commit()

    obj_list = OrderFactory.create_batch(2, user_slug=user_slug)

    for product in product_list:
        OrderProductFactory.create(order=obj_list[0], product=product, amount=2)

    for product in product_list[0:3]:
        OrderProductFactory.create(order=obj_list[1], product=product, amount=5)

    db_perm_session.commit()

    with token_app.test_client() as client:
        response = client.post(
            "api/order/user/%s" % user_slug
        )

    data = json.loads(response.data)
    UserOrdersSchema().load(data)
    assert response.status_code == 200
    assert len(data["orders"]) == 2
    assert data["total"] == 2
    assert data["pages"] == 1

    order_slug_list = [order["slug"] for order in data["orders"]]
    for slug in order_slug_list:
        assert slug in [obj.uuid_slug for obj in obj_list]

    user_slug_list = [order["user_slug"] for order in data["orders"]]
    for slug in user_slug_list:
        assert slug == user_slug

    for order in data["orders"]:
        if order["slug"] == obj_list[0].uuid_slug:
            assert order["product_types"] == 5
            assert order["items_amount"] == 10
        else:
            assert order["product_types"] == 3
            assert order["items_amount"] == 15

    with token_app.test_client() as client:
        response = client.post(
            "api/order/user/%s" % user_slug,
            json={
                "page": "1",
                "page_size": "1"
            }
        )

    data = json.loads(response.data)
    UserOrdersSchema().load(data)
    assert response.status_code == 200
    assert len(data["orders"]) == 1
    assert data["total"] == 2
    assert data["pages"] == 2

    with token_app.test_client() as client:
        response = client.post(
            "api/order/user/%s" % user_slug,
            json={
                "datespan": {
                    "start": str(date.today() - timedelta(days=1)),
                    "end": str(date.today() + timedelta(days=1))
                }
            }
        )

    data = json.loads(response.data)
    UserOrdersSchema().load(data)
    assert response.status_code == 200
    assert len(data["orders"]) == 2
    assert data["total"] == 2
    assert data["pages"] == 1

    with token_app.test_client() as client:
        response = client.post(
            "api/order/user/WILLrogerPEREIRAslugBR"
        )

    with pytest.raises(JSONDecodeError):
        json.loads(response.data)

    assert response.status_code == 204


def test_select_by_user_controller_not_registered(token_app, db_perm_session):
    user_slug = uuid_to_slug(uuid4())
    bad_obj_list = OrderFactory.create_batch(4, user_slug=user_slug)
    bad_product = ProductFactory.create()

    for order in bad_obj_list:
        OrderProductFactory.create(order=order, product=bad_product, amount=5)

    db_perm_session.commit()

    with token_app.test_client() as client:
        response = client.post(
            "api/order/user/%s" % user_slug
        )

    data = json.loads(response.data)
    ErrorSchema().load(data)
    assert response.status_code == 400
    assert data["error"].find("not registered") != -1


def test_select_by_user_controller_unauthorized(flask_app):
    with flask_app.test_client() as client:
        response = client.post(
            "api/order/user/WILLrogerPEREIRAslugBR",
        )

    data = json.loads(response.data)
    ErrorSchema().load(data)
    assert response.status_code == 401
