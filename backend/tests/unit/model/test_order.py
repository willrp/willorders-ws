import pytest
from uuid import uuid4
from sqlalchemy.exc import IntegrityError, DataError

from backend.model import Product, Order, OrderProduct
from backend.tests.factories import ProductFactory, OrderFactory
from backend.util.slug import uuid_to_slug
from backend.errors.request_error import SlugDecodeError


@pytest.fixture(scope="function", autouse=True)
def factory_session(db_session):
    ProductFactory._meta.sqlalchemy_session = db_session
    OrderFactory._meta.sqlalchemy_session = db_session


def test_order_select(db_session):
    assert db_session.query(Order).one_or_none() is None

    OrderFactory.create_batch(5)
    db_session.commit()

    assert len(db_session.query(Order).all()) == 5


def test_order_insert(db_session):
    obj = OrderFactory.create()
    db_session.commit()

    assert db_session.query(Order).one()
    assert db_session.query(Order).filter(Order.id == obj.id).one()
    assert db_session.query(Order).filter(Order.uuid == obj.uuid).one()
    assert db_session.query(Order).filter(Order.user_uuid == obj.user_uuid).one()

    user_slug = uuid_to_slug(uuid4())
    obj = OrderFactory.create(user_slug=user_slug)
    db_session.commit()
    assert uuid_to_slug(obj.user_uuid) == user_slug


def test_order_insert_same_uuid(db_session):
    test_uuid = uuid4()
    with pytest.raises(IntegrityError):
        OrderFactory.create(uuid=test_uuid)
        db_session.commit()
        OrderFactory.create(uuid=test_uuid)
        db_session.commit()


def test_order_insert_invalid_user_slug(db_session):
    with pytest.raises(SlugDecodeError):
        OrderFactory.create(user_slug="churros")


def test_order_update_set_items(db_session):
    obj = OrderFactory.create()
    db_session.commit()

    assert not obj.items
    assert db_session.query(Product).one_or_none() is None
    assert db_session.query(OrderProduct).one_or_none() is None

    prod_list = ProductFactory.create_batch(5)

    for p in prod_list:
        OrderProduct(order=obj, product=p, amount=2)

    db_session.commit()

    assert len(obj.items) == 5
    assert type(obj.items[0]) == OrderProduct

    assert len(db_session.query(Product).all()) == 5
    assert len(db_session.query(OrderProduct).all()) == 5

    obj = OrderFactory.create()
    for p in prod_list[0:3]:
        OrderProduct(order=obj, product=p, amount=1)

    db_session.commit()

    assert len(obj.items) == 3
    assert type(obj.items[0]) == OrderProduct

    assert len(db_session.query(Product).all()) == 5
    assert len(db_session.query(OrderProduct).all()) == 8


def test_order_delete(db_session):
    obj = OrderFactory.create()
    db_session.commit()

    assert not obj.items
    assert db_session.query(Product).one_or_none() is None
    assert db_session.query(OrderProduct).one_or_none() is None

    prod_list = ProductFactory.create_batch(5)

    for p in prod_list:
        OrderProduct(order=obj, product=p, amount=2)

    db_session.commit()

    assert len(obj.items) == 5
    assert type(obj.items[0]) == OrderProduct
    assert len(db_session.query(Product).all()) == 5
    assert len(db_session.query(OrderProduct).all()) == 5

    result = db_session.query(Order).filter(Order.id == obj.id).delete()
    assert result == 1
    db_session.commit()

    assert db_session.query(Order).one_or_none() is None
    assert len(db_session.query(Product).all()) == 5
    assert db_session.query(OrderProduct).one_or_none() is None


def test_order_delete_non_existant(db_session):
    result = db_session.query(Order).filter(Order.id == 1).delete()
    db_session.commit()

    assert result == 0


def test_order_dict(db_session):
    obj = OrderFactory.create()
    db_session.commit()
    obj_dict = obj.to_dict()
    for key in ["slug", "user_slug", "created_at", "updated_at", "product_types", "items_amount"]:
        assert key in obj_dict

    assert len(obj_dict.keys()) == 6
    assert obj_dict["product_types"] == 0
    assert obj_dict["items_amount"] == 0

    prod_list = ProductFactory.create_batch(5)

    for p in prod_list:
        OrderProduct(order=obj, product=p, amount=2)

    db_session.commit()
    obj_dict = obj.to_dict()

    assert obj_dict["product_types"] == 5
    assert obj_dict["items_amount"] == 10

    item = obj.items[0]
    item_dict = item.to_dict()
    for key in ["item_id", "amount"]:
        assert key in item_dict

    assert item_dict["item_id"] == item.product.es_id
    assert item_dict["amount"] == 2
