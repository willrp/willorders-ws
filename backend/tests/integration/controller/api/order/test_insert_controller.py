import pytest
from flask import json
from uuid import uuid4

from backend.model import Order, Product, OrderProduct
from backend.tests.factories import OrderFactory, ProductFactory
from backend.util.response.error import ErrorSchema
from backend.util.slug import uuid_to_slug


@pytest.fixture(scope="function", autouse=True)
def factory_session(db_perm_session):
    OrderFactory._meta.sqlalchemy_session = db_perm_session
    ProductFactory._meta.sqlalchemy_session = db_perm_session


def test_insert_controller(token_app, db_perm_session, prod_list):
    assert len(db_perm_session.query(Order).all()) == 0
    assert len(db_perm_session.query(Product).all()) == 0
    assert len(db_perm_session.query(OrderProduct).all()) == 0

    user_slug = uuid_to_slug(uuid4())
    prod_id_list = [p.meta["id"] for p in prod_list]
    item_list = [{"item_id": prod_id, "amount": 2} for prod_id in prod_id_list]

    with token_app.test_client() as client:
        response = client.put(
            "api/order/insert",
            json={"user_slug": user_slug, "item_list": item_list}
        )

    data = json.loads(response.data)
    assert data == {}
    assert response.status_code == 201
    assert len(db_perm_session.query(Order).all()) == 1
    assert len(db_perm_session.query(Product).all()) == 5
    assert len(db_perm_session.query(OrderProduct).all()) == 5

    with token_app.test_client() as client:
        response = client.put(
            "api/order/insert",
            json={"user_slug": user_slug, "item_list": item_list}
        )

    data = json.loads(response.data)
    assert data == {}
    assert response.status_code == 201
    assert len(db_perm_session.query(Order).all()) == 2
    assert len(db_perm_session.query(Product).all()) == 5
    assert len(db_perm_session.query(OrderProduct).all()) == 10


def test_insert_controller_not_registered(token_app, db_perm_session):
    assert len(db_perm_session.query(Order).all()) == 0
    assert len(db_perm_session.query(Product).all()) == 0
    assert len(db_perm_session.query(OrderProduct).all()) == 0

    user_slug = uuid_to_slug(uuid4())
    bad_item_list = [{"item_id": str(uuid4()), "amount": 2} for i in range(3)]

    with token_app.test_client() as client:
        response = client.put(
            "api/order/insert",
            json={"user_slug": user_slug, "item_list": bad_item_list}
        )

    data = json.loads(response.data)
    ErrorSchema().load(data)
    assert response.status_code == 400
    assert data["error"].find("not registered") != -1

    assert len(db_perm_session.query(Order).all()) == 0
    assert len(db_perm_session.query(Product).all()) == 0
    assert len(db_perm_session.query(OrderProduct).all()) == 0


def test_insert_controller_unauthorized(flask_app, prod_list):
    user_slug = uuid_to_slug(uuid4())
    prod_id_list = [p.meta["id"] for p in prod_list]
    item_list = [{"item_id": prod_id, "amount": 2} for prod_id in prod_id_list]

    with flask_app.test_client() as client:
        response = client.put(
            "api/order/insert",
            json={"user_slug": user_slug, "item_list": item_list}
        )

    data = json.loads(response.data)
    ErrorSchema().load(data)
    assert response.status_code == 401
