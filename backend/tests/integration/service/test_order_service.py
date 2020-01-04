import pytest
from datetime import date, timedelta
from sqlalchemy.exc import DataError
from uuid import uuid4

from backend.service import OrderService
from backend.model import Order, Product, OrderProduct
from backend.tests.factories import OrderFactory, ProductFactory
from backend.errors.no_content_error import NoContentError
from backend.errors.not_found_error import NotFoundError
from backend.util.slug import uuid_to_slug


@pytest.fixture(scope="function", autouse=True)
def factory_session(db_perm_session):
    OrderFactory._meta.sqlalchemy_session = db_perm_session
    ProductFactory._meta.sqlalchemy_session = db_perm_session


@pytest.fixture(scope="session")
def service():
    service = OrderService()
    return service


def test_order_service_select_by_slug(service, db_perm_session):
    user_slug = uuid_to_slug(uuid4())
    order_slug = uuid_to_slug(uuid4())

    with pytest.raises(NotFoundError):
        service.select_by_slug(user_slug=user_slug, order_slug=order_slug)

    obj = OrderFactory.create()
    db_perm_session.commit()

    order_slug = obj.uuid_slug
    user_slug = obj.user_slug
    result = service.select_by_slug(user_slug=user_slug, order_slug=order_slug)
    assert type(result) is Order

    user_slug = uuid_to_slug(uuid4())

    with pytest.raises(NotFoundError):
        service.select_by_slug(user_slug=user_slug, order_slug=order_slug)


def test_order_service_select_by_user_slug(service, db_perm_session):
    user_slug = uuid_to_slug(uuid4())

    with pytest.raises(NoContentError):
        service.select_by_user_slug(user_slug=user_slug)

    OrderFactory.create_batch(5, user_slug=user_slug)
    db_perm_session.commit()

    result = service.select_by_user_slug(user_slug=user_slug)
    assert len(result["orders"]) == 5
    assert type(result["orders"][0]) is Order
    assert result["total"] == 5
    assert result["pages"] == 1

    datenow = date.today()
    spanstart = datenow - timedelta(days=1)
    spanend = datenow + timedelta(days=1)
    result = service.select_by_user_slug(user_slug=user_slug, datespan={"start": spanstart, "end": spanend})
    assert len(result["orders"]) == 5
    assert type(result["orders"][0]) is Order
    assert result["total"] == 5
    assert result["pages"] == 1

    with pytest.raises(NoContentError):
        result = service.select_by_user_slug(user_slug=user_slug, datespan={"start": spanend, "end": spanstart})

    with pytest.raises(NoContentError):
        spanstart = datenow - timedelta(days=5)
        spanend = datenow - timedelta(days=4)
        result = service.select_by_user_slug(user_slug=user_slug, datespan={"start": spanstart, "end": spanend})


def test_order_service_select_by_user_slug_pages(service, db_perm_session):
    user_slug = uuid_to_slug(uuid4())
    OrderFactory.create_batch(22, user_slug=user_slug)
    db_perm_session.commit()

    result = service.select_by_user_slug(user_slug=user_slug, page=1, page_size=10)

    assert result is not None
    assert len(result["orders"]) == 10
    assert type(result["orders"][0]) is Order
    assert result["total"] == 22
    assert result["pages"] == 3

    result = service.select_by_user_slug(user_slug=user_slug, page=5, page_size=5)

    assert result is not None
    assert len(result["orders"]) == 2
    assert type(result["orders"][0]) is Order
    assert result["total"] == 22
    assert result["pages"] == 5

    with pytest.raises(NoContentError):
        service.select_by_user_slug(user_slug=user_slug, page=6, page_size=5)

    with pytest.raises(ZeroDivisionError):
        service.select_by_user_slug(user_slug=user_slug, page=1, page_size=0)

    with pytest.raises(DataError):
        service.select_by_user_slug(user_slug=user_slug, page=0, page_size=5)


def test_order_service_insert(service, db_perm_session):
    user_slug = uuid_to_slug(uuid4())

    with pytest.raises(NoContentError):
        service.select_by_user_slug(user_slug=user_slug)

    item_list = [{"item_id": str(uuid_to_slug(uuid4())), "amount": 2} for i in range(2)]
    ins = service.insert(user_slug=user_slug, item_list=item_list)

    assert ins is True
    assert len(db_perm_session.query(Order).all()) == 1
    assert len(db_perm_session.query(Product).all()) == 2
    assert len(db_perm_session.query(OrderProduct).all()) == 2

    result = service.select_by_user_slug(user_slug=user_slug)

    assert len(result["orders"]) == 1
    order_info = result["orders"][0].to_dict()
    assert order_info["product_types"] == 2
    assert order_info["items_amount"] == 4

    product_list = ProductFactory.create_batch(5)
    db_perm_session.commit()

    item_list = [{"item_id": p.es_id, "amount": 3} for p in product_list]
    ins = service.insert(user_slug=user_slug, item_list=item_list)

    assert ins is True
    assert len(db_perm_session.query(Order).all()) == 2
    assert len(db_perm_session.query(Product).all()) == 7
    assert len(db_perm_session.query(OrderProduct).all()) == 7

    result = service.select_by_user_slug(user_slug=user_slug)

    assert len(result["orders"]) == 2
    order_info = result["orders"][0].to_dict()
    assert order_info["product_types"] == 5
    assert order_info["items_amount"] == 15

    user_slug = uuid_to_slug(uuid4())
    ins = service.insert(user_slug=user_slug, item_list=item_list)

    assert ins is True
    assert len(db_perm_session.query(Order).all()) == 3
    assert len(db_perm_session.query(Product).all()) == 7
    assert len(db_perm_session.query(OrderProduct).all()) == 12

    result = service.select_by_user_slug(user_slug=user_slug)

    assert len(result["orders"]) == 1


def test_order_service_delete(service, db_perm_session):
    assert len(db_perm_session.query(Order).all()) == 0

    with pytest.raises(NotFoundError):
        service.delete(user_slug="WILLrogerPEREIRAslugBR", order_slug="WILLrogerPEREIRAslugBR")

    user_slug = uuid_to_slug(uuid4())
    obj = OrderFactory.create(user_slug=user_slug)
    db_perm_session.commit()

    prod_list = ProductFactory.create_batch(5)

    for p in prod_list:
        OrderProduct(order=obj, product=p, amount=2)    

    db_perm_session.commit()

    assert len(db_perm_session.query(Order).all()) == 1
    assert len(db_perm_session.query(Product).all()) == 5
    assert len(db_perm_session.query(OrderProduct).all()) == 5

    fake_user_slug = uuid_to_slug(uuid4())

    with pytest.raises(NotFoundError):
        service.delete(user_slug=fake_user_slug, order_slug=obj.uuid_slug)

    assert len(db_perm_session.query(Order).all()) == 1
    assert len(db_perm_session.query(Product).all()) == 5
    assert len(db_perm_session.query(OrderProduct).all()) == 5

    delete = service.delete(user_slug=user_slug, order_slug=obj.uuid_slug)

    assert delete is True

    assert len(db_perm_session.query(Order).all()) == 0
    assert len(db_perm_session.query(Product).all()) == 5
    assert len(db_perm_session.query(OrderProduct).all()) == 0
