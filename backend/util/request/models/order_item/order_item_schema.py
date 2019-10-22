from marshmallow import Schema, fields, validates
from backend.errors.request_error import ValidationError


class OrderItemSchema(Schema):
    item_id = fields.String(required=True)
    amount = fields.Integer(required=True)

    @validates("amount")
    def validate_amount(self, data):
        if data <= 0:
            raise ValidationError("order item amount must be a natural positive number")
