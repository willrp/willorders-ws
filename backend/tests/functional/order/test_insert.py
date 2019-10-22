import pytest
import requests
from uuid import uuid4

from backend.model import Order, Product, OrderProduct
from backend.tests.factories import OrderFactory, ProductFactory
from backend.util.response.error import ErrorSchema
from backend.util.slug import uuid_to_slug


@pytest.fixture(scope="function", autouse=True)
def factory_session(db_perm_session):
    OrderFactory._meta.sqlalchemy_session = db_perm_session
    ProductFactory._meta.sqlalchemy_session = db_perm_session


def test_insert(domain_url, db_perm_session, token_session, prod_list):
    assert len(db_perm_session.query(Order).all()) == 0
    assert len(db_perm_session.query(Product).all()) == 0
    assert len(db_perm_session.query(OrderProduct).all()) == 0

    user_slug = uuid_to_slug(uuid4())
    prod_id_list = [p.meta["id"] for p in prod_list]
    item_list = [{"item_id": prod_id, "amount": 2} for prod_id in prod_id_list]

    response = token_session.put(
        domain_url + "/api/order/insert",
        json={"user_slug": user_slug, "item_list": item_list}
    )

    data = response.json()
    assert data == {}
    assert response.status_code == 201
    assert len(db_perm_session.query(Order).all()) == 1
    assert len(db_perm_session.query(Product).all()) == 5
    assert len(db_perm_session.query(OrderProduct).all()) == 5

    response = token_session.put(
        domain_url + "/api/order/insert",
        json={"user_slug": user_slug, "item_list": item_list}
    )

    data = response.json()
    assert data == {}
    assert response.status_code == 201
    assert len(db_perm_session.query(Order).all()) == 2
    assert len(db_perm_session.query(Product).all()) == 5
    assert len(db_perm_session.query(OrderProduct).all()) == 10


def test_insert_not_registered(domain_url, db_perm_session, token_session):
    assert len(db_perm_session.query(Order).all()) == 0
    assert len(db_perm_session.query(Product).all()) == 0
    assert len(db_perm_session.query(OrderProduct).all()) == 0

    user_slug = uuid_to_slug(uuid4())
    bad_item_list = [{"item_id": str(uuid4()), "amount": 2} for i in range(3)]

    response = token_session.put(
        domain_url + "/api/order/insert",
        json={"user_slug": user_slug, "item_list": bad_item_list}
    )

    data = response.json()
    ErrorSchema().load(data)
    assert response.status_code == 400
    assert data["error"].find("not registered") != -1

    assert len(db_perm_session.query(Order).all()) == 0
    assert len(db_perm_session.query(Product).all()) == 0
    assert len(db_perm_session.query(OrderProduct).all()) == 0


def test_insert_unauthorized(domain_url, prod_list):
    user_slug = uuid_to_slug(uuid4())
    prod_id_list = [p.meta["id"] for p in prod_list]
    item_list = [{"item_id": prod_id, "amount": 2} for prod_id in prod_id_list]

    response = requests.put(
        domain_url + "/api/order/insert",
        json={"user_slug": user_slug, "item_list": item_list}
    )

    data = response.json()
    ErrorSchema().load(data)
    assert response.status_code == 401
