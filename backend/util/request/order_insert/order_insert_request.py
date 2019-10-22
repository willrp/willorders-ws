from flask import request
from flask_restplus import fields

from ..models.order_item import OrderItemRequest
from .order_insert_schema import OrderInsertSchema


class OrderInsertRequest(object):
    @staticmethod
    def get_model(api, name):
        return api.model(
            name,
            {
                "user_slug": fields.String(description="User slug.", required=True),
                "item_list": fields.List(fields.Nested(OrderItemRequest.get_model(api, "OrderItemRequest"), required=True), required=True)
            }
        )

    @staticmethod
    def parse_json():
        jsonrecv = request.get_json()
        schema = OrderInsertSchema()
        in_data = schema.load(jsonrecv)
        return in_data
