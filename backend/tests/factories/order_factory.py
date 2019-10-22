from factory import Sequence
from factory.alchemy import SQLAlchemyModelFactory
from uuid import uuid4

from ...model import Order
from ...util.slug import uuid_to_slug


class OrderFactory(SQLAlchemyModelFactory):
    user_slug = Sequence(lambda n: uuid_to_slug(uuid4()))

    class Meta:
        model = Order
