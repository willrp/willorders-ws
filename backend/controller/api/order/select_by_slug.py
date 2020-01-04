import os
from flask_restplus import Namespace, Resource
from flask import current_app as app
from requests import post

from backend.service import OrderService
from backend.util.response.order import OrderResponse
from backend.util.response.error import ErrorResponse
from backend.controller import ErrorHandler, auth_required


selectBySlugNS = Namespace("Order", description="Order related operations.")

RESPONSEMODEL = OrderResponse.get_model(selectBySlugNS, "OrderResponse")
ERRORMODEL = ErrorResponse.get_model(selectBySlugNS, "ErrorResponse")


@selectBySlugNS.route("/<string:user_slug>/<string:order_slug>", strict_slashes=False)
class SelectBySlugController(Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__orderservice = OrderService()

    @auth_required()
    @selectBySlugNS.doc(security=["token"])
    @selectBySlugNS.param("user_slug", description="User slug", _in="path", required=True)
    @selectBySlugNS.param("order_slug", description="Order slug", _in="path", required=True)
    @selectBySlugNS.response(200, "Success", RESPONSEMODEL)
    @selectBySlugNS.response(400, "Bad Request", ERRORMODEL)
    @selectBySlugNS.response(401, "Unauthorized", ERRORMODEL)
    @selectBySlugNS.response(404, "Not Found", ERRORMODEL)
    @selectBySlugNS.response(500, "Unexpected Error", ERRORMODEL)
    @selectBySlugNS.response(502, "Error while accessing the gateway server", ERRORMODEL)
    @selectBySlugNS.response(504, "No response from gateway server", ERRORMODEL)
    def get(self, user_slug, order_slug):
        """Order information."""
        try:
            order = self.__orderservice.select_by_slug(user_slug=user_slug, order_slug=order_slug)
            items_list = [item.to_dict() for item in order.items]
            items_info = {"item_list": items_list}

            url = app.config["WILLSTORES_WS"]
            headers = {"Authorization": "Bearer %s" % os.getenv("ACCESS_TOKEN")}
            req = post("%s/api/product/list" % (url), headers=headers, json=items_info)
            req.raise_for_status()
            result = req.json()

            for item in items_list:
                product = next(p for p in result["products"] if p["id"] == item["item_id"])
                product["amount"] = item["amount"]

            jsonsend = OrderResponse.marshall_json(dict(order.to_dict(), **result))
            return jsonsend
        except Exception as error:
            return ErrorHandler(error).handle_error()
