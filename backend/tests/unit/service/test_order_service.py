import pytest
from unittest.mock import MagicMock
from datetime import date, timedelta
from sqlalchemy.exc import DataError, DatabaseError

from backend.service import OrderService
from backend.errors.no_content_error import NoContentError
from backend.errors.not_found_error import NotFoundError
from backend.errors.request_error import SlugDecodeError


@pytest.fixture(scope="function", autouse=True)
def service_mocker(mocker, service_init_mock):
    mocker.patch("backend.service.OrderService.__init__", new=service_init_mock)


@pytest.fixture(scope="function")
def service():
    service = OrderService()
    return service


def test_order_service_select_by_slug(service):
    service.db_session.query().filter().one_or_none.return_value = MagicMock(autospec=True)
    service.select_by_slug(slug="WILLrogerPEREIRAslugBR")

    service.db_session.query().filter().one_or_none.return_value = None
    with pytest.raises(NotFoundError):
        service.select_by_slug(slug="WILLrogerPEREIRAslugBR")

    with pytest.raises(SlugDecodeError):
        service.select_by_slug(slug="churros")


def test_order_service_select_by_user_slug(service):
    service.db_session.query().filter().order_by().count.return_value = 10
    service.db_session.query().filter().order_by().limit().offset().all.return_value = [MagicMock(autospec=True) for i in range(10)]
    result = service.select_by_user_slug(user_slug="WILLrogerPEREIRAslugBR")

    assert len(result["orders"]) == 10
    assert result["total"] == 10
    assert result["pages"] == 1

    result = service.select_by_user_slug(user_slug="WILLrogerPEREIRAslugBR", page_size=3)

    assert result["pages"] == 4

    service.db_session.query().filter().filter().order_by().count.return_value = 5
    service.db_session.query().filter().filter().order_by().limit().offset().all.return_value = [MagicMock(autospec=True) for i in range(5)]

    result = service.select_by_user_slug(user_slug="WILLrogerPEREIRAslugBR", datespan={"start": date.today() - timedelta(days=1), "end": date.today() + timedelta(days=1)})

    assert len(result["orders"]) == 5
    assert result["total"] == 5
    assert result["pages"] == 1

    service.db_session.query().filter().order_by().count.return_value = 0
    service.db_session.query().filter().order_by().limit().offset().all.return_value = []

    with pytest.raises(NoContentError):
        service.select_by_user_slug(user_slug="WILLrogerPEREIRAslugBR")

    with pytest.raises(SlugDecodeError):
        result = service.select_by_user_slug(user_slug="churros")

    with pytest.raises(TypeError):
        result = service.select_by_user_slug(user_slug="WILLrogerPEREIRAslugBR", datespan={"start": "will", "end": "roger"})

    service.db_session.query().filter().order_by().limit().offset().all.side_effect = DataError("statement", "params", "DETAIL:  orig\n")

    with pytest.raises(DataError):
        service.select_by_user_slug(user_slug="WILLrogerPEREIRAslugBR")


def test_order_service_insert(service):
    service.db_session.query().filter().one_or_none.return_value = None

    result = service.insert(user_slug="WILLrogerPEREIRAslugBR", item_list=[{"item_id": "id", "amount": 2}])
    assert result is True

    service.db_session.query().filter().one_or_none.return_value = MagicMock(autospec=True)

    result = service.insert(user_slug="WILLrogerPEREIRAslugBR", item_list=[{"item_id": "id", "amount": 2}])
    assert result is True

    with pytest.raises(SlugDecodeError):
        result = service.insert(user_slug="churros", item_list=[{"item_id": "id", "amount": 2}])

    service.db_session.query().filter().one_or_none.side_effect = DatabaseError("statement", "params", "DETAIL:  orig\n"),

    with pytest.raises(DatabaseError):
        service.insert(user_slug="WILLrogerPEREIRAslugBR", item_list=[{"item_id": "id", "amount": 2}])


def test_order_service_delete(service):
    service.db_session.query().filter().delete.return_value = True
    result = service.delete(slug="WILLrogerPEREIRAslugBR")
    assert result is True

    service.db_session.query().filter().delete.return_value = False
    with pytest.raises(NotFoundError):
        service.delete(slug="WILLrogerPEREIRAslugBR")

    service.db_session.query().filter().delete.side_effect = DatabaseError("statement", "params", "DETAIL:  orig\n"),

    with pytest.raises(DatabaseError):
        service.delete(slug="WILLrogerPEREIRAslugBR")
