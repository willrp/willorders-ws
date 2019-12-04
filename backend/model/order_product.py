from sqlalchemy import Column, BigInteger, Integer, ForeignKey
from sqlalchemy.orm import relationship, backref

from ..dao.postgres_db import Base
from .order import Order
from .product import Product


class OrderProduct(Base):
    __tablename__ = "order_product"

    order_id = Column("order_id", BigInteger, ForeignKey("orders.id", onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)
    product_id = Column("product_id", BigInteger, ForeignKey("products.id", onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)
    amount = Column("amount", Integer, nullable=False)
    order = relationship("Order", backref=backref("order_link"))
    product = relationship("Product", backref=backref("product_link"))

    def __init__(self, order: Order, product: Product, amount: int) -> None:
        self.order: Order = order
        self.product: Product = product
        self.amount: int = amount

    def to_dict(self) -> dict:
        return {
            "item_id": self.product.es_id,
            "amount": self.amount
        }
