import pytest
import re
import os
from dotenv import load_dotenv, find_dotenv
from elasticsearch_dsl import Index
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend import create_app
from backend.model import Product, Order
from webservices.willstores.backend.dao.es import ES
from webservices.willstores.backend.tests.factories import ProductFactory


test_factory = sessionmaker()


@pytest.fixture(scope="session")
def domain_ip():
    load_dotenv(find_dotenv())
    return os.getenv("TEST_DOMAIN_IP")


@pytest.fixture(scope="session")
def database_url(domain_ip):
    test_db = os.getenv("TEST_DATABASE_URL")
    TEST_DATABASE_URL = re.sub("TEST_DOMAIN_IP", domain_ip, test_db)
    return TEST_DATABASE_URL


@pytest.fixture(scope="session")
def flask_app(domain_ip):
    app = create_app(flask_env="test")
    app.config["WILLSTORES_WS"] = "http://" + domain_ip + ":8001"
    return app


@pytest.fixture(scope="session")
def db_connection(database_url):
    engine = create_engine(database_url)
    connection = engine.connect()
    yield connection
    connection.close()


@pytest.fixture(scope="function")
def db_session(db_connection):
    transaction = db_connection.begin()
    session = test_factory(bind=db_connection)
    yield session
    session.close()
    transaction.rollback()


@pytest.fixture(scope="session")
def db_perm_connection(database_url):
    engine = create_engine(database_url)
    test_factory.configure(bind=engine)
    connection = engine.connect()
    yield connection
    connection.close()


@pytest.fixture(scope="function")
def db_perm_session(db_perm_connection):
    session = test_factory(bind=db_perm_connection)
    yield session
    session.query(Order).delete()
    session.query(Product).delete()
    session.commit()
    session.close()


@pytest.fixture(scope="session", autouse=True)
def prod_list(domain_ip):
    os.environ["ES_URL"] = "http://%s:9200" % domain_ip
    es_object = ES()
    prod_list = ProductFactory.create_batch(5)
    [prod_obj.save(using=es_object.connection) for prod_obj in prod_list]
    Index("store", using=es_object.connection).refresh()
    yield prod_list
    Index("store", using=es_object.connection).delete()


@pytest.fixture(scope="session", autouse=True)
def setup_teardown(database_url, db_perm_connection):
    os.environ["DATABASE_URL"] = database_url
    session = test_factory(bind=db_perm_connection)
    session.query(Order).delete()
    session.query(Product).delete()
    session.commit()
    session.close()
    create_app(flask_env="test").test_client().post("test")
    yield
    session = test_factory(bind=db_perm_connection)
    session.query(Order).delete()
    session.query(Product).delete()
    session.commit()
    session.close()


@pytest.fixture(scope="session")
def jwt_test_token():
    return os.getenv("ACCESS_TOKEN")
