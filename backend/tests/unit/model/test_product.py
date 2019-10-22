import pytest
from uuid import uuid4
from sqlalchemy.exc import IntegrityError

from backend.model import Product
from backend.tests.factories import ProductFactory


@pytest.fixture(scope="function", autouse=True)
def factory_session(db_session):
    ProductFactory._meta.sqlalchemy_session = db_session


def test_product_select(db_session):
    assert db_session.query(Product).one_or_none() is None

    ProductFactory.create_batch(5)
    db_session.commit()

    assert len(db_session.query(Product).all()) == 5


def test_product_insert(db_session):
    obj = ProductFactory.create()
    db_session.commit()

    assert db_session.query(Product).one()
    assert db_session.query(Product).filter(Product.id == obj.id).one()
    assert db_session.query(Product).filter(Product.uuid == obj.uuid).one()
    assert db_session.query(Product).filter(Product.es_id == obj.es_id).one()

    test_uuid = uuid4()
    obj = ProductFactory.create(uuid=test_uuid)
    db_session.commit()
    assert obj.uuid == test_uuid


def test_product_insert_same_uuid(db_session):
    test_uuid = uuid4()
    with pytest.raises(IntegrityError):
        ProductFactory.create(uuid=test_uuid)
        db_session.commit()
        ProductFactory.create(uuid=test_uuid)
        db_session.commit()


def test_product_insert_es_id(db_session):
    test_es_id = "asdfasdf"
    with pytest.raises(IntegrityError):
        ProductFactory.create(es_id=test_es_id)
        db_session.commit()
        ProductFactory.create(es_id=test_es_id)
        db_session.commit()
