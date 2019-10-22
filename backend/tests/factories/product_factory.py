from factory import Sequence
from factory.alchemy import SQLAlchemyModelFactory

from ...model import Product


class ProductFactory(SQLAlchemyModelFactory):
    es_id = Sequence(lambda n: "prodid%s" % n)

    class Meta:
        model = Product
