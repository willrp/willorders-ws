import os
from flask_restplus import Namespace, Resource
from flask import current_app as app
from requests import post

from backend.service import OrderService
from backend.util.request.order_insert import OrderInsertRequest
from backend.util.response.error import ErrorResponse
from backend.controller import ErrorHandler, auth_required


insertNS = Namespace("Order", description="Order related operations.")

REQUESTMODEL = OrderInsertRequest.get_model(insertNS, "OrderInsertRequest")
ERRORMODEL = ErrorResponse.get_model(insertNS, "ErrorResponse")


@insertNS.route("/insert", strict_slashes=False)
class InsertController(Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__orderservice = OrderService()

    @auth_required()
    @insertNS.doc(security=["token"])
    @insertNS.expect(REQUESTMODEL)
    @insertNS.response(201, description="Created", mask=False)
    @insertNS.response(400, "Bad Request", ERRORMODEL)
    @insertNS.response(401, "Unauthorized", ERRORMODEL)
    @insertNS.response(500, "Unexpected Error", ERRORMODEL)
    @insertNS.response(502, "Error while accessing the gateway server", ERRORMODEL)
    @insertNS.response(504, "No response from gateway server", ERRORMODEL)
    def put(self):
        """Order insert."""
        try:
            in_data = OrderInsertRequest.parse_json()

            url = app.config["WILLSTORES_WS"]
            headers = {"Authorization": "Bearer %s" % os.getenv("ACCESS_TOKEN")}
            req = post("%s/api/product/total" % (url), headers=headers, json={"item_list": in_data["item_list"]})
            req.raise_for_status()

            self.__orderservice.insert(**in_data)
            return {}, 201
        except Exception as error:
            return ErrorHandler(error).handle_error()
