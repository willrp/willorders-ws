import pytest
import requests
from uuid import uuid4

from backend.model import Order, Product, OrderProduct
from backend.tests.factories import OrderFactory, ProductFactory, OrderProductFactory
from backend.util.response.error import ErrorSchema
from backend.util.slug import uuid_to_slug


@pytest.fixture(scope="function", autouse=True)
def factory_session(db_perm_session):
    OrderFactory._meta.sqlalchemy_session = db_perm_session
    ProductFactory._meta.sqlalchemy_session = db_perm_session
    OrderProductFactory._meta.sqlalchemy_session = db_perm_session


def test_delete(domain_url, db_perm_session, token_session, prod_list):
    user_slug = uuid_to_slug(uuid4())
    obj = OrderFactory.create(user_slug=user_slug)
    db_perm_session.commit()

    order_slug = obj.uuid_slug
    prod_id_list = [p.meta["id"] for p in prod_list]

    for es_id in prod_id_list:
        product = ProductFactory.create(es_id=es_id)
        OrderProductFactory.create(order=obj, product=product, amount=2)

    db_perm_session.commit()

    assert len(db_perm_session.query(Order).all()) == 1
    assert len(db_perm_session.query(Product).all()) == 5
    assert len(db_perm_session.query(OrderProduct).all()) == 5

    fake_user_slug = uuid_to_slug(uuid4())

    response = token_session.delete(
        domain_url + "/api/order/delete/%s/%s" % (fake_user_slug, order_slug)
    )

    data = response.json()
    assert data == {}
    assert response.status_code == 404
    assert len(db_perm_session.query(Order).all()) == 1
    assert len(db_perm_session.query(Product).all()) == 5
    assert len(db_perm_session.query(OrderProduct).all()) == 5

    response = token_session.delete(
        domain_url + "/api/order/delete/%s/%s" % (user_slug, order_slug)
    )

    data = response.json()
    assert data == {}
    assert response.status_code == 200
    assert len(db_perm_session.query(Order).all()) == 0
    assert len(db_perm_session.query(Product).all()) == 5
    assert len(db_perm_session.query(OrderProduct).all()) == 0

    response = token_session.delete(
        domain_url + "/api/order/delete/%s/%s" % (user_slug, order_slug)
    )

    data = response.json()
    assert data == {}
    assert response.status_code == 404
    assert len(db_perm_session.query(Order).all()) == 0
    assert len(db_perm_session.query(Product).all()) == 5
    assert len(db_perm_session.query(OrderProduct).all()) == 0


def test_delete_unauthorized(domain_url):
    response = requests.delete(
        domain_url + "/api/order/delete/WILLrogerPEREIRAslugBR/WILLrogerPEREIRAslugBR",
    )

    data = response.json()
    ErrorSchema().load(data)
    assert response.status_code == 401
