import os
import asyncio
from flask_restplus import Namespace, Resource
from flask import current_app as app
from requests import Session

from backend.service import OrderService
from backend.util.request.user_orders import UserOrdersRequest
from backend.util.response.user_orders import UserOrdersResponse
from backend.util.response.error import ErrorResponse
from backend.controller import ErrorHandler, auth_required


selectByUserNS = Namespace("Order", description="Order related operations.")

REQUESTMODEL = UserOrdersRequest.get_model(selectByUserNS, "UserOrdersRequest")
RESPONSEMODEL = UserOrdersResponse.get_model(selectByUserNS, "UserOrdersResponse")
ERRORMODEL = ErrorResponse.get_model(selectByUserNS, "ErrorResponse")


async def fetch_order(session, url, order):
    req = session.post("%s/api/product/total" % (url), json={"item_list": [item.to_dict() for item in order.items]})
    req.raise_for_status()
    processed_order = order.to_dict()
    processed_order.update(req.json())
    return processed_order


async def process_orders(session, url, user_info):
    orders = await asyncio.gather(*[fetch_order(session, url, order) for order in user_info["orders"]])
    user_info["orders"] = orders
    return user_info


@selectByUserNS.route("/user/<string:user_slug>", strict_slashes=False)
class SelectByUserController(Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__orderservice = OrderService()

    @auth_required()
    @selectByUserNS.doc(security=["token"])
    @selectByUserNS.param("user_slug", description="User Slug", _in="path", required=True)
    @selectByUserNS.param("payload", description="Optional", _in="body", required=False)
    @selectByUserNS.expect(REQUESTMODEL)
    @selectByUserNS.response(200, "Success", RESPONSEMODEL)
    @selectByUserNS.response(204, "No Content", ERRORMODEL)
    @selectByUserNS.response(400, "Bad Request", ERRORMODEL)
    @selectByUserNS.response(401, "Unauthorized", ERRORMODEL)
    @selectByUserNS.response(500, "Unexpected Error", ERRORMODEL)
    @selectByUserNS.response(502, "Error while accessing the gateway server", ERRORMODEL)
    @selectByUserNS.response(504, "No response from gateway server", ERRORMODEL)
    def post(self, user_slug):
        """Orders for a user."""
        try:
            in_data = UserOrdersRequest.parse_json()
            user_info = self.__orderservice.select_by_user_slug(user_slug=user_slug, **in_data)

            url = app.config["WILLSTORES_WS"]
            with Session() as sess:
                sess.headers["Authorization"] = "Bearer %s" % os.getenv("ACCESS_TOKEN")
                processed_user_info = asyncio.run(process_orders(sess, url, user_info))

            jsonsend = UserOrdersResponse.marshall_json(processed_user_info)
            return jsonsend
        except Exception as error:
            return ErrorHandler(error).handle_error()
