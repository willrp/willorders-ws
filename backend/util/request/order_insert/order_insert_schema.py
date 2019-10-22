from marshmallow import Schema, fields, validates

from backend.errors.request_error import ValidationError
from ..models.order_item import OrderItemSchema


class OrderInsertSchema(Schema):
    user_slug = fields.String(required=True)
    item_list = fields.List(fields.Nested(OrderItemSchema, description="Must have unique item_id values", required=True), required=True)

    @validates("item_list")
    def validate_item_list(self, data):
        item_id_list = [item["item_id"] for item in data]
        if len(item_id_list) != len(set(item_id_list)):
            raise ValidationError("item_list must have unique item_id values")
