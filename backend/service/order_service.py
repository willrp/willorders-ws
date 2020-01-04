from typing import List
from math import ceil
from sqlalchemy import and_
from sqlalchemy.exc import DataError, DatabaseError
from datetime import timedelta

from backend.model import Order, Product, OrderProduct
from backend.dao.postgres_db import DBSession
from backend.util.slug import slug_to_uuid
from backend.errors.no_content_error import NoContentError
from backend.errors.not_found_error import NotFoundError


class OrderService(object):
    def __init__(self):
        self.db_session = DBSession()

    def select_by_slug(self, user_slug: str, order_slug: str) -> Order:
        user_uuid = slug_to_uuid(user_slug)
        uuid = slug_to_uuid(order_slug)
        result = self.db_session.query(Order).filter(Order.user_uuid == user_uuid).filter(Order.uuid == uuid).one_or_none()

        if result is None:
            raise NotFoundError()

        return result

    def select_by_user_slug(self,  user_slug: str, page: int = 1, page_size: int = 10, datespan: dict = None) -> dict:
        try:
            user_uuid = slug_to_uuid(user_slug)
            search_query = self.db_session.query(Order).filter(Order.user_uuid == user_uuid)

            if datespan is not None:
                search_query = search_query.filter(and_(Order.updated_at >= datespan["start"], Order.updated_at < datespan["end"] + timedelta(days=1)))

            data = search_query.order_by(Order.updated_at.desc()).limit(page_size).offset((page - 1) * page_size).all()
            total = search_query.order_by(None).count()
            pages = ceil(total / page_size)

            if not data:
                raise NoContentError()

            return {
                "orders": data,
                "total": total,
                "pages": pages
            }
        except DataError:
            self.db_session.rollback()
            raise

    def insert(self, user_slug: str, item_list: List[dict]) -> bool:
        try:
            order = Order(user_slug=user_slug)
            self.db_session.add(order)
            for item in item_list:
                product = self.db_session.query(Product).filter(Product.es_id == item["item_id"]).one_or_none()
                if product is None:
                    product = Product(es_id=item["item_id"])
                    self.db_session.add(product)

                OrderProduct(order=order, product=product, amount=item["amount"])

            self.db_session.commit()
            return True
        except DatabaseError:
            self.db_session.rollback()
            raise

    def delete(self, user_slug: str, order_slug: str) -> bool:
        try:
            user_uuid = slug_to_uuid(user_slug)
            uuid = slug_to_uuid(order_slug)
            result = self.db_session.query(Order).filter(Order.user_uuid == user_uuid).filter(Order.uuid == uuid).delete()
            self.db_session.commit()
            if result == 0:
                raise NotFoundError()
            else:
                return True
        except DatabaseError:
            self.db_session.rollback()
            raise
