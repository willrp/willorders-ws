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


def test_delete_controller(token_app, db_perm_session, prod_list):
    user_slug = uuid_to_slug(uuid4())
    obj = OrderFactory.create(user_slug=user_slug)
    db_perm_session.commit()

    slug = obj.uuid_slug
    prod_id_list = [p.meta["id"] for p in prod_list]

    for es_id in prod_id_list:
        product = ProductFactory.create(es_id=es_id)
        OrderProduct(order=obj, product=product, amount=2)

    db_perm_session.commit()

    assert len(db_perm_session.query(Order).all()) == 1
    assert len(db_perm_session.query(Product).all()) == 5
    assert len(db_perm_session.query(OrderProduct).all()) == 5

    with token_app.test_client() as client:
        response = client.delete(
            "api/order/delete/%s" % slug
        )

    data = json.loads(response.data)
    assert data == {}
    assert response.status_code == 200
    assert len(db_perm_session.query(Order).all()) == 0
    assert len(db_perm_session.query(Product).all()) == 5
    assert len(db_perm_session.query(OrderProduct).all()) == 0

    with token_app.test_client() as client:
        response = client.delete(
            "api/order/delete/%s" % slug
        )

    data = json.loads(response.data)
    assert data == {}
    assert response.status_code == 404
    assert len(db_perm_session.query(Order).all()) == 0
    assert len(db_perm_session.query(Product).all()) == 5
    assert len(db_perm_session.query(OrderProduct).all()) == 0


def test_delete_controller_unauthorized(flask_app):
    with flask_app.test_client() as client:
        response = client.delete(
            "api/order/delete/WILLrogerPEREIRAslugBR",
        )

    data = json.loads(response.data)
    ErrorSchema().load(data)
    assert response.status_code == 401
