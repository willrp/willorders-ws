from datetime import datetime
from sqlalchemy import Column, BigInteger, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4

from ..dao.postgres_db import Base
from ..util.slug import uuid_to_slug, slug_to_uuid


class Order(Base):
    __tablename__ = "orders"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uuid = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid4)
    user_uuid = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    items = relationship("OrderProduct", back_populates="order")

    def __init__(self, user_slug: str, uuid: UUID = None) -> None:
        self.user_uuid: UUID = slug_to_uuid(user_slug)
        self.uuid: UUID = uuid

    @property
    def uuid_slug(self):
        return uuid_to_slug(self.uuid)

    @property
    def user_slug(self):
        return uuid_to_slug(self.user_uuid)

    def to_dict(self) -> dict:
        return {
            "slug": self.uuid_slug,
            "user_slug": self.user_slug,
            "created_at": str(self.created_at),
            "updated_at": str(self.updated_at),
            "product_types": len(self.items),
            "items_amount": sum([item.amount for item in self.items])
        }
