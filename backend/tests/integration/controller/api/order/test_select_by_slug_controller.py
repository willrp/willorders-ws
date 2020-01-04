import pytest
from flask import json
from uuid import uuid4

from backend.tests.factories import OrderFactory, ProductFactory, OrderProductFactory
from backend.util.response.order import OrderSchema
from backend.util.response.error import ErrorSchema
from backend.util.slug import uuid_to_slug


@pytest.fixture(scope="function", autouse=True)
def factory_session(db_perm_session):
    OrderFactory._meta.sqlalchemy_session = db_perm_session
    ProductFactory._meta.sqlalchemy_session = db_perm_session
    OrderProductFactory._meta.sqlalchemy_session = db_perm_session


def test_select_by_slug_controller(token_app, db_perm_session, prod_list):
    user_slug = uuid_to_slug(uuid4())
    obj = OrderFactory.create(user_slug=user_slug)
    db_perm_session.commit()

    order_slug = obj.uuid_slug
    prod_id_list = [p.meta["id"] for p in prod_list]

    amount = 1
    for es_id in prod_id_list:
        product = ProductFactory.create(es_id=es_id)
        OrderProductFactory.create(order=obj, product=product, amount=amount)
        amount += 1

    db_perm_session.commit()

    with token_app.test_client() as client:
        response = client.get(
            "api/order/%s/%s" % (user_slug, order_slug)
        )

    data = json.loads(response.data)
    OrderSchema().load(data)
    assert response.status_code == 200
    assert data["slug"] == order_slug
    assert data["product_types"] == len(prod_list)
    assert data["items_amount"] == ((1 + len(prod_list)) * len(prod_list)) / 2
    assert len(data["products"]) == len(prod_list)

    for item in [item.to_dict() for item in obj.items]:
        product = next(p for p in data["products"] if p["id"] == item["item_id"])
        assert product["amount"] == item["amount"]

    with token_app.test_client() as client:
        response = client.get(
            "api/order/WILLrogerPEREIRAslugBR/WILLrogerPEREIRAslugBR"
        )

    data = json.loads(response.data)
    assert data == {}
    assert response.status_code == 404

    with token_app.test_client() as client:
        response = client.get(
            "api/order/WILLrogerPEREIRAslugBR/%s" % order_slug
        )

    data = json.loads(response.data)
    assert data == {}
    assert response.status_code == 404


def test_select_by_slug_controller_unauthorized(flask_app):
    with flask_app.test_client() as client:
        response = client.get(
            "api/order/WILLrogerPEREIRAslugBR/WILLrogerPEREIRAslugBR"
        )

    data = json.loads(response.data)
    ErrorSchema().load(data)
    assert response.status_code == 401
