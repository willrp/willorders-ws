from factory.alchemy import SQLAlchemyModelFactory

from ...model import OrderProduct


class OrderProductFactory(SQLAlchemyModelFactory):
    class Meta:
        model = OrderProduct
